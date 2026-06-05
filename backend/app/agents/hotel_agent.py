from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from typing import List, Dict, Any
from app.config import settings
from app.mcp.amap_client import AmapClient

amap = AmapClient()


@tool
async def search_nearby_hotels(
    city: str, location: str, tier: str
) -> List[Dict[str, Any]]:
    """搜索指定位置附近的酒店。location 格式: "lng,lat"，tier: economy/comfort/luxury"""
    price_ranges = {"economy": 200, "comfort": 500, "luxury": 2000}
    max_price = price_ranges.get(tier, 500)
    results = await amap.search_around(
        location=location,
        keywords="酒店|宾馆|旅馆|精品酒店|度假酒店",
        types="住宿服务",
        radius=5000,
        offset=10,
    )
    hotels = []
    for p in results:
        biz = p.get("biz_ext", {})
        try:
            price = float(biz.get("cost", 0)) if biz.get("cost") else 300
        except (ValueError, TypeError):
            price = 300
        hotels.append(
            {
                "name": p.get("name"),
                "lng": float(p.get("location", "0,0").split(",")[0]),
                "lat": float(p.get("location", "0,0").split(",")[1]),
                "rating": float(biz.get("rating", 0)) or 3.5,
                "price_per_night": price,
                "address": p.get("address", ""),
            }
        )
    hotels = [h for h in hotels if h["price_per_night"] <= max_price]
    hotels.sort(key=lambda h: h.get("rating") or 0, reverse=True)
    return hotels[:8]


HOTEL_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """你是一个酒店推荐专家。根据旅行计划推荐住宿。

要求：
1. 在主要景点集中区域搜索酒店，减少交通时间
2. 根据预算档位筛选: economy≤200/晚, comfort 200-500/晚, luxury 500+/晚
3. 优先推荐评分高、距景点近的酒店
4. 为每个档位推荐1-2家酒店

返回格式:
{{
  "economy": [{{"name": "...", "lng": ..., "lat": ..., "price_per_night": ..., "rating": ...}}, ...],
  "comfort": [...],
  "luxury": [...]
}}""",
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


async def run_hotel_agent(
    destination: str,
    attractions: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """运行酒店推荐 Agent"""
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.3,
    )
    tools = [search_nearby_hotels]
    agent = create_tool_calling_agent(llm, tools, HOTEL_PROMPT)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=8)

    if attractions:
        center_lng = sum(a.get("lng", 0) for a in attractions) / len(attractions)
        center_lat = sum(a.get("lat", 0) for a in attractions) / len(attractions)
        center = f"{center_lng},{center_lat}"
    else:
        center = f"116.397,39.908"

    input_text = (
        f"目的地: {destination}，景点中心坐标: {center}，"
        f"景点列表: {attractions[:5]}。请为 economy/comfort/luxury 三个档位分别搜索推荐酒店。"
    )
    result = await executor.ainvoke({"input": input_text})
    output = result.get("output", "{}")

    import json
    import re
    match = re.search(r"\{.*\}", output, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"economy": [], "comfort": [], "luxury": []}
