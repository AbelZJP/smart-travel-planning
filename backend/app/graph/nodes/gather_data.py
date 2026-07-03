"""数据采集节点 (gather_data)

当旅行需求已填满时，并行调用高德地图 API 采集景点、天气、酒店数据。
这是一个纯函数节点（非 LLM 节点），直接调用 Amap HTTP 接口。
"""
import asyncio
from typing import List, Dict, Any
from app.graph.state import GraphState
from app.graph.tools import search_attractions, get_weather_forecast, search_hotels


async def _gather_attractions(destination: str, preferences: List[str]) -> List[Dict[str, Any]]:
    """根据偏好并行搜索景点"""
    if not preferences:
        preferences = ["自然风光"]

    pref_keyword_map = {
        "nature": "自然风光", "history": "历史文化",
        "food": "美食购物", "family": "亲子休闲",
    }

    tasks = []
    for pref in preferences:
        keyword = pref_keyword_map.get(pref, pref)
        tasks.append(search_attractions.ainvoke({"keyword": keyword, "city": destination}))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    seen = set()
    all_attractions = []
    for r in results:
        if isinstance(r, Exception):
            continue
        for item in r:
            name = item.get("name", "")
            if name not in seen:
                seen.add(name)
                all_attractions.append(item)
    return all_attractions


async def gather_data_node(state: GraphState) -> dict:
    """并行采集景点、天气、酒店数据，存入 tools_cache"""
    req = state.get("requirements", {})
    cache = state.get("tools_cache", {})
    destination = req.get("destination", "")
    days = req.get("days", 3)
    start_date = req.get("start_date", "")
    preferences = req.get("preferences", ["nature"])

    if not destination:
        return {}

    # 只在缓存为空时采集
    tasks = []
    if not cache.get("attractions"):
        tasks.append(("attractions", _gather_attractions(destination, preferences)))
    else:
        tasks.append(("attractions", None))

    if not cache.get("weather") and start_date:
        tasks.append(("weather", get_weather_forecast.ainvoke({"city": destination, "days": days + 2})))
    else:
        tasks.append(("weather", None))

    if not cache.get("hotels", {}).get("economy"):
        tasks.append(("hotels", search_hotels.ainvoke({"city": destination, "price_max": 2000})))
    else:
        tasks.append(("hotels", None))

    new_cache = dict(cache)

    for key, coro in tasks:
        if coro is None:
            continue
        try:
            result = await coro
            if key == "attractions":
                new_cache["attractions"] = result[:days * 5]
            elif key == "weather":
                forecasts = result.get("forecasts", []) if isinstance(result, dict) else []
                new_cache["weather"] = forecasts[:days + 2]
            elif key == "hotels":
                new_cache["hotels"] = {"economy": [], "comfort": [], "luxury": []}
                for h in result:
                    price = h.get("price_per_night", 300)
                    if price <= 200:
                        new_cache["hotels"]["economy"].append(h)
                    elif price <= 500:
                        new_cache["hotels"]["comfort"].append(h)
                    else:
                        new_cache["hotels"]["luxury"].append(h)
        except Exception as e:
            print(f"[gather_data] Error gathering {key}: {e}")

    return {"tools_cache": new_cache}
