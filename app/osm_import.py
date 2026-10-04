"""Import punktów demo z cache OSM (data/*.geojson) do bazy."""
import json
import random
from pathlib import Path

from sqlalchemy import text

from . import db
from .geo import distance_m
from .models import Pickup, Point, ReportHistory

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

RYNEK = (50.0617, 19.9373)
KAZIMIERZ = (50.0513, 19.9447)  # Plac Nowy
GRZEGORZKI = (50.0590, 19.9600)

BIN_AREAS = [("Rynek", RYNEK, 33), ("Kazimierz", KAZIMIERZ, 21)]
BINS_NEAR_OVERLOADED_SHELTER = 3  # kosze uliczne przy przeciążonych altanach — pod regułę altana → kosz (200 m)
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
    """Zastępuje punkty w bazie: 60 koszy (Rynek, Kazimierz, kilka przy przeciążonych altanach) i 12 altan."""
    rng = random.Random(seed)
    for model in (Pickup, ReportHistory, Point):  # także punkty miasta i ich historia: import_city_points je odtwarza
        db.session.query(model).delete()
    if db.engine.dialect.name == "postgresql":  # id od 1 jak w SQLite: kosz demo nr 18 (QR na slajdach, /panel/18) musi istnieć
        db.session.execute(text("SELECT setval(pg_get_serial_sequence('point', 'id'), 1, false)"))
    shelters = select_spaced(cache["shelters"], GRZEGORZKI, SHELTERS, MIN_GAP_M)
    areas = list(BIN_AREAS) + [("Grzegórzki", (s["lat"], s["lon"]), BINS_NEAR_OVERLOADED_SHELTER)
                               for s in shelters[:OVERLOADED_SHELTERS]]

    taken, counter = [], {}
    streets = [p for p in cache["pois"] if p["tags"].get("addr:street")]
    for area, centre, n in areas:
        for b in select_spaced(cache["bins"], centre, n, MIN_GAP_M, taken=taken):
            taken.append(b)
            counter[area] = counter.get(area, 0) + 1
            db.session.add(Point(
                osm_id=b["osm_id"], kind="bin", area=area, lat=b["lat"], lon=b["lon"],
                name=b["tags"].get("name") or f"Kosz {area} {counter[area]:02d}", osm_tags=b["tags"],
                base_rate=bin_rate(b, cache["pois"], cache["stops"]),
                district=district_of(area), fraction="zmieszane", address=address_of(b, area, streets),
            ))

    for i, s in enumerate(shelters, 1):
        overloaded = i <= OVERLOADED_SHELTERS
        db.session.add(Point(
            osm_id=s["osm_id"], kind="shelter", area="Grzegórzki", lat=s["lat"], lon=s["lon"],
            name=s["tags"].get("name") or f"Altana Grzegórzki {i:02d}", osm_tags=s["tags"],
            base_rate=round(rng.uniform(0.8, 1.3) * (2 if overloaded else 1), 2), overloaded=overloaded,
            district=district_of("Grzegórzki"), fraction=shelter_fraction(s["tags"]),
            address=address_of(s, "Grzegórzki", streets),
        ))
    db.session.commit()


# --- dzielnice, frakcje, adresy (panel miasta) ---

FRACTION_TAGS = {"papier": ("recycling:paper", "recycling:cardboard"),
                 "metale_tworzywa": ("recycling:plastic", "recycling:cans", "recycling:plastic_packaging",
                                     "recycling:plastic_bottles", "recycling:scrap_metal", "recycling:metal"),
                 "szklo": ("recycling:glass_bottles", "recycling:glass"),
                 "bio": ("recycling:organic", "recycling:green_waste", "recycling:food_waste")}
AREA_ADDRESS = {"Rynek": "okolice Rynku Głównego", "Kazimierz": "okolice pl. Nowego", "Grzegórzki": "os. Grzegórzki"}
STREET_NEAR_M = 150
STREET_PREFIX = {"aleja": "al.", "aleje": "al.", "plac": "pl.", "osiedle": "os."}
NO_PREFIX = {"al.", "pl.", "os.", "rynek", "rondo", "bulwar", "bulwary", "most", "park", "planty", "skwer", "droga"}


def street_label(name):
    """„Aleja Przyjaźni” → „al. Przyjaźni”, „Rynek Główny” bez zmian, reszta → „ul. X”."""
    first, _, rest = name.partition(" ")
    if first.lower() in STREET_PREFIX:
        return f"{STREET_PREFIX[first.lower()]} {rest}"
    return name if first.lower() in NO_PREFIX else f"ul. {name}"


def near_label(name):
    """Adres przybliżony: „okolice ul. X” (skrót się nie odmienia), „okolice: Rynek Główny” (bez odmiany nazwy)."""
    label = street_label(name)
    return f"okolice {label}" if label.split()[0] in ("ul.", "al.", "pl.", "os.") else f"okolice: {label}"


def fractions(tags):
    """Frakcje pojemnika z tagów recycling:* (kolejność jak w FRACTION_TAGS)."""
    return [f for f, keys in FRACTION_TAGS.items() if any(tags.get(k) == "yes" for k in keys)]


def district_of(area):
    """Dzielnica 72 punktów demo z obszaru: Rynek i Kazimierz leżą w dzielnicy I Stare Miasto."""
    return "Grzegórzki" if area == "Grzegórzki" else "Stare Miasto"


