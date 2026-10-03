"""Prognoza zapełnienia (koncepcja, sekcja 6.3): statystyka i reguły, bez AI.

System nie ma czujników, więc nie zna prawdziwego poziomu (ten zna tylko symulator).
Szacunek = suma przyrostów z profilu tygodniowego od ostatniego opróżnienia × mnożnik wydarzeń.

Profil tygodniowy punktu: średni przyrost %/h w komórce (dzień tygodnia, godzina) z historii
sprzed zegara demo, plus kwantyle p20/p80 na przedział. Godziny wydarzeń dzielimy przez mnożnik,
żeby profil był „bazowy”, a mnożnik nakładamy dopiero w prognozie.
"""
from collections import defaultdict
from datetime import timedelta
from functools import lru_cache
from statistics import mean, quantiles

from . import db, weather
from .events import events_near, multiplier
from .models import Emptying, Event, Forecast, Point
from .simulation import MAX_LEVEL, hour_floor

THRESHOLD = 85
HORIZON = timedelta(hours=24)
HOUR = timedelta(hours=1)
DEFAULT_RATE = 2.0  # %/h dla punktu bez historii
QUALITY_DAYS = 7

EST, LOW, HIGH = 1, 2, 3  # indeksy w wierszu trajektorii: (at, est, low, high)


def clear_cache():
    """Profile zależą od zawartości bazy — czyścimy po każdej nowej symulacji lub zmianie wydarzeń."""
    build_profiles.cache_clear()
    forecast_quality.cache_clear()


def _summarize(cells):
    incs = [v for vals in cells.values() for v in vals]
    out = {}
    for key, vals in cells.items():
        if len(vals) >= 2:
            q = quantiles(vals, n=5)
            out[key] = (mean(vals), max(0.0, q[0]), q[3])
        else:
            out[key] = (vals[0], vals[0], vals[0])
    return {"cells": out, "avg": mean(incs) if incs else DEFAULT_RATE}


@lru_cache(maxsize=8)
def build_profiles(cutoff):
    """{point_id: {"cells": {(dzień, godzina): (średnia, p20, p80)}, "avg": średnia}} z historii < cutoff."""
    events = Event.query.all()
    near = {p.id: events_near(p.lat, p.lon, events) for p in Point.query}
    emptied = defaultdict(set)
    for pid, at in db.session.query(Emptying.point_id, Emptying.at).filter(Emptying.at < cutoff):
        emptied[pid].add(at)

    cells = defaultdict(lambda: defaultdict(list))
    prev = {}
    rows = (db.session.query(Forecast.point_id, Forecast.at, Forecast.level)
            .filter(Forecast.source == "sim", Forecast.at < cutoff).order_by(Forecast.point_id, Forecast.at))
    for pid, at, level in rows:
        if at in emptied[pid]:
            inc = level  # w godzinie opróżnienia poziom startuje od zera
        elif pid in prev and prev[pid][0] == at - HOUR:
            inc = level - prev[pid][1]
        else:
            inc = None
        prev[pid] = (at, level)
        if inc is None or level >= MAX_LEVEL:  # przy przepełnieniu przyrost jest ucięty — nie uczymy się z niego
            continue
        cells[pid][(at.weekday(), at.hour)].append(inc / multiplier(at, near.get(pid, [])))
    return {pid: _summarize(c) for pid, c in cells.items()}


def _cell(profile, at):
    if profile is None:
        return DEFAULT_RATE, DEFAULT_RATE * 0.7, DEFAULT_RATE * 1.3
    avg = profile["avg"]
    return profile["cells"].get((at.weekday(), at.hour), (avg, avg * 0.7, avg * 1.3))


def trajectory(profile, near, resets, start, end, now, weather_at=None):
    """Godzina po godzinie [(at, est, low, high)]. Do `now` zerujemy na opróżnieniach, dalej to prognoza.

    Przed pierwszym znanym opróżnieniem szacunku nie ma (None). `weather_at(at)` (app/weather.py) mnoży tylko
    godziny po `now`: przeszłość to szacunek z profilu, a profil, MAE i porównanie liczymy bez pogody.
    """
    out, est, low, high = [], None, None, None
    at = start
    while at <= end:
        if at in resets and at <= now:
            est = low = high = 0.0
        if est is not None:
            m, (mid, lo, hi) = multiplier(at, near), _cell(profile, at)
            if weather_at and at > now:
                m *= weather_at(at)
            est, low, high = (min(MAX_LEVEL, v + r * m) for v, r in ((est, mid), (low, lo), (high, hi)))
        out.append((at, est, low, high))
        at += HOUR
    return out


