
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

WEATHER_API = "https://api.open-meteo.com/v1/forecast"
GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"


def get_weather_data(location="Bengaluru, Karnataka"):
    """Fetch weather estimates for the requested city."""

    parts = [part.strip() for part in location.split(",") if part.strip()]
    if not parts:
        raise ValueError("Enter a valid city name.")

    response = requests.get(
        GEOCODING_API,
        params={
            "name": parts[0],
            "count": 10,
            "language": "en",
            "format": "json",
        },
        timeout=20,
    )
    response.raise_for_status()

    results = response.json().get("results", [])
    if not results:
        raise ValueError(f"Could not find the location: {location}")

    # Prefer a result matching the entered state/region, if supplied.
    match = results[0]
    if len(parts) > 1:
        for result in results:
            region = result.get("admin1", "")
            country = result.get("country", "")
            if any(
                part.casefold() in str(value).casefold()
                for part in parts[1:]
                for value in (region, country)
            ):
                match = result
                break

    city = match["name"]
    region = match.get("admin1", "")
    country = match.get("country", "")
    resolved_location = ", ".join(
        part for part in (city, region, country) if part
    )

    timezone = match.get("timezone") or "Asia/Kolkata"

    response = requests.get(
        WEATHER_API,
        params={
            "latitude": match["latitude"],
            "longitude": match["longitude"],
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation,"
                "wind_speed_10m,"
                "weather_code"
            ),
            "hourly": "precipitation,temperature_2m",
            "past_days": 1,
            "forecast_days": 2,
            "timezone": timezone,
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()

    current = payload.get("current")
    hourly = payload.get("hourly")
    if not current or not hourly:
        raise ValueError("The weather API returned incomplete data.")

    model_time = datetime.fromisoformat(current["time"])
    start_time = model_time - timedelta(hours=24)

    rainfall_values = [
        float(rainfall)
        for timestamp, rainfall in zip(
            hourly.get("time", []),
            hourly.get("precipitation", []),
        )
        if rainfall is not None
        and start_time < datetime.fromisoformat(timestamp) <= model_time
    ]

    return {
        "location": resolved_location,
        "latitude": match["latitude"],
        "longitude": match["longitude"],
        "source": "Open-Meteo Forecast API",
        "source_url": WEATHER_API,
        "data_type": "Weather-model estimates",
        "model_time": current["time"],
        "retrieved_at": datetime.now(
            ZoneInfo(timezone)
        ).isoformat(timespec="seconds"),
        "temperature_c": current.get("temperature_2m"),
        "relative_humidity_percent": current.get(
            "relative_humidity_2m"
        ),
        "current_precipitation_mm": current.get("precipitation"),
        "estimated_precipitation_last_24h_mm": (
            round(sum(rainfall_values), 2) if rainfall_values else None
        ),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "weather_code": current.get("weather_code"),
        "hourly_data": {
            "time": hourly.get("time", []),
            "precipitation_mm": hourly.get("precipitation", []),
            "temperature_c": hourly.get("temperature_2m", []),
        },
        "limitations": (
            "Weather-model estimates are not verified local rain-gauge "
            "measurements. Rainfall alone does not confirm flooding."
        ),
    }


if __name__ == "__main__":
    try:
        city = input("Enter a city (e.g. Chennai, Tamil Nadu): ").strip()
        weather = get_weather_data(city)

        print(f"\nLocation: {weather['location']}")
        print(f"Source: {weather['source']}")
        print(f"Model time: {weather['model_time']}")
        print(f"Temperature: {weather['temperature_c']} °C")
        print(f"Humidity: {weather['relative_humidity_percent']}%")
        print(
            "Current precipitation: "
            f"{weather['current_precipitation_mm']} mm"
        )
        print(
            "Estimated rainfall (24h): "
            f"{weather['estimated_precipitation_last_24h_mm']} mm"
        )
        print(weather["limitations"])

    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        print(f"Could not fetch weather: {error}")
