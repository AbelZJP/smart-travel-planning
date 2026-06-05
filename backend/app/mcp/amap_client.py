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
