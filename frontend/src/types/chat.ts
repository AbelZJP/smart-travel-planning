/** 对话相关 TypeScript 类型定义 */

/** 档位类型 */
export type TierKey = 'economy' | 'comfort' | 'luxury';

export interface ChatMessage {
  messageId: string;
  threadId: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt?: string;
}

export interface SSEChatEvent {
  thread_id: string;
  ts?: string;
}

export interface ChatTokenEvent extends SSEChatEvent {
  token: string;
}

export interface NodeEnterEvent extends SSEChatEvent {
  node: string;
  display_name: string;
}

export interface NodeExitEvent extends SSEChatEvent {
  node: string;
  display_name: string;
  duration_ms: number;
}

export interface ToolCallEvent extends SSEChatEvent {
  tool: string;
  display_name: string;
  arguments: Record<string, unknown>;
  call_id: string;
}

export interface ToolResultEvent extends SSEChatEvent {
  tool: string;
  display_name: string;
  call_id: string;
  summary: string;
  result_count?: number;
}

export interface ChatMessageDoneEvent extends SSEChatEvent {
  message_id: string;
}

/** 两阶段规划·概要事件（generate_plan 结束）*/
export interface PlanOverviewEvent extends SSEChatEvent {
  plan: Record<string, unknown>;
}

/** 两阶段规划·单档详情事件（generate_tier_detail 结束）*/
export interface TierDetailEvent extends SSEChatEvent {
  tier: string;
  plan: Record<string, unknown>;
}

/** 兼容旧版（已废弃，保留类型）*/
export interface PlanGeneratedEvent extends SSEChatEvent {
  tiers: string[];
  costs: Record<string, number>;
}

export interface ErrorEvent extends SSEChatEvent {
  code: string;
  message: string;
}

/** 工具调用日志条目（前端用于渲染 ToolCallCard） */
export interface ToolCallLog {
  callId: string;
  tool: string;
  displayName: string;
  arguments: Record<string, unknown>;
  summary?: string;
  status: 'running' | 'completed' | 'failed';
  timestamp: string;
}

/** 会话元数据（历史列表） */
export interface ThreadInfo {
  thread_id: string;
  title: string;
  created_at: string;
  last_active_at: string;
  message_count: number;
}
