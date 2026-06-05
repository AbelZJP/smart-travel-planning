from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class TravelMode(str, Enum):
    high_speed_rail = "high_speed_rail"
    flight = "flight"
    self_drive = "self_drive"
    bus = "bus"
    train = "train"


class CityTransit(str, Enum):
    public_transit = "public_transit"
    taxi = "taxi"
    rental_car = "rental_car"
    walking = "walking"
    mixed = "mixed"


class Preference(str, Enum):
    nature = "nature"
    history = "history"
    food = "food"
    family = "family"


class PlanRequest(BaseModel):
    origin: str = Field(..., description="出发地城市名", min_length=1, max_length=50)
    destination: str = Field(..., description="目的地城市名", min_length=1, max_length=50)
    budget: float = Field(..., description="总预算（元）", gt=0, le=1000000)
    intercity_mode: TravelMode = Field(..., description="城市间交通方式")
    city_transit: CityTransit = Field(CityTransit.mixed, description="市内交通方式")
    days: int = Field(..., description="出行天数", ge=1, le=15)
    preferences: List[Preference] = Field(default_factory=list, description="旅行偏好")
    start_date: str = Field(..., description="出发日期 YYYY-MM-DD", pattern=r"^\d{4}-\d{2}-\d{2}$")
