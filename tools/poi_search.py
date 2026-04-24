import requests
from typing import List, Dict, Optional

class POISearch:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/place/text"

    def search(self, keywords: str, city: str = None, types: str = None) -> List[Dict]:
        params = {
            "key": self.api_key,
            "keywords": keywords
        }
        if city:
            params["city"] = city
        if types:
            params["types"] = types

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            result = response.json()

            if result.get("status") == "1" and int(result.get("count", "0")) > 0:
                return result.get("pois", [])
            return []
        except Exception as e:
            print(f"POI search error: {e}")
            return []

    def search_nearby(self, keywords: str, location: str, radius: int = 5000) -> List[Dict]:
        url = "https://restapi.amap.com/v3/place/around"
        params = {
            "key": self.api_key,
            "keywords": keywords,
            "location": location,
            "radius": radius
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()

            if result.get("status") == "1" and int(result.get("count", "0")) > 0:
                return result.get("pois", [])
            return []
        except Exception as e:
            print(f"POI nearby search error: {e}")
            return []