import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from .geocoder import Geocoder
from .riding_route import RidingRoute
from .driving_route import DrivingRoute
from .poi_search import POISearch
from .config import config

VEHICLE_TYPES = {
    "motorcycle": {"name": "摩托车/汽车", "icon": "🏍️ 🚗", "color": "#3b82f6"},
    "bicycle": {"name": "自行车", "icon": "🚴", "color": "#10b981"},
    "walking": {"name": "步行", "icon": "🚶", "color": "#8b5cf6"}
}

class RoutePlanner:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.geocoder = Geocoder(api_key)
        self.riding = RidingRoute(api_key)
        self.driving = DrivingRoute(api_key)
        self.poi = POISearch(api_key)

    def geocode_address(self, address: str, city: str = None) -> Optional[Dict[str, Any]]:
        result = self.geocoder.geocode_or_poi(address, city)
        if result:
            location, formatted_address = result
            lng, lat = location.split(",")
            return {
                "address": address,
                "formatted_address": formatted_address,
                "location": location,
                "lng": float(lng),
                "lat": float(lat)
            }
        return None

    def plan_route(self, origin: Dict, destination: Dict, waypoints: List[Dict] = None,
                   vehicle_type: str = "motorcycle") -> Dict[str, Any]:
        full_route = {
            "origin": origin,
            "destination": destination,
            "waypoints": waypoints or [],
            "vehicle_type": vehicle_type,
            "segments": [],
            "total_distance": 0,
            "total_duration": 0
        }

        points = [origin] + (waypoints or []) + [destination]
        for i in range(len(points) - 1):
            start = points[i]
            end = points[i + 1]

            if vehicle_type == "bicycle":
                route_data = self.riding.plan(start["location"], end["location"])
                if route_data:
                    parsed = self.riding.parse_route(route_data)
                else:
                    parsed = None
            elif vehicle_type == "walking":
                parsed = self._plan_walking(start, end)
            else:
                route_data = self.driving.plan(start["location"], end["location"])
                if route_data:
                    parsed = self.driving.parse_route(route_data)
                else:
                    parsed = None

            if parsed:
                segment = {
                    "from": start.get("formatted_address", start["address"]),
                    "to": end.get("formatted_address", end["address"]),
                    "distance": parsed["distance"],
                    "duration": parsed["duration"],
                    "steps": parsed["steps"]
                }
                full_route["segments"].append(segment)
                full_route["total_distance"] += parsed["distance"]
                full_route["total_duration"] += parsed["duration"]

        return full_route

    def _plan_walking(self, origin: Dict, destination: Dict) -> Optional[Dict[str, Any]]:
        url = "https://restapi.amap.com/v3/direction/walking"
        params = {
            "key": self.api_key,
            "origin": origin["location"],
            "destination": destination["location"]
        }
        try:
            import requests
            response = requests.get(url, params=params, timeout=15)
            result = response.json()
            if result.get("status") == "1" and result.get("route"):
                path = result["route"]["paths"][0]
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
                    "distance": path.get("distance", 0),
                    "duration": path.get("time", 0),
                    "steps": parsed_steps
                }
        except Exception as e:
            print(f"Walking route planning error: {e}")
        return None

    def generate_route_book_data(self, origin_address: str, destination_address: str,
                                 return_via: List[str] = None,
                                 vehicle_type: str = "motorcycle") -> Dict[str, Any]:
        origin = self.geocode_address(origin_address)
        destination = self.geocode_address(destination_address)

        if not origin or not destination:
            return {"error": "无法解析地址坐标"}

        waypoints = []
        if return_via:
            for addr in return_via:
                wp = self.geocode_address(addr)
                if wp:
                    waypoints.append(wp)

        go_route = self.plan_route(origin, destination, waypoints if waypoints else None, vehicle_type)

        return_route = None
        if return_via:
            return_route = self.plan_route(destination, origin, waypoints, vehicle_type)

        return {
            "created_at": datetime.now().isoformat(),
            "origin": origin,
            "destination": destination,
            "waypoints": waypoints,
            "go_route": go_route,
            "return_route": return_route,
            "vehicle_type": vehicle_type,
            "vehicle_info": VEHICLE_TYPES.get(vehicle_type, VEHICLE_TYPES["motorcycle"])
        }

    def save_route_book(self, route_data: Dict, output_dir: str = None) -> str:
        if output_dir is None:
            dest_name = route_data["destination"]["address"]
            output_dir = config.get_output_dir(dest_name)

        os.makedirs(output_dir, exist_ok=True)

        html_path = os.path.join(output_dir, "route_book.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(self.generate_html(route_data))

        json_path = os.path.join(output_dir, "route_data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(route_data, f, ensure_ascii=False, indent=2)

        return output_dir

    def generate_html(self, route_data: Dict) -> str:
        go = route_data["go_route"]
        return_route = route_data.get("return_route")
        waypoints = route_data.get("waypoints", [])
        vehicle_info = route_data.get("vehicle_info", VEHICLE_TYPES["motorcycle"])
        vehicle_type = route_data.get("vehicle_type", "motorcycle")

        origin = route_data["origin"]
        destination = route_data["destination"]

        go_segments_html = self._generate_segments_html(go["segments"])

        return_segments_html = ""
        if return_route:
            return_segments_html = self._generate_segments_html(return_route["segments"])

        waypoints_html = ""
        if waypoints:
            waypoints_list = " → ".join([wp.get("formatted_address", wp["address"]) for wp in waypoints])
            waypoints_html = f'<p><strong>途经点：</strong>{waypoints_list}</p>'

        distance_km = go["total_distance"] / 1000
        duration_minutes = int(go["total_duration"] / 60)

        if vehicle_type == "walking":
            calories = int(distance_km * 200)
        elif vehicle_type == "bicycle":
            calories = int(distance_km * 30)
        else:
            calories = int(distance_km * 50)

        vehicle_name = vehicle_info["name"]
        vehicle_icon = vehicle_info["icon"]

        template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{vehicle_name}路书 - {destination['address']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        h1 {{ text-align: center; color: #1a1a1a; margin-bottom: 30px; }}
        .route-info {{ background: #f7f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid {vehicle_info["color"]}; margin: 20px 0; }}
        .route-info p {{ margin: 8px 0; font-size: 16px; }}
        .vehicle-badge {{ display: inline-block; background: {vehicle_info["color"]}; color: white; padding: 4px 12px; border-radius: 4px; font-size: 14px; margin-left: 10px; }}
        .map-section {{ margin: 30px 0; }}
        .map-section h2 {{ color: #1a1a1a; margin: 20px 0 15px; font-size: 20px; }}
        .map-container {{ width: 100%; max-width: 800px; margin: 0 auto; border-radius: 8px; overflow: hidden; border: 1px solid #e8e8e8; }}
        .map-container img {{ width: 100%; height: auto; display: block; }}
        .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }}
        .stat-box {{ background: linear-gradient(135deg, #fff7e6, #fff4e0); padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #ffd591; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #d46b08; }}
        .stat-label {{ font-size: 14px; color: #666; }}
        .steps {{ margin: 20px 0; max-height: 400px; overflow-y: auto; }}
        .step {{ padding: 15px; margin: 10px 0; background: #fafafa; border-radius: 6px; border-left: 4px solid {vehicle_info["color"]}; }}
        .step-num {{ display: inline-block; width: 28px; height: 28px; background: {vehicle_info["color"]}; color: white; border-radius: 50%; text-align: center; line-height: 28px; font-weight: bold; margin-right: 10px; }}
        .step-road {{ color: {vehicle_info["color"]}; font-weight: 500; }}
        .open-app {{ display: inline-block; margin: 15px 0; padding: 12px 24px; background: {vehicle_info["color"]}; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }}
        .open-app:hover {{ opacity: 0.9; }}
        .return-route {{ margin-top: 40px; padding-top: 30px; border-top: 2px solid #e8e8e8; }}
        .tips {{ background: #f6ffed; padding: 15px; border-radius: 6px; border: 1px solid #b7eb8f; margin-top: 20px; }}
        .tips h4 {{ color: #52c41a; margin-bottom: 10px; }}
        .tips ul {{ margin-left: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{vehicle_icon} {vehicle_name}路书</h1>

        <div class="route-info">
            <p><strong>起点：</strong>{origin.get('formatted_address', origin['address'])}</p>
            <p><strong>终点：</strong>{destination.get('formatted_address', destination['address'])}</p>
            {waypoints_html}
            <p><strong>生成时间：</strong>{route_data['created_at'][:10]}</p>
        </div>

        <div class="map-section">
            <h2>📍 去程路线</h2>
            <div class="map-container">
                <img src="https://restapi.amap.com/v3/staticmap?key={self.api_key}&center={self._get_center_lnglat(origin, destination)}&zoom=8&size=800*450&markers={origin['location']},S&markers={destination['location']},S"
                     alt="去程路线图"
                     onerror="this.style.display='none'">
            </div>
            <a href="https://uri.amap.com/marker?position={origin['location']},{origin.get('formatted_address','')}&position={destination['location']},{destination.get('formatted_address','')}&src=motobike&callnative=1"
               class="open-app" target="_blank">📱 在高德地图中查看</a>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{distance_km:.1f} km</div>
                <div class="stat-label">总距离</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{duration_minutes} min</div>
                <div class="stat-label">预计时间</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{calories} cal</div>
                <div class="stat-label">预计消耗</div>
            </div>
        </div>

        <div class="steps">
            <h3>🛣️ 去程路线详情</h3>
            {go_segments_html}
        </div>

        {"<div class=\'return-route\'>" if return_route else ""}
        {f'''
        <div class="return-route">
            <div class="map-section">
                <h2>📍 返程路线</h2>
                <div class="map-container">
                    <img src="https://restapi.amap.com/v3/staticmap?key={{self.api_key}}&center={{self._get_center_lnglat(origin, destination)}}&zoom=8&size=800*450&markers={{destination['location']}},S&markers={{waypoints[0]['location'] if waypoints else origin['location']}},S&markers={{origin['location']}},S"
                         alt="返程路线图"
                         onerror="this.style.display='none'">
                </div>
            </div>
            <div class="steps">
                <h3>🛣️ 返程路线详情</h3>
                {return_segments_html}
            </div>
        </div>
        ''' if return_route else ""}
        {"</div>" if return_route else ""}

        <div class="tips">
            <h4>💡 {vehicle_name}骑行小贴士</h4>
            <ul>
                <li>全程约 <strong>{distance_km:.1f} 公里</strong>，建议提前检查车辆状况</li>
                <li>携带足够的饮用水和必要的维修工具</li>
                <li>注意交通安全，遵守交通规则</li>
                <li>途中注意休息，避免疲劳驾驶</li>
            </ul>
        </div>
    </div>
</body>
</html>'''
        return template

    def _generate_segments_html(self, segments: List[Dict]) -> str:
        html = ""
        step_num = 1
        for segment in segments:
            for step in segment.get("steps", []):
                road = step.get("road", "道路")
                distance = step.get("distance", 0)
                instruction = step.get("instruction", "")
                duration = int(step.get("duration", 0) / 60)
                html += f'''
            <div class="step">
                <span class="step-num">{step_num}</span>
                <span class="step-instruction">{instruction}</span>
                <p class="step-detail">📏 {distance} 米 | 🛤️ <span class="step-road">{road}</span> | ⏱️ {duration} 分钟</p>
            </div>'''
                step_num += 1
        return html

    def _get_center_lnglat(self, origin: Dict, destination: Dict) -> str:
        center_lng = (origin["lng"] + destination["lng"]) / 2
        center_lat = (origin["lat"] + destination["lat"]) / 2
        return f"{center_lng},{center_lat}"