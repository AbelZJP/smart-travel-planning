"""景点搜索 Agent — 直接调用高德 POI，规则化估算时长/票价，无需 LLM"""
import asyncio
from typing import List, Dict, Any
from app.mcp.amap_client import AmapClient

amap = AmapClient()

PREFERENCE_KEYWORDS = {
    "nature": "自然风光",
    "history": "历史文化",
    "food": "美食购物",
    "family": "亲子休闲",
}

PREFERENCE_TYPES = {
    "自然风光": "风景名胜|公园|自然景观|山|湖|海滩|森林公园",
    "历史文化": "博物馆|古迹|寺庙|名人故居|历史建筑|纪念馆",
    "美食购物": "美食街|步行街|特色餐厅|购物中心|夜市",
    "亲子休闲": "游乐园|动物园|水族馆|科技馆|植物园|主题公园",
}

# 根据 POI 类型估算游玩时长和票价
CATEGORY_ESTIMATES = {
    "风景名胜": ("3h", 60),
    "公园": ("2h", 0),
    "博物馆": ("2h", 30),
    "古迹": ("1.5h", 40),
    "寺庙": ("1.5h", 30),
    "游乐园": ("4h", 200),
    "动物园": ("3h", 100),
    "购物": ("2h", 0),
    "美食": ("1.5h", 0),
}


def _estimate(category: str) -> tuple:
    for key, (dur, ticket) in CATEGORY_ESTIMATES.items():
        if key in category:
            return dur, ticket
    return "2h", 20


async def run_attraction_agent(
    destination: str,
    days: int,
    preferences: List[str],
) -> List[Dict[str, Any]]:
    """搜索景点（无 LLM，秒级响应），每种偏好并行搜一次"""
    seen = set()
    all_attractions = []

    async def search_pref(pref: str):
        keyword = PREFERENCE_KEYWORDS.get(pref, pref)
        types = PREFERENCE_TYPES.get(keyword, "风景名胜")
        results = await amap.search_poi(keywords=keyword, city=destination, types=types, offset=10)
        parsed = []
        for p in results:
            name = p.get("name", "")
            if name in seen:
                continue
            seen.add(name)
            cat = p.get("type", "")
            dur, ticket = _estimate(cat)
            try:
                lng, lat = p.get("location", "0,0").split(",")
                lng, lat = float(lng), float(lat)
            except (ValueError, AttributeError):
                lng, lat = 0.0, 0.0
            biz = p.get("biz_ext", {})
            rating = 3.5
            if isinstance(biz, dict):
                r = biz.get("rating", 0)
                rating = float(r) if r else 3.5
            parsed.append({
                "name": name,
                "lng": lng,
                "lat": lat,
                "rating": rating,
                "category": cat,
                "address": p.get("address", ""),
                "suggested_duration_h": dur,
                "estimated_ticket": ticket,
            })
        return parsed

    prefs = preferences if preferences else ["nature"]
    tasks = [search_pref(p) for p in prefs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if not isinstance(r, Exception):
            all_attractions.extend(r)

    all_attractions.sort(key=lambda a: a.get("rating") or 0, reverse=True)
    return all_attractions[: days * 5]
