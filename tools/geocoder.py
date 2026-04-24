import requests
from typing import Tuple, Optional, Dict, Any

class Geocoder:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/geocode/geo"
        self.poi_url = "https://restapi.amap.com/v3/place/text"

    def geocode(self, address: str, city: str = None) -> Optional[Tuple[str, str]]:
        params = {
            "key": self.api_key,
            "address": address
        }
        if city:
            params["city"] = city

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            result = response.json()

            if result.get("status") == "1" and result.get("count", "0") != "0":
                geocode_info = result["geocodes"][0]
                location = geocode_info["location"]
                formatted_address = geocode_info.get("formatted_address", address)
                return location, formatted_address
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None

    def poi_search(self, keywords: str, city: str = None) -> Optional[Dict[str, Any]]:
        params = {
            "key": self.api_key,
            "keywords": keywords
        }
        if city:
            params["city"] = city

        try:
            response = requests.get(self.poi_url, params=params, timeout=10)
            result = response.json()

            if result.get("status") == "1" and int(result.get("count", "0")) > 0:
                pois = result.get("pois", [])
                if pois:
                    poi = pois[0]
                    location = poi.get("location")
                    name = poi.get("name", keywords)
                    addr = poi.get("address", name)
                    if location:
                        return location, f"{addr}({name})"
            return None
        except Exception as e:
            print(f"POI search error: {e}")
            return None

    def geocode_or_poi(self, address: str, city: str = None) -> Optional[Tuple[str, str]]:
        result = self.geocode(address, city)
        if result:
            return result
        print(f"Geocoding failed for '{address}', trying POI search...")
        return self.poi_search(address, city)

    def geocode_to_coords(self, address: str, city: str = None) -> Optional[Tuple[float, float]]:
        result = self.geocode_or_poi(address, city)
        if result:
            location = result[0]
            lng, lat = location.split(",")
            return float(lng), float(lat)
        return None