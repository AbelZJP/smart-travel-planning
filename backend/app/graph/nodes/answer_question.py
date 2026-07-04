"""问答节点 (answer_question)

当用户询问已有计划的内容或进行一般聊天时使用。
LLM 可自主调用高德工具（景点/天气/酒店/地理编码/路线）查询实时信息——
例如用户问"杭州明天天气怎样"时，LLM 自己调 get_weather_forecast 再回答。

实现为 ReAct 工具循环（最多 MAX_TOOL_ITERS 轮）：
    LLM(astream) → 有 tool_calls → 执行工具 → 结果回喂 → LLM(astream) → …
                 → 无 tool_calls → 最终答案（已通过 on_chat_model_stream 流式推送）

工具调用/结果经 on_tool_start/on_tool_event 自动由 sse_bridge 推送（tool_call/tool_result），
最终答案 token 经 on_chat_model_stream 推送（chat_token），前端无需改动。
"""
import json
from typing import Dict

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    AIMessageChunk,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig

from app.graph.state import GraphState
from app.llm.factory import get_smart_llm
from app.graph.tools import AMAP_TOOLS


# 工具名 → 工具实例，供循环中按 tool_call 名字分发
_TOOL_BY_NAME: Dict[str, object] = {t.name: t for t in AMAP_TOOLS}

# 最大工具调用轮数，防止死循环
MAX_TOOL_ITERS = 5


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

# 工具使用引导：告知 LLM 可用工具与调用时机
TOOL_GUIDE = """

你可以调用以下高德地图工具获取实时信息：
- search_attractions：搜索景点（需 city 城市名 + keyword 关键词，如"自然风光""博物馆"）
- get_weather_forecast：查询天气预报（需 city 城市名）
- search_hotels：搜索酒店（需 city 城市名）
- geocode：地址转坐标（需 address 地名，如"西湖"）
- plan_transport_route：规划两点路线（需起终点经纬度 + city；先用 geocode 把地名转坐标）

调用规则：
- 当用户询问实时天气/景点/酒店/路线等真实数据时，主动调用对应工具，不要凭记忆臆造
- 工具返回后，用自然语言总结结果回答用户
- 与实时数据无关的闲聊不要调用工具
"""


async def answer_question_node(state: GraphState, config: RunnableConfig) -> dict:
    """回答用户问题，可自主调用高德工具查询实时信息"""
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

    # 构建 system prompt（有/无计划两套，均附加工具引导）
    if plan:
        plan_summary = _summarize_plan(plan, active_tier)
        system_content = SYSTEM_WITH_PLAN.format(
            plan_data=plan_summary,
            active_tier=active_tier,
        ) + TOOL_GUIDE
    else:
        system_content = SYSTEM_WITHOUT_PLAN + TOOL_GUIDE

    # 绑定工具；模型若不支持 function calling 则退回纯文本 LLM
    base_llm = get_smart_llm(temperature=0.7)
    try:
        llm = base_llm.bind_tools(AMAP_TOOLS)
    except Exception:
        llm = base_llm

    convo = [SystemMessage(content=system_content), HumanMessage(content=last_user_msg)]

    accumulated = AIMessageChunk(content="")

    # ReAct 循环
    for _ in range(MAX_TOOL_ITERS):
        # 流式输出：最终答案 token 经 on_chat_model_stream → chat_token 实时推送
        accumulated = AIMessageChunk(content="")
        try:
            async for chunk in llm.astream(convo, config=config):
                accumulated += chunk
        except Exception as e:
            return {"messages": [AIMessage(content=f"回答生成失败：{e}")]}

        tool_calls = accumulated.tool_calls or []

        # 无工具调用 → 最终答案已流式输出，落盘消息后结束
        if not tool_calls:
            return {"messages": [AIMessage(content=accumulated.content)]}

        # 有工具调用 → 逐个执行，结果作为 ToolMessage 回喂
        ai_msg = AIMessage(content=accumulated.content, tool_calls=tool_calls)
        convo.append(ai_msg)
        for tc in tool_calls:
            tool = _TOOL_BY_NAME.get(tc.get("name", ""))
            tool_call_id = tc.get("id", "")
            if tool is None:
                convo.append(ToolMessage(
                    content=f"未知工具: {tc.get('name')}",
                    tool_call_id=tool_call_id,
                ))
                continue
            try:
                result = await tool.ainvoke(tc.get("args", {}), config=config)
                result_str = result if isinstance(result, str) else json.dumps(
                    result, ensure_ascii=False
                )
            except Exception as e:
                result_str = f"工具调用失败: {e}"
            convo.append(ToolMessage(content=result_str, tool_call_id=tool_call_id))

    # 达到最大轮数仍未结束：强制让 LLM（不绑工具）做总结性回答
    try:
        final_acc = AIMessageChunk(content="")
        async for chunk in base_llm.astream(
                convo + [HumanMessage(content="请根据已获取的信息直接回答用户，不要再调用工具。")],
                config=config,
            ):
            final_acc += chunk
        return {"messages": [AIMessage(content=final_acc.content)]}
    except Exception:
        return {"messages": [AIMessage(content="（工具调用次数已达上限，请细化你的问题）")]}


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
