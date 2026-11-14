"""Weather tool for DMart Conversational Analytics Agent.
Supports stub mode (deterministic formula) and live mode (Open-Meteo archive API).
"""

from datetime import datetime
import os
import re

CITIES = {
    "Mumbai": {"latitude": 19.0760, "longitude": 72.8777},
    "Pune": {"latitude": 18.5204, "longitude": 73.8567},
    "Hyderabad": {"latitude": 17.3850, "longitude": 78.4867},
    "Bengaluru": {"latitude": 12.9716, "longitude": 77.5946},
    "Ahmedabad": {"latitude": 23.0225, "longitude": 72.5714},
}


def validate_iso_date(date_str: str) -> bool:
  if not isinstance(date_str, str):
    return False
  if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
    return False
  try:
    datetime.strptime(date_str, "%Y-%m-%d")
    return True
  except ValueError:
    return False


def get_weather(city: str, date: str) -> dict:
  if city not in CITIES:
    return {"ok": False, "error": f"unsupported city: {city}"}

  if not validate_iso_date(date):
    return {"ok": False, "error": f"invalid date format or date: {date}"}

  mode = os.environ.get("WEATHER_MODE", "stub")

  if mode == "live":
    try:
      import requests

      lat = CITIES[city]["latitude"]
      lon = CITIES[city]["longitude"]
      url = "https://archive-api.open-meteo.com/v1/archive"
      params = {
          "latitude": lat,
          "longitude": lon,
          "start_date": date,
          "end_date": date,
          "timezone": "Asia/Kolkata",
          "daily": (
              "temperature_2m_mean,relative_humidity_2m_mean,wind_speed_10m_max,precipitation_sum"
          ),
      }
      response = requests.get(url, params=params, timeout=10)
      if response.status_code != 200:
        return {
            "ok": False,
            "error": f"HTTP status {response.status_code}",
        }
      data = response.json()
      daily = data.get("daily", {})
      temps = daily.get("temperature_2m_mean", [0.0])
      humids = daily.get("relative_humidity_2m_mean", [0.0])
      winds = daily.get("wind_speed_10m_max", [0.0])
      rains = daily.get("precipitation_sum", [0.0])

      return {
          "ok": True,
          "city": city,
          "date": date,
          "mode": "live",
          "temperature_c": float(temps[0]) if temps and temps[0] is not None else 0.0,
          "humidity_pct": float(humids[0]) if humids and humids[0] is not None else 0.0,
          "wind_kmh": float(winds[0]) if winds and winds[0] is not None else 0.0,
          "rain_mm": float(rains[0]) if rains and rains[0] is not None else 0.0,
      }
    except Exception as e:
      return {"ok": False, "error": str(e)}

  else:
    # Stub mode formula
    dt = datetime.strptime(date, "%Y-%m-%d")
    doy = dt.timetuple().tm_yday
    n = len(city)

    temp = float(20 + (n + doy) % 15)
    humidity = float(40 + (3 * n + doy) % 50)
    wind = float(5 + doy % 10)
    rain = 6.5 if doy % 4 == 0 else 0.0

    return {
        "ok": True,
        "city": city,
        "date": date,
        "mode": "stub",
        "temperature_c": temp,
        "humidity_pct": humidity,
        "wind_kmh": wind,
        "rain_mm": rain,
    }