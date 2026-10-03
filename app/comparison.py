"""Porównanie „przed i po” (koncepcja, sekcja 6.7): stały harmonogram MPO kontra Trash Fairy.

Odtwarzamy `weeks` tygodni przed zegarem demo na TYCH SAMYCH przyrostach zapełnienia (wspólny seed).
- Stały harmonogram: wszystkie kosze o 6:00 i 14:00, wszystkie altany co 3 dni o 6:00 (jak dziś).
- Trash Fairy: przed każdym kursem reguły z app/routes.py stosowane do WŁASNEGO szacunku
  (profil z wcześniejszych tygodni, zerowany na własnych opróżnieniach). Bez podglądania prawdy
  i bez przycisków — to wariant ostrożny.
"""
import random
from collections import defaultdict
from datetime import timedelta
from functools import lru_cache

from .events import events_near, multiplier
from .forecast import THRESHOLD, _cell, build_profiles
from .models import Event, Point
from .routes import DEPOT, FLEETS, select_reason, solve_route
from .simulation import (BIN_EMPTY_HOURS, MAX_LEVEL, SHELTER_EMPTY_EVERY_DAYS, SHELTER_EMPTY_HOUR, hour_floor,
                         is_nightlife, rate_factor)

HOUR = timedelta(hours=1)
WEEKS = 4
EMPTY_VISIT_BELOW = 50  # przyjazd do kosza zapełnionego poniżej 50% = „pusty przyjazd”


def fixed_selects(kind, at, start):
    if kind == "bin":
        return at.hour in BIN_EMPTY_HOURS
    return at.hour == SHELTER_EMPTY_HOUR and (at - start).days % SHELTER_EMPTY_EVERY_DAYS == 0


def is_run(kind, at):
    return at.hour in FLEETS[kind]["hours"]


def following_run(kind, at):
    t = at + HOUR
    while not is_run(kind, t):
        t += HOUR
    return t


def run_policy(policy, points, hours, incs, profiles, near):
    """Zwraca miary jednej polityki. `incs[pid][i]` = prawdziwy przyrost w godzinie hours[i]."""
    start = hours[0]
    level = {p.id: 0.0 for p in points}  # prawda
    est = {p.id: 0.0 for p in points}  # szacunek Trash Fairy
    last = {p.id: start for p in points}
    kinds = {p.id: p.kind for p in points}
    stats = {k: {"km": 0.0, "visits": 0, "empty_visits": 0, "overflow_hours": 0, "runs": 0} for k in FLEETS}
    for i, at in enumerate(hours):
        for kind in FLEETS:
            if not is_run(kind, at):
                continue
            fleet = [p for p in points if p.kind == kind]
            if policy == "fixed":
                chosen = fleet if fixed_selects(kind, at, start) else []
            else:
                following = following_run(kind, at)
                chosen = []
                for p in fleet:
                    projected, crossing, t = est[p.id], None, at
                    while t < following and crossing is None:  # kiedy szacunek przekroczy 85%?
                        before = projected
                        projected += _cell(profiles.get(p.id), t)[0] * multiplier(t, near[p.id])
                        if before <= THRESHOLD < projected:
                            crossing = t
                        t += HOUR
                    state = "bad" if est[p.id] > THRESHOLD else "ok"
                    if select_reason(kind, state, crossing, last[p.id], at, following):
                        chosen.append(p)
            if not chosen:
                continue
            coords = ((DEPOT["lat"], DEPOT["lon"]),) + tuple((p.lat, p.lon) for p in chosen)
            stats[kind]["km"] += solve_route(coords)[1] / 1000
            stats[kind]["runs"] += 1
            for p in chosen:
                stats[kind]["visits"] += 1
                stats[kind]["empty_visits"] += level[p.id] < EMPTY_VISIT_BELOW
                level[p.id] = est[p.id] = 0.0
                last[p.id] = at
        for p in points:
            level[p.id] = min(MAX_LEVEL, level[p.id] + incs[p.id][i])
            est[p.id] = min(MAX_LEVEL, est[p.id] + _cell(profiles.get(p.id), at)[0] * multiplier(at, near[p.id]))
            stats[kinds[p.id]]["overflow_hours"] += level[p.id] > 100
    stats["total"] = {key: sum(stats[k][key] for k in FLEETS) for key in stats["bin"]}
    for k in stats.values():
        k["km"] = round(k["km"], 1)
        k["empty_share"] = round(100 * k["empty_visits"] / k["visits"]) if k["visits"] else 0
    return stats


@lru_cache(maxsize=2)
def compare(cutoff, weeks=WEEKS, seed=11):
    """Miary obu polityk na `weeks` tygodniach przed `cutoff` (pełna godzina)."""
    cutoff = hour_floor(cutoff)
    start = cutoff - timedelta(weeks=weeks)
    profiles = build_profiles(start)  # uczymy się tylko na danych sprzed okresu porównania
    points = Point.query.order_by(Point.id).all()
    events = Event.query.all()
    near = {p.id: events_near(p.lat, p.lon, events) for p in points}
    hours = [start + k * HOUR for k in range(int((cutoff - start) / HOUR))]

    rng = random.Random(seed)
    incs = defaultdict(list)
    for p in points:
        nightlife = is_nightlife(p)
        for at in hours:
            incs[p.id].append(p.base_rate * rate_factor(p, at, nightlife, near[p.id]) * max(0.0, rng.gauss(1.0, 0.25)))

    fixed = run_policy("fixed", points, hours, incs, profiles, near)
    fairy = run_policy("fairy", points, hours, incs, profiles, near)
    return {"weeks": weeks, "from": start.isoformat(), "to": cutoff.isoformat(), "fixed": fixed, "fairy": fairy}


def clear_cache():
    compare.cache_clear()