def shelter_fraction(tags):
    """Altana ma kilka pojemników, więc „zmieszane” — chyba że tagi OSM wskazują dokładnie jedną frakcję."""
    f = fractions(tags)
    return f[0] if len(f) == 1 else "zmieszane"


def address_of(p, area, streets):
    """addr:street (+ numer) z tagów punktu, inaczej ulica najbliższego lokalu z adresem w 150 m, inaczej opis obszaru.
    Numerów nie zgadujemy: „okolice ul. X” to tylko ulica."""
    t = p["tags"]
    if t.get("addr:street"):
        return f"{street_label(t['addr:street'])} {t.get('addr:housenumber', '')}".strip()
    near = min(streets, key=lambda s: distance_m(p["lat"], p["lon"], s["lat"], s["lon"]), default=None)
    if near and distance_m(p["lat"], p["lon"], near["lat"], near["lon"]) <= STREET_NEAR_M:
        return near_label(near["tags"]["addr:street"])
    return AREA_ADDRESS.get(area, area)


# Punkty panelu miasta (live=False) z data/city_bins.geojson (scripts/fetch_osm.py --city). Dzielnica z cache:
# przypisana przez Overpass (węzeł wewnątrz relacji dzielnicy, admin_level=9) — point-in-polygon, nie centroid.
CITY_TARGETS = {"Krowodrza": (18, 12), "Podgórze": (18, 12), "Nowa Huta": (18, 12), "Dębniki": (18, 12),
                "Stare Miasto": (9, 6), "Grzegórzki": (9, 6)}  # (kosze uliczne, pojemniki do selektywnej zbiórki)
CITY_SEED = 2026
FRACTION_LABELS = {"papier": "Papier", "metale_tworzywa": "Metale i tworzywa sztuczne", "szklo": "Szkło",
                   "bio": "Bio", "zmieszane": "Zmieszane"}


def load_city_cache(data_dir=DATA_DIR):
    fc = json.loads((data_dir / "city_bins.geojson").read_text(encoding="utf-8"))
    return [{**f["properties"], "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1]}
            for f in fc["features"]]


def city_rate(kind, fraction, district, rng):
    """Tempo zapełniania %/h (jak base_rate punktów demo). Kosze w centrum szybciej; pojemniki wg frakcji."""
    if kind == "bin":
        return round(rng.uniform(1.6, 3.0) if district == "Stare Miasto" else rng.uniform(0.7, 1.4), 2)
    per_day = {"papier": (9, 14), "metale_tworzywa": (10, 15), "szklo": (4, 7), "bio": (16, 26)}[fraction]
    return round(rng.uniform(*per_day) / 24, 3)


def import_city_points(cache=None, seed=CITY_SEED):
    """Zastępuje punkty miasta: ~150 punktów w 6 dzielnicach, dopisane PO 72 punktach demo (wyższe id), z własnym RNG.
    Pomija punkty demo i wszystko bliżej niż MIN_GAP_M od już wybranych. Zwraca liczbę punktów miasta."""
    rng = random.Random(seed)
    city = db.session.query(Point.id).filter(Point.live.is_(False))
    for model in (Pickup, ReportHistory):  # historia wskazuje na punkty (klucz obcy na Postgresie)
        db.session.query(model).filter(model.point_id.in_(city)).delete(synchronize_session=False)
    db.session.query(Point).filter(Point.live.is_(False)).delete()
    live = Point.live_query().all()
    live_ids = {p.osm_id for p in live}
    taken = [{"lat": p.lat, "lon": p.lon} for p in live]
    counts = {d: {"bin": 0, "container": 0} for d in CITY_TARGETS}
    used = {d: {f: 0 for f in FRACTION_TAGS} for d in CITY_TARGETS}
    for c in cache if cache is not None else load_city_cache():
        d, is_bin = c["district"], c["tags"].get("amenity") == "waste_basket"
        kind = "bin" if is_bin else "container"
        if d not in CITY_TARGETS or c["osm_id"] in live_ids or counts[d][kind] >= CITY_TARGETS[d][0 if is_bin else 1]:
            continue
        if any(distance_m(c["lat"], c["lon"], o["lat"], o["lon"]) < MIN_GAP_M for o in taken):
            continue
        if is_bin:
            fraction = "zmieszane"
        else:  # z kilku frakcji pojemnika bierzemy najrzadszą dotąd w dzielnicy (równowaga frakcji)
            options = fractions(c["tags"])
            if not options:
                continue
            fraction = min(options, key=lambda f: used[d][f])
            used[d][fraction] += 1
        taken.append(c)
        counts[d][kind] += 1
        label = "Kosz" if is_bin else f"Pojemnik – {FRACTION_LABELS[fraction].lower()}"
        db.session.add(Point(
            osm_id=c["osm_id"], kind=kind, area=d, lat=c["lat"], lon=c["lon"], osm_tags=c["tags"],
            name=c["tags"].get("name") or f"{label}, {d} {counts[d][kind]:02d}", base_rate=city_rate(kind, fraction, d, rng),
            live=False, district=d, fraction=fraction, address=c.get("address") or f"{d} (położenie wg OSM)",
        ))
    db.session.commit()
    return Point.query.filter(Point.live.is_(False)).count()
