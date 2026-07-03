"""增量重规划节点 (replan)

当用户要求修改已有行程时执行。例如："第二天换成西湖"、"预算改成5000"。
只重新生成受影响的天数，其他天数保持不变（最小修改原则）。

适配两阶段规划结构：详细行程位于 plan.details[active_tier]，
因此 replan 只修改当前选中档位（active_tier）的详情。
"""
import json
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.graph.state import GraphState
from app.llm.factory import get_smart_llm
from app.llm.structured import invoke_structured
from app.graph.tools import search_attractions


class ModificationIntent(BaseModel):
    """用户修改意图的结构化描述"""
    change_type: str = Field(description="修改类型: replace_attraction / remove_attraction / add_attraction / update_budget / switch_tier / extend_trip / change_hotel")
    target_day: Optional[int] = Field(None, description="目标天数（从1开始）")
    target_tiers: List[str] = Field(default_factory=lambda: ["economy", "comfort", "luxury"], description="要修改的档位")
    new_attraction_name: Optional[str] = Field(None, description="新景点名称（替换/添加时）")
    old_attraction_name: Optional[str] = Field(None, description="被替换的景点名称")
    new_value: Optional[float] = Field(None, description="新的预算/天数等数值")
    description: str = Field(description="人类可读的修改描述")


EXTRACT_PROMPT = """你是一个行程修改意图解析器。用户想修改已经生成的旅行计划。

当前计划的简要摘要（{active_tier}档）：
{plan_summary}

用户修改要求: {user_message}

请解析出：
- change_type: 修改类型
- target_day: 影响哪一天（未知则为 None）
- target_tiers: 影响哪些档位（默认当前档位）
- new_attraction_name: 如果是替换/添加景点，新景点名叫什么
- old_attraction_name: 如果是替换，被替换的景点叫什么
- new_value: 如果是改预算/天数，新值是多少
- description: 一句话描述修改内容

注意：如果是"改成经济档""切换档位"这类操作，change_type 应为 switch_tier"""


def _get_tier_detail(plan: dict, tier: str) -> dict:
    """从两阶段 plan 结构中取某档详细行程"""
    return (plan.get("details") or {}).get(tier, {})


async def replan_node(state: GraphState) -> dict:
    """执行增量重规划（仅修改 active_tier 的详情）"""
    messages = state.get("messages", [])
    plan = state.get("plan")
    req = state.get("requirements", {})

    if not plan:
        return {"error": "还没有行程计划，无法修改"}

    active_tier = state.get("active_tier", "comfort")
    tier_detail = _get_tier_detail(plan, active_tier)

    # 当前档位还没有详细行程 → 提示先选档生成详情
    if not tier_detail.get("daily_plans"):
        return {
            "messages": [AIMessage(content=f"当前 {active_tier} 档还没有详细行程，请先点击该档位卡片生成详情，再进行修改 😊")],
            "replan_context": None,
        }

    # 找最后一条用户消息
    last_user_msg = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            last_user_msg = msg.content
            break
    if not last_user_msg:
        return {}

    # Step 1: LLM 解析修改意图
    plan_summary = _summarize_plan_for_replan(plan, active_tier)
    llm = get_smart_llm(temperature=0.3)
    modification = await invoke_structured(
        llm,
        [
            SystemMessage(content=EXTRACT_PROMPT.format(
                active_tier=active_tier,
                plan_summary=plan_summary,
                user_message=last_user_msg,
            )),
            HumanMessage(content=last_user_msg),
        ],
        ModificationIntent,
    )

    updated_plan = json.loads(json.dumps(plan))  # deep copy

    # switch_tier：切换档位（设置 active_tier，由 present_plan 引导生成/查看新档）
    if modification.change_type == "switch_tier":
        new_tier = modification.target_tiers[0] if modification.target_tiers else active_tier
        return {
            "active_tier": new_tier,
            "replan_context": {"modification": modification.description, "affected_days": []},
        }

    # update_budget：预算变更，已有详情可能失效 → 清空 details 回到概要
    if modification.change_type == "update_budget":
        new_budget = modification.new_value
        if new_budget and new_budget > 0:
            updated_plan["details"] = {}
            for t in (updated_plan.get("tiers") or {}):
                if isinstance(updated_plan["tiers"][t], dict):
                    updated_plan["tiers"][t]["has_detail"] = False
            return {
                "plan": updated_plan,
                "requirements": {**req, "budget": new_budget},
                "replan_context": {"modification": modification.description, "affected_days": []},
            }

    # replace/add attraction：仅修改 active_tier 的对应天
    if modification.change_type in ("replace_attraction", "add_attraction"):
        new_attraction_name = modification.new_attraction_name
        target_day = modification.target_day

        if not (new_attraction_name and target_day):
            return {"error": "缺少新景点名或目标天数", "replan_context": {"modification": modification.description, "affected_days": []}}

        destination = req.get("destination", "")
        new_poi_data = await search_attractions.ainvoke({
            "keyword": new_attraction_name,
            "city": destination,
        })

        daily_plans = updated_plan["details"][active_tier].get("daily_plans", [])
        day_idx = target_day - 1
        if day_idx < 0 or day_idx >= len(daily_plans):
            return {"error": f"第 {target_day} 天不存在", "replan_context": {"modification": modification.description, "affected_days": []}}

        day_plan = daily_plans[day_idx]
        old_attractions = day_plan.get("attractions", [])

        if modification.change_type == "replace_attraction" and old_attractions:
            old_name = modification.old_attraction_name or old_attractions[0].get("name", "")
            for i, attr in enumerate(old_attractions):
                if attr.get("name") == old_name or i == 0:
                    if new_poi_data:
                        new_poi = new_poi_data[0]
                        old_attractions[i] = {
                            "name": new_poi.get("name", new_attraction_name),
                            "lng": new_poi.get("lng", 0),
                            "lat": new_poi.get("lat", 0),
                            "duration": "2h",
                            "ticket": 0,
                            "time_slot": attr.get("time_slot", "09:00-11:00"),
                            "rating": new_poi.get("rating", 4.0),
                            "category": new_poi.get("category", ""),
                            "order": attr.get("order", i + 1),
                        }
                    break
            day_plan["attractions"] = old_attractions
        elif modification.change_type == "add_attraction" and new_poi_data:
            new_poi = new_poi_data[0]
            new_order = len(old_attractions) + 1
            old_attractions.append({
                "name": new_poi.get("name", new_attraction_name),
                "lng": new_poi.get("lng", 0),
                "lat": new_poi.get("lat", 0),
                "duration": "2h",
                "ticket": 0,
                "time_slot": "14:00-16:00",
                "rating": new_poi.get("rating", 4.0),
                "category": new_poi.get("category", ""),
                "order": new_order,
            })

        # 用 LLM 重新生成这一天
        new_day = await _regenerate_single_day(
            active_tier, day_plan, updated_plan["details"][active_tier],
            req, new_poi_data if new_poi_data else [],
        )
        daily_plans[day_idx] = new_day
        updated_plan["details"][active_tier]["daily_plans"] = daily_plans

        # 重算总花费
        total = sum(d.get("daily_cost", 0) for d in daily_plans)
        updated_plan["details"][active_tier]["total_cost"] = total
        budget = req.get("budget", 3000)
        updated_plan["details"][active_tier]["budget_usage"] = round(total / budget * 100, 1) if budget else 0

        # 同步概要
        if active_tier in (updated_plan.get("tiers") or {}):
            updated_plan["tiers"][active_tier]["est_cost"] = total
            updated_plan["tiers"][active_tier]["budget_usage"] = round(total / budget * 100, 1) if budget else 0

        return {
            "plan": updated_plan,
            "replan_context": {"modification": modification.description, "affected_days": [target_day]},
        }

    # 兜底：无法处理的修改类型
    return {
        "error": f"无法处理此修改类型: {modification.change_type}",
        "replan_context": {"modification": modification.description, "affected_days": []},
    }


