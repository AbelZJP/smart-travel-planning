import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.schemas.response import TaskStatus, PlanResult


class TaskManager:
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._results: Dict[str, PlanResult] = {}
        self._queues: Dict[str, asyncio.Queue] = {}

    def create_task(self) -> str:
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = {
            "status": TaskStatus.pending,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "events": [],
        }
        self._queues[task_id] = asyncio.Queue()
        return task_id

    def get_status(self, task_id: str) -> Dict[str, Any]:
        task = self._tasks.get(task_id)
        if not task:
            return {"status": "not_found"}
        return {"task_id": task_id, "status": task["status"], "created_at": task["created_at"]}

    async def update_status(self, task_id: str, status: TaskStatus):
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = status

    async def push_event(self, task_id: str, event: str, data: Optional[Dict[str, Any]] = None):
        """推送 SSE 事件到任务的队列"""
        if task_id in self._queues:
            payload = {
                "event": event,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data or {},
            }
            await self._queues[task_id].put(payload)
        if task_id in self._tasks:
            self._tasks[task_id]["events"].append({"event": event, "data": data})

    async def event_stream(self, task_id: str):
        """SSE 事件生成器，前端通过 EventSource 消费"""
        if task_id not in self._queues:
            yield f"event: error\ndata: {{\"error\": \"task not found\"}}\n\n"
            return
        queue = self._queues[task_id]
        while True:
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=30)
                event_type = payload["event"]
                import json
                data_str = json.dumps(payload["data"], ensure_ascii=False)
                yield f"event: {event_type}\ndata: {data_str}\n\n"
                if event_type in ("task_done", "task_failed"):
                    break
            except asyncio.TimeoutError:
                yield f"event: heartbeat\ndata: {{\"ts\": \"{datetime.now(timezone.utc).isoformat()}\"}}\n\n"

    def store_result(self, task_id: str, result: PlanResult):
        self._results[task_id] = result

    def get_result(self, task_id: str) -> Optional[PlanResult]:
        return self._results.get(task_id)

    def cleanup(self, task_id: str):
        self._tasks.pop(task_id, None)
        self._results.pop(task_id, None)
        self._queues.pop(task_id, None)


task_manager = TaskManager()
