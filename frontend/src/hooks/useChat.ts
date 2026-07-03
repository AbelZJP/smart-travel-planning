/** 对话 Hook — useChat

管理 Web SSE 连接、消息列表、流式渲染、工具调用日志与行程计划。
两阶段规划：plan_overview（概要）→ tier_detail（选档详情）。
*/
import { useState, useRef, useCallback, useEffect } from 'react';
import type { ChatMessage, ToolCallLog, TierKey } from '../types/chat';
import { getChatHistory, getChatPlan } from '../api/client';

interface UseChatOptions {
  threadId: string | null;
  onError?: (error: string) => void;
}

export function useChat({ threadId, onError }: UseChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [toolCallLogs, setToolCallLogs] = useState<ToolCallLog[]>([]);
  const [planData, setPlanData] = useState<Record<string, unknown> | null>(null);
  const [activeTier, setActiveTier] = useState<TierKey>('comfort');
  const [generatingTier, setGeneratingTier] = useState<TierKey | null>(null);

  const currentStreamingRef = useRef('');
  const rafRef = useRef<number | null>(null);

  // 批量更新流式内容（使用 requestAnimationFrame）
  const scheduleStreamingUpdate = useCallback((content: string) => {
    currentStreamingRef.current = content;
    if (rafRef.current !== null) return;
    rafRef.current = requestAnimationFrame(() => {
      setStreamingContent(currentStreamingRef.current);
      rafRef.current = null;
    });
  }, []);

  const handleChatToken = useCallback((data: { token: string }) => {
    const newContent = currentStreamingRef.current + data.token;
    scheduleStreamingUpdate(newContent);
  }, [scheduleStreamingUpdate]);

  const handleChatMessageDone = useCallback((data: { message_id: string }) => {
    const finalContent = currentStreamingRef.current;
    if (finalContent) {
      const assistantMessage: ChatMessage = {
        messageId: data.message_id || `ai_${Date.now()}`,
        threadId: threadId || '',
        role: 'assistant',
        content: finalContent,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    }
    currentStreamingRef.current = '';
    scheduleStreamingUpdate('');
  }, [threadId, scheduleStreamingUpdate]);

  const handleToolCall = useCallback((data: { tool: string; display_name?: string; call_id: string; arguments: Record<string, unknown> }) => {
    const log: ToolCallLog = {
      callId: data.call_id,
      tool: data.tool,
      displayName: data.display_name || data.tool,
      arguments: data.arguments,
      status: 'running',
      timestamp: new Date().toISOString(),
    };
    setToolCallLogs((prev) => [...prev, log]);
  }, []);

  const handleToolResult = useCallback((data: { tool: string; call_id: string; summary: string; display_name?: string }) => {
    setToolCallLogs((prev) =>
      prev.map((log) =>
        log.callId === data.call_id ? { ...log, status: 'completed', summary: data.summary } : log
      )
    );
  }, []);

  const handleEvent = useCallback((event: string, data: Record<string, unknown>) => {
    switch (event) {
      case 'chat_token':
        handleChatToken(data as { token: string });
        break;
      case 'chat_message_done':
        handleChatMessageDone(data as { message_id: string });
        break;
      case 'tool_call':
        handleToolCall(data as { tool: string; display_name?: string; call_id: string; arguments: Record<string, unknown> });
        break;
      case 'tool_result':
        handleToolResult(data as { tool: string; call_id: string; summary: string; display_name?: string });
        break;
      case 'plan_overview': {
        const plan = (data as { plan: Record<string, unknown> }).plan;
        setPlanData(plan);
        break;
      }
      case 'tier_detail': {
        const { tier, plan } = data as { tier: TierKey; plan: Record<string, unknown> };
        setPlanData(plan);
        setActiveTier(tier);
        setGeneratingTier(null);
        break;
      }
      case 'error':
        onError?.((data.message as string) || '未知错误');
        setGeneratingTier(null);
        break;
    }
  }, [onError, handleChatToken, handleChatMessageDone, handleToolCall, handleToolResult]);

  // 通用 SSE 消费：读取 Response 流并派发事件
  const consumeSSEResponse = useCallback(async (response: Response) => {
    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      let currentEvent = '';
      let currentData = '';
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          currentData = line.slice(6).trim();
        } else if (line === '' && currentEvent && currentData) {
          try {
            const data = JSON.parse(currentData);
            handleEvent(currentEvent, data);
          } catch {
            // ignore parse errors
          }
          currentEvent = '';
          currentData = '';
        }
      }
    }
  }, [handleEvent]);

  const sendMessage = useCallback(async (content: string) => {
    if (!threadId || !content.trim() || isStreaming) return;

    const userMessage: ChatMessage = {
      messageId: `user_${Date.now()}`,
      threadId,
      role: 'user',
      content: content.trim(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsStreaming(true);
    setStreamingContent('');
    setToolCallLogs([]);

    try {
      const response = await fetch(`/api/chat/${threadId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content.trim() }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      await consumeSSEResponse(response);
    } catch (err) {
      onError?.(err instanceof Error ? err.message : '发送失败');
    } finally {
      setIsStreaming(false);
    }
  }, [threadId, isStreaming, onError, consumeSSEResponse]);

  const selectTier = useCallback(async (tier: TierKey) => {
    if (!threadId || isStreaming) return;
    setActiveTier(tier);

    // 已有详情则只切换，不重新生成
    const details = planData?.details as Record<string, { daily_plans?: unknown[] }> | undefined;
    if (details && details[tier]?.daily_plans?.length) {
      return;
    }

    setGeneratingTier(tier);
    setIsStreaming(true);
    setStreamingContent('');

    try {
      const response = await fetch(`/api/chat/${threadId}/tier/${tier}`, { method: 'POST' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      await consumeSSEResponse(response);
    } catch (err) {
      onError?.(err instanceof Error ? err.message : '生成失败');
      setGeneratingTier(null);
    } finally {
      setIsStreaming(false);
    }
  }, [threadId, isStreaming, planData, onError, consumeSSEResponse]);

  const loadHistory = useCallback(async (tid: string) => {
    try {
      const hist = await getChatHistory(tid);
      const msgs: ChatMessage[] = ((hist.messages as Array<{ message_id: string; role: string; content: string }>) || []).map((m) => ({
        messageId: m.message_id,
        threadId: tid,
        role: m.role as 'user' | 'assistant',
        content: m.content,
      }));
      setMessages(msgs);
      setToolCallLogs([]);
      setStreamingContent('');
      currentStreamingRef.current = '';

      try {
        const plan = await getChatPlan(tid);
        setPlanData(plan as Record<string, unknown>);
        const details = (plan as { details?: Record<string, { daily_plans?: unknown[] }> })?.details || {};
        const firstWithDetail = (['comfort', 'economy', 'luxury'] as TierKey[]).find((t) => details[t]?.daily_plans?.length);
        setActiveTier(firstWithDetail || 'comfort');
      } catch {
        setPlanData(null);
        setActiveTier('comfort');
      }
    } catch (err) {
      onError?.(err instanceof Error ? err.message : '加载历史失败');
    }
  }, [onError]);

  const reset = useCallback(() => {
    setMessages([]);
    setPlanData(null);
    setStreamingContent('');
    setToolCallLogs([]);
    setGeneratingTier(null);
    setActiveTier('comfort');
    currentStreamingRef.current = '';
  }, []);

  // 清理
  useEffect(() => {
    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, []);

  return {
    messages,
    streamingContent,
    isStreaming,
    toolCallLogs,
    planData,
    activeTier,
    generatingTier,
    sendMessage,
    selectTier,
    loadHistory,
    reset,
  };
}
