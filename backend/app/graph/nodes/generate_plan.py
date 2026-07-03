"""行程生成节点 (generate_plan) — 两阶段规划·第一阶段

需求与数据就绪后，快速产出三档【概要】（预估总价 + 亮点 + 档次信息），
不生成详细每日行程。首屏因此几乎瞬间：
- 预算总价由 calculate_budget_allocation 确定性计算（零 LLM）
- 三档亮点由一次轻量 LLM 调用产出（失败降级为模板）

详细行程由 generate_tier_detail 在用户选档后按需生成（复用本文件的 plan_one_tier）。
"""
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.graph.state import GraphState
from app.llm.factory import get_fast_llm, get_smart_llm
from app.utils.budget import calculate_budget_allocation


# ── 概要档位元信息 ──
TIER_OVERVIEW_META = {
    "economy": {"label": "经济", "transit_mode": "公交/地铁为主", "hotel_level": "平价民宿/快捷酒店"},
    "comfort": {"label": "舒适", "transit_mode": "打车+地铁混合", "hotel_level": "舒适连锁/精品酒店"},
    "luxury": {"label": "豪华", "transit_mode": "专车/租车", "hotel_level": "高端/奢华酒店"},
}

# ── 详细行程档位参数（供 plan_one_tier 使用）──
TIER_META = {
    "economy": {"label": "经济", "transit_mode": "公交/地铁为主", "hotel_budget": "200", "meals_budget": "80"},
    "comfort": {"label": "舒适", "transit_mode": "打车+地铁混合", "hotel_budget": "500", "meals_budget": "200"},
    "luxury": {"label": "豪华", "transit_mode": "专车/租车", "hotel_budget": "不设限", "meals_budget": "400"},
}

FALLBACK_HIGHLIGHTS = {
    "economy": "高性价比之选",
    "comfort": "品质与均衡兼顾",
    "luxury": "尊享深度体验",
}

PLANNER_SYSTEM_PROMPT = """你是资深旅行规划师。生成 {tier_label} 档行程方案。

## 用户需求
{user_input}

## 可用景点（含坐标、评分、分类）
{attractions}

## 酒店候选
{hotels}

## 天气情况
{weather}

## 预算约束
{budget_allocation}

## 档位参数
- 档位: {tier_label}
- 酒店: ≤¥{hotel_budget}/晚
- 餐饮: ≤¥{meals_budget}/天
- 市内交通: {transit_mode}

## 要求
1. 总花费必须 ≤ 预算红线
2. 每天同区域 2-3 个景点
3. 景点间穿插餐饮
4. 酒店在当天最后景点附近
5. 每天的交通衔接用 route_coordinates 标注

## 输出严格JSON（不要markdown包装）:
{{
  "daily_plans": [
    {{
      "day": 1,
      "date": "YYYY-MM-DD",
      "weather_summary": "天气概况",
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
}}"""


HIGHLIGHT_PROMPT = """你是旅行规划师。根据以下信息，为三档行程各写一句简短亮点（≤15字），突出该档特色，不要重复档位名称。

目的地: {destination}
天数: {days}天
偏好: {preferences}
推荐景点: {attractions}
天气: {weather}

严格输出JSON（不要markdown包装）:
{{"economy": "经济档亮点", "comfort": "舒适档亮点", "luxury": "豪华档亮点"}}"""


