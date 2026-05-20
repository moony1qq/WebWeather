import urllib.request
import urllib.parse
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from dataclasses import dataclass

load_dotenv()
API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')

@dataclass
class WeatherData:
    city: str
    country: str
    temperature: float
    feels_like: float
    humidity: int
    description: str
    wind_speed: float
    icon: str


@dataclass
class ForecastDay:
    date: str
    weekday: str
    temp_min: float
    temp_max: float
    description: str
    icon: str


@dataclass
class ForecastData:
    city: str
    country: str
    days: list


class WeatherService:
    BASE_URL = "https://api.openweathermap.org"

    def __init__(self, api_key: str = API_KEY):
        self.api_key = api_key

    def _fetch(self, url: str) -> dict:
        try:
            response = urllib.request.urlopen(url, timeout=10)
            return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            #API error
            raise ValueError(f"API error: {e.code} {e.reason}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Network error: {e.reason}")
            #No internet

    def _get_coordinates(self, city: str):
        city_encoded = urllib.parse.quote(city)
        url = (
            f"{self.BASE_URL}/geo/1.0/direct"
            f"?q={city_encoded}&limit=1&appid={self.api_key}"
        )
        locations = self._fetch(url)
        if not locations:
            raise ValueError(f"City '{city}' not found.")
        loc = locations[0]
        return loc["lat"], loc["lon"], loc["name"], loc.get("country", "")

    def get_current_weather(self, city: str) -> WeatherData:
        lat, lon, name, country = self._get_coordinates(city)
        url = (
            f"{self.BASE_URL}/data/2.5/weather"
            f"?lat={lat}&lon={lon}&units=metric&appid={self.api_key}"
        )
        data = self._fetch(url)
        return WeatherData(
            city=name,
            country=country,
            temperature=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            humidity=data["main"]["humidity"],
            description=data["weather"][0]["description"].capitalize(),
            wind_speed=data["wind"]["speed"],
            icon=data["weather"][0]["icon"],
        )

    def get_forecast(self, city: str) -> ForecastData:
        lat, lon, name, country = self._get_coordinates(city)
        url = (
            f"{self.BASE_URL}/data/2.5/forecast"
            f"?lat={lat}&lon={lon}&units=metric&appid={self.api_key}"
        )
        data = self._fetch(url)
        seen_days = {}
        for item in data["list"]:
            dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            day_key = dt.strftime("%Y-%m-%d")
            if day_key not in seen_days:
                seen_days[day_key] = ForecastDay(
                    date=dt.strftime("%d.%m"),
                    weekday=dt.strftime("%A"),
                    temp_min=item["main"]["temp_min"],
                    temp_max=item["main"]["temp_max"],
                    description=item["weather"][0]["description"].capitalize(),
                    icon=item["weather"][0]["icon"],
                )
            else:
                day = seen_days[day_key]
                day.temp_min = min(day.temp_min, item["main"]["temp_min"])
                day.temp_max = max(day.temp_max, item["main"]["temp_max"])
        return ForecastData(
            city=name,
            country=country,
            days=list(seen_days.values())[:5],
        )
