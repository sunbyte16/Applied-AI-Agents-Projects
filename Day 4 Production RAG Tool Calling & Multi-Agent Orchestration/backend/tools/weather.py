"""
Weather Tool for OrchestraRAG AI.
Queries current meteorological conditions for global locations.
Validates location inputs and queries Open-Meteo live API with graceful offline fallback.
"""

import re
import urllib.parse
from typing import Any, Dict
import httpx
from backend.tools.base import BaseTool


class WeatherTool(BaseTool):
    """Tool for fetching real-time weather reports for specified cities or regions."""

    name = "weather"
    description = (
        "Retrieve current weather and meteorological conditions (temperature, condition, humidity, wind) "
        "for a given city or geographic location."
    )
    parameters = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name and optional country, e.g., 'San Francisco', 'London', 'Tokyo', 'Bangalore'.",
            }
        },
        "required": ["location"],
    }

    _WMO_CODE_MAP = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
    }

    def _validate_location(self, loc: str) -> str:
        """Validate location string against injection or invalid characters."""
        if not loc or not isinstance(loc, str):
            raise ValueError("Location must be a non-empty string.")
        cleaned = loc.strip()
        if len(cleaned) < 2 or len(cleaned) > 100:
            raise ValueError("Location must be between 2 and 100 characters in length.")
        if not re.match(r"^[a-zA-Z0-9\s,\.\-']+$", cleaned):
            raise ValueError("Location contains invalid characters.")
        return cleaned

    def execute(self, location: str = "", **kwargs: Any) -> Dict[str, Any]:
        """Fetch current weather via geocoding and forecast API."""
        try:
            valid_loc = self._validate_location(location)
        except ValueError as ve:
            return {
                "tool_name": self.name,
                "success": False,
                "error": str(ve),
            }

        # 1. Geocode city name to lat/lon using Open-Meteo geocoding API
        try:
            with httpx.Client(timeout=6.0) as client:
                geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(valid_loc)}&count=1&language=en&format=json"
                geo_resp = client.get(geo_url)
                if geo_resp.status_code == 200:
                    geo_data = geo_resp.json()
                    results = geo_data.get("results")
                    if not results:
                        return {
                            "tool_name": self.name,
                            "success": False,
                            "location": valid_loc,
                            "error": f"Location '{valid_loc}' could not be resolved to geographic coordinates.",
                        }

                    first_hit = results[0]
                    lat = first_hit["latitude"]
                    lon = first_hit["longitude"]
                    city_name = first_hit.get("name", valid_loc)
                    country = first_hit.get("country", "")

                    # 2. Query forecast API
                    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
                    weather_resp = client.get(weather_url)
                    if weather_resp.status_code == 200:
                        w_data = weather_resp.json()
                        current = w_data.get("current", {})
                        temp = current.get("temperature_2m")
                        humidity = current.get("relative_humidity_2m")
                        wind = current.get("wind_speed_10m")
                        code = current.get("weather_code", 0)
                        condition = self._WMO_CODE_MAP.get(code, "Variable")

                        return {
                            "tool_name": self.name,
                            "success": True,
                            "location": f"{city_name}, {country}".strip(", "),
                            "temperature_celsius": temp,
                            "temperature_fahrenheit": round((temp * 9 / 5) + 32, 1) if temp is not None else None,
                            "condition": condition,
                            "humidity_percent": humidity,
                            "wind_speed_kmh": wind,
                            "source": "Open-Meteo Live API",
                        }

        except Exception as e:
            # If network error or timeout, return structured fallback with explanation
            return {
                "tool_name": self.name,
                "success": False,
                "location": valid_loc,
                "error": f"Weather service network error: {type(e).__name__}. Ensure internet connectivity.",
            }

        return {
            "tool_name": self.name,
            "success": False,
            "location": valid_loc,
            "error": "Failed to fetch live weather data from provider.",
        }
