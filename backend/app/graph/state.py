"""LangGraph GraphState 定义

整个对话智能体的核心数据契约。每个节点读取/写入此状态。
"""
from typing import Annotated, List, Optional, Dict, Any, Literal
from typing_extensions import TypedDict
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class GraphState(TypedDict):
    # ── LangGraph 标准消息列表（按 ID 去重、自动追加）──
    messages: Annotated[List[BaseMessage], add_messages]

    # ── 对话语境 ──
    user_intent: Literal["greeting", "new_plan", "modify_plan", "query_plan", "general_chat"]
    """当前用户消息的意图分类"""

    # ── 旅行需求（结构化，逐步填充）──
    requirements: Dict[str, Any]
    """从对话中提取的结构化需求：
       {origin, destination, budget, days, preferences, start_date, intercity_mode, city_transit, completed}
       使用增量填充：每轮对话补充缺失字段，已有字段不覆盖。"""

    # ── 当前计划 ──
    plan: Optional[Dict[str, Any]]
    """两阶段行程计划数据：
       {
         tiers: {economy: {label,est_cost,budget_usage,hotel_level,transit_mode,highlight,has_detail}, comfort:..., luxury:...},
         details: {comfort: {daily_plans,total_cost,budget_usage}, ...},  # 按需生成的单档详情
         weather: [...], created_at: ""
       }
       阶段1（generate_plan）只填 tiers；阶段2（generate_tier_detail）按 active_tier 填 details。"""

    # ── 工具调用缓存 ──
    tools_cache: Dict[str, Any]
    """缓存的搜索结果，避免重复查高德 API：
       {attractions: [...], weather: [...], hotels: {economy: [], comfort: [], luxury: []}}
       当目的地改变时清空。"""

    # ── 重规划上下文 ──
    replan_context: Optional[Dict[str, Any]]
    """增量重规划的修改指令：
       {modification: "第二天换成西湖", target_day: 2, target_tiers: ["economy", "comfort"]}"""

    # ── 渲染控制 ──
    pending_plan: bool
    """是否正在生成计划（前端可用于显示加载态）"""
    active_tier: Literal["economy", "comfort", "luxury"]
    """当前选中的档位"""
    error: Optional[str]
    """错误信息"""

    # ── 会话元数据 ──
    thread_id: str
    """LangGraph 的 thread_id，用于 Checkpointer 恢复上下文"""


def initial_state(thread_id: str) -> Dict[str, Any]:
    """创建一个全新的初始状态"""
    return {
        "messages": [],
        "user_intent": "greeting",
        "requirements": {
            "origin": None,
            "destination": None,
            "budget": None,
            "days": None,
            "preferences": [],
            "start_date": None,
            "intercity_mode": "high_speed_rail",
            "city_transit": "mixed",
            "completed": False,
        },
        "plan": None,
        "tools_cache": {
            "attractions": [],
            "weather": [],
            "hotels": {"economy": [], "comfort": [], "luxury": []},
        },
        "replan_context": None,
        "pending_plan": False,
        "active_tier": "comfort",
        "error": None,
        "thread_id": thread_id,
    }
