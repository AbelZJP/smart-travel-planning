import { useState, useCallback } from 'react';
import type {
  PlanRequest,
  PlanResponse,
  PlanResult,
  TierKey,
} from '../types/plan';
import { createPlan, getPlanResult, subscribeToProgress } from '../api/client';

interface AgentProgress {
  attractions: string; // 'idle' | 'running' | 'done' | 'failed'
  weather: string;
  hotels: string;
  planner: string;
}

export function usePlan() {
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
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

  const startPlanning = useCallback(async (request: PlanRequest) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setAgentProgress({
      attractions: 'idle',
      weather: 'idle',
      hotels: 'idle',
      planner: 'idle',
    });
    setProgressMessages([]);

    try {
      const response: PlanResponse = await createPlan(request);
      setTaskId(response.task_id);

      const es = subscribeToProgress(
        response.task_id,
        (event: string, data: Record<string, unknown>) => {
          switch (event) {
            case 'agent_started':
              setAgentProgress((prev) => ({
                ...prev,
                [data.agent as string]: 'running',
              }));
              setProgressMessages((prev) => [
                ...prev,
                `🔍 ${getAgentLabel(data.agent as string)} 查询中...`,
              ]);
              break;
            case 'agent_completed':
              setAgentProgress((prev) => ({
                ...prev,
                [data.agent as string]: 'done',
              }));
              setProgressMessages((prev) => [
                ...prev,
                `✅ ${getAgentLabel(data.agent as string)} 完成`,
              ]);
              break;
            case 'agent_failed':
              setAgentProgress((prev) => ({
                ...prev,
                [data.agent as string]: 'failed',
              }));
              setProgressMessages((prev) => [
                ...prev,
                `❌ ${getAgentLabel(data.agent as string)} 失败: ${data.error}`,
              ]);
              break;
            case 'planning_started':
              setAgentProgress((prev) => ({ ...prev, planner: 'running' }));
              setProgressMessages((prev) => [...prev, '📋 正在生成行程方案...']);
              break;
            case 'planning_completed':
              setAgentProgress((prev) => ({ ...prev, planner: 'done' }));
              break;
            case 'task_done':
              setProgressMessages((prev) => [...prev, '🎉 行程规划完成!']);
              es.close();
              getPlanResult(response.task_id).then(setResult).catch(console.error);
              setLoading(false);
              break;
            case 'task_failed':
              setError((data.error as string) || '规划失败');
              setLoading(false);
              es.close();
              break;
          }
        },
        () => {
          console.error('SSE error');
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : '请求失败');
      setLoading(false);
    }
  }, []);

  return {
    loading,
    taskId,
    result,
    activeTier,
    setActiveTier,
    error,
    agentProgress,
    progressMessages,
    startPlanning,
  };
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
