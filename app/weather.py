"""Pogoda z Open-Meteo (bez klucza) jako mnożnik tempa zapełniania w prognozie. Reguła w kodzie, bez AI.

Reguła (koncepcja: pogoda zmienia ruch pieszy, a więc tempo zapełniania koszy):
  opad ≥ 1 mm/h                                  → ×0,8  (mniej ludzi na ulicy)
  weekend 10–22, ≥ 20 °C i sucho (opad < 0,1 mm)  → ×1,25 (Planty i bulwary pełne)
  inaczej                                         → ×1,0
Godziny bez danych mają ×1,0. Odpowiedź trzymamy w pamięci i w data/weather_cache.json: odświeżamy co 1 h,
po błędzie najwcześniej za 10 min, a do tego czasu pracujemy na ostatnim wyniku. WEATHER_URL="" wyłącza integrację.
"""
import json
import time
from datetime import datetime
from pathlib import Path

from . import http

DEFAULT_URL = "https://api.open-meteo.com/v1/forecast"
LAT, LON = 50.0614, 19.9366  # Rynek Główny
TTL_S, RETRY_S = 3600, 600
RAIN_MM, DRY_MM, WARM_C = 1.0, 0.1, 20.0
RAIN_FACTOR, NICE_FACTOR = 0.8, 1.25
NICE_HOURS = range(10, 22)
CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "weather_cache.json"
_state = {"data": None, "next_try": 0.0}


def _load_cache():
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _fetch(url):
    status, body = http.get_json(url, {"latitude": LAT, "longitude": LON, "timezone": "Europe/Warsaw",
                                       "hourly": "temperature_2m,precipitation,weather_code",
                                       "past_days": 2, "forecast_days": 2})
    h = (body or {}).get("hourly") if status == 200 else None
    if not h or not h.get("time"):
        raise ValueError(f"Open-Meteo: {status}")
    rows = {t: {"temp": temp, "rain": rain, "code": code}
            for t, temp, rain, code in zip(h["time"], h["temperature_2m"], h["precipitation"], h["weather_code"])}
    return {"fetched_at": time.time(), "hours": rows}


def data():
    """{"fetched_at", "hours": {"2026-10-03T13:00": {"temp", "rain", "code"}}} albo None (brak integracji i cache)."""
    url = http.config("WEATHER_URL", DEFAULT_URL)
    if not url:
        return None
    if _state["data"] is None:
        _state["data"] = _load_cache()
    d, now = _state["data"], time.time()
    if (d is None or now - d["fetched_at"] > TTL_S) and now >= _state["next_try"]:
        try:
            d = _state["data"] = _fetch(url)
        except Exception:  # sieć, limit, zła odpowiedź: zostaje ostatni wynik
            _state["next_try"] = now + RETRY_S
        else:
            try:
                CACHE_FILE.write_text(json.dumps(d), encoding="utf-8")
            except OSError:
                pass  # pamięć wystarczy
    return d


def factor(row, at):
    if row is None or row["rain"] is None:
        return 1.0
    if row["rain"] >= RAIN_MM:
        return RAIN_FACTOR
    if at.weekday() >= 5 and at.hour in NICE_HOURS and (row["temp"] or 0) >= WARM_C and row["rain"] < DRY_MM:
        return NICE_FACTOR
    return 1.0


def _row(d, at):
    return d["hours"].get(f"{at:%Y-%m-%dT%H}:00") if d else None


def factor_at():
    """Funkcja at → mnożnik dla prognozy (jedno pobranie danych na całe wyliczenie)."""
    d = data()
    return lambda at: factor(_row(d, at), at)


WMO = {0: "bezchmurnie", 1: "przeważnie słonecznie", 2: "częściowe zachmurzenie", 3: "pochmurno", 45: "mgła", 48: "mgła",
       51: "mżawka", 53: "mżawka", 55: "mżawka", 61: "deszcz", 63: "deszcz", 65: "ulewa", 71: "śnieg", 73: "śnieg",
       75: "śnieżyca", 80: "przelotny deszcz", 81: "przelotny deszcz", 82: "ulewa", 95: "burza", 96: "burza", 99: "burza"}


def conditions(now):
    """Pogoda dla godziny zegara demo: tekst do panelu i otwartego API."""
    d = data()
    row = _row(d, now)
    if row is None:
        return {"available": False}
    f = factor(row, now)
    return {"available": True, "temp_c": row["temp"], "rain_mm": row["rain"], "code": row["code"],
            "label": WMO.get(row["code"], "pogoda"), "factor": f,
            "effect": "deszcz: mniej ludzi, wolniejsze zapełnianie" if f < 1 else
                      "ciepły, suchy weekend: szybsze zapełnianie" if f > 1 else "bez wpływu na prognozę",
            "fetched_at": datetime.fromtimestamp(d["fetched_at"]).isoformat(timespec="minutes"), "source": "Open-Meteo"}
