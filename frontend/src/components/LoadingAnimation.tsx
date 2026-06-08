import React from 'react';

const LoadingAnimation: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      {/* 中心旋转地球 */}
      <div className="relative w-28 h-28 mb-8">
        {/* 外圈脉冲 */}
        <div className="absolute inset-0 rounded-full border-2 border-travel-blue/20 animate-ping" />
        {/* 中圈旋转 */}
        <div className="absolute inset-2 rounded-full border-2 border-t-transparent border-travel-green animate-spin" style={{ animationDuration: '3s' }} />
        {/* 内圈反向旋转 */}
        <div className="absolute inset-4 rounded-full border-2 border-travel-blue/30 border-t-travel-blue animate-spin" style={{ animationDuration: '2s', animationDirection: 'reverse' }} />
        {/* 中心地球 */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-5xl animate-pulse" style={{ animationDuration: '2s' }}>🌍</span>
        </div>
      </div>

      {/* 粒子点 */}
      <div className="flex gap-3 mb-6">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2.5 h-2.5 rounded-full bg-travel-blue/60 animate-bounce"
            style={{ animationDelay: `${i * 0.15}s`, animationDuration: '1s' }}
          />
        ))}
      </div>

      {/* 扫描线动画 */}
      <div className="relative w-60 h-1.5 bg-gray-100 rounded-full overflow-hidden mb-3">
        <div className="absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-travel-blue to-transparent rounded-full animate-pulse" />
      </div>
      <p className="text-sm text-travel-muted font-medium">AI 智能规划中...</p>
    </div>
  );
};

export default LoadingAnimation;
