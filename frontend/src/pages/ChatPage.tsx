import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import ChatHeader from '../components/chat/ChatHeader';
import ChatInput from '../components/chat/ChatInput';
import MessageList from '../components/chat/MessageList';
import WelcomeSuggestions from '../components/chat/WelcomeSuggestions';
import ToolCallCard from '../components/chat/ToolCallCard';
import HistoryDrawer from '../components/chat/HistoryDrawer';
import { useChat } from '../hooks/useChat';
import type { ToolCallLog } from '../types/chat';

const ChatPage: React.FC = () => {
  const { threadId: paramThreadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  // "/chat/new" → threadId 应为 null（需要创建新会话）
  const effectiveThreadId = paramThreadId && paramThreadId !== 'new' ? paramThreadId : null;
  const [threadId, setThreadId] = useState<string | null>(effectiveThreadId);
  const [showWelcome, setShowWelcome] = useState(true);
  const [chatToolLogs, setChatToolLogs] = useState<ToolCallLog[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);

  const {
    messages,
    streamingContent,
    isStreaming,
    toolCallLogs,
    planData,
    activeTier,
    generatingTier,
    sendMessage,
    selectTier,
    loadHistory,
    reset,
  } = useChat({
    threadId,
    onError: (error) => console.error('Chat error:', error),
  });

  // 同步工具日志到展示态。切换会话/新建/发新消息时 toolCallLogs 会被清空，
  // 这里随之清空执行摘要，避免残留上一会话的工具调用摘要。
  useEffect(() => {
    setChatToolLogs(toolCallLogs);
  }, [toolCallLogs]);

  // 历史会话：URL threadId 变化时加载
  useEffect(() => {
    if (!effectiveThreadId) return;
    if (effectiveThreadId === threadId) return;
    setChatToolLogs([]); // 立即清空上一会话的执行摘要，不等历史加载完成
    setThreadId(effectiveThreadId);
    loadHistory(effectiveThreadId);
    setShowWelcome(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectiveThreadId]);

  // 新会话：threadId 为空时创建
  // ref guard 防止 React StrictMode（dev）双调用 effect 导致创建两个会话、产生孤儿
  const creatingRef = useRef(false);
  useEffect(() => {
    if (threadId) return;
    if (creatingRef.current) return;
    creatingRef.current = true;
    fetch('/api/chat', { method: 'POST' })
      .then((res) => res.json())
      .then((data) => {
        setThreadId(data.thread_id);
        navigate(`/chat/${data.thread_id}`, { replace: true });
        creatingRef.current = false;
      })
      .catch((e) => {
        console.error(e);
        creatingRef.current = false;
      });
  }, [threadId, navigate]);

  // 隐藏欢迎页
  useEffect(() => {
    if (messages.length > 0) {
      setShowWelcome(false);
    }
  }, [messages.length]);

  const handleSend = useCallback(
    (message: string) => {
      setShowWelcome(false);
      sendMessage(message);
    },
    [sendMessage]
  );

  const handleNewChat = useCallback(() => {
    reset();
    setThreadId(null);
    setChatToolLogs([]);
    setShowWelcome(true);
    setHistoryOpen(false);
    navigate('/chat/new');
  }, [navigate, reset]);

  const handleSelectHistory = useCallback(
    (tid: string) => {
      setHistoryOpen(false);
      navigate(`/chat/${tid}`);
    },
    [navigate]
  );

  const handleBack = useCallback(() => {
    navigate('/');
  }, [navigate]);

  const runningToolLogs = chatToolLogs.filter((log) => log.status === 'running');

  return (
    <div className="flex flex-col h-screen max-w-lg mx-auto bg-gradient-to-b from-green-50/50 to-blue-50/50">
      <ChatHeader
        onBack={handleBack}
        onOpenHistory={() => setHistoryOpen(true)}
      />

      {/* 欢迎页（首屏无消息时） */}
      {showWelcome && threadId && !isStreaming && messages.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center px-6 pb-16">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 mb-4 rounded-2xl bg-gradient-to-br from-travel-blue to-travel-green shadow-lg">
              <span className="text-4xl">🌍</span>
            </div>
            <h2 className="text-xl font-bold text-gray-800 mb-2">智能旅行规划</h2>
            <p className="text-sm text-gray-500">
              告诉我你的旅行想法，我来帮你规划行程 ✨
            </p>
          </div>
          <WelcomeSuggestions onSelect={handleSend} />
        </div>
      )}

      {/* 消息列表 + 行程卡片（卡片在列表内，跟随滚动） */}
      <MessageList
        messages={messages}
        streamingContent={streamingContent}
        isStreaming={isStreaming}
        planData={planData}
        activeTier={activeTier}
        generatingTier={generatingTier}
        onSelectTier={selectTier}
      />

      {/* 工具调用日志（流式执行中显示） */}
      {isStreaming && runningToolLogs.length > 0 && (
        <div className="max-w-lg mx-auto w-full px-4 pb-2 space-y-1.5">
          {runningToolLogs.map((log) => (
            <ToolCallCard key={log.callId} log={log} />
          ))}
        </div>
      )}

      {/* 已完成工具日志摘要（执行完毕后折叠） */}
      {!isStreaming && chatToolLogs.length > 0 && (
        <div className="max-w-lg mx-auto w-full px-4 pb-2">
          <details className="text-xs text-gray-500">
            <summary className="cursor-pointer hover:text-gray-700">
              执行摘要 ({chatToolLogs.length} 个工具调用)
            </summary>
            <div className="mt-1 space-y-1">
              {chatToolLogs.map((log) => (
                <ToolCallCard key={log.callId} log={log} />
              ))}
            </div>
          </details>
        </div>
      )}

      {/* 输入框（固定底部） */}
      <div className="flex-shrink-0 bg-white/50 backdrop-blur-sm">
        <ChatInput onSend={handleSend} disabled={isStreaming || !threadId} />
      </div>

      {/* 对话历史抽屉 */}
      <HistoryDrawer
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        currentThreadId={threadId}
        onSelect={handleSelectHistory}
        onNewChat={handleNewChat}
      />
    </div>
  );
};

export default ChatPage;
