# 智能旅行规划助手 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a smart travel planning H5 app with 4 AI Agents (attractions, weather, hotels, planner) orchestrated via LangGraph, calling 高德地图 APIs through MCP protocol.

**Architecture:** React 18 single-page H5 frontend → FastAPI SSE backend → LangGraph Agent orchestrator (3 parallel agents + 1 coordinator) → MCP tool layer → 高德地图 Web APIs. Results include 3 budget tiers with daily maps.

**Tech Stack:** React 18 + Vite 5 + TailwindCSS 3 + TypeScript + html2canvas | FastAPI + LangChain + LangGraph + mcp Python SDK + httpx + Pydantic v2 | 高德 Maps JS API 2.0 + 高德 Web API

---

### Task 1: Backend project scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
langchain==0.3.14
langgraph==0.2.61
langchain-openai==0.3.0
mcp==1.3.0
httpx==0.28.1
pydantic==2.10.4
pydantic-settings==2.7.1
python-dotenv==1.0.1
sse-starlette==2.2.1
```

- [ ] **Step 2: Create .env.example**

```
# 高德地图 API
AMAP_API_KEY=your_amap_key_here

# LLM API (OpenAI 兼容接口)
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# Server
HOST=0.0.0.0
PORT=8000
```

- [ ] **Step 3: Create app/__init__.py (empty)**

```python
```

- [ ] **Step 4: Create app/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    amap_api_key: str = ""
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 5: Create app/main.py (skeleton)**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Smart Travel Planning API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Install deps and verify startup**

Run: `cd backend && pip install -r requirements.txt && python -c "from app.main import app; print('OK')"`

- [ ] **Step 7: Commit**

```bash
git add backend/ && git commit -m "feat: scaffold backend project with FastAPI + config"
```

---

### Task 2: Pydantic schemas (request & response models)

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/request.py`
- Create: `backend/app/schemas/response.py`

- [ ] **Step 1: Create schemas/__init__.py (empty)**

```python
```

- [ ] **Step 2: Create schemas/request.py**

```python
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
```

- [ ] **Step 3: Create schemas/response.py**

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
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
    budget_usage: float = 0  # percentage


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
```

- [ ] **Step 4: Verify schemas import**

Run: `cd backend && python -c "from app.schemas.request import PlanRequest; from app.schemas.response import PlanResult; print('OK')"`

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/ && git commit -m "feat: add Pydantic request/response schemas"
```

---

### Task 3: 高德地图 API client

**Files:**
- Create: `backend/app/mcp/__init__.py`
- Create: `backend/app/mcp/amap_client.py`

- [ ] **Step 1: Create mcp/__init__.py (empty)**

```python
```

- [ ] **Step 2: Create mcp/amap_client.py**

```python
import httpx
from typing import Optional, List, Dict, Any
from app.config import settings

AMAP_BASE = "https://restapi.amap.com/v3"


class AmapClient:
    def __init__(self):
        self.key = settings.amap_api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(15.0))
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        client = await self._get_client()
        params["key"] = self.key
        resp = await client.get(f"{AMAP_BASE}{path}", params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "1":
            raise Exception(f"Amap API error: {data.get('info', 'unknown')}")
        return data

    async def search_poi(
        self,
        keywords: str,
        city: str,
        types: Optional[str] = None,
        offset: int = 20,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """POI 2.0 关键词搜索"""
        params = {"keywords": keywords, "city": city, "offset": offset, "page": page}
        if types:
            params["types"] = types
        data = await self._get("/place/text", params)
        return data.get("pois", [])

    async def search_around(
        self,
        location: str,  # "lng,lat"
        keywords: str = "",
        types: Optional[str] = None,
        radius: int = 5000,
        offset: int = 20,
    ) -> List[Dict[str, Any]]:
        """POI 2.0 周边搜索"""
        params = {
            "location": location,
            "keywords": keywords,
            "radius": radius,
            "offset": offset,
        }
        if types:
            params["types"] = types
        data = await self._get("/place/around", params)
        return data.get("pois", [])

    async def get_weather(
        self, city: str, extensions: str = "all"
    ) -> Dict[str, Any]:
        """天气查询 - extensions: base(实时) / all(预报)"""
        params = {"city": city, "extensions": extensions}
        data = await self._get("/weather/weatherInfo", params)
        return data

    async def plan_driving(
        self, origin: str, destination: str, waypoints: Optional[str] = None
    ) -> Dict[str, Any]:
        """驾车路径规划"""
        params = {"origin": origin, "destination": destination, "strategy": "0"}
        if waypoints:
            params["waypoints"] = waypoints
        data = await self._get("/direction/driving", params)
        return data

    async def plan_transit(
        self, origin: str, destination: str, city: str
    ) -> Dict[str, Any]:
        """公交路径规划"""
        params = {"origin": origin, "destination": destination, "city": city}
        data = await self._get("/direction/transit/integrated", params)
        return data

    async def geocode(self, address: str, city: Optional[str] = None) -> Dict[str, Any]:
        """地理编码 - 地址转坐标"""
        params = {"address": address}
        if city:
            params["city"] = city
        data = await self._get("/geocode/geo", params)
        geocodes = data.get("geocodes", [])
        if geocodes:
            return geocodes[0]
        raise Exception(f"Geocode failed for: {address}")

    async def get_static_map_url(
        self,
        markers: List[Dict[str, str]],
        path_points: List[str],  # ["lng1,lat1", "lng2,lat2"]
        size: str = "800*180",
    ) -> str:
        """生成高德静态图 URL"""
        base = "https://restapi.amap.com/v3/staticmap"
        marker_str = ""
        for i, m in enumerate(markers):
            style = "mid,0xFF6B6B,A" if m.get("type") == "hotel" else "mid,0x3B82F6,"
            marker_str += f"&markers={style}:{m['lng']},{m['lat']}"
        path = ",".join(f"{p}" for p in path_points[:8])  # max 8 waypoints
        url = f"{base}?key={self.key}&size={size}&scale=2&zoom=13"
        if path_points:
            url += f"&path=0x3B82F6,2,0:{path}"
        return url
```

- [ ] **Step 3: Verify client imports**

Run: `cd backend && python -c "from app.mcp.amap_client import AmapClient; print('OK')"`

- [ ] **Step 4: Commit**

```bash
git add backend/app/mcp/ && git commit -m "feat: add 高德地图 API async client"
```

---

### Task 4: MCP tool definitions

**Files:**
- Create: `backend/app/mcp/tools.py`

- [ ] **Step 1: Create mcp/tools.py**

