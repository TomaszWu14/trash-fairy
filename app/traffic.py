"""Ruch drogowy z TomTom Traffic Flow (TOMTOM_API_KEY) jako mnożnik czasu przejazdu. Reguła w kodzie, bez AI.

Korek w punkcie = prędkość swobodna / prędkość teraz, przycięty do 1,0–3,0 (zamknięta droga = 3,0); korek miasta
to średnia z 8 punktów na głównych drogach między centrum a bazą MPO. Pomiar starszy niż 2 h ignorujemy.
Ruch zmienia **tylko czas**: przejazdu trasy (km / 20 km/h × korek) i ETA (dojazd ok. 6 km z bazy). Nigdy wyboru
punktów ani km: trasa to decyzja o potrzebie, a nie o korkach (ruch w macierzy OR-Tools: ROADMAPA.md).
Odświeżamy co 10 min z timeoutem 2 s; pierwszy błąd kończy serię (limit klucza, brak sieci), zostają stare pomiary.
"""
import json
import time
from pathlib import Path

from . import http

URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
REFRESH_S, MAX_AGE_S, TIMEOUT_S = 600, 7200, 2
MIN_RATIO, MAX_RATIO = 1.0, 3.0
CITY_KMH, APPROACH_KM = 20, 6
CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "traffic_cache.json"  # w .gitignore
SAMPLES = [  # główne drogi (FRC 0–2 w TomTom); sprawdzone na żywo, patrz DECYZJE.md
    ("Al. Mickiewicza", 50.0645, 19.9238),
    ("Al. Krasińskiego", 50.0560, 19.9245),
    ("ul. Westerplatte", 50.0605, 19.9450),
    ("ul. Dietla", 50.0505, 19.9440),
    ("Rondo Mogilskie", 50.0655, 19.9600),
    ("ul. Grzegórzecka", 50.0570, 19.9560),
    ("al. Pokoju", 50.0590, 19.9800),
    ("ul. Nowohucka", 50.0660, 20.0000),
]
_state = {"data": None, "next_try": 0.0}


def _load_cache():
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def ratio(segment):
    """Korek z odpowiedzi flowSegmentData: swobodna / teraz, 1,0–3,0; zamknięta droga = 3,0."""
    if segment.get("roadClosure"):
        return MAX_RATIO
    current, free = segment.get("currentSpeed") or 0, segment.get("freeFlowSpeed") or 0
    if current <= 0 or free <= 0:
        return MAX_RATIO if free > 0 else MIN_RATIO
    return round(min(MAX_RATIO, max(MIN_RATIO, free / current)), 2)


def _refresh(key, old):
    samples = {s["name"]: s for s in (old or {}).get("samples", [])}
    for name, lat, lon in SAMPLES:
        try:
            status, body = http.get_json(URL, {"key": key, "point": f"{lat},{lon}", "unit": "KMPH"}, timeout=TIMEOUT_S)
        except Exception:
            break  # brak sieci: nie męczymy pozostałych 7 punktów
        seg = (body or {}).get("flowSegmentData") if status == 200 else None
        if not seg:
            break  # 403/429 itd.
        samples[name] = {"name": name, "lat": lat, "lon": lon, "ratio": ratio(seg), "frc": seg.get("frc"),
                         "current_kmh": seg.get("currentSpeed"), "free_kmh": seg.get("freeFlowSpeed"),
                         "closed": bool(seg.get("roadClosure")), "measured_at": time.time()}
    return {"samples": list(samples.values())}


def data():
    """{"samples": [...]} albo None, gdy brak klucza i cache."""
    key = http.config("TOMTOM_API_KEY")
    if not key:
        return None
    if _state["data"] is None:
        _state["data"] = _load_cache()
    now = time.time()
    if now >= _state["next_try"]:
        _state["next_try"] = now + REFRESH_S
        _state["data"] = _refresh(key, _state["data"])
        try:
            CACHE_FILE.write_text(json.dumps(_state["data"]), encoding="utf-8")
        except OSError:
            pass
    return _state["data"]


def fresh_samples():
    d, now = data(), time.time()
    return [s for s in (d or {}).get("samples", []) if now - s["measured_at"] <= MAX_AGE_S]


def city_ratio():
    """Średni korek ze świeżych pomiarów albo None (brak danych = bez korekty, a nie „brak korków”)."""
    fresh = fresh_samples()
    return round(sum(s["ratio"] for s in fresh) / len(fresh), 2) if fresh else None


def drive_min(km, k=None):
    """Czas przejazdu trasy w minutach: km / 20 km/h × korek."""
    return round(km / CITY_KMH * 60 * (k or 1.0))


def delay_min(k=None):
    """O ile korek opóźnia dojazd z bazy (ok. 6 km) — dodajemy do ETA kursu."""
    return round(APPROACH_KM / CITY_KMH * 60 * ((k or 1.0) - 1))


def conditions():
    fresh = fresh_samples()
    k = city_ratio()
    if k is None:
        return {"available": False}
    return {"available": True, "ratio": k, "delay_min": delay_min(k), "source": "TomTom Traffic Flow",
            "label": "płynnie" if k < 1.2 else "umiarkowany ruch" if k < 1.6 else "korki",
            "samples": [{"name": s["name"], "lat": s["lat"], "lon": s["lon"], "ratio": s["ratio"], "closed": s["closed"]}
                        for s in fresh]}
