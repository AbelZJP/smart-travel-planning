"""LangGraph StateGraph 构建器

将定义的节点、边、条件路由组装成一个可执行的图。
"""
from langgraph.graph import StateGraph, END

from app.graph.state import GraphState, initial_state
from app.graph.router import (
    route_after_intent,
    route_after_extract,
    route_after_gather,
    route_after_generate,
)
from app.graph.checkpointer import get_checkpointer

# ── 节点引用（lazy import 避免循环依赖）──
_NODES = {}


def _lazy_import_nodes():
    """延迟导入节点模块，防止 import 时图还没建好"""
    global _NODES
    if _NODES:
        return _NODES
    from app.graph.nodes.intent_router import intent_router_node
    from app.graph.nodes.greeting import greeting_node
    from app.graph.nodes.extract_requirements import extract_requirements_node
    from app.graph.nodes.gather_data import gather_data_node
    from app.graph.nodes.generate_plan import generate_plan_node
    from app.graph.nodes.generate_tier_detail import generate_tier_detail_node
    from app.graph.nodes.present_plan import present_plan_node
    from app.graph.nodes.answer_question import answer_question_node
    from app.graph.nodes.replan import replan_node

    _NODES = {
        "intent_router": intent_router_node,
        "greeting": greeting_node,
        "extract_requirements": extract_requirements_node,
        "gather_data": gather_data_node,
        "generate_plan": generate_plan_node,
        "generate_tier_detail": generate_tier_detail_node,
        "present_plan": present_plan_node,
        "answer_question": answer_question_node,
        "replan": replan_node,
    }
    return _NODES


def build_graph() -> StateGraph:
    """构建完整的旅行规划 StateGraph

    图拓扑（两阶段规划）：
        __start__ → intent_router
          ├── "greeting" → greeting → __end__
          ├── "new_plan" → extract_requirements
          │     └── (filled?) → gather_data → generate_plan(三档概要) → present_plan → __end__
          │     └── (missing) → __end__
          ├── "select_tier" → generate_tier_detail(单档详情) → present_plan → __end__
          ├── "modify_plan" → replan → present_plan → __end__
          └── "query_plan" | "general_chat" → answer_question → __end__
    """
    nodes = _lazy_import_nodes()

    builder = StateGraph(GraphState)

    # 注册所有节点
    for name, node_fn in nodes.items():
        builder.add_node(name, node_fn)

    # 入口：intent_router（所有用户消息先经过此节点）
    builder.set_entry_point("intent_router")

    # 条件路由：根据意图分类结果
    builder.add_conditional_edges(
        "intent_router",
        route_after_intent,
        {
            "greeting": "greeting",
            "extract_requirements": "extract_requirements",
            "generate_tier_detail": "generate_tier_detail",
            "replan": "replan",
            "answer_question": "answer_question",
        },
    )

    # greeting / answer_question 直接结束
    builder.add_edge("greeting", END)
    builder.add_edge("answer_question", END)

    # extract_requirements → (filled? → gather_data | END)
    builder.add_conditional_edges(
        "extract_requirements",
        route_after_extract,
        {"gather_data": "gather_data", "__end__": END},
    )

    # gather_data → generate_plan
    builder.add_conditional_edges(
        "gather_data",
        route_after_gather,
        {"generate_plan": "generate_plan", "__end__": END},
    )

    # generate_plan / generate_tier_detail / replan → present_plan
    builder.add_edge("generate_plan", "present_plan")
    builder.add_edge("generate_tier_detail", "present_plan")
    builder.add_edge("replan", "present_plan")

    # present_plan → end
    builder.add_edge("present_plan", END)

    # 编译为可执行图（附加 Checkpointer）
    graph = builder.compile(checkpointer=get_checkpointer())

    return graph


# 全局单例（延迟初始化，供 API 路由使用）
_graph = None


def get_graph() -> StateGraph:
    """获取全局图实例"""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
