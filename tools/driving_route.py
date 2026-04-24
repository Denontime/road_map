import requests
from typing import Dict, List, Optional, Any

DRIVING_STRATEGIES = {
    0: "推荐模式",
    1: "避免收费",
    2: "高速优先",
    3: "躲避拥堵",
    4: "避免收费且躲避拥堵",
    5: "高速优先且躲避拥堵",
    6: "躲避拥堵且不走高速",
    7: "多策略（同时规划多种路线）",
    8: "躲避拥堵且避免收费",
    9: "躲避拥堵且高速优先",
    10: "默认（综合最优）"
}

class DrivingRoute:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/direction/driving"

    def plan(self, origin: str, destination: str, strategy: int = 10) -> Optional[Dict[str, Any]]:
        params = {
            "key": self.api_key,
            "origin": origin,
            "destination": destination,
            "strategy": strategy
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            result = response.json()

            if result.get("status") == "1" and result.get("route"):
                return result["route"]
            return None
        except Exception as e:
            print(f"Driving route planning error: {e}")
            return None

    def parse_route(self, route_data: Dict) -> Dict[str, Any]:
        if not route_data or "paths" not in route_data:
            return {}

        path = route_data["paths"][0]
        steps = path.get("steps", [])

        parsed_steps = []
        for step in steps:
            parsed_steps.append({
                "instruction": step.get("instruction", ""),
                "road": step.get("road", ""),
                "distance": int(step.get("distance", 0)),
                "duration": int(step.get("duration", 0)),
                "action": step.get("action", ""),
                "orientation": step.get("orientation", ""),
                "polyline": step.get("polyline", "")
            })

        return {
            "distance": int(path.get("distance", 0)),
            "duration": int(path.get("duration", 0)),
            "steps": parsed_steps
        }