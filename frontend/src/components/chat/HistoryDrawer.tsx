import React, { useEffect, useState } from 'react';
import type { ThreadInfo } from '../../types/chat';
import { listConversations, deleteConversation } from '../../api/client';

interface HistoryDrawerProps {
  open: boolean;
  onClose: () => void;
  currentThreadId: string | null;
  onSelect: (threadId: string) => void;
  onNewChat: () => void;
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    const now = new Date();
    if (d.toDateString() === now.toDateString()) {
      return d.toTimeString().slice(0, 5);
    }
    return `${d.getMonth() + 1}/${d.getDate()}`;
  } catch {
    return '';
  }
}

const HistoryDrawer: React.FC<HistoryDrawerProps> = ({
  open,
  onClose,
  currentThreadId,
  onSelect,
  onNewChat,
}) => {
  const [threads, setThreads] = useState<ThreadInfo[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const list = await listConversations();
      setThreads(list);
    } catch (e) {
      console.error('加载会话列表失败:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) refresh();
  }, [open]);

  const handleDelete = async (tid: string) => {
    if (!window.confirm('确定删除这个对话？此操作不可恢复。')) return;
    try {
      await deleteConversation(tid);
      if (tid === currentThreadId) {
        // 删的是当前会话：新建一个空白会话并关闭抽屉
        onNewChat();
        onClose();
      } else {
        // 删的是其他会话：重新加载列表，确保与后端一致
        await refresh();
      }
    } catch (e) {
      console.error('删除会话失败:', e);
      window.alert('删除失败，请稍后重试');
    }
  };

  const handleSelect = (tid: string) => {
    onSelect(tid);
    onClose();
  };

  return (
    <>
      {/* 遮罩 */}
      {open && (
        <div className="fixed inset-0 bg-black/30 z-30" onClick={onClose} />
      )}
      {/* 抽屉 */}
      <div
        className={`fixed top-0 left-0 h-full w-72 bg-white z-40 shadow-xl transition-transform duration-300 flex flex-col ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h2 className="font-bold text-gray-800">对话历史</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition"
          >
            ✕
          </button>
        </div>

        <div className="p-3 border-b border-gray-100">
          <button
            onClick={() => {
              onNewChat();
              onClose();
            }}
            className="w-full px-3 py-2 text-sm text-travel-blue bg-blue-50 rounded-lg hover:bg-blue-100 transition font-medium"
          >
            ✨ 新对话
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-1">
          {loading && (
            <p className="text-xs text-gray-400 text-center py-4">加载中…</p>
          )}
          {!loading && threads.length === 0 && (
            <p className="text-xs text-gray-400 text-center py-4">
              还没有对话记录
            </p>
          )}
          {threads.map((t) => (
            <div
              key={t.thread_id}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 cursor-pointer transition ${
                t.thread_id === currentThreadId ? 'bg-blue-50' : 'hover:bg-gray-50'
              }`}
              onClick={() => handleSelect(t.thread_id)}
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-700 truncate">
                  {t.title || '新对话'}
                </div>
                <div className="text-[10px] text-gray-400">
                  {t.message_count} 条 · {formatTime(t.last_active_at)}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(t.thread_id);
                }}
                className="shrink-0 text-gray-300 hover:text-red-500 text-base transition px-1 py-1 active:scale-90"
                title="删除对话"
              >
                🗑
              </button>
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

export default HistoryDrawer;
