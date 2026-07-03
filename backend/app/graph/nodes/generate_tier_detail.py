"""单档详细行程生成节点 (generate_tier_detail) — 两阶段规划·第二阶段

用户选定某档位后执行：只为 active_tier 生成详细 daily_plans，
写入 plan.details[active_tier]，并用真实总价回填概要。
比一次性三档并行快约 2/3（只一次 LLM 调用）。已生成过的档位直接复用（幂等）。
"""
from app.graph.state import GraphState
from app.graph.nodes.generate_plan import plan_one_tier


async def generate_tier_detail_node(state: GraphState) -> dict:
    """根据 active_tier 生成单档详细行程"""
    req = state.get("requirements", {})
    cache = state.get("tools_cache", {})
    plan = state.get("plan") or {}
    tier = state.get("active_tier", "comfort")

    if not req.get("destination"):
        return {"error": "缺少目的地信息", "pending_plan": False}

    details = dict(plan.get("details") or {})

    # 幂等：已生成过则直接返回，避免重复 LLM 调用
    if tier in details and details[tier].get("daily_plans"):
        return {"plan": plan, "pending_plan": False}

    attractions = cache.get("attractions", [])
    weather = cache.get("weather", [])
    hotels = cache.get("hotels", {"economy": [], "comfort": [], "luxury": []})

    detail = await plan_one_tier(tier, req, attractions, weather, hotels, cache)
    details[tier] = detail

    # 用真实总价回填该档概要
    tiers = dict(plan.get("tiers") or {})
    if tier in tiers:
        real_cost = detail.get("total_cost", 0) or 0
        budget = req.get("budget", 0) or 0
        tiers[tier] = {
            **tiers[tier],
            "est_cost": real_cost if real_cost else tiers[tier].get("est_cost", 0),
            "budget_usage": round(real_cost / budget * 100, 1) if budget else tiers[tier].get("budget_usage", 0),
            "has_detail": True,
        }

    new_plan = {**plan, "details": details, "tiers": tiers}
    # 同时返回 active_tier，供 sse_bridge 在 tier_detail 事件中携带
    return {"plan": new_plan, "active_tier": tier, "pending_plan": False}
