"""Import punktów demo z cache OSM (data/*.geojson) do bazy."""
import json
import random
from pathlib import Path

from . import db
from .geo import distance_m
from .models import Point

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

RYNEK = (50.0617, 19.9373)
KAZIMIERZ = (50.0513, 19.9447)  # Plac Nowy
GRZEGORZKI = (50.0590, 19.9600)

BIN_AREAS = [("Rynek", RYNEK, 36), ("Kazimierz", KAZIMIERZ, 24)]
SHELTERS = 12
MIN_GAP_M = 80  # żeby kosze nie zbijały się w jednym miejscu na mapie
OVERLOADED_SHELTERS = 2  # celowo przeciążone altany (koncepcja, sekcja 7)


def load_cache(data_dir=DATA_DIR):
    """{'bins': [{osm_id, lat, lon, tags}], 'shelters': [...], 'pois': [...], 'stops': [...]}"""
    out = {}
    for name in ("bins", "shelters", "pois", "stops"):
        fc = json.loads((data_dir / f"{name}.geojson").read_text(encoding="utf-8"))
        out[name] = [
            {"osm_id": f["properties"]["osm_id"], "tags": f["properties"]["tags"],
             "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1]}
            for f in fc["features"]
        ]
    return out


def select_spaced(candidates, centre, n, min_gap_m, taken=()):
    """Bierze do n punktów najbliżej centre, pomijając te bliżej niż min_gap_m od już wybranych."""
    chosen = list(taken)
    out = []
    for c in sorted(candidates, key=lambda c: distance_m(*centre, c["lat"], c["lon"])):
        if len(out) == n:
            break
        if all(distance_m(c["lat"], c["lon"], o["lat"], o["lon"]) >= min_gap_m for o in chosen):
            chosen.append(c)
            out.append(c)
    return out


def bin_rate(b, pois, stops):
    """Tempo zapełniania kosza (%/h) z liczby lokali i przystanków w promieniu 100 m."""
    near = lambda pts: sum(distance_m(b["lat"], b["lon"], p["lat"], p["lon"]) <= 100 for p in pts)
    return round(min(1.5 + 0.06 * near(pois) + 0.6 * near(stops), 8.0), 2)


def import_points(cache, seed=42):
    """Zastępuje punkty w bazie: 60 koszy (Rynek + Kazimierz) i 12 altan (Grzegórzki)."""
    rng = random.Random(seed)
    db.session.query(Point).delete()

    taken = []
    for area, centre, n in BIN_AREAS:
        for i, b in enumerate(select_spaced(cache["bins"], centre, n, MIN_GAP_M, taken=taken), 1):
            taken.append(b)
            db.session.add(Point(
                osm_id=b["osm_id"], kind="bin", area=area, lat=b["lat"], lon=b["lon"],
                name=b["tags"].get("name") or f"Kosz {area} {i:02d}", osm_tags=b["tags"],
                base_rate=bin_rate(b, cache["pois"], cache["stops"]),
            ))

    for i, s in enumerate(select_spaced(cache["shelters"], GRZEGORZKI, SHELTERS, MIN_GAP_M), 1):
        overloaded = i <= OVERLOADED_SHELTERS
        db.session.add(Point(
            osm_id=s["osm_id"], kind="shelter", area="Grzegórzki", lat=s["lat"], lon=s["lon"],
            name=s["tags"].get("name") or f"Altana Grzegórzki {i:02d}", osm_tags=s["tags"],
            base_rate=round(rng.uniform(0.8, 1.3) * (2 if overloaded else 1), 2), overloaded=overloaded,
        ))
    db.session.commit()
