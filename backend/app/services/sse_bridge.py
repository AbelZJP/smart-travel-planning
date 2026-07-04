"""SSE Bridge — LangGraph astream_events → SSE 推送

监听 LangGraph 图执行中的 astream_events，
将每个事件映射为自定义 SSE 事件推送给前端。

LangGraph v0.2.x astream_events(version="v2") 事件类型：
- on_chat_model_stream: LLM token 输出
- on_chain_start / on_chain_end: 节点/链开始和结束
- on_tool_start / on_tool_end: 工具调用开始和结束
"""
import asyncio
import json
import time
from datetime import datetime
from typing import AsyncGenerator, Dict, Any
from app.services.task_manager import task_manager


# LangGraph 节点名称 → 对外展示名称
NODE_DISPLAY_NAMES = {
    "intent_router": "意图分析",
    "greeting": "问候",
    "extract_requirements": "需求提取",
    "gather_data": "数据采集",
    "generate_plan": "生成概要",
    "generate_tier_detail": "生成档位详情",
    "present_plan": "结果展示",
    "answer_question": "智能问答",
    "replan": "行程调整",
}

# 需要透传给前端的节点名
VISIBLE_NODES = set(NODE_DISPLAY_NAMES.keys())

# 内部节点：这些节点的 LLM 结构化输出不应作为 chat_token 推送到前端
# 只有 answer_question / present_plan 产生的是用户可见的自然语言回复
TOKEN_FILTERED_NODES = {"intent_router", "extract_requirements", "generate_plan", "generate_tier_detail", "replan"}

# LangGraph tool 内部名称 → 前端展示名
TOOL_DISPLAY_NAMES = {
    "search_attractions": "搜索景点",
    "get_weather_forecast": "查询天气",
    "search_hotels": "推荐酒店",
    "plan_transport_route": "规划路线",
    "geocode": "地理编码",
}


async def stream_graph_events(
    thread_id: str,
    events: AsyncGenerator[Dict[str, Any], None],
) -> AsyncGenerator[str, None]:
    """将 LangGraph astream_events 生成器转为 SSE 文本行

    Args:
        thread_id: 会话 ID（作为所有 SSE 事件的公共字段）
        events: graph.astream_events() 返回的异步生成器

    Yields:
        SSE 格式的文本行: "event: xxx\\ndata: {json}\\n\\n"

    保活机制：generate_tier_detail 等节点会调用 LLM，期间可能 10~30s 无事件
    产出（其 token 在 TOKEN_FILTERED_NODES 中被过滤）。经 nginx/HTTP2 反代时空闲
    超过读超时会被掐断（ERR_HTTP2_PROTOCOL_ERROR）。因此用独立 producer 任务
    消费 events 并入队，主循环每 HEARTBEAT_INTERVAL 秒读不到事件就发一条 SSE
    注释 keepalive，保持连接活跃。
    """
    ctx = {
        "node_start_times": {},
        "current_message_id": f"msg_{int(time.time() * 1000)}",
        "current_visible_node": None,
        "aq_streamed": False,  # answer_question 是否已通过 on_chat_model_stream 流式输出
        "_dbg": set(),  # 临时调试：记录已打印过的事件类型，定位后删除
    }

    HEARTBEAT_INTERVAL = 12  # 秒，需小于 nginx 的 proxy_read_timeout
    queue: asyncio.Queue = asyncio.Queue()
    SENTINEL = object()

    async def _producer():
        try:
            async for event in events:
                await queue.put(event)
        except BaseException as exc:  # 透传给主循环抛出，由上层 chat_routes 兜底
            await queue.put(("__error__", exc))
        finally:
            await queue.put(SENTINEL)

    producer_task = asyncio.create_task(_producer())

    try:
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_INTERVAL)
            except asyncio.TimeoutError:
                # 空闲保活：SSE 注释行，前端解析器（仅识别 event:/data:）会忽略
                yield ": keepalive\n\n"
                continue

            if item is SENTINEL:
                break
            if isinstance(item, tuple) and len(item) == 2 and item[0] == "__error__":
                raise item[1]

            async for sse_line in _process_event(item, thread_id, ctx):
                yield sse_line

        # 消息流结束
        yield _format_sse("chat_message_done", {
            "thread_id": thread_id,
            "message_id": ctx["current_message_id"],
        })
    finally:
        if not producer_task.done():
            producer_task.cancel()
            try:
                await producer_task
            except BaseException:
                pass


