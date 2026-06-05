from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    attractions_done = "attractions_done"
    weather_done = "weather_done"
    hotels_done = "hotels_done"
    planning = "planning"
    completed = "completed"
    failed = "failed"


class PlanResponse(BaseModel):
    task_id: str
    status: TaskStatus
    created_at: str


class RouteCoordinate(BaseModel):
    lng: float
    lat: float
    name: str
    type: str  # "attraction" | "hotel" | "restaurant"
    order: int


class AttractionItem(BaseModel):
    name: str
    lng: float
    lat: float
    duration: str
    ticket: float
    time_slot: str
    rating: Optional[float] = None
    category: Optional[str] = None
    order: int


class HotelItem(BaseModel):
    name: str
    lng: float
    lat: float
    price: float
    rating: Optional[float] = None
    address: Optional[str] = None


class MealItem(BaseModel):
    type: str  # breakfast | lunch | dinner
    suggestion: str
    estimated_cost: float


class TransportItem(BaseModel):
    from_place: str = Field(alias="from")
    to: str
    mode: str
    cost: float

    model_config = {"populate_by_name": True}


class DailyPlan(BaseModel):
    day: int
    date: str
    weather: Optional[Dict[str, Any]] = None
    attractions: List[AttractionItem] = []
    hotel: Optional[HotelItem] = None
    meals: List[MealItem] = []
    transport: List[TransportItem] = []
    daily_cost: float = 0
    route_coordinates: List[RouteCoordinate] = []


class TierPlan(BaseModel):
    daily_plans: List[DailyPlan] = []
    total_cost: float = 0
    budget_usage: float = Field(0, ge=0, le=100)  # percentage


class PlanResult(BaseModel):
    task_id: str
    input: Dict[str, Any]
    weather: List[Dict[str, Any]] = []
    plans: Dict[str, TierPlan] = {}  # keys: economy, comfort, luxury


class SSEEvent(BaseModel):
    event: str
    agent: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: str
