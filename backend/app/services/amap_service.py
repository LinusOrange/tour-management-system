import httpx
import os

AMAP_KEY = os.getenv("AMAP_API_KEY")

async def get_driving_duration(origin: str, destination: str) -> int:
    """
    计算两点间的行车耗时（单位：分钟）
    origin/destination 格式: "经度,纬度" (例如: "116.481028,39.989643")
    """
    url = "https://restapi.amap.com/v3/direction/driving"
    params = {
        "key": AMAP_KEY,
        "origin": origin,
        "destination": destination,
        "extensions": "base"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        
        if data["status"] == "1" and data["route"]["paths"]:
            # duration 单位是秒，我们转换为分钟并向上取整
            seconds = int(data["route"]["paths"][0]["duration"])
            return (seconds // 60) + 1
        return 30  # 如果调用失败，默认预留30分钟作为保底