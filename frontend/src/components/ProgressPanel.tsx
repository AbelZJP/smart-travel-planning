import React from 'react';

interface AgentProgress {
  attractions: string;
  weather: string;
  hotels: string;
  planner: string;
}

interface ProgressPanelProps {
  agentProgress: AgentProgress;
  messages: string[];
}

const AGENTS = [
  { key: 'attractions', label: '景点搜索', icon: '🏛' },
  { key: 'weather', label: '天气查询', icon: '🌤' },
  { key: 'hotels', label: '酒店推荐', icon: '🏨' },
  { key: 'planner', label: '行程规划', icon: '📋' },
] as const;

const ProgressPanel: React.FC<ProgressPanelProps> = ({ agentProgress, messages }) => {
  return (
    <div className="mx-4 mt-4 p-5 bg-white rounded-card shadow-md">
      <h3 className="text-sm font-semibold text-travel-text mb-3">🤖 AI Agent 工作中...</h3>
      <div className="space-y-2">
        {AGENTS.map(({ key, label, icon }) => {
          const status = agentProgress[key as keyof AgentProgress];
          let statusEl: React.ReactNode;
          switch (status) {
            case 'running':
              statusEl = <span className="inline-block w-5 h-5 border-2 border-travel-blue/30 border-t-travel-blue rounded-full animate-spin" />;
              break;
            case 'done':
              statusEl = <span className="text-travel-green font-bold">✓</span>;
              break;
            case 'failed':
              statusEl = <span className="text-red-500 font-bold">✗</span>;
              break;
            default:
              statusEl = <span className="w-5 h-5 inline-block rounded-full border-2 border-gray-200" />;
          }

          return (
            <div key={key}
              className={`flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-colors ${
                status === 'running' ? 'bg-blue-50 text-travel-blue'
                : status === 'done' ? 'bg-green-50 text-travel-green'
                : status === 'failed' ? 'bg-red-50 text-red-500'
                : 'bg-gray-50 text-travel-muted'
              }`}>
              <span className="text-base">{icon}</span>
              <span className="flex-1 font-medium">{label}</span>
              {statusEl}
            </div>
          );
        })}
      </div>
      {messages.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="text-xs text-travel-muted space-y-0.5 max-h-32 overflow-y-auto">
            {messages.map((msg, i) => <div key={i}>{msg}</div>)}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProgressPanel;