```python
from mcp.server.fastmcp import FastMCP
from app.mcp.amap_client import AmapClient

mcp = FastMCP("SmartTravelMCP")
amap = AmapClient()


@mcp.tool()
async def search_attractions(
    keyword: str, city: str, radius: int = 10000
) -> list[dict]:
    """搜索目的地景点。

    Args:
        keyword: 搜索关键词，如"自然风光""历史文化遗迹""美食街"
        city: 目的地城市名，如"杭州"
        radius: 搜索半径（米），默认10000
    """
    # 按不同关键词分别搜索后合并
    keywords_map = {
        "自然风光": "风景名胜|公园|自然景观|山|湖|海滩",
        "历史文化": "博物馆|古迹|寺庙|名人故居|历史建筑",
        "美食购物": "美食街|步行街|特色餐厅|购物中心",
        "亲子休闲": "游乐园|动物园|水族馆|科技馆|植物园",
    }
    types = keywords_map.get(keyword, "风景名胜")
    results = await amap.search_poi(
        keywords=keyword, city=city, types=types, offset=15
    )
    return [
        {
            "name": p.get("name"),
            "lng": float(p.get("location", "0,0").split(",")[0]),
            "lat": float(p.get("location", "0,0").split(",")[1]),
            "rating": float(p.get("biz_ext", {}).get("rating", 0)) or None,
            "category": p.get("type", ""),
            "address": p.get("address", ""),
            "adname": p.get("adname", ""),
        }
        for p in results
    ]


@mcp.tool()
async def get_weather_forecast(city: str, days: int = 7) -> dict:
    """查询城市天气预报。

    Args:
        city: 城市名，如"杭州"
        days: 查询天数，默认7天
    """
    data = await amap.get_weather(city, extensions="all")
    forecasts = data.get("forecasts", [])
    if not forecasts:
        return {"city": city, "forecasts": []}
    daily = forecasts[0].get("casts", [])[:days]
    return {
        "city": forecasts[0].get("city", city),
        "report_time": forecasts[0].get("reporttime", ""),
        "forecasts": [
            {
                "date": d.get("date"),
                "day_weather": d.get("dayweather"),
                "night_weather": d.get("nightweather"),
                "day_temp": int(d.get("daytemp", 0)),
                "night_temp": int(d.get("nighttemp", 0)),
                "day_wind": d.get("daywind", ""),
                "day_power": d.get("daypower", ""),
            }
            for d in daily
        ],
    }


@mcp.tool()
async def search_hotels(
    city: str, location: str, radius: int = 5000, price_max: float = 500
) -> list[dict]:
    """搜索目的地酒店。

    Args:
        city: 城市名
        location: 搜索中心坐标 "lng,lat"
        radius: 搜索半径（米）
        price_max: 最高价格（元/晚），默认500
    """
    results = await amap.search_around(
        location=location,
        keywords="酒店|宾馆|旅馆",
        types="住宿服务",
        radius=radius,
        offset=15,
    )
    hotels = []
    for p in results:
        biz = p.get("biz_ext", {})
        price_str = biz.get("cost", "0")
        try:
            price = float(price_str) if price_str else 300
        except (ValueError, TypeError):
            price = 300
        hotels.append(
            {
                "name": p.get("name"),
                "lng": float(p.get("location", "0,0").split(",")[0]),
                "lat": float(p.get("location", "0,0").split(",")[1]),
                "rating": float(biz.get("rating", 0)) or None,
                "price_per_night": price,
                "address": p.get("address", ""),
            }
        )
    # 按价格筛选并排序
    hotels = [h for h in hotels if h["price_per_night"] <= price_max]
    hotels.sort(key=lambda h: h.get("rating") or 0, reverse=True)
    return hotels


@mcp.tool()
async def plan_transport_route(
    origin_lng: float,
    origin_lat: float,
    dest_lng: float,
    dest_lat: float,
    city: str,
    mode: str = "transit",
) -> dict:
    """规划两点之间的交通路线。

    Args:
        origin_lng: 起点经度
        origin_lat: 起点纬度
        dest_lng: 终点经度
        dest_lat: 终点纬度
        city: 所在城市
        mode: 出行方式 - "driving" 驾车 / "transit" 公交
    """
    origin = f"{origin_lng},{origin_lat}"
    destination = f"{dest_lng},{dest_lat}"
    if mode == "driving":
        data = await amap.plan_driving(origin, destination)
        route = data.get("route", {})
        paths = route.get("paths", [])
        if paths:
            return {
                "mode": "driving",
                "distance_m": int(paths[0].get("distance", 0)),
                "duration_s": int(paths[0].get("duration", 0)),
                "cost_estimated": round(int(paths[0].get("distance", 0)) / 1000 * 1.5, 1),
            }
    else:
        data = await amap.plan_transit(origin, destination, city)
        route = data.get("route", {})
        transits = route.get("transits", [])
        if transits:
            t = transits[0]
            return {
                "mode": "transit",
                "distance_m": int(t.get("distance", 0)),
                "duration_s": int(t.get("duration", 0)),
                "cost_estimated": round(float(t.get("cost", 5)), 1),
                "walking_distance_m": int(t.get("walking_distance", 0)),
            }
    return {"mode": mode, "distance_m": 0, "duration_s": 0, "cost_estimated": 0}
```

- [ ] **Step 2: Verify MCP tools import**

Run: `cd backend && python -c "from app.mcp.tools import mcp; print(f'MCP server: {mcp.name}'); print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add backend/app/mcp/tools.py && git commit -m "feat: define MCP tools wrapping 高德 APIs"
```

---

### Task 5: Task manager (state + SSE)

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/task_manager.py`

- [ ] **Step 1: Create services/__init__.py (empty)**

```python
```

- [ ] **Step 2: Create services/task_manager.py**

```python
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
```

- [ ] **Step 3: Verify imports**

Run: `cd backend && python -c "from app.services.task_manager import task_manager; print('OK')"`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/ && git commit -m "feat: add task manager with SSE event streaming"
```

---

### Task 6: Budget utility

**Files:**
- Create: `backend/app/utils/__init__.py`
- Create: `backend/app/utils/budget.py`

- [ ] **Step 1: Create utils/__init__.py (empty)**

```python
```

- [ ] **Step 2: Create utils/budget.py**

```python
"""预算分档计算"""

# 每档参数的每日人均预算（元）
TIER_CONFIG = {
    "economy": {
        "label": "经济",
        "hotel_per_night": 150,
        "meals_per_day": 65,
        "city_transit_per_day": 20,
        "free_attractions_first": True,
    },
    "comfort": {
        "label": "舒适",
        "hotel_per_night": 350,
        "meals_per_day": 150,
        "city_transit_per_day": 60,
        "free_attractions_first": False,
    },
    "luxury": {
        "label": "豪华",
        "hotel_per_night": 600,
        "meals_per_day": 300,
        "city_transit_per_day": 150,
        "free_attractions_first": False,
    },
}


def get_tier_config(tier: str) -> dict:
    """获取指定档位的预算配置"""
    return TIER_CONFIG.get(tier, TIER_CONFIG["comfort"])


def calculate_budget_allocation(
    total_budget: float, days: int, tier: str, intercity_mode: str
) -> dict:
    """根据档位分配预算到各分类。

    Returns dict with keys: hotel, meals, transit, tickets, intercity, contingency
    """
    config = get_tier_config(tier)
    # 城市间交通预估（根据出行方式）
    intercity_estimates = {
        "high_speed_rail": 300,
        "flight": 800,
        "self_drive": 200,
        "bus": 100,
        "train": 150,
    }
    intercity_cost = intercity_estimates.get(intercity_mode, 300) * 2  # 往返

    remaining = total_budget - intercity_cost

    hotel_budget = config["hotel_per_night"] * days
    meals_budget = config["meals_per_day"] * days
    transit_budget = config["city_transit_per_day"] * days
    tickets_budget = remaining - hotel_budget - meals_budget - transit_budget

    if tickets_budget < 0:
        # 预算不足，等比压缩
        scale = remaining / (hotel_budget + meals_budget + transit_budget + 1)
        hotel_budget *= scale
        meals_budget *= scale
        transit_budget *= scale
        tickets_budget = 0

    return {
        "intercity": round(intercity_cost, 1),
        "hotel": round(hotel_budget, 1),
        "meals": round(meals_budget, 1),
        "transit": round(transit_budget, 1),
        "tickets": round(tickets_budget, 1),
    }
```

- [ ] **Step 3: Verify**

Run: `cd backend && python -c "from app.utils.budget import calculate_budget_allocation; r = calculate_budget_allocation(3000, 3, 'comfort', 'high_speed_rail'); print(r); print('OK')"`

- [ ] **Step 4: Commit**

```bash
git add backend/app/utils/ && git commit -m "feat: add budget tier calculation utility"
```

---

### Task 7: Attraction search agent

**Files:**
- Create: `backend/app/agents/__init__.py`
- Create: `backend/app/agents/attraction_agent.py`

- [ ] **Step 1: Create agents/__init__.py (empty)**

```python
```

- [ ] **Step 2: Create agents/attraction_agent.py**

```python
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from typing import List, Dict, Any
from app.config import settings
from app.mcp.amap_client import AmapClient

amap = AmapClient()

PREFERENCE_KEYWORDS = {
    "nature": "自然风光",
    "history": "历史文化",
    "food": "美食购物",
    "family": "亲子休闲",
}


@tool
async def search_destination_attractions(
    preference: str, city: str
) -> List[Dict[str, Any]]:
    """搜索目的地景点。preference 可选: 自然风光/历史文化/美食购物/亲子休闲"""
    keyword = PREFERENCE_KEYWORDS.get(preference, preference)
    types_map = {
        "自然风光": "风景名胜|公园|自然景观|山|湖|海滩|森林公园",
        "历史文化": "博物馆|古迹|寺庙|名人故居|历史建筑|纪念馆",
        "美食购物": "美食街|步行街|特色餐厅|购物中心|夜市",
        "亲子休闲": "游乐园|动物园|水族馆|科技馆|植物园|主题公园",
    }
    types = types_map.get(keyword, "风景名胜")
    results = await amap.search_poi(keywords=keyword, city=city, types=types, offset=10)
    return [
        {
            "name": p.get("name"),
            "lng": float(p.get("location", "0,0").split(",")[0]),
            "lat": float(p.get("location", "0,0").split(",")[1]),
            "rating": float(p.get("biz_ext", {}).get("rating", 0)) or 3.5,
            "category": p.get("type", ""),
            "address": p.get("address", ""),
        }
        for p in results
    ]


ATTRACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """你是一个景点搜索专家。根据用户的旅行偏好和目的地，搜索合适的景点。

要求：
1. 每种偏好至少搜索一次
2. 根据评分和知名度筛选推荐景点
3. 估算每个景点的建议游玩时长(hours)和门票价格(元)
4. 返回景点列表，格式: [{{"name": "...", "lng": ..., "lat": ..., "rating": ..., "suggested_duration_h": ..., "estimated_ticket": ...}}, ...]
5. 至少返回 days*3 个景点，确保足够的天数分配""",
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


async def run_attraction_agent(
    destination: str,
    days: int,
    preferences: List[str],
) -> List[Dict[str, Any]]:
    """运行景点搜索 Agent"""
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.3,
    )
    tools = [search_destination_attractions]
    agent = create_tool_calling_agent(llm, tools, ATTRACTION_PROMPT)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=8)

    pref_labels = [PREFERENCE_KEYWORDS.get(p, p) for p in preferences]
    input_text = f"目的地: {destination}，出行天数: {days}天，旅行偏好: {', '.join(pref_labels)}。请为每个偏好搜索景点，然后综合推荐。"

    result = await executor.ainvoke({"input": input_text})
    # 解析 LLM 输出，提取景点列表
    output = result.get("output", "[]")
    import json
    import re

    # 尝试从输出中提取 JSON 数组
    match = re.search(r"\[.*\]", output, re.DOTALL)
    if match:
        try:
            attractions = json.loads(match.group())
            return attractions
        except json.JSONDecodeError:
            pass
    return []
```

