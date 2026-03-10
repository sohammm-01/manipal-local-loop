"""Weather scraper using OpenWeatherMap API for Manipal coordinates."""

import logging
from datetime import datetime, timezone
from typing import List

from manipal_loop.config import config
from manipal_loop.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_LAT = 13.3525
_LON = 74.7868
_OWM_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
    "?lat={lat}&lon={lon}&appid={key}&units=metric"
)

# Thresholds for alert-worthy conditions
_HEAVY_RAIN_MM = 10.0
_EXTREME_HEAT_C = 35.0


class WeatherScraper(BaseScraper):
    """Fetches current weather for Manipal and flags alert-worthy conditions."""

    def fetch(self) -> List[dict]:
        """Query OpenWeatherMap and return a weather update if conditions warrant it.

        Returns:
            List with a single item if data is available, empty list otherwise.
        """
        if not config.OPENWEATHER_API_KEY:
            logger.warning("OPENWEATHER_API_KEY not set; skipping weather scrape")
            return []

        url = _OWM_URL.format(
            lat=_LAT, lon=_LON, key=config.OPENWEATHER_API_KEY
        )
        logger.info("Fetching weather data from OpenWeatherMap")
        response = self._make_request(url)
        if response is None:
            return []

        try:
            data = response.json()
        except Exception as exc:
            logger.error("Failed to parse OWM JSON: %s", exc)
            return []

        return self._parse_weather(data)

    # ------------------------------------------------------------------

    def _parse_weather(self, data: dict) -> List[dict]:
        """Extract weather metrics and build an item if alert-worthy.

        Args:
            data: Raw OWM JSON response.

        Returns:
            List with one weather item, or empty list.
        """
        try:
            weather_desc = data["weather"][0].get("description", "")
            weather_main = data["weather"][0].get("main", "")
            temp = data["main"].get("temp", 0)
            humidity = data["main"].get("humidity", 0)
            rain_1h = data.get("rain", {}).get("1h", 0)
            city_name = data.get("name", "Manipal")
            ts = datetime.fromtimestamp(
                data.get("dt", 0), tz=timezone.utc
            ).isoformat()
        except (KeyError, TypeError) as exc:
            logger.error("Unexpected OWM data structure: %s", exc)
            return []

        alert_worthy = (
            rain_1h > _HEAVY_RAIN_MM
            or "thunderstorm" in weather_main.lower()
            or temp > _EXTREME_HEAT_C
        )

        if not alert_worthy:
            logger.info("Weather normal in %s — no alert needed", city_name)
            return []

        title = f"Weather Update: {city_name} — {weather_desc.capitalize()}"
        body = (
            f"Temperature: {temp:.1f}°C | Humidity: {humidity}% | "
            f"Condition: {weather_desc}. "
        )
        if rain_1h > 0:
            body += f"Rainfall (last 1h): {rain_1h} mm. "
        if alert_worthy:
            body += "⚠️ Alert-worthy conditions detected."

        item = self._build_item(
            title=title,
            body_text=body,
            url="https://openweathermap.org",
            source="OpenWeatherMap",
            category="Weather",
            timestamp=ts,
        )
        return [item]
