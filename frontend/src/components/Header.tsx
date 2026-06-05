import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="px-6 pt-8 pb-4 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 mb-3 rounded-2xl bg-gradient-to-br from-travel-blue to-travel-green shadow-lg">
        <span className="text-3xl">🌍</span>
      </div>
      <h1 className="text-2xl font-bold text-travel-text">智能旅行规划</h1>
      <p className="mt-1 text-sm text-travel-muted">输入需求，一键生成专属行程</p>
    </header>
  );
};

export default Header;
