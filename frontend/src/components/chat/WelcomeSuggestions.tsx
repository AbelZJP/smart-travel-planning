import React from 'react';

interface WelcomeSuggestionsProps {
  onSelect: (text: string) => void;
}

const SUGGESTIONS = [
  { icon: '🏛️', text: '去杭州玩 3 天，预算 3000' },
  { icon: '🏔️', text: '从北京出发去成都，喜欢自然风光' },
  { icon: '🍜', text: '想去广州吃美食，4 天预算 5000' },
  { icon: '🏖️', text: '三亚亲子游，5 天预算 8000' },
];

const WelcomeSuggestions: React.FC<WelcomeSuggestionsProps> = ({ onSelect }) => {
  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-500 font-medium text-center">试试这些 👇</p>
      <div className="grid grid-cols-1 gap-2">
        {SUGGESTIONS.map((s, i) => (
          <button
            key={i}
            onClick={() => onSelect(s.text)}
            className="flex items-center gap-2 px-4 py-3 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:border-travel-blue/30 transition-all active:scale-[0.98] text-left"
          >
            <span className="text-lg">{s.icon}</span>
            <span className="text-sm text-gray-700">{s.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default WelcomeSuggestions;
