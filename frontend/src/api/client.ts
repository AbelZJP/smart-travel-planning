import axios from 'axios';
import type { PlanRequest, PlanResponse, PlanResult } from '../types/plan';

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

export async function createPlan(request: PlanRequest): Promise<PlanResponse> {
  const { data } = await api.post<PlanResponse>('/plan', request);
  return data;
}

export function subscribeToProgress(
  taskId: string,
  onEvent: (event: string, data: Record<string, unknown>) => void,
  onError: (error: Event) => void
): EventSource {
  const es = new EventSource(`/api/plan/${taskId}/status`);

  const eventTypes = [
    'agent_started',
    'agent_progress',
    'agent_completed',
    'agent_failed',
    'planning_started',
    'planning_completed',
    'task_done',
    'task_failed',
    'heartbeat',
    'error',
  ];

  eventTypes.forEach((type) => {
    es.addEventListener(type, (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        onEvent(type, data);
      } catch {
        onEvent(type, { raw: e.data });
      }
    });
  });

  es.onerror = onError;

  return es;
}

export async function getPlanResult(taskId: string): Promise<PlanResult> {
  const { data } = await api.get<PlanResult>(`/plan/${taskId}/result`);
  return data;
}
