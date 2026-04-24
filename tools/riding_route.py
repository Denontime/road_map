import requests
from typing import Dict, List, Optional, Any

class RidingRoute:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v4/direction/bicycling"

    def plan(self, origin: str, destination: str) -> Optional[Dict[str, Any]]:
        params = {
            "key": self.api_key,
            "origin": origin,
            "destination": destination
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            result = response.json()

            if result.get("errcode") == 0 and result.get("data"):
                return result["data"]
            return None
        except Exception as e:
            print(f"Riding route planning error: {e}")
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
                "duration": step.get("duration", 0),
                "action": step.get("action", ""),
                "orientation": step.get("orientation", ""),
                "polyline": step.get("polyline", "")
            })

        return {
            "distance": path.get("distance", 0),
            "duration": path.get("duration", 0),
            "steps": parsed_steps
        }