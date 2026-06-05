import asyncio
import httpx
from typing import Optional, List, Dict, Any
from app.config import settings

AMAP_BASE = "https://restapi.amap.com/v3"

# 个人开发者 QPS 限制，串行化请求 + 间隔
_amap_semaphore = asyncio.Semaphore(1)
_REQUEST_GAP = 0.6  # 每次请求间隔 600ms
_last_request_time = 0.0


class AmapError(Exception):
    """高德地图 API 错误"""
    pass


class AmapClient:
    def __init__(self):
        self.key = settings.amap_api_key
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    self._client = httpx.AsyncClient(timeout=httpx.Timeout(15.0))
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """带限流和重试的 API 请求"""
        global _last_request_time

        async with _amap_semaphore:
            # 强制请求间隔，避免超 QPS
            now = asyncio.get_event_loop().time()
            gap = _REQUEST_GAP - (now - _last_request_time)
            if gap > 0:
                await asyncio.sleep(gap)

            for attempt in range(4):
                try:
                    client = await self._get_client()
                    params["key"] = self.key
                    resp = await client.get(f"{AMAP_BASE}{path}", params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    if data.get("status") != "1":
                        info = data.get("info", "unknown")
                        # QPS 超限，等一等重试
                        if "EXCEEDED" in str(info).upper() or "LIMIT" in str(info).upper():
                            wait = 1.5 * (attempt + 1)
                            await asyncio.sleep(wait)
                            continue
                        raise AmapError(f"Amap API error: {info}")
                    return data
                except httpx.RequestError:
                    if attempt < 3:
                        await asyncio.sleep(1 * (attempt + 1))
                        continue
                    raise

            raise AmapError("Amap API request failed after 4 retries")

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
        for m in markers:
            style = "mid,0xFF6B6B,A" if m.get("type") == "hotel" else "mid,0x3B82F6,"
            marker_str += f"&markers={style}:{m['lng']},{m['lat']}"
        path = ",".join(f"{p}" for p in path_points[:8])  # max 8 waypoints
        url = f"{base}?key={self.key}&size={size}&scale=2&zoom=13{marker_str}"
        if path_points:
            url += f"&path=0x3B82F6,2,0:{path}"
        return url