def first_crossing(traj, idx, threshold=THRESHOLD):
    """Chwila przekroczenia progu (interpolacja w obrębie godziny) w trajektorii jednego cyklu."""
    before = 0.0
    for row in traj:
        value = row[idx]
        if value is None:
            continue
        if before <= threshold < value:
            return row[0] + HOUR * ((threshold - before) / (value - before))
        before = value
    return None


def point_forecasts(now, last_emptying):
    """{point_id: {"est", "crossing", "early", "late", "recent"}} dla chwili `now` zegara demo."""
    hour = hour_floor(now)
    profiles = build_profiles(hour)
    events = Event.query.all()
    weather_at = weather.factor_at()
    out = {}
    for p in Point.query.order_by(Point.id):
        le = last_emptying.get(p.id)
        start = hour_floor(le) if le else hour - timedelta(hours=72)
        traj = trajectory(profiles.get(p.id), events_near(p.lat, p.lon, events), {start}, start, hour + HORIZON, now, weather_at)
        by_hour = {row[0]: row for row in traj}
        out[p.id] = {
            "est": by_hour[hour][EST] or 0.0,
            "crossing": first_crossing(traj, EST),
            "early": first_crossing(traj, HIGH),  # szybsze tempo (p80) → wcześniej
            "late": first_crossing(traj, LOW),
            "recent": [by_hour[hour - h * HOUR][EST] for h in range(6) if hour - h * HOUR in by_hour],
        }
    return out


def point_series(point, now, hours_back=48):
    """Wykres szczegółów: szacunek z ostatnich `hours_back` h i prognoza na 24 h z przedziałem."""
    hour = hour_floor(now)
    window_start = hour - timedelta(hours=hours_back)
    resets = {at for (at,) in db.session.query(Emptying.at)
              .filter(Emptying.point_id == point.id, Emptying.at <= now, Emptying.at >= window_start - timedelta(days=4))}
    start = min(resets) if resets else window_start
    near = events_near(point.lat, point.lon, Event.query.all())
    traj = trajectory(build_profiles(hour).get(point.id), near, resets, start, hour + HORIZON, now, weather.factor_at())
    return [row for row in traj if row[0] >= window_start]


@lru_cache(maxsize=4)
def forecast_quality(cutoff):
    """MAE (p.p.) prognozy na ostatnim tygodniu przed `cutoff`, z profilem uczonym na wcześniejszej historii,
    porównany z naiwną stałą średnią (bez profilu godzinowego i bez wydarzeń)."""
    window = cutoff - timedelta(days=QUALITY_DAYS)
    profiles = build_profiles(window)
    events = Event.query.all()
    truth = defaultdict(dict)
    for pid, at, level in (db.session.query(Forecast.point_id, Forecast.at, Forecast.level)
                           .filter(Forecast.source == "sim", Forecast.at >= window, Forecast.at < cutoff)):
        truth[pid][at] = level
    resets = defaultdict(set)
    for pid, at in db.session.query(Emptying.point_id, Emptying.at).filter(Emptying.at < cutoff):
        resets[pid].add(at)

    errors, naive_errors = [], []
    for p in Point.query:
        profile = profiles.get(p.id)
        naive = {"cells": {}, "avg": profile["avg"] if profile else DEFAULT_RATE}
        args = (resets[p.id], window - timedelta(days=4), cutoff - HOUR, cutoff)
        smart = trajectory(profile, events_near(p.lat, p.lon, events), *args)
        dumb = trajectory(naive, [], *args)
        for (at, est, *_), (_, est_naive, *_) in zip(smart, dumb):
            if at in truth[p.id] and est is not None:
                errors.append(abs(est - truth[p.id][at]))
                naive_errors.append(abs(est_naive - truth[p.id][at]))
    if not errors:
        return None
    return {"mae": round(mean(errors), 1), "naive_mae": round(mean(naive_errors), 1), "days": QUALITY_DAYS}