def _parse_json(content: str) -> dict:
    content = re.sub(r"^```(?:json)?\s*", "", content.strip())
    content = re.sub(r"\s*```$", "", content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


async def plan_one_tier(
    tier: str,
    req: dict,
    attractions: List[Dict[str, Any]],
    weather: List[Dict[str, Any]],
    hotels: Dict[str, List[Dict[str, Any]]],
    tools_cache: Dict[str, Any],
) -> dict:
    """为单个档位生成详细行程（供 generate_tier_detail 节点复用）

    返回 {daily_plans, total_cost, budget_usage}，失败返回空骨架。
    """
    meta = TIER_META[tier]
    budget = req.get("budget", 3000)
    days = req.get("days", 3)
    intercity_mode = req.get("intercity_mode", "high_speed_rail")
    alloc = calculate_budget_allocation(budget, days, tier, intercity_mode)

    budget_detail = (
        f"总预算上限: ¥{alloc['target_total']}（含往返交通约¥{alloc['intercity']}，"
        f"住宿≤¥{alloc['hotel']}，餐饮≤¥{alloc['meals']}，"
        f"门票≤¥{alloc['tickets']}，市内交通≤¥{alloc['transit']}）"
    )

    user_input = (
        f"出发地: {req.get('origin', '?')}，目的地: {req.get('destination', '?')}，"
        f"城市间交通: {intercity_mode}，市内交通: {req.get('city_transit', 'mixed')}，"
        f"出行天数: {days}天，偏好: {req.get('preferences', [])}，"
        f"出发日期: {req.get('start_date', '?')}"
    )

    weather_text = str(weather[:days]) if weather else "暂无天气数据"

    llm = get_smart_llm(temperature=0.5)
    response = await llm.ainvoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT.format(
            tier_label=meta["label"],
            user_input=user_input,
            attractions=str(attractions[:days * 3]),
            weather=weather_text,
            hotels=str(hotels.get(tier, [])[:6]),
            budget_allocation=budget_detail,
            hotel_budget=meta["hotel_budget"],
            meals_budget=meta["meals_budget"],
            transit_mode=meta["transit_mode"],
        )),
        HumanMessage(content=f"请为 {req.get('destination', '?')} 生成 {meta['label']} 档 {days} 天行程"),
    ])

    content = response.content if hasattr(response, "content") else str(response)
    parsed = _parse_json(content)
    if not parsed:
        return {"daily_plans": [], "total_cost": 0, "budget_usage": 0}
    return parsed


async def _fill_highlights(
    req: dict,
    attractions: List[Dict[str, Any]],
    weather: List[Dict[str, Any]],
    tiers_overview: Dict[str, dict],
) -> Dict[str, dict]:
    """一次轻量 LLM 调用为三档生成亮点（best-effort，失败降级模板）"""
    try:
        llm = get_fast_llm(temperature=0.5)
        resp = await llm.ainvoke([
            SystemMessage(content=HIGHLIGHT_PROMPT.format(
                destination=req.get("destination", "?"),
                days=req.get("days", 3),
                preferences=req.get("preferences", []),
                attractions=", ".join(a.get("name", "") for a in attractions[:6]) or "暂无",
                weather=str(weather[:3]) if weather else "暂无",
            )),
            HumanMessage(content="请输出三档亮点 JSON"),
        ])
        content = resp.content if hasattr(resp, "content") else str(resp)
        data = _parse_json(content)
    except Exception:
        data = {}

    for tier in ["economy", "comfort", "luxury"]:
        hl = data.get(tier)
        if isinstance(hl, str) and hl.strip():
            tiers_overview[tier]["highlight"] = hl.strip()[:20]
        else:
            tiers_overview[tier]["highlight"] = FALLBACK_HIGHLIGHTS[tier]
    return tiers_overview


async def generate_plan_node(state: GraphState) -> dict:
    """生成三档概要（不生成详细每日行程）"""
    req = state.get("requirements", {})
    cache = state.get("tools_cache", {})

    if not req.get("destination"):
        return {"error": "缺少目的地信息", "pending_plan": False}

    attractions = cache.get("attractions", [])
    weather = cache.get("weather", [])
    budget = req.get("budget", 3000)
    days = req.get("days", 3)
    intercity_mode = req.get("intercity_mode", "high_speed_rail")

    # 1. 确定性计算每档预估总价（零 LLM）
    tiers_overview: Dict[str, dict] = {}
    for tier in ["economy", "comfort", "luxury"]:
        meta = TIER_OVERVIEW_META[tier]
        alloc = calculate_budget_allocation(budget, days, tier, intercity_mode)
        est_cost = round(alloc["target_total"])
        tiers_overview[tier] = {
            "label": meta["label"],
            "est_cost": est_cost,
            "budget_usage": round(est_cost / budget * 100, 1) if budget else 0,
            "hotel_level": meta["hotel_level"],
            "transit_mode": meta["transit_mode"],
            "highlight": "",
            "has_detail": False,
        }

    # 2. 一次轻量 LLM 填充亮点
    tiers_overview = await _fill_highlights(req, attractions, weather, tiers_overview)

    plan = {
        "tiers": tiers_overview,
        "details": {},
        "weather": weather,
        "budget": budget,
        "created_at": datetime.utcnow().isoformat(),
    }
    return {"plan": plan, "pending_plan": False}
