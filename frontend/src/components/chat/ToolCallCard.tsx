import React, { memo } from 'react';
import type { ToolCallLog } from '../../types/chat';

interface ToolCallCardProps {
  log: ToolCallLog;
}

const TOOL_ICONS: Record<string, string> = {
  search_attractions: '🏛️',
  get_weather_forecast: '🌤️',
  search_hotels: '🏨',
  plan_transport_route: '🚗',
};

const ToolCallCard: React.FC<ToolCallCardProps> = memo(({ log }) => {
  const isRunning = log.status === 'running';
  const isCompleted = log.status === 'completed';
  const isFailed = log.status === 'failed';

  const argsSummary = Object.entries(log.arguments)
    .filter(([_, v]) => typeof v === 'string' || typeof v === 'number')
    .slice(0, 3)
    .map(([k, v]) => `${v}`)
    .join(', ');

  return (
    <div
      className={`flex items-start gap-2 px-3 py-2 rounded-lg text-xs ${
        isRunning
          ? 'bg-blue-50 border border-blue-100'
          : isCompleted
          ? 'bg-green-50 border border-green-100'
          : isFailed
          ? 'bg-red-50 border border-red-100'
          : 'bg-gray-50 border border-gray-100'
      }`}
    >
      <span className="text-base mt-0.5">
        {isRunning ? '⏳' : isCompleted ? '✅' : isFailed ? '❌' : TOOL_ICONS[log.tool] || '🔧'}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="font-medium text-gray-700">{log.displayName}</span>
          {isRunning && (
            <span className="inline-block w-3 h-3 border-2 border-travel-blue/30 border-t-travel-blue rounded-full animate-spin" />
          )}
        </div>
        {argsSummary && (
          <p className="text-gray-500 truncate mt-0.5">{argsSummary}</p>
        )}
        {log.summary && (
          <p className={isCompleted ? 'text-green-600 mt-0.5' : 'text-gray-500 mt-0.5'}>
            {log.summary}
          </p>
        )}
      </div>
    </div>
  );
});

ToolCallCard.displayName = 'ToolCallCard';

export default ToolCallCard;
