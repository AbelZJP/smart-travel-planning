"""对话 / 会话相关的 Pydantic Schema。"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ThreadInfo(BaseModel):
    """会话线程元数据"""
    thread_id: str
    title: str = "新对话"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    last_active_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    message_count: int = 0


class ChatRequest(BaseModel):
    """用户发送的消息"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息内容")


class ChatResponse(BaseModel):
    """发送消息后的响应"""
    thread_id: str
    message_id: str
    status: str = "running"  # running | done | error


class ChatMessage(BaseModel):
    """一条对话消息"""
    message_id: str
    thread_id: str
    role: str = "user"  # user | assistant
    content: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: Optional[Dict[str, Any]] = None  # 关联的工具调用、plan 等


class ThreadListResponse(BaseModel):
    """会话列表"""
    threads: List[ThreadInfo]


class ChatHistoryResponse(BaseModel):
    """历史消息"""
    thread_id: str
    messages: List[ChatMessage]
    has_more: bool = False
