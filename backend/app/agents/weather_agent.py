from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.config import settings
from app.mcp.amap_client import AmapClient

amap = AmapClient()


@tool
async def fetch_weather(city: str) -> Dict[str, Any]:
    """获取城市天气预报（未来7天）"""
    data = await amap.get_weather(city, extensions="all")
    forecasts = data.get("forecasts", [])
    if not forecasts:
        return {"city": city, "forecasts": []}
    daily = forecasts[0].get("casts", [])
    return {
        "city": forecasts[0].get("city", city),
        "forecasts": [
            {
                "date": d.get("date"),
                "day_weather": d.get("dayweather"),
                "night_weather": d.get("nightweather"),
                "day_temp": int(d.get("daytemp", 0)),
                "night_temp": int(d.get("nighttemp", 0)),
                "day_wind": d.get("daywind", ""),
                "day_power": d.get("daypower", ""),
            }
            for d in daily
        ],
    }


WEATHER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """你是一个天气分析专家。根据天气数据，为旅行提供建议。

对每一天的天气做分析，输出格式:
[
  {{
    "date": "YYYY-MM-DD",
    "day_weather": "晴",
    "night_weather": "多云",
    "high_temp": 30,
    "low_temp": 22,
    "wind": "东北风3级",
    "rain_probability": 0.1,
    "clothing_advice": "建议穿短袖，带一件薄外套",
    "travel_advice": "天气晴好，非常适合户外活动",
    "suitable": true
  }},
  ...
]""",
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


async def run_weather_agent(
    destination: str, start_date: str, days: int
) -> List[Dict[str, Any]]:
    """运行天气查询 Agent"""
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.1,
    )
    tools = [fetch_weather]
    agent = create_tool_calling_agent(llm, tools, WEATHER_PROMPT)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=3)

    start = datetime.strptime(start_date, "%Y-%m-%d")
    date_range = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

    input_text = f"目的地: {destination}，出发日期: {start_date}，出行天数: {days}天，需要天气的日期: {', '.join(date_range)}。请先获取天气数据，然后分析每天的出行建议。"

    result = await executor.ainvoke({"input": input_text})
    output = result.get("output", "[]")

    import json
    import re
    match = re.search(r"\[.*\]", output, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return []
