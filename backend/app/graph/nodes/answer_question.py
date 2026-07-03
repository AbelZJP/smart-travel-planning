"""问答节点 (answer_question)

当用户询问已有计划的内容或进行一般聊天时使用。
如果已有计划，LLM 会参考 plan 数据回答；否则直接聊天。
"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.graph.state import GraphState
from app.llm.factory import get_smart_llm


SYSTEM_WITH_PLAN = """你是一个旅行规划助手。用户在查看他们的行程计划，可能会有以下问题：

1. 询问某天的具体安排（"第三天是什么"）
2. 询问费用（"总花费多少"）
3. 询问推荐理由（"为什么选这个酒店"）
4. 要求比较档位（"经济和舒适差多少"）
5. 其他关于行程的询问

请根据以下计划数据回答用户问题，回答要简洁、有帮助。

当前计划数据：
{plan_data}

当前选中的档位: {active_tier}"""

SYSTEM_WITHOUT_PLAN = """你是一个旅行规划助手。用户在和你聊天。

你可以：
1. 回答旅行相关的一般问题
2. 询问他们是否需要帮助规划行程
3. 提供旅行建议

回答要友好、简洁。"""


async def answer_question_node(state: GraphState) -> dict:
    """回答用户关于行程的询问"""
    messages = state.get("messages", [])
    plan = state.get("plan")
    active_tier = state.get("active_tier", "comfort")

    # 找最后一条用户消息
    last_user_msg = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            last_user_msg = msg.content
            break

    if not last_user_msg:
        return {}

    llm = get_smart_llm(temperature=0.7)

    if plan:
        plan_summary = _summarize_plan(plan, active_tier)
        response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_WITH_PLAN.format(
                plan_data=plan_summary,
                active_tier=active_tier,
            )),
            HumanMessage(content=last_user_msg),
        ])
    else:
        response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_WITHOUT_PLAN),
            HumanMessage(content=last_user_msg),
        ])

    content = response.content if hasattr(response, "content") else str(response)
    return {"messages": [AIMessage(content=content)]}


def _summarize_plan(plan: dict, active_tier: str) -> str:
    """生成计划的文字摘要，供 LLM 参考"""
    tier = plan.get(active_tier, {})
    daily_plans = tier.get("daily_plans", [])
    total_cost = tier.get("total_cost", 0)

    lines = [
        f"目的地: {plan.get('destination', '?')}",
        f"档位: {active_tier}，总花费: ¥{total_cost:,}",
        f"天数: {len(daily_plans)} 天",
        "",
    ]

    for dp in daily_plans:
        day = dp.get("day", "?")
        names = [a.get("name", "?") for a in dp.get("attractions", [])]
        hotel = dp.get("hotel", {}).get("name", "?")
        lines.append(f"Day {day}: {', '.join(names)} | 住: {hotel} | 花费: ¥{dp.get('daily_cost', 0)}")

    return "\n".join(lines)
