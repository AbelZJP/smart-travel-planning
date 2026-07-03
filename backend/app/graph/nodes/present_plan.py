"""行程展示节点 (present_plan)

两阶段规划的展示入口。故意不在此输出完整行程 Markdown，
避免与前端 PlanCard 重复堆砌、挤占对话窗口——只发简短引导，
详细数据通过 SSE 的 plan_overview / tier_detail 事件交给 PlanCard 渲染。
"""
from langchain_core.messages import AIMessage
from app.graph.state import GraphState


TIER_LABELS = {"economy": "经济", "comfort": "舒适", "luxury": "豪华"}


async def present_plan_node(state: GraphState) -> dict:
    """生成简短引导消息；详细行程由前端 PlanCard 渲染"""
    plan = state.get("plan")
    if not plan:
        return {"messages": [AIMessage(content="😅 抱歉，行程生成似乎出了点问题，请重新描述您的需求。")]}

    active_tier = state.get("active_tier", "comfort")
    details = plan.get("details") or {}
    tier_label = TIER_LABELS.get(active_tier, "舒适")

    replan_ctx = state.get("replan_context")
    header = ""
    if replan_ctx:
        modification = replan_ctx.get("modification", "")
        affected = replan_ctx.get("affected_days", [])
        affected_str = f"（影响第 {', '.join(str(d) for d in affected)} 天）" if affected else ""
        header = f"✅ **已按你的需求调整行程{affected_str}**：{modification}\n\n"

    if active_tier in details and details[active_tier].get("daily_plans"):
        content = (
            f"{header}📍 已为你生成 **{tier_label}档** 详细行程，点击下方卡片查看每日安排 👇\n\n"
            f"💡 如需调整可告诉我，如 *“第二天换成西湖”*、*“换经济档”*。"
        )
    else:
        content = (
            f"{header}🏆 已为你准备 **三档方案概要**（经济 / 舒适 / 豪华），"
            f"点击下方任一档位卡片即可生成该档详细行程 👇\n\n"
            f"也可以直接回复 *“我要舒适档”*。"
        )

    return {"messages": [AIMessage(content=content)]}
