import React from 'react';

const TypingIndicator: React.FC = () => {
  return (
    <div className="flex items-start gap-2">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-travel-blue to-travel-green flex items-center justify-center text-sm shadow-sm">
        🌍
      </div>
      <div className="bg-white rounded-2xl px-4 py-3 shadow-sm border border-gray-100">
        <div className="flex gap-1.5">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
