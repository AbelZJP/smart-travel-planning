import React, { useRef, useCallback, useState } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled = false,
  placeholder = '输入你的旅行需求...',
}) => {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
    // 聚焦回输入框
    setTimeout(() => inputRef.current?.focus(), 0);
  }, [value, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      // Enter 发送，Shift+Enter 换行
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <div className="max-w-lg mx-auto px-4 pb-4 pt-2">
      <div className="flex items-end gap-2 bg-white rounded-2xl shadow-sm border border-gray-200 focus-within:border-travel-blue/50 focus-within:shadow-md transition-all px-4 py-3">
        <div className="flex-1 min-w-0">
          <textarea
            ref={inputRef as React.RefObject<HTMLTextAreaElement>}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="w-full resize-none text-sm text-gray-800 bg-transparent outline-none placeholder-gray-400 max-h-32"
            style={{ lineHeight: '1.5' }}
          />
        </div>

        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-xl bg-gradient-to-r from-travel-blue to-travel-green text-white hover:shadow-md disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-90"
        >
          {disabled ? (
            <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 2L11 13" />
              <path d="M22 2L15 22L11 13L2 9L22 2Z" />
            </svg>
          )}
        </button>
      </div>
      <p className="text-center text-[10px] text-gray-400 mt-1.5">
        Enter 发送 · Shift+Enter 换行
      </p>
    </div>
  );
};

export default ChatInput;
