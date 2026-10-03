"""Generator danych syntetycznych (koncepcja, sekcja 7). Deterministyczny dla danego seeda.

- poziom zapełnienia co godzinę: `weeks` tygodni historii + FUTURE_HOURS „przyszłości”,
  którą odsłania przewijanie zegara demo;
- opróżnienia według dzisiejszego, stałego harmonogramu MPO: kosze o 6:00 i 14:00, altany co 3 dni o 6:00;
- naciśnięcia przycisków (tylko w przeszłości): przy poziomie > 80%, rzadkie fałszywe alarmy,
  2 trollowane przyciski w dni robocze 14–16. Zgłoszenia budowane tymi samymi regułami co na żywo.
"""
import random
from datetime import datetime, timedelta

from sqlalchemy import insert

from . import db
from .geo import distance_m
from .models import Emptying, Forecast, Point, Press, Report
from .osm_import import KAZIMIERZ
from .reports import MERGE_WINDOW, is_hit, reliability

# Zamrożony zegar demo: sobota 13:30, jarmark na Rynku (sekcja 7)
DEMO_NOW = datetime(2026, 10, 3, 13, 30)
FUTURE_HOURS = 24

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

PRESS_ABOVE = 80
FALSE_ALARM_RATE = 0.004  # na godzinę × mnożnik ruchu
TROLLED_BUTTONS = 2
TROLL_HOURS = {14, 15}


def hour_floor(at):
    return at.replace(minute=0, second=0, microsecond=0)


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


def trolled_ids(points):
    """Dwa najspokojniejsze kosze na Kazimierzu („przy szkole”) — ktoś naciska je dla żartu."""
    quiet = sorted((p for p in points if p.kind == "bin" and p.area == "Kazimierz"), key=lambda p: (p.base_rate, p.id))
    return {p.id for p in quiet[:TROLLED_BUTTONS]}


def sim_presses(rng, at, level, mult, trolled, now):
    n = 0
    if level > PRESS_ABOVE and rng.random() < min(0.8, 0.25 * mult):
        n = rng.randint(1, 4)
    elif rng.random() < FALSE_ALARM_RATE * mult:
        n = 1
    if trolled and at.weekday() < 5 and at.hour in TROLL_HOURS and rng.random() < 0.7:
        n += rng.randint(2, 6)
    times = sorted(at + timedelta(minutes=rng.randrange(60)) for _ in range(n))
    return [t for t in times if t < now]


def simulate(weeks=8, seed=7, now=DEMO_NOW):
    """Zastępuje całą symulację (poziomy, opróżnienia, naciśnięcia, zgłoszenia)."""
    rng = random.Random(seed)
    start = hour_floor(now) - timedelta(weeks=weeks)
    end = hour_floor(now) + timedelta(hours=FUTURE_HOURS)
    db.session.query(Forecast).filter_by(source="sim").delete()
    for model in (Emptying, Press, Report):
        db.session.query(model).delete()

    points = Point.query.order_by(Point.id).all()
    trolled = trolled_ids(points)
    levels, emptyings, presses, reports = [], [], [], []
    for p in points:
        nightlife = p.kind == "bin" and distance_m(p.lat, p.lon, *KAZIMIERZ) <= NIGHTLIFE_RADIUS_M
        level, at = rng.uniform(0, 30), start
        outcomes, open_reports = [], []
        while at <= end:
            if is_emptying_time(p, at, start):
                e_level = min(100, round(level / 25) * 25)
                emptyings.append({"point_id": p.id, "at": at, "level": e_level})
                if at <= now:  # przyszłe opróżnienia rozstrzyga dopiero przewijanie zegara
                    for r in open_reports:
                        r["hit"], r["resolved_at"] = is_hit(e_level), at
                        outcomes.append(r["hit"])
                    open_reports = []
                level = 0.0
            mult = hourly_multiplier(p, at, nightlife)
            level = min(MAX_LEVEL, level + p.base_rate * mult * max(0.0, rng.gauss(1.0, 0.25)))
            levels.append({"point_id": p.id, "at": at, "level": round(level, 1), "source": "sim"})

            for t in sim_presses(rng, at, level, mult, p.id in trolled, now):
                presses.append({"point_id": p.id, "at": t})
                if open_reports and open_reports[-1]["first_at"] > t - MERGE_WINDOW:
                    open_reports[-1]["presses"] += 1
                    open_reports[-1]["last_at"] = t
                else:
                    r = {"point_id": p.id, "first_at": t, "last_at": t, "presses": 1,
                         "weight": reliability(outcomes), "hit": None, "resolved_at": None}
                    open_reports.append(r)
                    reports.append(r)
            at += timedelta(hours=1)

    for model, rows in ((Forecast, levels), (Emptying, emptyings), (Press, presses), (Report, reports)):
        if rows:
            db.session.execute(insert(model), rows)
    db.session.commit()
    return {"levels": len(levels), "emptyings": len(emptyings), "presses": len(presses), "reports": len(reports)}
