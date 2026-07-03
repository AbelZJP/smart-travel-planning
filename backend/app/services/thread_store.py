"""会话线程元数据持久化 (thread_store)

存储每个对话的元信息（thread_id, title, created_at, last_active_at, message_count），
配合 LangGraph Checkpointer（存 GraphState）实现完整的会话历史管理：
- Checkpointer 保存对话状态（消息/需求/行程）
- thread_store 保存会话列表与标题，用于"历史会话"展示

使用独立 SQLite 表 `threads`，与 checkpointer 的表共用同一 db 文件。
所有写操作通过全局锁串行化，避免 SQLite 写并发冲突。
"""
import sqlite3
import threading
from datetime import datetime
from typing import Optional, List
from app.config import settings


_lock = threading.Lock()
_conn: sqlite3.Connection = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(settings.memory_db_path, check_same_thread=False, timeout=30)
        _conn.row_factory = sqlite3.Row
        _init_db(_conn)
    return _conn


def _init_db(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS threads (
            thread_id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '新对话',
            created_at TEXT NOT NULL,
            last_active_at TEXT NOT NULL,
            message_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def create_thread(thread_id: str, title: str = "新对话", message_count: int = 0) -> dict:
    """新建会话记录（若已存在则忽略）"""
    now = _now()
    with _lock:
        conn = _get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO threads (thread_id, title, created_at, last_active_at, message_count) "
            "VALUES (?, ?, ?, ?, ?)",
            (thread_id, title, now, now, message_count),
        )
        conn.commit()
    return get_thread(thread_id)


def list_threads(limit: int = 100) -> List[dict]:
    """列出所有会话，按最后活跃时间倒序"""
    with _lock:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT thread_id, title, created_at, last_active_at, message_count "
            "FROM threads ORDER BY last_active_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_thread(thread_id: str) -> Optional[dict]:
    with _lock:
        conn = _get_conn()
        row = conn.execute(
            "SELECT thread_id, title, created_at, last_active_at, message_count "
            "FROM threads WHERE thread_id = ?",
            (thread_id,),
        ).fetchone()
    return dict(row) if row else None


def update_thread(
    thread_id: str,
    title: Optional[str] = None,
    bump_active: bool = True,
    increment_messages: int = 0,
) -> None:
    """更新会话元数据：可选地设置标题、刷新活跃时间、累加消息数"""
    now = _now()
    with _lock:
        conn = _get_conn()
        if title is not None:
            conn.execute(
                "UPDATE threads SET title = ?, last_active_at = ?, message_count = message_count + ? "
                "WHERE thread_id = ?",
                (title, now, increment_messages, thread_id),
            )
        elif bump_active or increment_messages:
            conn.execute(
                "UPDATE threads SET last_active_at = ?, message_count = message_count + ? "
                "WHERE thread_id = ?",
                (now, increment_messages, thread_id),
            )
        conn.commit()


def delete_thread(thread_id: str) -> None:
    """删除会话元数据记录（GraphState 由调用方清理 checkpointer）"""
    with _lock:
        conn = _get_conn()
        conn.execute("DELETE FROM threads WHERE thread_id = ?", (thread_id,))
        conn.commit()


def reset_thread(thread_id: str) -> None:
    """重置会话：标题归为“新对话”、消息数归零、刷新活跃时间"""
    now = _now()
    with _lock:
        conn = _get_conn()
        conn.execute(
            "UPDATE threads SET title = '新对话', message_count = 0, last_active_at = ? "
            "WHERE thread_id = ?",
            (now, thread_id),
        )
        conn.commit()
