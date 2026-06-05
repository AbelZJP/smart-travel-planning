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
        if not isinstance(biz, dict):
            biz = {}
        # cost 可能为字符串、数字、列表，统一安全处理
        cost = biz.get("cost", "0")
        try:
            if isinstance(cost, (list, tuple)):
                price = float(cost[0]) if cost else 300
            else:
                price = float(cost) if cost else 300
        except (ValueError, TypeError, IndexError):
            price = 300
        # rating 同理
        rating_raw = biz.get("rating", 0)
        try:
            if isinstance(rating_raw, (list, tuple)):
                rating = float(rating_raw[0]) if rating_raw else 0
            else:
                rating = float(rating_raw) if rating_raw else 0
        except (ValueError, TypeError, IndexError):
            rating = 0
        hotels.append(
            {
                "name": p.get("name"),
                "lng": float(p.get("location", "0,0").split(",")[0]),
                "lat": float(p.get("location", "0,0").split(",")[1]),
                "rating": rating or None,
                "price_per_night": price,
                "address": p.get("address", ""),
            }
        )
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
