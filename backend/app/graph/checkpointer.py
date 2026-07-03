"""Checkpointer 配置

LangGraph 的 Checkpointer 负责保存/恢复每个 thread_id 的 GraphState，
使得多轮对话可以跨请求恢复上下文（消息、需求、行程计划）。

使用 AsyncSqliteSaver 持久化到本地 SQLite 文件（settings.memory_db_path），
支持 async 图执行（astream_events / ainvoke / aget_state），进程重启后仍可恢复。
必须在应用启动时（async 上下文）调用 init_checkpointer() 完成初始化。
"""
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.config import settings

# 兼容补丁：langgraph-checkpoint-sqlite 2.0.11 的 AsyncSqliteSaver.setup() 会调用
# conn.is_alive()，但 aiosqlite 0.22.x 的 Connection 没有此方法，导致 AttributeError。
# 这里补一个总是返回 True 的实现——连接由本模块管理，init_checkpointer 时已建立。
if not hasattr(aiosqlite.Connection, "is_alive"):
    aiosqlite.Connection.is_alive = lambda self: True  # type: ignore[attr-defined]


_checkpointer: AsyncSqliteSaver = None
_conn = None


async def init_checkpointer() -> AsyncSqliteSaver:
    """在 async 上下文初始化全局 AsyncSqliteSaver（应用启动时调用一次）"""
    global _checkpointer, _conn
    if _checkpointer is None:
        _conn = await aiosqlite.connect(settings.memory_db_path, timeout=30)
        _checkpointer = AsyncSqliteSaver(_conn)
        try:
            await _checkpointer.setup()
        except Exception as e:
            # setup 失败不致命：首次写入时也会建表
            print(f"[checkpointer] setup warning: {e}")
    return _checkpointer


def get_checkpointer() -> AsyncSqliteSaver:
    """返回已初始化的 checkpointer 实例（需先调用 init_checkpointer）"""
    return _checkpointer
