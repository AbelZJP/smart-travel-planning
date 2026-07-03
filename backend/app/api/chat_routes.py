"""对话 API 路由

提供对话式旅行规划的 REST + SSE 端点。

会话状态通过 LangGraph SqliteSaver 持久化（消息/需求/行程），
会话元数据通过 thread_store 管理（标题/活跃时间/列表）。
进程重启后仍可恢复全部对话历史。
"""
import uuid
import sqlite3
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatHistoryResponse, ThreadInfo, ThreadListResponse
from app.schemas.chat import ChatMessage as ChatMessageSchema
from app.services.thread_store import (
    create_thread,
    list_threads,
    get_thread,
    update_thread,
    delete_thread,
    reset_thread,
)
from app.services.sse_bridge import stream_graph_events
from app.graph.state import initial_state
from app.graph.builder import get_graph
from app.config import settings

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _derive_title(messages) -> str:
    """从消息列表推导会话标题（首条用户消息前 16 字）"""
    for msg in messages:
        if getattr(msg, "type", "") == "human":
            content = getattr(msg, "content", "")
            if isinstance(content, str) and content.strip():
                return content.strip()[:16]
    return "新对话"


async def _ensure_thread(thread_id: str) -> dict:
    """确保会话存在：先查 thread_store，没有则尝试从 checkpointer 恢复元数据"""
    info = get_thread(thread_id)
    if info is not None:
        return info

    # 重启后 thread_store 可能丢失，但 checkpointer 仍有状态 → 恢复元数据
    graph = get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    try:
        snapshot = await graph.aget_state(config)
    except Exception:
        snapshot = None
    if snapshot is None or not snapshot.values:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = snapshot.values.get("messages", [])
    return create_thread(
        thread_id,
        title=_derive_title(messages),
        message_count=len(messages),
    )


def _purge_checkpointer_state(thread_id: str):
    """清理 SqliteSaver 中该会话的全部 checkpoint 记录（容错，表名因版本而异）"""
    try:
        conn = sqlite3.connect(settings.memory_db_path, check_same_thread=False)
        for table in ("checkpoints", "checkpoint_blobs", "checkpoint_writes", "writes"):
            try:
                conn.execute(f"DELETE FROM {table} WHERE thread_id = ?", (thread_id,))
            except Exception:
                pass
        conn.commit()
        conn.close()
    except Exception:
        pass


@router.get("")
async def list_conversations():
    """列出所有会话（按最后活跃时间倒序）"""
    threads = list_threads()
    return ThreadListResponse(threads=[ThreadInfo(**t) for t in threads])


@router.post("")
async def new_conversation():
    """创建新的对话会话（thread）"""
    thread_id = str(uuid.uuid4())
    create_thread(thread_id)

    # 初始化 LangGraph checkpointer 状态
    graph = get_graph()
    init_state = initial_state(thread_id)
    await graph.ainvoke(init_state, {"configurable": {"thread_id": thread_id}})
    return {"thread_id": thread_id, "status": "created"}


@router.delete("/{thread_id}")
async def delete_conversation(thread_id: str):
    """删除会话（元数据 + checkpointer 状态）"""
    delete_thread(thread_id)
    _purge_checkpointer_state(thread_id)
    return {"thread_id": thread_id, "status": "deleted"}


@router.post("/{thread_id}")
async def send_message(thread_id: str, request: ChatRequest):
    """发送消息到对话，返回 SSE 事件流

    使用 LangGraph StateGraph 处理消息，通过 SSE 流式返回：
    - chat_token: LLM 输出 token
    - node_enter/node_exit: 节点执行状态
    - tool_call/tool_result: 工具调用日志
    - plan_overview: 三档概要（首屏，轻量）
    - tier_detail: 单档详细行程（选档后）
    - chat_message_done: 消息结束
    """
    info = await _ensure_thread(thread_id)

    # 首条消息用作用户可读的会话标题
    is_first = info.get("message_count", 0) == 0
    update_thread(
        thread_id,
        title=(request.message.strip()[:16] if is_first else None),
        bump_active=True,
        increment_messages=1,
    )

    graph = get_graph()
    config = {"configurable": {"thread_id": thread_id}}

    # 准备输入：将用户消息包装为初始状态变更
    from langchain_core.messages import HumanMessage

    input_data = {
        "messages": [HumanMessage(content=request.message)],
        "user_intent": "new_plan",  # 入口标记，intent_router 会重新分类
        "thread_id": thread_id,
    }

    async def event_stream():
        try:
            events = graph.astream_events(input_data, config, version="v2")
            async for sse_line in stream_graph_events(thread_id, events):
                yield sse_line
        except Exception as e:
            import traceback
            traceback.print_exc()
            import json
            yield f"event: error\ndata: {json.dumps({'thread_id': thread_id, 'code': 'STREAM_ERROR', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{thread_id}/tier/{tier}")
async def select_tier(thread_id: str, tier: str):
    """选定某档位，流式生成该档详细行程（点击档位卡片触发）

    预设 user_intent="select_tier" + active_tier，intent_router 直接放行到
    generate_tier_detail → present_plan，SSE 推送 tier_detail 事件。
    """
    if tier not in ("economy", "comfort", "luxury"):
        raise HTTPException(status_code=400, detail="档位无效，需为 economy/comfort/luxury")
    await _ensure_thread(thread_id)

    graph = get_graph()
    config = {"configurable": {"thread_id": thread_id}}

    input_data = {
        "active_tier": tier,
        "user_intent": "select_tier",
        "thread_id": thread_id,
    }

    async def event_stream():
        try:
            events = graph.astream_events(input_data, config, version="v2")
            async for sse_line in stream_graph_events(thread_id, events):
                yield sse_line
        except Exception as e:
            import traceback
            traceback.print_exc()
            import json
            yield f"event: error\ndata: {json.dumps({'thread_id': thread_id, 'code': 'STREAM_ERROR', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{thread_id}/history")
async def get_history(thread_id: str):
    """获取对话历史消息"""
    await _ensure_thread(thread_id)

    graph = get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    try:
        snapshot = await graph.aget_state(config)
    except Exception:
        raise HTTPException(status_code=500, detail="无法读取对话状态")

    messages = []
    if snapshot and snapshot.values:
        for i, msg in enumerate(snapshot.values.get("messages", [])):
            role = "assistant" if getattr(msg, "type", "") in ("ai", "chat") else "user"
            messages.append(
                ChatMessageSchema(
                    message_id=f"{thread_id}_{i}",
                    thread_id=thread_id,
                    role=role,
                    content=getattr(msg, "content", str(msg)),
                )
            )

    return ChatHistoryResponse(thread_id=thread_id, messages=messages, has_more=False)


@router.get("/{thread_id}/plan")
async def get_current_plan(thread_id: str):
    """获取当前会话的最新行程计划"""
    await _ensure_thread(thread_id)

    graph = get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    try:
        snapshot = await graph.aget_state(config)
    except Exception:
        raise HTTPException(status_code=500, detail="无法读取规划状态")

    plan = snapshot.values.get("plan") if (snapshot and snapshot.values) else None
    if not plan:
        raise HTTPException(status_code=404, detail="当前会话还没有行程计划")

    return plan


@router.post("/{thread_id}/reset")
async def reset_conversation(thread_id: str):
    """重置当前会话（清空消息和计划，保留 thread_id）"""
    await _ensure_thread(thread_id)

    graph = get_graph()
    config = {"configurable": {"thread_id": thread_id}}

    init = initial_state(thread_id)
    await graph.ainvoke(init, config)
    reset_thread(thread_id)

    return {"thread_id": thread_id, "status": "reset"}
