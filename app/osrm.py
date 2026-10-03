"""Przebieg tras po ulicach z OSRM, tylko do rysowania na mapie. Kilometry nadal liczy routes.road_m (linia prosta × 1,3).

Wynik trzymamy w pamięci i w data/osrm_cache.json, żeby demo działało bez sieci. Brak odpowiedzi = linia prosta
z flagą approx (panel pisze „przybliżenie w linii prostej”), nigdy błąd.
"""
import json
import os
import urllib.request
from pathlib import Path

from flask import current_app

DEFAULT_URL = "https://router.project-osrm.org"
TIMEOUT_S = 4
CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "osrm_cache.json"
_cache = None


def _load():
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _cache = {}
    return _cache


def _fetch(base, coords):
    lonlat = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coords)
    req = urllib.request.Request(f"{base}/route/v1/driving/{lonlat}?overview=full&geometries=geojson",
                                 headers={"User-Agent": "TrashFairy/1.0 (HackYeah 2026)"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
        data = json.load(r)
    return [[lat, lon] for lon, lat in data["routes"][0]["geometry"]["coordinates"]]


def street_path(coords):
    """coords: lista [lat, lon]. Zwraca (punkty linii [lat, lon], approx)."""
    coords = [tuple(c) for c in coords]
    if len(coords) < 2:
        return [list(c) for c in coords], False
    key = ";".join(f"{lat:.5f},{lon:.5f}" for lat, lon in coords)
    cache = _load()
    if key in cache:
        return cache[key], False
    base = current_app.config.get("OSRM_URL", os.environ.get("OSRM_URL", DEFAULT_URL))
    if not base:
        return [list(c) for c in coords], True
    try:
        path = _fetch(base, coords)
    except Exception:  # sieć, limit, zła odpowiedź — rysujemy linię prostą
        return [list(c) for c in coords], True
    cache[key] = path
    try:
        CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")
    except OSError:
        pass  # cache w pamięci wystarczy
    return path, False
