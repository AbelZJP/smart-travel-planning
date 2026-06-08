import React, { createContext, useContext, useCallback, useState, useRef } from 'react';
import type { PlanRequest, PlanResult, TierKey } from '../types/plan';
import { createPlan, getPlanResult, subscribeToProgress } from '../api/client';

export interface AgentProgress {
  attractions: string;
  weather: string;
  hotels: string;
  planner: string;
}

export interface PlanContextType {
  loading: boolean;
  result: PlanResult | null;
  activeTier: TierKey;
  setActiveTier: (tier: TierKey) => void;
  error: string | null;
  agentProgress: AgentProgress;
  progressMessages: string[];
  startPlanning: (request: PlanRequest) => void;
}

const PlanContext = createContext<PlanContextType | null>(null);

export function PlanProvider({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PlanResult | null>(null);
  const [activeTier, setActiveTier] = useState<TierKey>('economy');
  const [error, setError] = useState<string | null>(null);
  const [agentProgress, setAgentProgress] = useState<AgentProgress>({
    attractions: 'idle',
    weather: 'idle',
    hotels: 'idle',
    planner: 'idle',
  });
  const [progressMessages, setProgressMessages] = useState<string[]>([]);
  const esRef = useRef<EventSource | null>(null);

  const startPlanning = useCallback(async (request: PlanRequest) => {
    // 清理旧的 SSE 连接
    if (esRef.current) {
      esRef.current.close();
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setAgentProgress({ attractions: 'idle', weather: 'idle', hotels: 'idle', planner: 'idle' });
    setProgressMessages([]);

    try {
      const response = await createPlan(request);

      const es = subscribeToProgress(
        response.task_id,
        (event: string, data: Record<string, unknown>) => {
          switch (event) {
            case 'agent_started':
              setAgentProgress((prev) => ({ ...prev, [data.agent as string]: 'running' }));
              setProgressMessages((prev) => [...prev, `${getAgentIcon(data.agent as string)} ${getAgentLabel(data.agent as string)} 查询中...`]);
              break;
            case 'agent_completed':
              setAgentProgress((prev) => ({ ...prev, [data.agent as string]: 'done' }));
              setProgressMessages((prev) => [...prev, `${getAgentIcon(data.agent as string)} ${getAgentLabel(data.agent as string)} 完成`]);
              break;
            case 'agent_failed':
              setAgentProgress((prev) => ({ ...prev, [data.agent as string]: 'failed' }));
              break;
            case 'planning_started':
              setAgentProgress((prev) => ({ ...prev, planner: 'running' }));
              setProgressMessages((prev) => [...prev, '🧠 正在生成行程方案...']);
              break;
            case 'planning_completed':
              setAgentProgress((prev) => ({ ...prev, planner: 'done' }));
              break;
            case 'task_done':
              es.close();
              getPlanResult(response.task_id).then((data) => {
                setResult(data);
                setLoading(false);
              }).catch(console.error);
              break;
            case 'task_failed':
              setError((data.error as string) || '规划失败');
              setLoading(false);
              es.close();
              break;
          }
        },
        () => { /* SSE error, ignore */ }
      );
      esRef.current = es;
    } catch (err) {
      setError(err instanceof Error ? err.message : '请求失败');
      setLoading(false);
    }
  }, []);

  return (
    <PlanContext.Provider value={{ loading, result, activeTier, setActiveTier, error, agentProgress, progressMessages, startPlanning }}>
      {children}
    </PlanContext.Provider>
  );
}

export function usePlanContext() {
  const ctx = useContext(PlanContext);
  if (!ctx) throw new Error('usePlanContext must be inside PlanProvider');
  return ctx;
}

function getAgentLabel(agent: string): string {
  const labels: Record<string, string> = {
    attractions: '景点搜索',
    weather: '天气查询',
    hotels: '酒店推荐',
    planner: '行程规划',
  };
  return labels[agent] || agent;
}

function getAgentIcon(agent: string): string {
  const icons: Record<string, string> = {
    attractions: '🏛',
    weather: '🌤',
    hotels: '🏨',
    planner: '📋',
  };
  return icons[agent] || '🤖';
}
