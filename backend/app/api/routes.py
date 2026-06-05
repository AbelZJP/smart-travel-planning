import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.request import PlanRequest
from app.schemas.response import PlanResponse, TaskStatus
from app.services.task_manager import task_manager
from app.agents.orchestrator import run_travel_planning

router = APIRouter(prefix="/api", tags=["planning"])


@router.post("/plan", response_model=PlanResponse)
async def create_plan(request: PlanRequest):
    """创建旅行规划任务"""
    from datetime import datetime
    if request.destination == request.origin:
        raise HTTPException(status_code=400, detail="出发地和目的地不能相同")
    if request.start_date < datetime.now().strftime("%Y-%m-%d"):
        raise HTTPException(status_code=400, detail="出发日期不能早于今天")

    task_id = task_manager.create_task()
    asyncio.create_task(run_travel_planning(task_id, request))

    status = task_manager.get_status(task_id)
    return PlanResponse(
        task_id=task_id,
        status=status["status"],
        created_at=status["created_at"],
    )


@router.get("/plan/{task_id}/status")
async def get_plan_status(task_id: str):
    """SSE 端点 - 实时推送任务进度"""
    status = task_manager.get_status(task_id)
    if status.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="任务不存在")

    return StreamingResponse(
        task_manager.event_stream(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/plan/{task_id}/result")
async def get_plan_result(task_id: str):
    """获取规划结果"""
    result = task_manager.get_result(task_id)
    if not result:
        status = task_manager.get_status(task_id)
        if status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="任务不存在")
        raise HTTPException(status_code=202, detail=f"任务尚未完成，当前状态: {status['status']}")
    return result