- [ ] **Step 3: Verify agent import**

Run: `cd backend && python -c "from app.agents.attraction_agent import run_attraction_agent; print('OK')"`

- [ ] **Step 4: Commit**

```bash
git add backend/app/agents/ && git commit -m "feat: add attraction search agent"
```

---

### Task 8: Weather query agent

**Files:**
- Create: `backend/app/agents/weather_agent.py`

- [ ] **Step 1: Create agents/weather_agent.py**

```python
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.config import settings
from app.mcp.amap_client import AmapClient

amap = AmapClient()


@tool
async def fetch_weather(city: str) -> Dict[str, Any]:
    """获取城市天气预报（未来7天）"""
    data = await amap.get_weather(city, extensions="all")
    forecasts = data.get("forecasts", [])
    if not forecasts:
        return {"city": city, "forecasts": []}
    daily = forecasts[0].get("casts", [])
    return {
        "city": forecasts[0].get("city", city),
        "forecasts": [
            {
                "date": d.get("date"),
                "day_weather": d.get("dayweather"),
                "night_weather": d.get("nightweather"),
                "day_temp": int(d.get("daytemp", 0)),
                "night_temp": int(d.get("nighttemp", 0)),
                "day_wind": d.get("daywind", ""),
                "day_power": d.get("daypower", ""),
            }
            for d in daily
        ],
    }


WEATHER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """你是一个天气分析专家。根据天气数据，为旅行提供建议。

对每一天的天气做分析，输出格式:
[
  {{
    "date": "YYYY-MM-DD",
    "day_weather": "晴",
    "night_weather": "多云",
    "high_temp": 30,
    "low_temp": 22,
    "wind": "东北风3级",
    "rain_probability": 0.1,
    "clothing_advice": "建议穿短袖，带一件薄外套",
    "travel_advice": "天气晴好，非常适合户外活动",
    "suitable": true
  }},
  ...
]""",
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


async def run_weather_agent(
    destination: str, start_date: str, days: int
) -> List[Dict[str, Any]]:
    """运行天气查询 Agent"""
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.1,
    )
    tools = [fetch_weather]
    agent = create_tool_calling_agent(llm, tools, WEATHER_PROMPT)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=3)

    # 计算日期范围
    start = datetime.strptime(start_date, "%Y-%m-%d")
    date_range = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

    input_text = f"目的地: {destination}，出发日期: {start_date}，出行天数: {days}天，需要天气的日期: {', '.join(date_range)}。请先获取天气数据，然后分析每天的出行建议。"

    result = await executor.ainvoke({"input": input_text})
    output = result.get("output", "[]")

    import json
    import re
    match = re.search(r"\[.*\]", output, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return []
```

- [ ] **Step 2: Verify import**

Run: `cd backend && python -c "from app.agents.weather_agent import run_weather_agent; print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add backend/app/agents/weather_agent.py && git commit -m "feat: add weather query agent"
```

---

### Task 9: Hotel recommendation agent

**Files:**
- Create: `backend/app/agents/hotel_agent.py`

- [ ] **Step 1: Create agents/hotel_agent.py**

```python
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from typing import List, Dict, Any
from app.config import settings
from app.mcp.amap_client import AmapClient

amap = AmapClient()


@tool
async def search_nearby_hotels(
    city: str, location: str, tier: str
) -> List[Dict[str, Any]]:
    """搜索指定位置附近的酒店。location 格式: "lng,lat"，tier: economy/comfort/luxury"""
    price_ranges = {"economy": 200, "comfort": 500, "luxury": 2000}
    max_price = price_ranges.get(tier, 500)
    results = await amap.search_around(
        location=location,
        keywords="酒店|宾馆|旅馆|精品酒店|度假酒店",
        types="住宿服务",
        radius=5000,
        offset=10,
    )
    hotels = []
    for p in results:
        biz = p.get("biz_ext", {})
        try:
            price = float(biz.get("cost", 0)) if biz.get("cost") else 300
        except (ValueError, TypeError):
            price = 300
        hotels.append(
            {
                "name": p.get("name"),
                "lng": float(p.get("location", "0,0").split(",")[0]),
                "lat": float(p.get("location", "0,0").split(",")[1]),
                "rating": float(biz.get("rating", 0)) or 3.5,
                "price_per_night": price,
                "address": p.get("address", ""),
            }
        )
    hotels = [h for h in hotels if h["price_per_night"] <= max_price]
    hotels.sort(key=lambda h: h.get("rating") or 0, reverse=True)
    return hotels[:8]


HOTEL_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """你是一个酒店推荐专家。根据旅行计划推荐住宿。

要求：
1. 在主要景点集中区域搜索酒店，减少交通时间
2. 根据预算档位筛选: economy≤200/晚, comfort 200-500/晚, luxury 500+/晚
3. 优先推荐评分高、距景点近的酒店
4. 为每个档位推荐1-2家酒店

返回格式:
{{
  "economy": [{{"name": "...", "lng": ..., "lat": ..., "price_per_night": ..., "rating": ...}}, ...],
  "comfort": [...],
  "luxury": [...]
}}""",
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)


async def run_hotel_agent(
    destination: str,
    attractions: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """运行酒店推荐 Agent"""
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.3,
    )
    tools = [search_nearby_hotels]
    agent = create_tool_calling_agent(llm, tools, HOTEL_PROMPT)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=8)

    # 从景点列表中提取中心坐标
    if attractions:
        center_lng = sum(a.get("lng", 0) for a in attractions) / len(attractions)
        center_lat = sum(a.get("lat", 0) for a in attractions) / len(attractions)
        center = f"{center_lng},{center_lat}"
    else:
        center = f"116.397,39.908"  # fallback

    input_text = (
        f"目的地: {destination}，景点中心坐标: {center}，"
        f"景点列表: {attractions[:5]}。请为 economy/comfort/luxury 三个档位分别搜索推荐酒店。"
    )
    result = await executor.ainvoke({"input": input_text})
    output = result.get("output", "{}")

    import json
    import re
    match = re.search(r"\{.*\}", output, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"economy": [], "comfort": [], "luxury": []}
```

- [ ] **Step 2: Verify import**

Run: `cd backend && python -c "from app.agents.hotel_agent import run_hotel_agent; print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add backend/app/agents/hotel_agent.py && git commit -m "feat: add hotel recommendation agent"
```

---

### Task 10: Planner coordination agent

**Files:**
- Create: `backend/app/agents/planner_agent.py`

- [ ] **Step 1: Create agents/planner_agent.py**

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Any
from app.config import settings
from app.utils.budget import calculate_budget_allocation, TIER_CONFIG

PLANNER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """你是一个资深的旅行规划师。你需要根据景点列表、天气数据、酒店候选和用户预算，生成三档完整行程方案。

## 输入数据:
- 用户需求: {user_input}
- 景点列表: {attractions}
- 天气数据: {weather}
- 酒店候选: {hotels}
- 预算分配: {budget_allocations}

## 规划原则:
1. 景点按地理分布分组，每天安排同区域的2-3个景点，减少路途时间
2. 上午安排户外景点（天气好时优先），下午安排室内或半室内景点
3. 每2-3个景点之间安排餐饮/休息
4. 酒店安排在当天最后一个景点附近
5. 交通方式根据预算档位选择：经济=公交地铁，舒适=打车+地铁，豪华=专车/租车
6. 城市间交通根据出行方式选择并计算费用
7. 严格控制预算，每档总花费不超过分配预算的110%

## 输出格式（严格的JSON，不要包含任何markdown代码块标记）:
{{
  "economy": {{
    "daily_plans": [
      {{
        "day": 1,
        "date": "YYYY-MM-DD",
        "attractions": [
          {{"name": "...", "lng": 120.14, "lat": 30.24, "duration": "3h", "ticket": 0, "time_slot": "09:00-12:00", "rating": 4.5, "category": "自然风光", "order": 1}}
        ],
        "hotel": {{"name": "...", "lng": ..., "lat": ..., "price": 180, "rating": 4.0, "address": "..."}},
        "meals": [{{"type": "lunch", "suggestion": "...", "estimated_cost": 30}}],
        "transport": [{{"from": "出发地", "to": "目的地", "mode": "高铁", "cost": 73}}],
        "daily_cost": 358,
        "route_coordinates": [
          {{"lng": 120.14, "lat": 30.24, "name": "西湖", "type": "attraction", "order": 1}},
          {{"lng": 120.12, "lat": 30.23, "name": "灵隐寺", "type": "attraction", "order": 2}},
          {{"lng": 120.16, "lat": 30.25, "name": "如家快捷", "type": "hotel", "order": 3}}
        ]
      }}
    ],
    "total_cost": 2380,
    "budget_usage": 79.3
  }},
  "comfort": {{...}},
  "luxury": {{...}}
}}

注意: route_coordinates 必须按游览顺序排列，包括景点和酒店，用于前端绘制路线图。""",
        ),
        ("human", "请生成三档行程方案"),
    ]
)


