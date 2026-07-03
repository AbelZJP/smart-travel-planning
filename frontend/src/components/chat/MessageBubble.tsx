import React, { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = memo(({ role, content, isStreaming = false }) => {
  const isUser = role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} gap-2`}>
      {/* AI 头像 */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-travel-blue to-travel-green flex items-center justify-center text-sm shadow-sm">
          🌍
        </div>
      )}

      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
          isUser
            ? 'bg-gradient-to-r from-travel-blue to-travel-green text-white shadow-sm'
            : 'bg-white text-gray-800 shadow-sm border border-gray-100'
        } ${isStreaming ? 'animate-in' : ''}`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{content}</p>
        ) : (
          <div className="prose prose-sm max-w-none prose-p:leading-relaxed prose-headings:text-gray-800 prose-strong:text-gray-800 prose-code:px-1 prose-code:py-0.5 prose-code:bg-gray-100 prose-code:rounded prose-code:text-xs">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // 自定义表格样式
                table: ({ node, ...props }) => (
                  <div className="overflow-x-auto my-2">
                    <table className="min-w-full text-xs border-collapse" {...props} />
                  </div>
                ),
                th: ({ node, ...props }) => (
                  <th className="border border-gray-200 bg-gray-50 px-2 py-1 text-left font-medium" {...props} />
                ),
                td: ({ node, ...props }) => (
                  <td className="border border-gray-200 px-2 py-1" {...props} />
                ),
                // 流式输出时给行内代码加闪烁
                code: ({ node, className, children, ...props }) => (
                  <code className={className} {...props}>{children}</code>
                ),
              }}
            >
              {content}
            </ReactMarkdown>
            {isStreaming && (
              <span className="inline-block w-1.5 h-4 bg-travel-blue/60 ml-0.5 animate-pulse align-text-bottom" />
            )}
          </div>
        )}
      </div>

      {/* 用户头像 */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-sm shadow-sm">
          👤
        </div>
      )}
    </div>
  );
});

MessageBubble.displayName = 'MessageBubble';

export default MessageBubble;
