import React, { useEffect, useRef } from 'react';
import type { ChatMessage, TierKey } from '../../types/chat';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import PlanCard from './PlanCard';

interface MessageListProps {
  messages: ChatMessage[];
  streamingContent: string;
  isStreaming: boolean;
  planData: Record<string, unknown> | null;
  activeTier: TierKey;
  generatingTier: TierKey | null;
  onSelectTier: (tier: TierKey) => void;
}

const MessageList: React.FC<MessageListProps> = ({
  messages,
  streamingContent,
  isStreaming,
  planData,
  activeTier,
  generatingTier,
  onSelectTier,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const prevLengthRef = useRef(0);

  // 自动滚动到底部（只在有新消息时滚动，避免打断手动滚动）
  useEffect(() => {
    if (messages.length > prevLengthRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    prevLengthRef.current = messages.length;
  }, [messages.length]);

  // 流式输出 / 行程卡片更新时持续滚动
  useEffect(() => {
    if (isStreaming) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [streamingContent, isStreaming, planData]);

  const hasContent = messages.length > 0 || streamingContent || planData;
  if (!hasContent) return null;

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.messageId} role={msg.role} content={msg.content} />
      ))}

      {/* 流式消息 */}
      {streamingContent && (
        <MessageBubble role="assistant" content={streamingContent} isStreaming />
      )}

      {/* 输入中指示器 */}
      {isStreaming && !streamingContent && <TypingIndicator />}

      {/* 行程卡片（跟随消息流滚动，不再固定挡住对话） */}
      {planData && (
        <PlanCard
          planData={planData}
          activeTier={activeTier}
          generatingTier={generatingTier}
          onSelectTier={onSelectTier}
        />
      )}

      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;
