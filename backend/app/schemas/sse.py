"""SSE 事件类型全量定义

前端通过 EventSource 接收这些事件，驱动消息流 + 工具日志 + 行程卡片实时更新。
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union, Literal
from datetime import datetime


class SSEEventBase(BaseModel):
    """所有 SSE 事件的公共字段"""
    ts: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    thread_id: str


# ── Token 级别事件 ──

class ChatTokenEvent(SSEEventBase):
    """LLM 输出的一个 token/文本块，前端用于流式渲染"""
    event: Literal["chat_token"] = "chat_token"
    token: str


class ChatMessageDoneEvent(SSEEventBase):
    """一条完整消息生成完毕"""
    event: Literal["chat_message_done"] = "chat_message_done"
    message_id: str


# ── 节点级别事件 ──

class NodeEnterEvent(SSEEventBase):
    """LangGraph 节点开始执行"""
    event: Literal["node_enter"] = "node_enter"
    node: str  # intent_router | extract_requirements | gather_data | generate_plan | present_plan | replan


class NodeExitEvent(SSEEventBase):
    """LangGraph 节点执行完毕"""
    event: Literal["node_exit"] = "node_exit"
    node: str
    duration_ms: int


# ── 工具级别事件 ──

class ToolCallEvent(SSEEventBase):
    """LLM 调用了一个外部工具"""
    event: Literal["tool_call"] = "tool_call"
    tool: str  # search_attractions | get_weather_forecast | search_hotels | plan_transport_route
    arguments: Dict[str, Any]
    call_id: str


class ToolResultEvent(SSEEventBase):
    """工具调用返回结果"""
    event: Literal["tool_result"] = "tool_result"
    tool: str
    call_id: str
    summary: str  # "找到 15 个景点" / "获取 7 天天气预报"
    result_count: Optional[int] = None


# ── 业务级别事件 ──

class PlanGeneratedEvent(SSEEventBase):
    """行程计划生成（含三档数据）"""
    event: Literal["plan_generated"] = "plan_generated"
    tiers: List[str]  # ["economy", "comfort", "luxury"]
    costs: Dict[str, float]  # {"economy": 1680, "comfort": 2380}


class PlanModifiedEvent(SSEEventBase):
    """行程计划被修改"""
    event: Literal["plan_modified"] = "plan_modified"
    modification: str  # "第二天换成西湖"
    affected_days: List[int]


# ── 错误事件 ──

class ErrorEvent(SSEEventBase):
    """后端出错"""
    event: Literal["error"] = "error"
    code: str  # INTENT_CLASSIFICATION_FAILED | TOOL_CALL_FAILED | PLAN_GENERATION_FAILED
    message: str


# ── 事件联合类型 ──

SSEEvent = Union[
    ChatTokenEvent, ChatMessageDoneEvent,
    NodeEnterEvent, NodeExitEvent,
    ToolCallEvent, ToolResultEvent,
    PlanGeneratedEvent, PlanModifiedEvent,
    ErrorEvent,
]
