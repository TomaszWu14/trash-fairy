"""Pobiera punkty z OSM (Overpass API) dla obszaru demo i zapisuje cache do data/*.geojson.

Uruchom raz: `python scripts/fetch_osm.py`. Pliki są commitowane, żeby demo nie zależało od Overpass.
Gdy Overpass nie odpowiada, skrypt kończy się błędem i nie nadpisuje istniejącego cache.
Dane: © OpenStreetMap contributors, ODbL 1.0.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Stare Miasto + Kazimierz + Grzegórzki (S, W, N, E)
BBOX = "50.045,19.925,50.070,19.975"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

QUERY = f"""
[out:json][timeout:60];
(
  node["amenity"="waste_basket"]({BBOX});
  nwr["amenity"="waste_disposal"]({BBOX});
  nwr["amenity"="recycling"]["recycling_type"="container"]({BBOX});
  node["amenity"~"^(restaurant|cafe|fast_food|bar|pub|ice_cream)$"]({BBOX});
  node["shop"]({BBOX});
  node["highway"="bus_stop"]({BBOX});
  node["railway"="tram_stop"]({BBOX});
);
out center tags;
"""


def classify(tags):
    a = tags.get("amenity")
    if a == "waste_basket":
        return "bins"
    if a in ("waste_disposal", "recycling"):
        return "shelters"
    if tags.get("highway") == "bus_stop" or tags.get("railway") == "tram_stop":
        return "stops"
    return "pois"


def to_feature(el):
    lat = el.get("lat") or el.get("center", {}).get("lat")
    lon = el.get("lon") or el.get("center", {}).get("lon")
    if lat is None:
        return None
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {"osm_id": f"{el['type']}/{el['id']}", "tags": el.get("tags", {})},
    }


def main():
    req = urllib.request.Request(
        "https://overpass-api.de/api/interpreter",
        data=urllib.parse.urlencode({"data": QUERY}).encode(),
        headers={"User-Agent": "trash-fairy-hackyeah/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = json.load(r)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        sys.exit(f"Overpass nie odpowiada ({e}). Cache w {DATA_DIR} pozostaje bez zmian.")

    groups = {"bins": [], "shelters": [], "pois": [], "stops": []}
    for el in raw["elements"]:
        f = to_feature(el)
        if f:
            groups[classify(el.get("tags", {}))].append(f)

    DATA_DIR.mkdir(exist_ok=True)
    for name, features in groups.items():
        fc = {"type": "FeatureCollection", "features": features}
        (DATA_DIR / f"{name}.geojson").write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    print("Zapisano:", {k: len(v) for k, v in groups.items()})


if __name__ == "__main__":
    main()