async def _regenerate_single_day(
    tier_key: str,
    day_plan: dict,
    tier_plan: dict,
    req: dict,
    new_poi: List[dict],
) -> dict:
    """用 LLM 单天重规划"""
    llm = get_smart_llm(temperature=0.5)

    prompt = f"""你是一个旅行规划助手。请重新规划 {req.get('destination', '?')} 的第 {day_plan.get('day', '?')} 天行程。

修改后的景点列表：
{json.dumps([a.get('name') for a in day_plan.get('attractions', [])], ensure_ascii=False)}

新景点数据：
{json.dumps(new_poi[:3], ensure_ascii=False, indent=2) if new_poi else '无'}

请：
1. 重新安排时间线（time_slot）
2. 建议合理的交通衔接
3. 插入餐饮
4. 推荐附近酒店
5. 标注 route_coordinates

输出格式与原来完全一致（JSON，不要markdown）：
{{
  "day": {day_plan.get('day', 1)},
  "date": "{day_plan.get('date', '')}",
  "weather_summary": "",
  "attractions": [...],
  "hotel": {{...}},
  "meals": [...],
  "transport": [...],
  "daily_cost": 0,
  "route_coordinates": [...]
}}"""

    response = await llm.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, "content") else str(response)
    try:
        content_clean = re.sub(r"^```(?:json)?\s*", "", content.strip())
        content_clean = re.sub(r"\s*```$", "", content_clean)
        return json.loads(content_clean)
    except json.JSONDecodeError:
        return day_plan


def _summarize_plan_for_replan(plan: dict, active_tier: str) -> str:
    """生成计划摘要（重规划用，基于 active_tier 详情）"""
    tier_detail = (plan.get("details") or {}).get(active_tier, {})
    daily_plans = tier_detail.get("daily_plans", [])
    lines = [f"共 {len(daily_plans)} 天，当前档位: {active_tier}，总花费: ¥{tier_detail.get('total_cost', 0)}"]
    for dp in daily_plans:
        names = [a.get("name", "?") for a in dp.get("attractions", [])]
        hotel = dp.get("hotel", {}).get("name", "?")
        lines.append(f"  Day {dp.get('day', '?')}: {', '.join(names)} | 酒店: {hotel} | ¥{dp.get('daily_cost', 0)}")
    return "\n".join(lines)
