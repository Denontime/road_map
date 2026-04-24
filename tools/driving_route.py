import requests
from typing import Dict, List, Optional, Any

class DrivingRoute:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/direction/driving"

    def plan(self, origin: str, destination: str, strategy: int = 0) -> Optional[Dict[str, Any]]:
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
                "distance": step.get("distance", 0),
                "duration": step.get("time", 0),
                "action": step.get("action", ""),
                "orientation": step.get("orientation", ""),
                "polyline": step.get("polyline", "")
            })

        return {
            "distance": int(path.get("distance", 0)),
            "duration": int(path.get("time", 0)),
            "steps": parsed_steps
        }