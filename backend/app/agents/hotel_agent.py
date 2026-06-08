"""酒店推荐 Agent — 直接调用高德周边搜索，按档位筛选，无需 LLM"""
from typing import List, Dict, Any
from app.mcp.amap_client import AmapClient

amap = AmapClient()

TIER_PRICE_MAX = {"economy": 200, "comfort": 500, "luxury": 2000}


def _parse_hotels(results: list, max_price: float) -> list:
    hotels = []
    for p in results:
        biz = p.get("biz_ext", {})
        if not isinstance(biz, dict):
            biz = {}
        cost = biz.get("cost", 0)
        try:
            price = float(cost[0]) if isinstance(cost, (list, tuple)) else float(cost) if cost else 300
        except (ValueError, TypeError):
            price = 300
        rating_raw = biz.get("rating", 0)
        try:
            rating = float(rating_raw[0]) if isinstance(rating_raw, (list, tuple)) else float(rating_raw) if rating_raw else 0
        except (ValueError, TypeError):
            rating = 0
        hotels.append({
            "name": p.get("name"),
            "lng": float(p.get("location", "0,0").split(",")[0]),
            "lat": float(p.get("location", "0,0").split(",")[1]),
            "rating": rating or 3.5,
            "price_per_night": price,
            "address": p.get("address", ""),
        })

    hotels = [h for h in hotels if h["price_per_night"] <= max_price]
    hotels.sort(key=lambda h: h.get("rating") or 0, reverse=True)
    return hotels[:6]


async def run_hotel_agent(destination: str) -> Dict[str, List[Dict[str, Any]]]:
    """搜索酒店，三个档位并行查询（无 LLM，秒级响应）"""
    try:
        geo = await amap.geocode(destination)
        center = geo.get("location", "116.397,39.908")
    except Exception:
        center = "116.397,39.908"

    # 三个档位并行搜索
    import asyncio

    async def search_tier(tier: str):
        max_price = TIER_PRICE_MAX[tier]
        results = await amap.search_around(
            location=center,
            keywords="酒店|宾馆|旅馆|精品酒店|度假酒店",
            types="住宿服务",
            radius=5000,
            offset=10,
        )
        return tier, _parse_hotels(results, max_price)

    tasks = [search_tier(t) for t in ["economy", "comfort", "luxury"]]
    tier_results = await asyncio.gather(*tasks, return_exceptions=True)

    hotels = {}
    for r in tier_results:
        if isinstance(r, Exception):
            continue
        tier, data = r
        hotels[tier] = data

    for t in ["economy", "comfort", "luxury"]:
        if t not in hotels:
            hotels[t] = []

    return hotels
