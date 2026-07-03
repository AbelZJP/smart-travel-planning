import React from 'react';

interface ChatHeaderProps {
  onBack?: () => void;
  onOpenHistory?: () => void;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({ onBack, onOpenHistory }) => {
  return (
    <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-lg border-b border-gray-100">
      <div className="max-w-lg mx-auto flex items-center justify-between px-4 h-14">
        <div className="flex items-center gap-1">
          {onBack && (
            <button
              onClick={onBack}
              className="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-gray-100 transition active:scale-95"
            >
              <span className="text-lg">←</span>
            </button>
          )}
          <div className="flex items-center gap-2 ml-1">
            <span className="text-xl">🌍</span>
            <h1 className="text-base font-bold text-gray-800">智能旅行规划</h1>
          </div>
        </div>

        {onOpenHistory && (
          <button
            onClick={onOpenHistory}
            className="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-gray-100 transition active:scale-95"
            title="对话历史"
          >
            <span className="text-lg">☰</span>
          </button>
        )}
      </div>
    </header>
  );
};

export default ChatHeader;
