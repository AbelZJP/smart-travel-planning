"""高德 MCP 工具 → LangChain Tool 注册

将 app/mcp/amap_client.py 的 4 个核心搜索方法
封装为 LangChain @tool 装饰器格式，供 LLM 绑定调用。

注意：这些工具主要用于 gather_data（函数节点直接调用）
和 replan（LLM 自主调用）。generate_plan 节点不走这里。
"""
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from app.mcp.amap_client import AmapClient

amap = AmapClient()


@tool
async def search_attractions(
    keyword: str,
    city: str,
    radius: int = 10000,
    offset: int = 15,
) -> list[dict]:
    """搜索目的地景点。当用户提到想去某个城市/目的地时，调用此工具获取景点列表。

    Args:
        keyword: 搜索关键词，如 "自然风光" "西湖" "博物馆" "游乐园"
        city: 目的地城市名，如 "杭州"
        radius: 搜索半径（米），默认 10000
        offset: 返回结果数量上限，默认 15
    """
    types_map = {
        "自然风光": "风景名胜|公园|自然景观|山|湖|海滩",
        "历史文化": "博物馆|古迹|寺庙|名人故居|历史建筑",
        "美食购物": "美食街|步行街|特色餐厅|购物中心",
        "亲子休闲": "游乐园|动物园|水族馆|科技馆|植物园",
    }
    types = types_map.get(keyword, "风景名胜")
    pois = await amap.search_poi(keywords=keyword, city=city, types=types, offset=offset)
    results = []
    for p in pois:
        try:
            lng, lat = p.get("location", "0,0").split(",")
            lng, lat = float(lng), float(lat)
        except (ValueError, AttributeError):
            lng, lat = 0.0, 0.0
        biz = p.get("biz_ext", {}) or {}
        rating_raw = biz.get("rating", 0)
        try:
            rating = float(rating_raw) if rating_raw else None
        except (ValueError, TypeError):
            rating = None
        results.append({
            "name": p.get("name", ""),
            "lng": lng,
            "lat": lat,
            "rating": rating,
            "category": p.get("type", ""),
            "address": p.get("address", ""),
            "adname": p.get("adname", ""),
        })
    return results


@tool
async def get_weather_forecast(city: str, days: int = 7) -> dict:
    """查询目的地天气预报。用于了解旅行期间的天气情况，给出穿衣/出行建议。

    Args:
        city: 城市名，如 "杭州"
        days: 预报天数，默认 7 天，最大 7 天
    """
    data = await amap.get_weather(city, extensions="all")
    forecasts = data.get("forecasts", [])
    if not forecasts:
        return {"city": city, "forecasts": []}
    casts = forecasts[0].get("casts", [])[:days]
    return {
        "city": forecasts[0].get("city", city),
        "report_time": forecasts[0].get("reporttime", ""),
        "forecasts": [
            {
                "date": d.get("date"),
                "day_weather": d.get("dayweather"),
                "night_weather": d.get("nightweather"),
                "high_temp": int(d.get("daytemp", 0)),
                "low_temp": int(d.get("nighttemp", 0)),
                "day_wind": d.get("daywind", ""),
                "day_power": d.get("daypower", ""),
            }
            for d in casts
        ],
    }


@tool
async def search_hotels(
    city: str,
    location: str = "",
    radius: int = 5000,
    price_max: float = 500,
) -> list[dict]:
    """搜索目的地酒店。推荐住宿时调用此工具。

    Args:
        city: 城市名
        location: 搜索中心坐标 "lng,lat"，留空会自动地理编码
        radius: 搜索半径（米），默认 5000
        price_max: 最高价格（元/晚），默认 500
    """
    if not location:
        try:
            geo = await amap.geocode(city)
            location = geo.get("location", "116.397,39.908")
        except Exception:
            location = "116.397,39.908"

    pois = await amap.search_around(
        location=location,
        keywords="酒店|宾馆|旅馆|精品酒店|度假酒店",
        types="住宿服务",
        radius=radius,
        offset=15,
    )
    hotels = []
    for p in pois:
        biz = p.get("biz_ext", {}) or {}
        cost = biz.get("cost", "0")
        try:
            price = float(cost[0]) if isinstance(cost, (list, tuple)) and cost else float(cost) if cost else 300
        except (ValueError, TypeError):
            price = 300
        rating_raw = biz.get("rating", 0)
        try:
            rating = float(rating_raw[0]) if isinstance(rating_raw, (list, tuple)) and rating_raw else float(rating_raw) if rating_raw else 0
        except (ValueError, TypeError):
            rating = 0
        if price <= price_max:
            try:
                lng, lat = p.get("location", "0,0").split(",")
                lng, lat = float(lng), float(lat)
            except (ValueError, AttributeError):
                lng, lat = 0.0, 0.0
            hotels.append({
                "name": p.get("name", ""),
                "lng": lng,
                "lat": lat,
                "rating": rating or None,
                "price_per_night": price,
                "address": p.get("address", ""),
            })
    hotels.sort(key=lambda h: h.get("rating") or 0, reverse=True)
    return hotels[:10]


@tool
async def plan_transport_route(
    origin_lng: float,
    origin_lat: float,
    dest_lng: float,
    dest_lat: float,
    city: str,
    mode: str = "transit",
) -> dict:
    """规划两点之间的交通路线。用于安排每日景点间的交通衔接。

    Args:
        origin_lng: 起点经度
        origin_lat: 起点纬度
        dest_lng: 终点经度
        dest_lat: 终点纬度
        city: 所在城市
        mode: 出行方式 "driving"（驾车）或 "transit"（公交/地铁）
    """
    origin = f"{origin_lng},{origin_lat}"
    destination = f"{dest_lng},{dest_lat}"
    if mode == "driving":
        data = await amap.plan_driving(origin, destination)
        paths = data.get("route", {}).get("paths", [])
        if paths:
            p = paths[0]
            return {
                "mode": "driving",
                "distance_m": int(p.get("distance", 0)),
                "duration_s": int(p.get("duration", 0)),
                "cost_estimated": round(int(p.get("distance", 0)) / 1000 * 1.5, 1),
            }
    else:
        data = await amap.plan_transit(origin, destination, city)
        transits = data.get("route", {}).get("transits", [])
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


@tool
async def geocode(address: str, city: str = "") -> dict:
    """地址转坐标。需要根据地名查询经纬度时调用（如规划路线前先把地名转成坐标）。

    Args:
        address: 地址或地名，如"西湖""灵隐寺""北京天安门"
        city: 所在城市（可选，提高准确性），如"杭州"
    """
    try:
        geo = await amap.geocode(address, city=city or None)
        lng, lat = geo.get("location", "0,0").split(",")
        return {
            "address": address,
            "lng": float(lng),
            "lat": float(lat),
            "formatted": geo.get("formatted_address", ""),
        }
    except Exception as e:
        return {"address": address, "error": str(e)}


# 统一导出给 LLM 绑定
AMAP_TOOLS = [search_attractions, get_weather_forecast, search_hotels, plan_transport_route, geocode]
