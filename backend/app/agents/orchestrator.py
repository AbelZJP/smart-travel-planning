import asyncio
import traceback
from typing import Dict, Any, List
from app.schemas.request import PlanRequest
from app.schemas.response import PlanResult, TaskStatus
from app.services.task_manager import task_manager
from app.agents.attraction_agent import run_attraction_agent
from app.agents.weather_agent import run_weather_agent
from app.agents.hotel_agent import run_hotel_agent
from app.agents.planner_agent import run_planner_agent


async def run_travel_planning(task_id: str, request: PlanRequest):
    """编排执行完整的旅行规划流程。

    1. 三个 Agent 完全并行执行
    2. 等待全部完成后运行规划协调 Agent
    3. 通过 SSE 实时推送进度
    """
    try:
        await task_manager.update_status(task_id, TaskStatus.running)

        # --- Phase 1: 三个 Agent 并行执行 ---
        await task_manager.push_event(task_id, "agent_started", {"agent": "attractions"})
        await task_manager.push_event(task_id, "agent_started", {"agent": "weather"})
        await task_manager.push_event(task_id, "agent_started", {"agent": "hotels"})

        attractions_task = asyncio.create_task(
            run_attraction_agent(
                destination=request.destination,
                days=request.days,
                preferences=[p.value for p in request.preferences],
            )
        )
        weather_task = asyncio.create_task(
            run_weather_agent(
                destination=request.destination,
                start_date=request.start_date,
                days=request.days,
            )
        )
        hotels_task = asyncio.create_task(
            run_hotel_agent(destination=request.destination)
        )

        attractions, weather, hotels = await asyncio.gather(
            attractions_task, weather_task, hotels_task, return_exceptions=True
        )

        # 处理景点结果
        if isinstance(attractions, Exception):
            await task_manager.push_event(
                task_id, "agent_failed",
                {"agent": "attractions", "error": str(attractions)},
            )
            attractions = []
        else:
            await task_manager.push_event(
                task_id, "agent_completed",
                {"agent": "attractions", "found": len(attractions)},
            )
        await task_manager.update_status(task_id, TaskStatus.attractions_done)

        # 处理天气结果
        if isinstance(weather, Exception):
            await task_manager.push_event(
                task_id, "agent_failed",
                {"agent": "weather", "error": str(weather)},
            )
            weather = []
        else:
            await task_manager.push_event(
                task_id, "agent_completed",
                {"agent": "weather", "days_covered": len(weather)},
            )
        await task_manager.update_status(task_id, TaskStatus.weather_done)

        # 处理酒店结果
        if isinstance(hotels, Exception):
            await task_manager.push_event(
                task_id, "agent_failed",
                {"agent": "hotels", "error": str(hotels)},
            )
            hotels = {"economy": [], "comfort": [], "luxury": []}
        else:
            await task_manager.push_event(
                task_id, "agent_completed",
                {"agent": "hotels", "hotels_found": sum(len(v) for v in hotels.values())},
            )
        await task_manager.update_status(task_id, TaskStatus.hotels_done)

        # --- Phase 2: 规划协调 ---
        await task_manager.update_status(task_id, TaskStatus.planning)
        await task_manager.push_event(task_id, "planning_started", {})

        plan = await run_planner_agent(
            origin=request.origin,
            destination=request.destination,
            budget=request.budget,
            intercity_mode=request.intercity_mode.value,
            city_transit=request.city_transit.value,
            days=request.days,
            preferences=[p.value for p in request.preferences],
            start_date=request.start_date,
            attractions=attractions if isinstance(attractions, list) else [],
            weather=weather if isinstance(weather, list) else [],
            hotels=hotels,
        )

        await task_manager.push_event(task_id, "planning_completed", {})

        # --- 构建结果 ---
        from app.schemas.response import (
            TierPlan, DailyPlan, AttractionItem, HotelItem,
            MealItem, TransportItem, RouteCoordinate,
        )

        def build_tier_plan(tier_data: dict) -> TierPlan:
            if not tier_data:
                return TierPlan()
            daily_plans = []
            for dp_data in tier_data.get("daily_plans", []):
                daily_plans.append(
                    DailyPlan(
                        day=dp_data.get("day", 1),
                        date=dp_data.get("date", ""),
                        attractions=[
                            AttractionItem(**a)
                            for a in dp_data.get("attractions", [])
                        ],
                        hotel=HotelItem(**dp_data["hotel"]) if dp_data.get("hotel") else None,
                        meals=[MealItem(**m) for m in dp_data.get("meals", [])],
                        transport=[
                            TransportItem(**t) for t in dp_data.get("transport", [])
                        ],
                        daily_cost=dp_data.get("daily_cost", 0),
                        route_coordinates=[
                            RouteCoordinate(**rc)
                            for rc in dp_data.get("route_coordinates", [])
                        ],
                    )
                )
            return TierPlan(
                daily_plans=daily_plans,
                total_cost=tier_data.get("total_cost", 0),
                budget_usage=tier_data.get("budget_usage", 0),
            )

        result = PlanResult(
            task_id=task_id,
            input={
                "origin": request.origin,
                "destination": request.destination,
                "budget": request.budget,
                "intercity_mode": request.intercity_mode.value,
                "city_transit": request.city_transit.value,
                "days": request.days,
                "preferences": [p.value for p in request.preferences],
                "start_date": request.start_date,
            },
            weather=weather if isinstance(weather, list) else [],
            plans={
                "economy": build_tier_plan(plan.get("economy", {})),
                "comfort": build_tier_plan(plan.get("comfort", {})),
                "luxury": build_tier_plan(plan.get("luxury", {})),
            },
        )
        task_manager.store_result(task_id, result)
        await task_manager.update_status(task_id, TaskStatus.completed)
        await task_manager.push_event(task_id, "task_done", {"status": "completed"})

    except Exception as e:
        await task_manager.push_event(
            task_id, "task_failed", {"error": str(e)},
        )
        await task_manager.update_status(task_id, TaskStatus.failed)
        traceback.print_exc()
