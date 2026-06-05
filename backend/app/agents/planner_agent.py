from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Any
from app.config import settings
from app.utils.budget import calculate_budget_allocation, TIER_CONFIG

PLANNER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """你是一个资深的旅行规划师。你需要根据景点列表、天气数据、酒店候选和用户预算，生成三档完整行程方案。

## 输入数据:
- 用户需求: {user_input}
- 景点列表: {attractions}
- 天气数据: {weather}
- 酒店候选: {hotels}
- 预算分配: {budget_allocations}

## 规划原则:
1. 景点按地理分布分组，每天安排同区域的2-3个景点，减少路途时间
2. 上午安排户外景点（天气好时优先），下午安排室内或半室内景点
3. 每2-3个景点之间安排餐饮/休息
4. 酒店安排在当天最后一个景点附近
5. 交通方式根据预算档位选择：经济=公交地铁，舒适=打车+地铁，豪华=专车/租车
6. 城市间交通根据出行方式选择并计算费用
7. 严格控制预算，每档总花费不超过分配预算的110%

## 输出格式（严格的JSON，不要包含任何markdown代码块标记）:
{{
  "economy": {{
    "daily_plans": [
      {{
        "day": 1,
        "date": "YYYY-MM-DD",
        "attractions": [
          {{"name": "...", "lng": 120.14, "lat": 30.24, "duration": "3h", "ticket": 0, "time_slot": "09:00-12:00", "rating": 4.5, "category": "自然风光", "order": 1}}
        ],
        "hotel": {{"name": "...", "lng": ..., "lat": ..., "price": 180, "rating": 4.0, "address": "..."}},
        "meals": [{{"type": "lunch", "suggestion": "...", "estimated_cost": 30}}],
        "transport": [{{"from": "出发地", "to": "目的地", "mode": "高铁", "cost": 73}}],
        "daily_cost": 358,
        "route_coordinates": [
          {{"lng": 120.14, "lat": 30.24, "name": "西湖", "type": "attraction", "order": 1}},
          {{"lng": 120.12, "lat": 30.23, "name": "灵隐寺", "type": "attraction", "order": 2}},
          {{"lng": 120.16, "lat": 30.25, "name": "如家快捷", "type": "hotel", "order": 3}}
        ]
      }}
    ],
    "total_cost": 2380,
    "budget_usage": 79.3
  }},
  "comfort": {{...}},
  "luxury": {{...}}
}}

注意: route_coordinates 必须按游览顺序排列，包括景点和酒店，用于前端绘制路线图。""",
        ),
        ("human", "请生成三档行程方案"),
    ]
)


async def run_planner_agent(
    origin: str,
    destination: str,
    budget: float,
    intercity_mode: str,
    city_transit: str,
    days: int,
    preferences: List[str],
    start_date: str,
    attractions: List[Dict[str, Any]],
    weather: List[Dict[str, Any]],
    hotels: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """运行规划协调 Agent，生成三档方案"""
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.5,
    )

    budget_allocations = {}
    for tier in ["economy", "comfort", "luxury"]:
        budget_allocations[tier] = calculate_budget_allocation(
            budget, days, tier, intercity_mode
        )

    user_input = (
        f"出发地: {origin}，目的地: {destination}，总预算: {budget}元，"
        f"城市间交通: {intercity_mode}，市内交通: {city_transit}，"
        f"出行天数: {days}天，偏好: {preferences}，出发日期: {start_date}"
    )

    chain = PLANNER_PROMPT | llm
    response = await chain.ainvoke(
        {
            "user_input": user_input,
            "attractions": str(attractions),
            "weather": str(weather),
            "hotels": str(hotels),
            "budget_allocations": str(budget_allocations),
        }
    )

    import json
    import re

    content = response.content if hasattr(response, "content") else str(response)
    content = re.sub(r"^```(?:json)?\s*", "", content.strip())
    content = re.sub(r"\s*```$", "", content)

    try:
        plan = json.loads(content)
        return plan
    except json.JSONDecodeError:
        return {
            "economy": {"daily_plans": [], "total_cost": 0, "budget_usage": 0},
            "comfort": {"daily_plans": [], "total_cost": 0, "budget_usage": 0},
            "luxury": {"daily_plans": [], "total_cost": 0, "budget_usage": 0},
        }
