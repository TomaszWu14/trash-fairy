"""Generator danych syntetycznych: historia zapełnienia punktów co godzinę (koncepcja, sekcja 7).

Wszystko jest deterministyczne dla danego seeda. Opróżnienia według dzisiejszego, stałego
harmonogramu MPO: kosze o 6:00 i 14:00, altany co 3 dni o 6:00.
"""
import random
from datetime import datetime, timedelta

from sqlalchemy import insert

from . import db
from .geo import distance_m
from .models import Emptying, Forecast, Point
from .osm_import import KAZIMIERZ

# Zamrożony zegar demo: sobota 13:30, jarmark na Rynku (sekcja 7)
DEMO_NOW = datetime(2026, 10, 3, 13, 30)

# mnożnik tempa wg godziny: obiad i wieczór w górę, noc w dół
BIN_HOURLY = [0.4, 0.3, 0.2, 0.1, 0.1, 0.2, 0.4, 0.7, 0.9, 0.9, 1.0, 1.2,
              1.6, 1.7, 1.4, 1.2, 1.2, 1.4, 1.6, 1.6, 1.4, 1.1, 0.8, 0.6]
NIGHTLIFE_HOURS = {21, 22, 23, 0, 1, 2}
NIGHTLIFE_RADIUS_M = 600  # wokół Placu Nowego
SHELTER_PEAK_HOURS = {7, 8, 9, 18, 19, 20, 21}

BIN_EMPTY_HOURS = (6, 14)
SHELTER_EMPTY_HOUR = 6
SHELTER_EMPTY_EVERY_DAYS = 3
MAX_LEVEL = 120  # powyżej 100% = przepełnienie, odpady obok kosza


def hourly_multiplier(point, at, nightlife):
    weekend = at.weekday() >= 5
    if point.kind == "shelter":
        return (1.3 if at.hour in SHELTER_PEAK_HOURS else 0.8) * (1.1 if weekend else 1.0)
    m = BIN_HOURLY[at.hour] * (1.4 if weekend else 1.0)
    if nightlife and at.hour in NIGHTLIFE_HOURS:
        m *= 2.5
    return m


def is_emptying_time(point, at, start):
    if point.kind == "bin":
        return at.hour in BIN_EMPTY_HOURS
    return at.hour == SHELTER_EMPTY_HOUR and (at - start).days % SHELTER_EMPTY_EVERY_DAYS == 0


def simulate(weeks=8, seed=7, now=DEMO_NOW):
    """Zastępuje historię 'sim' i opróżnienia: `weeks` tygodni co 1 h, kończąc na `now`."""
    rng = random.Random(seed)
    end = now.replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(weeks=weeks)
    db.session.query(Forecast).filter_by(source="sim").delete()
    db.session.query(Emptying).delete()

    levels, emptyings = [], []
    for p in Point.query.order_by(Point.id):
        nightlife = p.kind == "bin" and distance_m(p.lat, p.lon, *KAZIMIERZ) <= NIGHTLIFE_RADIUS_M
        level, at = rng.uniform(0, 30), start
        while at <= end:
            if is_emptying_time(p, at, start):
                emptyings.append({"point_id": p.id, "at": at, "level": min(100, round(level / 25) * 25)})
                level = 0.0
            noise = max(0.0, rng.gauss(1.0, 0.25))
            level = min(MAX_LEVEL, level + p.base_rate * hourly_multiplier(p, at, nightlife) * noise)
            levels.append({"point_id": p.id, "at": at, "level": round(level, 1), "source": "sim"})
            at += timedelta(hours=1)

    db.session.execute(insert(Forecast), levels)
    if emptyings:
        db.session.execute(insert(Emptying), emptyings)
    db.session.commit()
    return len(levels), len(emptyings)