async def _process_event(
    event: Dict[str, Any],
    thread_id: str,
    ctx: Dict[str, Any],
) -> AsyncGenerator[str, None]:
    """处理单个 LangGraph 事件，产出对应的 SSE 文本行"""
    node_start_times: Dict[str, float] = ctx["node_start_times"]
    kind = event.get("event", "")
    name = event.get("name", "")
    data = event.get("data", {})
    event_id = event.get("run_id", "")

    # 临时调试：记录嵌套 runnable 事件是否被捕获（定位 on_chat_model_stream 不触发的问题）
    if kind in ("on_chat_model_start", "on_chat_model_stream", "on_tool_start", "on_tool_end"):
        key = (kind, ctx["current_visible_node"])
        if key not in ctx["_dbg"]:
            ctx["_dbg"].add(key)
            print(f"[sse_debug] {kind} | node={ctx['current_visible_node']} | name={name}", flush=True)

    try:
        # ── Token 级别 ──
        if kind == "on_chat_model_stream":
            # 如果当前在内部节点中，跳过 token 输出
            if ctx["current_visible_node"] in TOKEN_FILTERED_NODES:
                return
            chunk = data.get("chunk", None)
            token = ""
            if hasattr(chunk, "content"):
                token = chunk.content or ""
            elif isinstance(chunk, dict):
                token = chunk.get("content", "")
            if token:
                # 标记 answer_question 已流式输出，供 on_chain_end 判断是否需要兜底
                if ctx["current_visible_node"] == "answer_question":
                    ctx["aq_streamed"] = True
                yield _format_sse("chat_token", {
                    "thread_id": thread_id,
                    "token": token,
                })

        # ── Chain/节点 级别 ──
        elif kind == "on_chain_start" and name in VISIBLE_NODES:
            node_start_times[name] = time.time()
            ctx["current_visible_node"] = name
            yield _format_sse("node_enter", {
                "thread_id": thread_id,
                "node": name,
                "display_name": NODE_DISPLAY_NAMES.get(name, name),
            })

        elif kind == "on_chain_end" and name in VISIBLE_NODES:
            ctx["current_visible_node"] = None
            start = node_start_times.pop(name, None)
            duration_ms = int((time.time() - start) * 1000) if start else 0
            yield _format_sse("node_exit", {
                "thread_id": thread_id,
                "node": name,
                "display_name": NODE_DISPLAY_NAMES.get(name, name),
                "duration_ms": duration_ms,
            })
            # 提取节点返回的非流式 AIMessage（present_plan 的引导语、extract_requirements 的追问）
            # answer_question 优先靠 on_chat_model_stream 流式输出；若该节点未产生流式 token
            # （部分 LLM 部署不支持流式），在此兜底整条推送，避免回复不显示
            output = data.get("output", {})
            if isinstance(output, dict):
                emit_full_msg = name != "answer_question" or not ctx.get("aq_streamed")
                if emit_full_msg:
                    new_msgs = output.get("messages", [])
                    for msg in new_msgs:
                        msg_type = getattr(msg, "type", "")
                        msg_content = getattr(msg, "content", "") or str(msg)
                        if msg_type == "ai" and msg_content:
                            yield _format_sse("chat_token", {
                                "thread_id": thread_id,
                                "token": msg_content,
                            })
                if name == "answer_question":
                    ctx["aq_streamed"] = False  # 重置，供下一轮对话使用

                # generate_plan → plan_overview 事件（三档概要）
                if name == "generate_plan":
                    plan_data = output.get("plan", {})
                    if plan_data:
                        yield _format_sse("plan_overview", {
                            "thread_id": thread_id,
                            "plan": plan_data,
                        })

                # generate_tier_detail → tier_detail 事件（单档详情）
                if name == "generate_tier_detail":
                    plan_data = output.get("plan", {})
                    tier = output.get("active_tier", "comfort")
                    if plan_data:
                        yield _format_sse("tier_detail", {
                            "thread_id": thread_id,
                            "tier": tier,
                            "plan": plan_data,
                        })

        # ── 工具级别 ──
        elif kind == "on_tool_start":
            tool_input = data.get("input", {})
            yield _format_sse("tool_call", {
                "thread_id": thread_id,
                "tool": name,
                "display_name": TOOL_DISPLAY_NAMES.get(name, name),
                "arguments": tool_input,
                "call_id": event_id,
            })
            # 同时推给 task_manager（兼容旧版事件机制）
            await task_manager.push_event(thread_id, "tool_call", {
                "tool": name,
                "arguments": tool_input,
            })

        elif kind == "on_tool_end":
            output = data.get("output", "")
            summary = _summarize_tool_output(name, output)
            yield _format_sse("tool_result", {
                "thread_id": thread_id,
                "tool": name,
                "display_name": TOOL_DISPLAY_NAMES.get(name, name),
                "call_id": event_id,
                "summary": summary,
            })

    except Exception as e:
        print(f"[sse_bridge] Error processing event {kind}/{name}: {e}")


def _summarize_tool_output(tool_name: str, output: Any) -> str:
    """对工具输出做文本摘要，不把大量原始数据推给前端"""
    if isinstance(output, list):
        return f"找到 {len(output)} 个结果"
    if isinstance(output, dict):
        if "forecasts" in output:
            return f"获取 {len(output['forecasts'])} 天天气预报"
        if "distance_m" in output:
            dist = output.get("distance_m", 0)
            cost = output.get("cost_estimated", 0)
            return f"距离 {dist/1000:.1f}km，预估费用 ¥{cost}"
        for key in ("economy", "comfort", "luxury"):
            if key in output and isinstance(output[key], list):
                total = sum(len(v) for v in output.values() if isinstance(v, list))
                return f"找到 {total} 个酒店"
    summary = str(output)[:80] if output else "执行完成"
    return summary


def _format_sse(event_type: str, data: dict) -> str:
    """格式化为 SSE 协议文本"""
    data_str = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {data_str}\n\n"
