"""条件路由函数

定义 LangGraph 图中各节点之间的条件路由逻辑。
"""
from typing import Literal
from app.graph.state import GraphState


def _is_requirements_complete(req: dict) -> bool:
    """检查旅行需求是否已填满必要字段"""
    required = ["origin", "destination", "budget", "days", "start_date"]
    return all(req.get(f) is not None for f in required)


def route_after_intent(
    state: GraphState,
) -> Literal["greeting", "extract_requirements", "generate_tier_detail", "replan", "answer_question"]:
    """根据意图分类决定下一个执行节点"""
    intent = state.get("user_intent", "general_chat")

    if intent == "greeting":
        return "greeting"

    if intent == "new_plan":
        return "extract_requirements"

    if intent == "select_tier":
        # 选档需要已有概要 plan
        if state.get("plan"):
            return "generate_tier_detail"
        return "answer_question"

    if intent == "modify_plan":
        return "replan"

    # query_plan / general_chat / clarify
    return "answer_question"


def route_after_extract(
    state: GraphState,
) -> Literal["gather_data", "__end__"]:
    """需求提取后的路由：字段齐全则去采集数据，否则结束等用户继续"""
    req = state.get("requirements", {})
    if _is_requirements_complete(req):
        return "gather_data"
    return "__end__"


def route_after_gather(
    state: GraphState,
) -> Literal["generate_plan", "__end__"]:
    """数据采集后的路由"""
    req = state.get("requirements", {})
    # 只要有目的地就继续生成行程（天气数据为可选，缺失不应阻断流程）
    if req.get("destination"):
        return "generate_plan"
    return "__end__"


def route_after_generate(
    state: GraphState,
) -> Literal["present_plan"]:
    """计划生成后的路由"""
    return "present_plan"
