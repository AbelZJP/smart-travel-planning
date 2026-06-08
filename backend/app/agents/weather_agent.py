"""天气查询 Agent — 直接调用高德 API，规则化生成穿衣/出行建议，无需 LLM"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.mcp.amap_client import AmapClient

amap = AmapClient()


def _clothing_advice(high: int, low: int, weather: str) -> str:
    """根据温度和天气生成穿衣建议"""
    if "雨" in weather:
        return "记得带雨伞，穿防滑鞋"
    if "雪" in weather:
        return "注意保暖，穿防滑靴，戴手套围巾"
    avg = (high + low) / 2
    if avg > 30:
        return "建议穿短袖短裤，注意防晒"
    elif avg > 25:
        return "建议穿短袖，带一件薄外套"
    elif avg > 20:
        return "建议穿薄长袖或短袖+薄外套"
    elif avg > 15:
        return "建议穿长袖，早晚加一件外套"
    elif avg > 10:
        return "建议穿薄毛衣或卫衣，加一件外套"
    elif avg > 5:
        return "建议穿厚毛衣/卫衣+外套"
    else:
        return "建议穿羽绒服，注意保暖"


def _travel_advice(weather: str, high: int) -> str:
    """根据天气生成出行建议"""
    if "雨" in weather or "雪" in weather:
        return "建议安排室内景点，备好雨具"
    if high > 35:
        return "高温天气，避免正午户外活动，多补水"
    if "晴" in weather:
        return "天气晴好，非常适合户外活动"
    if "多云" in weather or "阴" in weather:
        return "适合户外活动，体感舒适"
    return "可以正常出行"


def _rain_probability(weather: str) -> float:
    """简单判断降雨概率"""
    if "暴雨" in weather:
        return 0.9
    if "大雨" in weather:
        return 0.8
    if "中雨" in weather:
        return 0.7
    if "小雨" in weather or "阵雨" in weather or "雷阵雨" in weather:
        return 0.6
    if "阴" in weather:
        return 0.3
    if "多云" in weather:
        return 0.15
    return 0.05


async def run_weather_agent(
    destination: str, start_date: str, days: int
) -> List[Dict[str, Any]]:
    """查询天气并生成建议（无 LLM，毫秒级响应）"""
    # 先地理编码获取 adcode，比直接传城市名更稳定
    try:
        geo = await amap.geocode(destination)
        adcode = geo.get("adcode", destination)
    except Exception:
        adcode = destination

    data = await amap.get_weather(adcode, extensions="all")
    forecasts = data.get("forecasts", [])
    if not forecasts:
        return []

    daily = forecasts[0].get("casts", [])
    start = datetime.strptime(start_date, "%Y-%m-%d")
    date_range = {(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)}

    result = []
    for d in daily:
        date = d.get("date", "")
        if date not in date_range:
            continue
        dw = d.get("dayweather", "")
        nw = d.get("nightweather", "")
        high = int(d.get("daytemp", 0))
        low = int(d.get("nighttemp", 0))
        wind = f"{d.get('daywind', '')}{d.get('daypower', '')}"

        result.append({
            "date": date,
            "day_weather": dw,
            "night_weather": nw,
            "high_temp": high,
            "low_temp": low,
            "wind": wind if wind else "微风",
            "rain_probability": max(_rain_probability(dw), _rain_probability(nw)),
            "clothing_advice": _clothing_advice(high, low, dw),
            "travel_advice": _travel_advice(dw, high),
            "suitable": "雨" not in dw or "小雨" in dw,
        })

    return result
