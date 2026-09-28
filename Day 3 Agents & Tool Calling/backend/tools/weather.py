"""
Weather Tool for AgentLab AI.
Fetches real-time live meteorological data from Open-Meteo (free, no key required)
or OpenWeatherMap if WEATHER_API_KEY is configured.
"""

import os
from typing import Any, Dict
import requests
from backend.tools.base import BaseTool

# WMO Weather interpretation codes (WW)
WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
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
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherTool(BaseTool):
    """Tool for fetching real-world live weather data for any city or region."""

    name = "weather"
    description = (
        "Get current real-time weather information (temperature, weather condition, "
        "humidity, wind speed) for a specified city or location. "
        "Use this tool whenever the user asks about current weather, temperature, or climate conditions."
    )
    parameters = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city or locality name, e.g., 'London', 'Hyderabad', 'Tokyo', 'San Francisco'.",
            }
        },
        "required": ["location"],
    }

    def execute(self, location: str = "", **kwargs: Any) -> Dict[str, Any]:
        """Fetch live weather data for the specified location."""
        if not location or not isinstance(location, str) or not location.strip():
            return {
                "tool": self.name,
                "success": False,
                "error": "Location parameter is required and cannot be empty.",
            }

        city = location.strip()

        # 1. Check if OpenWeatherMap API key is provided
        owm_key = os.getenv("WEATHER_API_KEY")
        if owm_key and owm_key.strip() and "your_" not in owm_key:
            try:
                resp = requests.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={"q": city, "appid": owm_key, "units": "metric"},
                    timeout=8.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "tool": self.name,
                        "success": True,
                        "location": data.get("name", city),
                        "country": data.get("sys", {}).get("country", ""),
                        "temperature": round(data["main"]["temp"], 1),
                        "condition": data["weather"][0]["main"],
                        "humidity": data["main"]["humidity"],
                        "wind_speed": round(data["wind"]["speed"] * 3.6, 1),
                        "unit": "Celsius",
                    }
            except Exception:
                pass

        # 2. Use Open-Meteo live global meteorological API (reliable, free, live)
        try:
            # Step A: Geocode city name to latitude/longitude
            geo_resp = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "en", "format": "json"},
                timeout=8.0,
            )
            if geo_resp.status_code != 200:
                return {
                    "tool": self.name,
                    "success": False,
                    "location": city,
                    "error": f"Geocoding service returned status code {geo_resp.status_code}.",
                }

            geo_data = geo_resp.json()
            results = geo_data.get("results")
            if not results:
                return {
                    "tool": self.name,
                    "success": False,
                    "location": city,
                    "error": f"Location '{city}' could not be found. Please check the spelling.",
                }

            top_match = results[0]
            lat = top_match["latitude"]
            lon = top_match["longitude"]
            resolved_city = top_match.get("name", city)
            country = top_match.get("country", "")

            # Step B: Fetch current weather for latitude/longitude
            weather_resp = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                },
                timeout=8.0,
            )
            if weather_resp.status_code != 200:
                return {
                    "tool": self.name,
                    "success": False,
                    "location": city,
                    "error": f"Weather API returned status code {weather_resp.status_code}.",
                }

            w_data = weather_resp.json().get("current", {})
            weather_code = w_data.get("weather_code", 0)
            condition = WMO_WEATHER_CODES.get(weather_code, "Clear")

            return {
                "tool": self.name,
                "success": True,
                "location": f"{resolved_city}, {country}" if country else resolved_city,
                "temperature": round(w_data.get("temperature_2m", 0.0), 1),
                "condition": condition,
                "humidity": w_data.get("relative_humidity_2m", 0),
                "wind_speed": round(w_data.get("wind_speed_10m", 0.0), 1),
                "unit": "Celsius",
            }
        except requests.exceptions.Timeout:
            return {
                "tool": self.name,
                "success": False,
                "location": city,
                "error": "Weather request timed out. Please try again.",
            }
        except Exception as e:
            return {
                "tool": self.name,
                "success": False,
                "location": city,
                "error": f"Weather service error: {str(e)}",
            }
