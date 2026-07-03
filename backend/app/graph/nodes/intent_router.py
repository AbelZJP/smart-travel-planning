"""意图分类节点 (intent_router)

每次用户发送消息后第一个执行的节点。
用小模型快速分类用户意图，决定后续走哪个分支。

支持两条选档路径：
- 点击卡片 → select_tier 端点预设 user_intent="select_tier" + active_tier，本节点直接放行
- 文字回复"我要舒适档" → LLM 分类为 select_tier 并解析 target_tier 写入 active_tier
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from app.graph.state import GraphState
from app.llm.factory import get_fast_llm
from app.llm.structured import invoke_structured


class IntentClassification(BaseModel):
    """意图分类结构化输出"""
    intent: Literal["greeting", "new_plan", "modify_plan", "query_plan", "general_chat", "select_tier"] = Field(
        description="用户当前消息的意图分类"
    )
    target_tier: Optional[Literal["economy", "comfort", "luxury"]] = Field(
        None, description="当 intent=select_tier 时用户选定的目标档位；其他意图为 None"
    )
    reasoning: str = Field(description="分类理由（简要）")
    confidence: float = Field(description="置信度 0~1", ge=0, le=1)


SYSTEM_PROMPT = """你是旅行规划助手的意图分类器。根据用户最新一条消息，判断其意图。

意图定义：
- greeting: 打招呼、问候（"你好" "hi" "在吗"）
- new_plan: 想开始新的旅行规划（"我想去杭州" "帮我规划去成都" "我要旅游"）
- select_tier: 选定或切换某个档位（"我要舒适档" "来个豪华版" "选经济档" "换个经济档" "看豪华的"）。此时 target_tier 必须填 economy/comfort/luxury 之一。
- modify_plan: 修改已有行程的细节（"第二天换成西湖" "删掉灵隐寺" "加个景点" "预算改成5000"）
- query_plan: 询问已有计划的内容（"第三天是什么" "总花费多少" "酒店在哪"）
- general_chat: 其他通用聊天（"谢谢" "好的" "什么是xxx"）

注意：
- 如果还没有 plan（从未生成过行程），不应分类为 modify_plan / select_tier / query_plan
- "换档/选档"属于 select_tier；"改某天景点/预算数值"属于 modify_plan
- 如果用户同时提到多个意图，选最重要的那个
- 置信度低于 0.6 时优先选 general_chat"""


async def intent_router_node(state: GraphState) -> dict:
    """意图分类节点：使用 fast_llm + 结构化输出"""
    # 端点预设的 select_tier（点击档位卡片触发）：直接放行，active_tier 已由端点设置
    if state.get("user_intent") == "select_tier":
        return {"user_intent": "select_tier"}

    messages = state.get("messages", [])
    if not messages:
        return {"user_intent": "greeting"}

    last_msg = messages[-1]
    user_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    has_plan = state.get("plan") is not None
    llm = get_fast_llm()

    system_content = SYSTEM_PROMPT
    if not has_plan:
        system_content += "\n\n注意：当前还没有生成过行程计划，所以不要分类为 modify_plan、select_tier 或 query_plan。"

    result = await invoke_structured(
        llm,
        [
            SystemMessage(content=system_content),
            HumanMessage(content=f"用户最新消息: {user_text}"),
        ],
        IntentClassification,
        fallback={"intent": "general_chat", "reasoning": "fallback", "confidence": 0.5},
    )

    update: dict = {"user_intent": result.intent}
    # 文字选档：解析出目标档位并设置 active_tier
    if result.intent == "select_tier" and result.target_tier:
        update["active_tier"] = result.target_tier
    return update
