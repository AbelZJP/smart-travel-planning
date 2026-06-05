from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from typing import List, Dict, Any
from app.config import settings
from app.mcp.amap_client import AmapClient

amap = AmapClient()

PREFERENCE_KEYWORDS = {
    "nature": "自然风光",
    "history": "历史文化",
    "food": "美食购物",
    "family": "亲子休闲",
}


@tool
async def search_destination_attractions(
    preference: str, city: str
) -> List[Dict[str, Any]]:
    """搜索目的地景点。preference 可选: 自然风光/历史文化/美食购物/亲子休闲"""
    keyword = PREFERENCE_KEYWORDS.get(preference, preference)
    types_map = {
        "自然风光": "风景名胜|公园|自然景观|山|湖|海滩|森林公园",
        "历史文化": "博物馆|古迹|寺庙|名人故居|历史建筑|纪念馆",
        "美食购物": "美食街|步行街|特色餐厅|购物中心|夜市",
        "亲子休闲": "游乐园|动物园|水族馆|科技馆|植物园|主题公园",
    }
    types = types_map.get(keyword, "风景名胜")
    results = await amap.search_poi(keywords=keyword, city=city, types=types, offset=10)
    return [
        {
            "name": p.get("name"),
            "lng": float(p.get("location", "0,0").split(",")[0]),
            "lat": float(p.get("location", "0,0").split(",")[1]),
            "rating": float(p.get("biz_ext", {}).get("rating", 0)) or 3.5,
            "category": p.get("type", ""),
            "address": p.get("address", ""),
        }
        for p in results
    ]


ATTRACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """你是一个景点搜索专家。根据用户的旅行偏好和目的地，搜索合适的景点。

要求：
1. 每种偏好至少搜索一次
2. 根据评分和知名度筛选推荐景点
3. 估算每个景点的建议游玩时长(hours)和门票价格(元)
4. 返回景点列表，格式: [{{"name": "...", "lng": ..., "lat": ..., "rating": ..., "suggested_duration_h": ..., "estimated_ticket": ...}}, ...]
5. 至少返回 days*3 个景点，确保足够的天数分配""",
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


async def run_attraction_agent(
    destination: str,
    days: int,
    preferences: List[str],
) -> List[Dict[str, Any]]:
    """运行景点搜索 Agent"""
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.3,
    )
    tools = [search_destination_attractions]
    agent = create_tool_calling_agent(llm, tools, ATTRACTION_PROMPT)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=8)

    pref_labels = [PREFERENCE_KEYWORDS.get(p, p) for p in preferences]
    input_text = f"目的地: {destination}，出行天数: {days}天，旅行偏好: {', '.join(pref_labels)}。请为每个偏好搜索景点，然后综合推荐。"

    result = await executor.ainvoke({"input": input_text})
    output = result.get("output", "[]")
    import json
    import re

    match = re.search(r"\[.*\]", output, re.DOTALL)
    if match:
        try:
            attractions = json.loads(match.group())
            return attractions
        except json.JSONDecodeError:
            pass
    return []
