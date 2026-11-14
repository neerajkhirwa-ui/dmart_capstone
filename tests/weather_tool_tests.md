# Weather Tool Tests - DMart Capstone Project

## Test Cases & Pasted Outputs

### 1. Check Value 1: Mumbai on 2026-05-15 (Stub Mode)
- **Input:** `get_weather("Mumbai", "2026-05-15")`
- **Output:**
```json
{
  "ok": true,
  "city": "Mumbai",
  "date": "2026-05-15",
  "mode": "stub",
  "temperature_c": 26.0,
  "humidity_pct": 43.0,
  "wind_kmh": 10.0,
  "rain_mm": 0.0
}
{
  "ok": true,
  "city": "Pune",
  "date": "2026-05-16",
  "mode": "stub",
  "temperature_c": 25.0,
  "humidity_pct": 88.0,
  "wind_kmh": 11.0,
  "rain_mm": 6.5
}
{
  "ok": true,
  "city": "Hyderabad",
  "date": "2026-04-01",
  "mode": "stub",
  "temperature_c": 30.0,
  "humidity_pct": 58.0,
  "wind_kmh": 6.0,
  "rain_mm": 0.0
}
{
  "ok": false,
  "error": "unsupported city: Kolkata"
}
{
  "ok": false,
  "error": "invalid date format or date: 15 May 2026"
}
{
  "ok": true,
  "city": "Bengaluru",
  "date": "2026-06-10",
  "mode": "stub",
  "temperature_c": 24.0,
  "humidity_pct": 81.0,
  "wind_kmh": 7.0,
  "rain_mm": 0.0
}