async def run_planner_agent(
    origin: str,
    destination: str,
    budget: float,
    intercity_mode: str,
    city_transit: str,
    days: int,
    preferences: List[str],
    start_date: str,
    attractions: List[Dict[str, Any]],
    weather: List[Dict[str, Any]],
    hotels: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """运行规划协调 Agent，生成三档方案"""
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0.5,
    )

    # 为每档计算预算分配
    budget_allocations = {}
    for tier in ["economy", "comfort", "luxury"]:
        budget_allocations[tier] = calculate_budget_allocation(
            budget, days, tier, intercity_mode
        )

    user_input = (
        f"出发地: {origin}，目的地: {destination}，总预算: {budget}元，"
        f"城市间交通: {intercity_mode}，市内交通: {city_transit}，"
        f"出行天数: {days}天，偏好: {preferences}，出发日期: {start_date}"
    )

    chain = PLANNER_PROMPT | llm
    response = await chain.ainvoke(
        {
            "user_input": user_input,
            "attractions": str(attractions),
            "weather": str(weather),
            "hotels": str(hotels),
            "budget_allocations": str(budget_allocations),
        }
    )

    import json
    import re

    content = response.content if hasattr(response, "content") else str(response)
    # 去除可能的 markdown 代码块标记
    content = re.sub(r"^```(?:json)?\s*", "", content.strip())
    content = re.sub(r"\s*```$", "", content)

    try:
        plan = json.loads(content)
        return plan
    except json.JSONDecodeError:
        # 如果解析失败，返回一个基础结构
        return {
            "economy": {"daily_plans": [], "total_cost": 0, "budget_usage": 0},
            "comfort": {"daily_plans": [], "total_cost": 0, "budget_usage": 0},
            "luxury": {"daily_plans": [], "total_cost": 0, "budget_usage": 0},
        }
