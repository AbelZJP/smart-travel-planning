from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Any
from app.config import settings
from app.utils.budget import calculate_budget_allocation

PLANNER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """你是资深旅行规划师。生成 {tier_label} 档行程方案。

## 用户需求: {user_input}
## 景点: {attractions}
## 酒店候选: {hotels}

## ⚠️ 预算红线（绝对不能超）:
{budget_allocation}

## 档位参数:
- 酒店: ≤¥{hotel_budget}/晚
- 餐饮: ≤¥{meals_budget}/天
- 交通: {transit_mode}

## 要求:
1. ⚠️ 总花费必须 ≤ 预算红线，超出则选更便宜的景点/酒店/交通
2. 每天同区域 2-3 个景点
3. 景点间穿插餐饮
4. 酒店在当天最后景点附近

## 输出严格JSON（不要markdown）:
{{
  "daily_plans": [
    {{
      "day": 1,
      "date": "YYYY-MM-DD",
      "attractions": [
        {{"name": "...", "lng": 120.14, "lat": 30.24, "duration": "3h", "ticket": 0, "time_slot": "09:00-12:00", "rating": 4.5, "category": "自然风光", "order": 1}}
      ],
      "hotel": {{"name": "...", "lng": 0, "lat": 0, "price": 180, "rating": 4.0, "address": "..."}},
      "meals": [{{"type": "lunch", "suggestion": "...", "estimated_cost": 30}}],
      "transport": [{{"from": "出发地", "to": "目的地", "mode": "高铁", "cost": 73}}],
      "daily_cost": 358,
      "route_coordinates": [
        {{"lng": 120.14, "lat": 30.24, "name": "西湖", "type": "attraction", "order": 1}}
      ]
    }}
  ],
  "total_cost": 2380,
  "budget_usage": 79.3
}}

route_coordinates 按游览顺序排列景点+酒店，用于地图路线。""",
        ),
        ("human", "请生成{tier_label}档行程方案"),
    ]
)


import asyncio
import json
import re

TIER_META = {
    "economy": {
        "label": "经济",
        "transit_mode": "公交/地铁为主",
        "hotel_budget": "200",
        "meals_budget": "80",
    },
    "comfort": {
        "label": "舒适",
        "transit_mode": "打车+地铁混合",
        "hotel_budget": "500",
        "meals_budget": "200",
    },
    "luxury": {
        "label": "豪华",
        "transit_mode": "专车/租车",
        "hotel_budget": "不设限",
        "meals_budget": "400",
    },
}


def _parse_json(content: str) -> dict:
    content = re.sub(r"^```(?:json)?\s*", "", content.strip())
    content = re.sub(r"\s*```$", "", content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"daily_plans": [], "total_cost": 0, "budget_usage": 0}


async def _plan_one_tier(
    tier: str,
    llm: ChatOpenAI,
    user_input: str,
    attractions: List[Dict[str, Any]],
    weather: List[Dict[str, Any]],
    hotels: Dict[str, List[Dict[str, Any]]],
    budget_allocation: dict,
) -> tuple:
    """为单个档位生成行程"""
    meta = TIER_META[tier]
    target = budget_allocation.get("target_total", 0)
    budget_detail = (
        f"总预算上限: ¥{target}（含往返交通约¥{budget_allocation.get('intercity', 0)}，"
        f"住宿≤¥{budget_allocation.get('hotel', 0)}，餐饮≤¥{budget_allocation.get('meals', 0)}，"
        f"门票≤¥{budget_allocation.get('tickets', 0)}，市内交通≤¥{budget_allocation.get('transit', 0)}）"
    )
    chain = PLANNER_PROMPT | llm
    response = await chain.ainvoke(
        {
            "tier_label": meta["label"],
            "user_input": user_input,
            "attractions": str(attractions),
            "weather": str(weather),
            "hotels": str(hotels.get(tier, [])),
            "budget_allocation": budget_detail,
            "hotel_budget": meta["hotel_budget"],
            "meals_budget": meta["meals_budget"],
            "transit_mode": meta["transit_mode"],
        }
    )
    content = response.content if hasattr(response, "content") else str(response)
    return tier, _parse_json(content)


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
    """运行规划协调 Agent，三档并行生成"""
    fast_model = settings.llm_fast_model or settings.llm_model
    llm = ChatOpenAI(
        model=fast_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.5,
    )

    user_input = (
        f"出发地: {origin}，目的地: {destination}，"
        f"城市间交通: {intercity_mode}，市内交通: {city_transit}，"
        f"出行天数: {days}天，偏好: {preferences}，出发日期: {start_date}"
    )

    # 三档并行生成
    tasks = []
    for tier in ["economy", "comfort", "luxury"]:
        alloc = calculate_budget_allocation(budget, days, tier, intercity_mode)
        tasks.append(
            _plan_one_tier(tier, llm, user_input, attractions, weather, hotels, alloc)
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    plan = {}
    for r in results:
        if isinstance(r, Exception):
            plan[str(r)] = {"daily_plans": [], "total_cost": 0, "budget_usage": 0}
        else:
            tier, data = r
            plan[tier] = data

    # 确保三档都存在
    for tier in ["economy", "comfort", "luxury"]:
        if tier not in plan:
            plan[tier] = {"daily_plans": [], "total_cost": 0, "budget_usage": 0}

    return plan
