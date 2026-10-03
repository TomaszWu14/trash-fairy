"""Pobiera punkty z OSM (Overpass API) dla obszaru demo i zapisuje cache do data/*.geojson.

Uruchom raz: `python scripts/fetch_osm.py` (obszar demo) albo `python scripts/fetch_osm.py --city` (panel miasta → data/city_bins.geojson). Pliki są commitowane, żeby demo nie zależało od Overpass.
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
sys.path.insert(0, str(DATA_DIR.parent))
from app.osm_import import fractions, near_label, street_label  # noqa: E402  frakcje z tagów recycling:* — jedna definicja w aplikacji

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


def overpass(query, timeout=180):
    req = urllib.request.Request(
        "https://overpass-api.de/api/interpreter",
        data=urllib.parse.urlencode({"data": query}).encode(),
        headers={"User-Agent": "trash-fairy-hackyeah/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        sys.exit(f"Overpass nie odpowiada ({e}). Cache w {DATA_DIR} pozostaje bez zmian.")


# Dzielnice Krakowa (relacje OSM boundary=administrative, admin_level=9) dla danych panelu miasta
CITY_DISTRICTS = {"Krowodrza": 2649407, "Podgórze": 2398485, "Nowa Huta": 2648045, "Dębniki": 2398482,
                  "Stare Miasto": 2642241, "Grzegórzki": 2648849}
CITY_KEEP = {"bins": 45, "containers": 25}  # kandydaci na dzielnicę; ostateczny wybór robi app/osm_import.py: import_city_points
CITY_GAP_M = 80


def spaced(cands, keep, taken):
    """Kolejność z hasha osm_id (rozrzut po całej dzielnicy, deterministycznie), odstęp ≥ CITY_GAP_M."""
    import hashlib
    from math import cos, radians
    out = []
    for c in sorted(cands, key=lambda c: hashlib.sha1(c["osm_id"].encode()).hexdigest()):
        if len(out) == keep:
            break
        far = all(((c["lat"] - o["lat"]) * 111_320) ** 2 + ((c["lon"] - o["lon"]) * 111_320 * cos(radians(c["lat"]))) ** 2
                  >= CITY_GAP_M ** 2 for o in taken)
        if far:
            taken.append(c)
            out.append(c)
    return out


def nearest_streets(points):
    """{osm_id: nazwa najbliższej nazwanej ulicy w 80 m}. Jedno zapytanie: foreach po węzłach, każdy węzeł
    wypisany przed swoimi ulicami (Overpass zachowuje kolejność wyjścia)."""
    ids = ",".join(p["osm_id"].split("/")[1] for p in points)
    raw = overpass(f"[out:json][timeout:300];node(id:{ids})->.s;"
                   "foreach.s->.n(.n out ids;way(around.n:80)[highway][name];out tags geom;);", timeout=330)
    by_id = {p["osm_id"]: p for p in points}
    out, cur = {}, None
    for el in raw["elements"]:
        if el["type"] == "node":
            cur = by_id.get(f"node/{el['id']}")
            continue
        if cur is None or not el.get("geometry"):
            continue
        d = min((g["lat"] - cur["lat"]) ** 2 + ((g["lon"] - cur["lon"]) * 0.64) ** 2 for g in el["geometry"])
        if cur["osm_id"] not in out or d < out[cur["osm_id"]][0]:
            out[cur["osm_id"]] = (d, el["tags"]["name"])
    return {k: v[1] for k, v in out.items()}


def fetch_city():
    """Kosze i pojemniki do selektywnej zbiórki w 6 dzielnicach → data/city_bins.geojson (dane panelu miasta).

    Dzielnicę przypisuje Overpass (point-in-polygon: węzły wewnątrz obszaru relacji dzielnicy).
    Adres: addr:street/addr:housenumber z tagów, inaczej najbliższa nazwana ulica w 80 m („okolice ul. X”).
    """
    areas = "".join(f"area({3600000000 + rid});" for rid in CITY_DISTRICTS.values())
    raw = overpass(f"[out:json][timeout:180];({areas})->.all;foreach.all->.a(.a out ids;"
                   "(node(area.a)[amenity=waste_basket];node(area.a)[amenity=recycling][recycling_type=container];);out;);")
    names = {3600000000 + rid: name for name, rid in CITY_DISTRICTS.items()}
    by_district, cur = {n: {"bins": [], "containers": []} for n in CITY_DISTRICTS}, None
    for el in raw["elements"]:
        if el["type"] == "area":
            cur = names[el["id"]]
            continue
        tags = el.get("tags", {})
        c = {"osm_id": f"node/{el['id']}", "lat": el["lat"], "lon": el["lon"], "tags": tags, "district": cur}
        if tags.get("amenity") == "waste_basket":
            by_district[cur]["bins"].append(c)
        elif fractions(tags):
            by_district[cur]["containers"].append(c)

    chosen, taken = [], []
    for groups in by_district.values():
        bio = [c for c in groups["containers"] if "bio" in fractions(c["tags"])]  # rzadkie w OSM: bierzemy wszystkie
        chosen += spaced(bio, len(bio), taken)
        chosen += spaced([c for c in groups["containers"] if c not in bio], CITY_KEEP["containers"], taken)
        chosen += spaced(groups["bins"], CITY_KEEP["bins"], taken)

    streets = nearest_streets(chosen)
    features = []
    for c in chosen:
        t = c["tags"]
        if t.get("addr:street"):
            address = f"{street_label(t['addr:street'])} {t.get('addr:housenumber', '')}".strip()
        elif c["osm_id"] in streets:
            address = near_label(streets[c["osm_id"]])
        else:
            address = None
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [c["lon"], c["lat"]]},
                         "properties": {"osm_id": c["osm_id"], "tags": t, "district": c["district"], "address": address}})
    fc = {"type": "FeatureCollection", "features": features}
    (DATA_DIR / "city_bins.geojson").write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    print("Zapisano city_bins:", len(features), "z adresem:", sum(f["properties"]["address"] is not None for f in features))


def main():
    if "--city" in sys.argv:
        return fetch_city()
    raw = overpass(QUERY, timeout=90)

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