```

- [ ] **Step 2: Verify import**

Run: `cd backend && python -c "from app.agents.planner_agent import run_planner_agent; print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add backend/app/agents/planner_agent.py && git commit -m "feat: add planner coordination agent"
```

---

### Task 11: Agent orchestrator (LangGraph)

**Files:**
- Create: `backend/app/agents/orchestrator.py`

- [ ] **Step 1: Create agents/orchestrator.py**

```python
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

    1. 并行运行景点搜索、天气查询、酒店推荐 Agent
    2. 等待全部完成后运行规划协调 Agent
    3. 通过 SSE 实时推送进度
    """
    try:
        await task_manager.update_status(task_id, TaskStatus.running)

        # --- Phase 1: 并行执行三个 Agent ---
        await task_manager.push_event(task_id, "agent_started", {"agent": "attractions"})
        await task_manager.push_event(task_id, "agent_started", {"agent": "weather"})
        await task_manager.push_event(task_id, "agent_started", {"agent": "hotels"})

        # 景点搜索 + 天气查询 先并行
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

        # 等待景点和天气完成
        attractions, weather = await asyncio.gather(
            attractions_task, weather_task, return_exceptions=True
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

        # 酒店推荐（依赖景点结果中的坐标信息）
        hotels = await run_hotel_agent(
            destination=request.destination,
            attractions=attractions if isinstance(attractions, list) else [],
        )
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
        await task_manager.push_event(task_id, "task_done", {"status": "completed"})

        # --- 存储结果 ---
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

    except Exception as e:
        await task_manager.push_event(
            task_id, "task_failed", {"error": str(e)},
        )
        await task_manager.update_status(task_id, TaskStatus.failed)
        traceback.print_exc()
```

- [ ] **Step 2: Verify imports**

Run: `cd backend && python -c "from app.agents.orchestrator import run_travel_planning; print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add backend/app/agents/orchestrator.py && git commit -m "feat: add LangGraph-style agent orchestrator"
```

---

### Task 12: API routes

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/routes.py`

- [ ] **Step 1: Create api/__init__.py (empty)**

```python
```

- [ ] **Step 2: Create api/routes.py**

```python
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
    # 基础校验
    if request.destination == request.origin:
        raise HTTPException(status_code=400, detail="出发地和目的地不能相同")
    if request.start_date < __import__("datetime").datetime.now().strftime("%Y-%m-%d"):
        raise HTTPException(status_code=400, detail="出发日期不能早于今天")

    task_id = task_manager.create_task()

    # 异步后台执行
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
```

- [ ] **Step 3: Register routes in main.py**

Modify `backend/app/main.py` — insert after the CORS middleware, before `@app.get("/health")`:

```python
from app.api.routes import router

app.include_router(router)
```

- [ ] **Step 4: Verify app starts**

Run: `cd backend && python -c "from app.main import app; print([r.path for r in app.routes]); print('OK')"`

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/ backend/app/main.py && git commit -m "feat: add API routes with SSE streaming"
```

---

### Task 13: Frontend project scaffolding

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/index.css`

- [ ] **Step 1: Create frontend/package.json**

```json
{
  "name": "smart-travel-planning",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "axios": "^1.7.9",
    "html2canvas": "^1.4.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "typescript": "^5.7.2",
    "vite": "^5.4.11"
  }
}
```

- [ ] **Step 2: Create frontend/index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <meta name="description" content="智能旅行规划助手 - 一键生成专属行程" />
    <title>智能旅行规划</title>
    <script src="https://webapi.amap.com/maps?v=2.0&key=YOUR_AMAP_KEY"></script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 3: Create frontend/vite.config.ts**

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});
```

- [ ] **Step 4: Create frontend/tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        travel: {
          blue: '#3B82F6',
          green: '#10B981',
          light: '#F0FDF4',
          card: '#FFFFFF',
          text: '#1F2937',
          muted: '#6B7280',
          accent: '#F59E0B',
        },
      },
      borderRadius: {
        card: '16px',
      },
    },
  },
  plugins: [],
};
```

- [ ] **Step 5: Create frontend/postcss.config.js**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 6: Create frontend/tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"]
}
```

- [ ] **Step 7: Create frontend/src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial,
    sans-serif;
  -webkit-font-smoothing: antialiased;
  background: linear-gradient(135deg, #F0FDF4 0%, #EFF6FF 100%);
  min-height: 100vh;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-thumb {
  background: #D1D5DB;
  border-radius: 2px;
}
```

- [ ] **Step 8: Create frontend/src/main.tsx**

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 9: Install deps and verify**

Run: `cd frontend && npm install && npm run build`

- [ ] **Step 10: Commit**

```bash
git add frontend/ && git commit -m "feat: scaffold React frontend with Vite + TailwindCSS"
```

---

### Task 14: TypeScript types

**Files:**
- Create: `frontend/src/types/plan.ts`

- [ ] **Step 1: Create types/plan.ts**

```typescript
export interface PlanRequest {
  origin: string;
  destination: string;
  budget: number;
  intercity_mode: TravelMode;
  city_transit: CityTransit;
  days: number;
  preferences: Preference[];
  start_date: string;
}

export type TravelMode = 'high_speed_rail' | 'flight' | 'self_drive' | 'bus' | 'train';
export type CityTransit = 'public_transit' | 'taxi' | 'rental_car' | 'walking' | 'mixed';
export type Preference = 'nature' | 'history' | 'food' | 'family';

export type TaskStatus =
  | 'pending'
  | 'running'
  | 'attractions_done'
  | 'weather_done'
  | 'hotels_done'
  | 'planning'
  | 'completed'
  | 'failed';

export interface PlanResponse {
  task_id: string;
  status: TaskStatus;
  created_at: string;
}

export interface RouteCoordinate {
  lng: number;
  lat: number;
  name: string;
  type: 'attraction' | 'hotel' | 'restaurant';
  order: number;
}

export interface AttractionItem {
  name: string;
  lng: number;
  lat: number;
  duration: string;
  ticket: number;
  time_slot: string;
  rating?: number;
  category?: string;
  order: number;
}

export interface HotelItem {
  name: string;
  lng: number;
  lat: number;
  price: number;
  rating?: number;
  address?: string;
}

export interface MealItem {
  type: 'breakfast' | 'lunch' | 'dinner';
  suggestion: string;
  estimated_cost: number;
}

export interface TransportItem {
  from: string;
  to: string;
  mode: string;
  cost: number;
}

export interface DailyPlan {
  day: number;
  date: string;
  weather?: {
    day_weather: string;
    night_weather: string;
    high_temp: number;
    low_temp: number;
    wind?: string;
    clothing_advice?: string;
    travel_advice?: string;
  };
  attractions: AttractionItem[];
  hotel: HotelItem | null;
  meals: MealItem[];
  transport: TransportItem[];
  daily_cost: number;
  route_coordinates: RouteCoordinate[];
}

export interface TierPlan {
  daily_plans: DailyPlan[];
  total_cost: number;
  budget_usage: number;
}

export interface PlanResult {
  task_id: string;
  input: PlanRequest;
  weather: Array<Record<string, unknown>>;
  plans: {
    economy: TierPlan;
    comfort: TierPlan;
    luxury: TierPlan;
  };
}

export type TierKey = 'economy' | 'comfort' | 'luxury';

export interface SSEEvent {
  event: string;
  agent?: string;
  message?: string;
  data?: Record<string, unknown>;
  timestamp: string;
}

export const TRAVEL_MODE_LABELS: Record<TravelMode, string> = {
  high_speed_rail: '高铁',
  flight: '飞机',
  self_drive: '自驾',
  bus: '大巴',
  train: '火车',
};

export const CITY_TRANSIT_LABELS: Record<CityTransit, string> = {
  public_transit: '公交/地铁',
  taxi: '打车',
  rental_car: '租车',
  walking: '步行',
  mixed: '打车+地铁',
};

export const PREFERENCE_LABELS: Record<Preference, string> = {
  nature: '🏔 自然风光',
  history: '🏛 历史文化',
  food: '🍜 美食购物',
  family: '👨‍👩‍👧 亲子休闲',
};

export const TIER_LABELS: Record<TierKey, string> = {
  economy: '经济',
  comfort: '舒适',
  luxury: '豪华',
};
```

- [ ] **Step 2: Verify TypeScript compilation**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/ && git commit -m "feat: add TypeScript type definitions"
```

---

### Task 15: API client

**Files:**
- Create: `frontend/src/api/client.ts`

- [ ] **Step 1: Create api/client.ts**

```typescript
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
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/ && git commit -m "feat: add API client with SSE support"
```

---

### Task 16: Custom hooks

**Files:**
- Create: `frontend/src/hooks/usePlan.ts`
- Create: `frontend/src/hooks/useSSE.ts`

- [ ] **Step 1: Create hooks/usePlan.ts**

```typescript
import { useState, useCallback } from 'react';
import type {
  PlanRequest,
  PlanResponse,
  PlanResult,
  TierKey,
  SSEEvent,
} from '../types/plan';
import { createPlan, getPlanResult, subscribeToProgress } from '../api/client';

interface AgentProgress {
  attractions: string; // 'idle' | 'running' | 'done' | 'failed'
  weather: string;
  hotels: string;
  planner: string;
}

export function usePlan() {
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [result, setResult] = useState<PlanResult | null>(null);
  const [activeTier, setActiveTier] = useState<TierKey>('economy');
  const [error, setError] = useState<string | null>(null);
  const [agentProgress, setAgentProgress] = useState<AgentProgress>({
    attractions: 'idle',
    weather: 'idle',
    hotels: 'idle',
    planner: 'idle',
  });
  const [progressMessages, setProgressMessages] = useState<string[]>([]);

  const startPlanning = useCallback(async (request: PlanRequest) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setAgentProgress({
      attractions: 'idle',
      weather: 'idle',
      hotels: 'idle',
      planner: 'idle',
    });
    setProgressMessages([]);

    try {
      const response: PlanResponse = await createPlan(request);
      setTaskId(response.task_id);

      // 订阅 SSE 进度
      const es = subscribeToProgress(
        response.task_id,
        (event: string, data: Record<string, unknown>) => {
          switch (event) {
            case 'agent_started':
              setAgentProgress((prev) => ({
                ...prev,
                [data.agent as string]: 'running',
              }));
              setProgressMessages((prev) => [
                ...prev,
                `🔍 ${getAgentLabel(data.agent as string)} 查询中...`,
              ]);
              break;
            case 'agent_completed':
              setAgentProgress((prev) => ({
                ...prev,
                [data.agent as string]: 'done',
              }));
              setProgressMessages((prev) => [
                ...prev,
                `✅ ${getAgentLabel(data.agent as string)} 完成`,
              ]);
              break;
            case 'agent_failed':
              setAgentProgress((prev) => ({
                ...prev,
                [data.agent as string]: 'failed',
              }));
              setProgressMessages((prev) => [
                ...prev,
                `❌ ${getAgentLabel(data.agent as string)} 失败: ${data.error}`,
              ]);
              break;
            case 'planning_started':
              setAgentProgress((prev) => ({ ...prev, planner: 'running' }));
              setProgressMessages((prev) => [...prev, '📋 正在生成行程方案...']);
              break;
            case 'planning_completed':
              setAgentProgress((prev) => ({ ...prev, planner: 'done' }));
              break;
            case 'task_done':
              setProgressMessages((prev) => [...prev, '🎉 行程规划完成!']);
              es.close();
              // 获取结果
              getPlanResult(response.task_id).then(setResult).catch(console.error);
              setLoading(false);
              break;
            case 'task_failed':
              setError((data.error as string) || '规划失败');
              setLoading(false);
              es.close();
              break;
          }
        },
        (err: Event) => {
          console.error('SSE error:', err);
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : '请求失败');
      setLoading(false);
    }
  }, []);

  return {
    loading,
    taskId,
    result,
    activeTier,
    setActiveTier,
    error,
    agentProgress,
    progressMessages,
    startPlanning,
  };
}

function getAgentLabel(agent: string): string {
  const labels: Record<string, string> = {
    attractions: '景点搜索',
    weather: '天气查询',
    hotels: '酒店推荐',
    planner: '行程规划',
  };
  return labels[agent] || agent;
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/ && git commit -m "feat: add usePlan and SSE hooks"
```

---

### Task 17: Header component

**Files:**
- Create: `frontend/src/components/Header.tsx`

- [ ] **Step 1: Create components/Header.tsx**

```tsx
import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="px-6 pt-8 pb-4 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 mb-3 rounded-2xl bg-gradient-to-br from-travel-blue to-travel-green shadow-lg">
        <span className="text-3xl">🌍</span>
      </div>
      <h1 className="text-2xl font-bold text-travel-text">智能旅行规划</h1>
      <p className="mt-1 text-sm text-travel-muted">输入需求，一键生成专属行程</p>
    </header>
  );
};

export default Header;
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Header.tsx && git commit -m "feat: add Header component"
```

---

### Task 18: PlanForm component

**Files:**
- Create: `frontend/src/components/PlanForm.tsx`

- [ ] **Step 1: Create components/PlanForm.tsx**

```tsx
import React, { useState } from 'react';
import type {
  PlanRequest,
  TravelMode,
  CityTransit,
  Preference,
} from '../types/plan';
import {
  TRAVEL_MODE_LABELS,
  CITY_TRANSIT_LABELS,
  PREFERENCE_LABELS,
} from '../types/plan';

interface PlanFormProps {
  onSubmit: (request: PlanRequest) => void;
  loading: boolean;
}

const TRAVEL_MODES: TravelMode[] = ['high_speed_rail', 'flight', 'self_drive', 'bus', 'train'];
const CITY_TRANSITS: CityTransit[] = ['public_transit', 'taxi', 'rental_car', 'mixed'];
const PREFERENCES: Preference[] = ['nature', 'history', 'food', 'family'];

const PlanForm: React.FC<PlanFormProps> = ({ onSubmit, loading }) => {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [budget, setBudget] = useState(3000);
  const [intercityMode, setIntercityMode] = useState<TravelMode>('high_speed_rail');
  const [cityTransit, setCityTransit] = useState<CityTransit>('mixed');
  const [days, setDays] = useState(3);
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 7);
    return d.toISOString().split('T')[0];
  });
  const [preferences, setPreferences] = useState<Preference[]>(['nature', 'history']);

  const togglePreference = (p: Preference) => {
    setPreferences((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!origin.trim() || !destination.trim()) return;
    onSubmit({
      origin: origin.trim(),
      destination: destination.trim(),
      budget,
      intercity_mode: intercityMode,
      city_transit: cityTransit,
      days,
      preferences,
      start_date: startDate,
    });
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <form
      onSubmit={handleSubmit}
      className="mx-4 p-5 bg-white rounded-card shadow-md space-y-4"
    >
      {/* 出发地与目的地 */}
      <div className="flex items-center gap-2">
        <div className="flex-1">
          <label className="block text-xs font-medium text-travel-muted mb-1">
            📍 出发地
          </label>
          <input
            type="text"
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder="例如：上海"
            className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-travel-blue/30 focus:border-travel-blue transition"
            required
          />
        </div>
        <div className="pt-5 text-travel-muted">→</div>
        <div className="flex-1">
          <label className="block text-xs font-medium text-travel-muted mb-1">
            🎯 目的地
          </label>
          <input
            type="text"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="例如：杭州"
            className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-travel-blue/30 focus:border-travel-blue transition"
            required
          />
        </div>
      </div>

      {/* 预算 */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-1">
          💰 总预算
        </label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={500}
            max={50000}
            step={100}
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
            className="flex-1 accent-travel-green"
          />
          <span className="text-sm font-semibold text-travel-text w-20 text-right">
            ¥{budget.toLocaleString()}
          </span>
        </div>
      </div>

      {/* 出行方式 - 城市间 */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-1">
          🚗 城市间交通
        </label>
        <div className="flex flex-wrap gap-2">
          {TRAVEL_MODES.map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setIntercityMode(mode)}
              className={`px-3 py-1.5 text-xs rounded-full border transition ${
                intercityMode === mode
                  ? 'bg-travel-blue text-white border-travel-blue'
                  : 'bg-white text-travel-text border-gray-200 hover:border-travel-blue'
              }`}
            >
              {TRAVEL_MODE_LABELS[mode]}
            </button>
          ))}
        </div>
      </div>

      {/* 出行方式 - 市内 */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-1">
          🚕 市内交通
        </label>
        <div className="flex flex-wrap gap-2">
          {CITY_TRANSITS.map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setCityTransit(mode)}
              className={`px-3 py-1.5 text-xs rounded-full border transition ${
                cityTransit === mode
                  ? 'bg-travel-green text-white border-travel-green'
                  : 'bg-white text-travel-text border-gray-200 hover:border-travel-green'
              }`}
            >
              {CITY_TRANSIT_LABELS[mode]}
            </button>
          ))}
        </div>
      </div>

      {/* 出行日期与天数 */}
      <div className="flex gap-3">
        <div className="flex-1">
          <label className="block text-xs font-medium text-travel-muted mb-1">
            📅 出发日期
          </label>
          <input
            type="date"
            value={startDate}
            min={today}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-travel-blue/30"
          />
        </div>
        <div className="flex-1">
          <label className="block text-xs font-medium text-travel-muted mb-1">
            📆 出行天数
          </label>
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5, 7, 10, 15].map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDays(d)}
                className={`flex-1 py-2 text-xs rounded-lg border transition ${
                  days === d
                    ? 'bg-travel-blue text-white border-travel-blue'
                    : 'bg-white text-travel-text border-gray-200 hover:border-travel-blue'
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 旅行偏好 */}
      <div>
        <label className="block text-xs font-medium text-travel-muted mb-1">
          🏷️ 旅行偏好（可多选）
        </label>
        <div className="flex flex-wrap gap-2">
          {PREFERENCES.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => togglePreference(p)}
              className={`px-3 py-1.5 text-xs rounded-full border transition ${
                preferences.includes(p)
                  ? 'bg-travel-green text-white border-travel-green'
                  : 'bg-white text-travel-text border-gray-200 hover:border-travel-green'
              }`}
            >
              {PREFERENCE_LABELS[p]}
            </button>
          ))}
        </div>
      </div>

      {/* 提交按钮 */}
      <button
        type="submit"
        disabled={loading || !origin.trim() || !destination.trim()}
        className="w-full py-3.5 bg-gradient-to-r from-travel-blue to-travel-green text-white font-semibold text-base rounded-xl shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            规划中...
          </span>
        ) : (
          '🚀 开始规划'
        )}
      </button>
    </form>
  );
};

export default PlanForm;
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/PlanForm.tsx && git commit -m "feat: add PlanForm component"
```

---

### Task 19: ProgressPanel component

**Files:**
- Create: `frontend/src/components/ProgressPanel.tsx`

- [ ] **Step 1: Create components/ProgressPanel.tsx**

```tsx
import React from 'react';

interface AgentProgress {
  attractions: string;
  weather: string;
  hotels: string;
  planner: string;
}

interface ProgressPanelProps {
  agentProgress: AgentProgress;
  messages: string[];
}

const AGENTS = [
  { key: 'attractions', label: '景点搜索', icon: '🏛' },
  { key: 'weather', label: '天气查询', icon: '🌤' },
  { key: 'hotels', label: '酒店推荐', icon: '🏨' },
  { key: 'planner', label: '行程规划', icon: '📋' },
] as const;

const ProgressPanel: React.FC<ProgressPanelProps> = ({ agentProgress, messages }) => {
  return (
    <div className="mx-4 mt-4 p-5 bg-white rounded-card shadow-md">
      <h3 className="text-sm font-semibold text-travel-text mb-3">
        🤖 AI Agent 工作中...
      </h3>
      <div className="space-y-2">
        {AGENTS.map(({ key, label, icon }) => {
          const status = agentProgress[key as keyof AgentProgress];
          let statusEl: React.ReactNode;
          switch (status) {
            case 'running':
              statusEl = (
                <span className="inline-block w-5 h-5 border-2 border-travel-blue/30 border-t-travel-blue rounded-full animate-spin" />
              );
              break;
            case 'done':
              statusEl = <span className="text-travel-green font-bold">✓</span>;
              break;
            case 'failed':
              statusEl = <span className="text-red-500 font-bold">✗</span>;
              break;
            default:
              statusEl = <span className="w-5 h-5 inline-block rounded-full border-2 border-gray-200" />;
          }

          return (
            <div
              key={key}
              className={`flex items-center gap-3 py-2 px-3 rounded-lg text-sm transition-colors ${
                status === 'running'
                  ? 'bg-blue-50 text-travel-blue'
                  : status === 'done'
                  ? 'bg-green-50 text-travel-green'
                  : status === 'failed'
                  ? 'bg-red-50 text-red-500'
                  : 'bg-gray-50 text-travel-muted'
              }`}
            >
              <span className="text-base">{icon}</span>
              <span className="flex-1 font-medium">{label}</span>
              {statusEl}
            </div>
          );
        })}
      </div>
      {messages.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="text-xs text-travel-muted space-y-0.5 max-h-32 overflow-y-auto">
            {messages.map((msg, i) => (
              <div key={i}>{msg}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProgressPanel;
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ProgressPanel.tsx && git commit -m "feat: add ProgressPanel component"
```

---

### Task 20: DailyMap component

**Files:**
- Create: `frontend/src/components/DailyMap.tsx`

- [ ] **Step 1: Create components/DailyMap.tsx**

```tsx
import React, { useEffect, useRef, useState } from 'react';
import type { RouteCoordinate } from '../types/plan';

interface DailyMapProps {
  coordinates: RouteCoordinate[];
  dayIndex: number;
  exportMode: boolean;
  amapKey: string;
}

declare global {
  interface Window {
    AMap: any;
  }
}

const DailyMap: React.FC<DailyMapProps> = ({
  coordinates,
  dayIndex,
  exportMode,
  amapKey,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const [staticMapUrl, setStaticMapUrl] = useState<string>('');

  useEffect(() => {
    if (exportMode) {
      buildStaticMap();
      return;
    }
    if (!coordinates.length || !containerRef.current) return;
    initDynamicMap();

    return () => {
      if (mapRef.current) {
        mapRef.current.destroy();
        mapRef.current = null;
      }
    };
  }, [coordinates, exportMode, dayIndex]);

  const initDynamicMap = () => {
    const AMap = window.AMap;
    if (!AMap || !containerRef.current) return;

    const map = new AMap.Map(containerRef.current, {
      zoom: 12,
      center: [coordinates[0].lng, coordinates[0].lat],
      resizeEnable: false,
      dragEnable: false,
      zoomEnable: false,
      scrollWheel: false,
      doubleClickZoom: false,
      touchZoom: false,
    });
    mapRef.current = map;

    // 添加标记
    coordinates.forEach((coord) => {
      const isHotel = coord.type === 'hotel';
      const content = isHotel
        ? `<div style="background:#FF6B6B;color:#fff;width:28px;height:28px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:16px;box-shadow:0 2px 6px rgba(0,0,0,.3);">🏨</div>`
        : `<div style="background:#3B82F6;color:#fff;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:bold;box-shadow:0 2px 6px rgba(0,0,0,.3);">${coord.order}</div>`;

      new AMap.Marker({
        position: [coord.lng, coord.lat],
        content,
        offset: new AMap.Pixel(isHotel ? -14 : -12, isHotel ? -14 : -12),
        map,
      });
    });

    // 添加连线
    if (coordinates.length >= 2) {
      const path = coordinates.map((c) => [c.lng, c.lat]);
      new AMap.Polyline({
        path,
        strokeColor: '#3B82F6',
        strokeWeight: 3,
        strokeOpacity: 0.7,
        strokeStyle: 'dashed',
        showDir: true,
        map,
      });
    }

    map.setFitView(null, false, [60, 40, 40, 40]);
  };

  const buildStaticMap = () => {
    if (!coordinates.length) return;
    const base = 'https://restapi.amap.com/v3/staticmap';
    const markers = coordinates
      .map((c) => {
        const style = c.type === 'hotel'
          ? 'mid,0xFF6B6B,A'
          : `mid,0x3B82F6,${c.order}`;
        return `markers=${style}:${c.lng},${c.lat}`;
      })
      .join('&');
    const points = coordinates.map((c) => `${c.lng},${c.lat}`).join(';');
    const path = `path=0x3B82F6,2,0:${points}`;
    const url = `${base}?key=${amapKey}&size=800*200&scale=2&zoom=12&${markers}&${path}`;
    setStaticMapUrl(url);
  };

  if (exportMode && staticMapUrl) {
    return (
      <div className="w-full h-[120px] rounded-lg overflow-hidden bg-gray-100 mt-2">
        <img
          src={staticMapUrl}
          alt={`Day ${dayIndex + 1} route map`}
          className="w-full h-full object-cover"
        />
      </div>
    );
  }

  return (
    <div className="w-full h-[180px] rounded-lg overflow-hidden bg-gray-100 mt-2">
      {coordinates.length > 0 ? (
        <div ref={containerRef} className="w-full h-full" />
      ) : (
        <div className="w-full h-full flex items-center justify-center text-travel-muted text-xs">
          暂无路线数据
        </div>
      )}
    </div>
  );
};

export default DailyMap;
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/DailyMap.tsx && git commit -m "feat: add DailyMap component with static fallback"
```

---

### Task 21: DailyCard component

**Files:**
- Create: `frontend/src/components/DailyCard.tsx`

- [ ] **Step 1: Create components/DailyCard.tsx**

```tsx
import React from 'react';
import type { DailyPlan } from '../types/plan';
import DailyMap from './DailyMap';

interface DailyCardProps {
  plan: DailyPlan;
  dayIndex: number;
  totalDays: number;
  exportMode: boolean;
  amapKey: string;
}

const DailyCard: React.FC<DailyCardProps> = ({
  plan,
  dayIndex,
  totalDays,
  exportMode,
  amapKey,
}) => {
  const weatherEmoji = (w: string) => {
    if (w.includes('晴')) return '☀️';
    if (w.includes('多云')) return '⛅';
    if (w.includes('阴')) return '☁️';
    if (w.includes('雨')) return '🌧';
    if (w.includes('雪')) return '❄️';
    return '🌤';
  };

  return (
    <div className="bg-white rounded-card shadow-md overflow-hidden">
      {/* Day header */}
      <div className="px-4 py-3 bg-gradient-to-r from-travel-blue/5 to-travel-green/5 border-b border-gray-50">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-travel-text">
            Day {dayIndex + 1} · {plan.date}
          </h3>
          <span className="text-xs text-travel-muted">
            {dayIndex + 1}/{totalDays}
          </span>
        </div>
        {plan.weather && (
          <div className="flex items-center gap-2 mt-1 text-xs text-travel-muted">
            <span>{weatherEmoji(plan.weather.day_weather)}</span>
            <span>
              {plan.weather.day_weather} {plan.weather.low_temp}°C ~ {plan.weather.high_temp}°C
            </span>
            {plan.weather.clothing_advice && (
              <span className="text-gray-400">· {plan.weather.clothing_advice}</span>
            )}
          </div>
        )}
      </div>

      {/* Daily Route Map */}
      {plan.route_coordinates.length > 0 && (
        <DailyMap
          coordinates={plan.route_coordinates}
          dayIndex={dayIndex}
          exportMode={exportMode}
          amapKey={amapKey}
        />
      )}

      {/* Timeline */}
      <div className="px-4 py-3 space-y-3">
        {/* Transport (intercity) */}
        {plan.transport.map((t, i) => (
          <div key={`t-${i}`} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-sm">
                🚄
              </div>
              {i < plan.transport.length - 1 && (
                <div className="w-0.5 h-full bg-blue-200 mt-1" />
              )}
            </div>
            <div>
              <p className="text-sm font-medium text-travel-text">
                {t.from} → {t.to}
              </p>
              <p className="text-xs text-travel-muted">
                {t.mode} · ¥{t.cost}
              </p>
            </div>
          </div>
        ))}

        {/* Attractions */}
        {plan.attractions.map((a) => (
          <div key={`a-${a.order}`} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-travel-blue text-white flex items-center justify-center text-xs font-bold">
                {a.order}
              </div>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-travel-text">{a.name}</p>
              <p className="text-xs text-travel-muted">
                {a.time_slot} · {a.duration}
                {a.ticket > 0 ? ` · ¥${a.ticket}` : ' · 免费'}
                {a.rating ? ` · ⭐${a.rating}` : ''}
              </p>
            </div>
          </div>
        ))}

        {/* Meals */}
        {plan.meals.map((m, i) => (
          <div key={`m-${i}`} className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center text-sm">
              {m.type === 'breakfast' ? '🥐' : m.type === 'lunch' ? '🍜' : '🍽'}
            </div>
            <div>
              <p className="text-sm font-medium text-travel-text">
                {m.suggestion}
              </p>
              <p className="text-xs text-travel-muted">
                {m.type === 'breakfast' ? '早餐' : m.type === 'lunch' ? '午餐' : '晚餐'}
                {' · '}约 ¥{m.estimated_cost}
              </p>
            </div>
          </div>
        ))}

        {/* Hotel */}
        {plan.hotel && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-sm">
              🏨
            </div>
            <div>
              <p className="text-sm font-medium text-travel-text">
                {plan.hotel.name}
              </p>
              <p className="text-xs text-travel-muted">
                ¥{plan.hotel.price}/晚
                {plan.hotel.rating ? ` · ⭐${plan.hotel.rating}` : ''}
                {plan.hotel.address ? ` · ${plan.hotel.address}` : ''}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Day cost summary */}
      <div className="px-4 py-2.5 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
        <span className="text-xs text-travel-muted">今日花费</span>
        <span className="text-sm font-bold text-travel-blue">
          ¥{plan.daily_cost.toLocaleString()}
        </span>
      </div>
    </div>
  );
};

export default DailyCard;
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/DailyCard.tsx && git commit -m "feat: add DailyCard component with map + timeline"
```

---

### Task 22: CostSummary component

**Files:**
- Create: `frontend/src/components/CostSummary.tsx`

- [ ] **Step 1: Create components/CostSummary.tsx**

```tsx
import React from 'react';
import type { TierPlan } from '../types/plan';

interface CostSummaryProps {
  plan: TierPlan;
  totalBudget: number;
  tierLabel: string;
}

const CostSummary: React.FC<CostSummaryProps> = ({
  plan,
  totalBudget,
  tierLabel,
}) => {
  // Aggregate costs across all days
  const transportCost = plan.daily_plans.reduce(
    (sum, d) => sum + d.transport.reduce((s, t) => s + t.cost, 0),
    0
  );
  const hotelCost = plan.daily_plans.reduce(
    (sum, d) => sum + (d.hotel?.price || 0),
    0
  );
  const ticketCost = plan.daily_plans.reduce(
    (sum, d) => sum + d.attractions.reduce((s, a) => s + (a.ticket || 0), 0),
    0
  );
  const mealsCost = plan.daily_plans.reduce(
    (sum, d) => sum + d.meals.reduce((s, m) => s + (m.estimated_cost || 0), 0),
    0
  );

  const usagePercent = Math.min(
    (plan.total_cost / totalBudget) * 100,
    100
  );
  const barColor =
    usagePercent > 90 ? 'bg-red-500' : usagePercent > 70 ? 'bg-yellow-500' : 'bg-travel-green';

  return (
    <div className="bg-white rounded-card shadow-md p-4">
      <h3 className="text-sm font-semibold text-travel-text mb-3">
        💰 {tierLabel}档费用总览
      </h3>
      <div className="grid grid-cols-2 gap-2 mb-3">
        {[
          { label: '交通', cost: transportCost, icon: '🚄' },
          { label: '住宿', cost: hotelCost, icon: '🏨' },
          { label: '门票', cost: ticketCost, icon: '🎫' },
          { label: '餐饮', cost: mealsCost, icon: '🍽' },
        ].map(({ label, cost, icon }) => (
          <div key={label} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
            <span className="text-lg">{icon}</span>
            <div>
              <p className="text-xs text-travel-muted">{label}</p>
              <p className="text-sm font-semibold text-travel-text">¥{cost.toLocaleString()}</p>
            </div>
          </div>
        ))}
      </div>
      {/* Budget bar */}
      <div>
        <div className="flex justify-between text-xs text-travel-muted mb-1">
          <span>
            总计: ¥{plan.total_cost.toLocaleString()} / 预算 ¥{totalBudget.toLocaleString()}
          </span>
          <span>{usagePercent.toFixed(0)}%</span>
        </div>
        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full ${barColor} rounded-full transition-all duration-500`}
            style={{ width: `${usagePercent}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default CostSummary;
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/CostSummary.tsx && git commit -m "feat: add CostSummary component with budget bar"
```

---

### Task 23: ResultPanel + ExportButton

**Files:**
- Create: `frontend/src/components/ResultPanel.tsx`
- Create: `frontend/src/components/ExportButton.tsx`

- [ ] **Step 1: Create components/ExportButton.tsx**

```tsx
import React, { useState } from 'react';
import html2canvas from 'html2canvas';

interface ExportButtonProps {
  resultRef: React.RefObject<HTMLDivElement | null>;
}

const ExportButton: React.FC<ExportButtonProps> = ({ resultRef }) => {
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    if (!resultRef.current) return;
    setExporting(true);
    try {
      // Find all DailyMap containers and add data-export-mode attribute
      const mapContainers = resultRef.current.querySelectorAll('[data-map-container]');
      mapContainers.forEach((el) => {
        el.setAttribute('data-export-mode', 'true');
        // Trigger a re-render by dispatching a custom event
        el.dispatchEvent(new CustomEvent('exportModeChange', { bubbles: true }));
      });

      // Wait for static map images to load
      await new Promise((resolve) => setTimeout(resolve, 800));

      const canvas = await html2canvas(resultRef.current, {
        backgroundColor: '#F0FDF4',
        scale: 2,
        useCORS: true,
        allowTaint: true,
        logging: false,
      });

      // Download as PNG
      const link = document.createElement('a');
      link.download = `旅行规划_${new Date().toISOString().slice(0, 10)}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();

      // Reset map containers
      mapContainers.forEach((el) => {
        el.removeAttribute('data-export-mode');
        el.dispatchEvent(new CustomEvent('exportModeChange', { bubbles: true }));
      });
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setExporting(false);
    }
  };

  return (
    <button
      onClick={handleExport}
      disabled={exporting}
      className="w-full py-3 bg-travel-text text-white font-semibold text-sm rounded-xl hover:bg-gray-800 disabled:opacity-50 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
    >
      {exporting ? (
        <>
          <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          导出中...
        </>
      ) : (
        '📥 导出长截图'
      )}
    </button>
  );
};

export default ExportButton;
```

- [ ] **Step 2: Create components/ResultPanel.tsx**

```tsx
import React, { useRef } from 'react';
import type { PlanResult, TierKey } from '../types/plan';
import { TIER_LABELS } from '../types/plan';
import DailyCard from './DailyCard';
import CostSummary from './CostSummary';
import ExportButton from './ExportButton';

interface ResultPanelProps {
  result: PlanResult;
  activeTier: TierKey;
  onTierChange: (tier: TierKey) => void;
  amapKey: string;
}

const TIERS: TierKey[] = ['economy', 'comfort', 'luxury'];

const ResultPanel: React.FC<ResultPanelProps> = ({
  result,
  activeTier,
  onTierChange,
  amapKey,
}) => {
  const resultRef = useRef<HTMLDivElement>(null);
  const plan = result.plans[activeTier];
  const totalBudget = result.input.budget;

  return (
    <div className="mx-4 mt-4 space-y-4" ref={resultRef}>
      {/* Tier Tabs */}
      <div className="flex bg-white rounded-card p-1 shadow-md">
        {TIERS.map((tier) => (
          <button
            key={tier}
            onClick={() => onTierChange(tier)}
            className={`flex-1 py-2.5 text-sm font-medium rounded-xl transition-all ${
              activeTier === tier
                ? 'bg-gradient-to-r from-travel-blue to-travel-green text-white shadow-md'
                : 'text-travel-muted hover:text-travel-text'
            }`}
          >
            {TIER_LABELS[tier]}
            {result.plans[tier]?.total_cost > 0 && (
              <span className="block text-xs opacity-80">
                ¥{result.plans[tier].total_cost.toLocaleString()}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Daily plans */}
      <div className="space-y-3">
        {plan.daily_plans.map((dayPlan, idx) => (
          <DailyCard
            key={`${activeTier}-day-${idx}`}
            plan={dayPlan}
            dayIndex={idx}
            totalDays={plan.daily_plans.length}
            exportMode={false}
            amapKey={amapKey}
          />
        ))}
      </div>

      {/* Cost summary */}
      {plan.daily_plans.length > 0 && (
        <CostSummary
          plan={plan}
          totalBudget={totalBudget}
          tierLabel={TIER_LABELS[activeTier]}
        />
      )}

      {/* Export */}
      <ExportButton resultRef={resultRef} />
    </div>
  );
};

export default ResultPanel;
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ResultPanel.tsx frontend/src/components/ExportButton.tsx && git commit -m "feat: add ResultPanel with tier tabs and screenshot export"
```

---

### Task 24: App root + wiring

**Files:**
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Create App.tsx**

```tsx
import React from 'react';
import Header from './components/Header';
import PlanForm from './components/PlanForm';
import ProgressPanel from './components/ProgressPanel';
import ResultPanel from './components/ResultPanel';
import { usePlan } from './hooks/usePlan';

const AMAP_KEY = 'YOUR_AMAP_KEY'; // 替换为实际的高德 JS API key

const App: React.FC = () => {
  const {
    loading,
    result,
    activeTier,
    setActiveTier,
    error,
    agentProgress,
    progressMessages,
    startPlanning,
  } = usePlan();

  return (
    <div className="max-w-lg mx-auto min-h-screen pb-10">
      <Header />
      <PlanForm onSubmit={startPlanning} loading={loading} />

      {error && (
        <div className="mx-4 mt-4 p-4 bg-red-50 border border-red-200 rounded-card">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {loading && !result && (
        <ProgressPanel agentProgress={agentProgress} messages={progressMessages} />
      )}

      {result && (
        <ResultPanel
          result={result}
          activeTier={activeTier}
          onTierChange={setActiveTier}
          amapKey={AMAP_KEY}
        />
      )}

      {/* Footer */}
      <footer className="mt-8 text-center text-xs text-travel-muted pb-4">
        <p>数据来源: 高德地图 API | AI 生成内容仅供参考</p>
        <p className="mt-0.5">Smart Travel Planning © 2026</p>
      </footer>
    </div>
  );
};

export default App;
```

- [ ] **Step 2: Full build verification**

Run: `cd frontend && npx tsc --noEmit && npm run build`
Expected: Build succeeds without errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx && git commit -m "feat: wire up App with all components"
```

---

### Task 25: Backend .env + startup test

**Files:**
- Create: `backend/.env` (from .env.example, with actual keys)

- [ ] **Step 1: Copy .env.example to .env and fill keys**

Run: `cd backend && cp .env.example .env`
Then manually edit .env to add actual API keys.

- [ ] **Step 2: Start backend and verify**

Run: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
Then in another terminal: `curl http://localhost:8000/health`
Expected: `{"status":"ok"}`

- [ ] **Step 3: Test POST /api/plan endpoint**

```bash
curl -X POST http://localhost:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "上海",
    "destination": "杭州",
    "budget": 3000,
    "intercity_mode": "high_speed_rail",
    "city_transit": "mixed",
    "days": 3,
    "preferences": ["nature", "history"],
    "start_date": "2026-06-20"
  }'
```
Expected: Returns `{"task_id": "...", "status": "pending", "created_at": "..."}`

- [ ] **Step 4: Commit**

```bash
git add backend/.env.example && git commit -m "chore: add env config and startup verification"
```

---

### Task 26: Integration verification

- [ ] **Step 1: Start both services**

Terminal 1: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
Terminal 2: `cd frontend && npm run dev`

- [ ] **Step 2: Open browser to http://localhost:3000**

Verify:
1. Page renders with Header, PlanForm ✓
2. Fill form → click "开始规划" → ProgressPanel shows agent progress ✓
3. After planning completes, ResultPanel renders with 3 tiers ✓
4. Each DailyCard shows map, timeline, weather ✓
5. Switch between economy/comfort/luxury tabs ✓
6. Click "导出长截图" downloads PNG ✓

- [ ] **Step 3: Commit final changes**

```bash
git add -A && git commit -m "feat: complete smart travel planning MVP"
```
