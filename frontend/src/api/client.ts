import axios from 'axios';
import type { PlanRequest, PlanResponse, PlanResult } from '../types/plan';
import type { ThreadInfo } from '../types/chat';

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

/**
 * 对话相关 API
 */

export async function createConversation(): Promise<{ thread_id: string }> {
  const { data } = await api.post('/chat');
  return data;
}

export async function listConversations(): Promise<ThreadInfo[]> {
  const { data } = await api.get<{ threads: ThreadInfo[] }>('/chat');
  return data.threads || [];
}

export async function deleteConversation(threadId: string): Promise<void> {
  await api.delete(`/chat/${threadId}`);
}

export async function sendChatMessage(
  threadId: string,
  message: string
): Promise<Response> {
  return fetch(`/api/chat/${threadId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
}

export function createChatSSEUrl(threadId: string): string {
  return `/api/chat/${threadId}`;
}

export async function getChatHistory(threadId: string) {
  const { data } = await api.get(`/chat/${threadId}/history`);
  return data;
}

export async function getChatPlan(threadId: string) {
  const { data } = await api.get(`/chat/${threadId}/plan`);
  return data;
}
