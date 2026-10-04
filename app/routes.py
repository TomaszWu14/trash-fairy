"""Trasy na najbliższy kurs (koncepcja, sekcja 6.6): wybór punktów regułami + OR-Tools VRP.

Dwie floty, start i koniec w bazie MPO. Odległości w linii prostej × 1,3 (ulice nie są proste; OSRM w roadmapie).
Pojemność pojazdu to wymiar OR-Tools: gdy odpady z wybranych punktów się nie mieszczą, flota dostaje kolejny pojazd.
"""
from datetime import datetime, timedelta
from functools import lru_cache

from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from sqlalchemy import func

from . import db
from .geo import distance_m
from .history import CAPACITY_L
from .models import Emptying, Point

DEPOT = {"name": "Baza MPO, ul. Nowohucka 1", "lat": 50.0702786, "lon": 20.0056628}  # OSM way/79814148
DETOUR = 1.3
# capacity_l: założenie demo — ile litrów odpadów z pojemników mieści pojazd (po zgniocie). Dobrane tak, że pełne
# wszystkie punkty demo (60 koszy × 120 l = 7 200 l, 12 altan × 1 100 l = 13 200 l) mieszczą się w jednym pojeździe;
# na skali miasta solver sam dokłada pojazdy, najwyżej max_vehicles na flotę.
FLEETS = {
    "bin": {"label": "Kosze uliczne", "vehicle": "mały pojazd", "hours": (6, 14), "safety": timedelta(days=3),
            "capacity_l": 8_000, "max_vehicles": 3},
    "shelter": {"label": "Altany osiedlowe", "vehicle": "śmieciarka", "hours": (6,), "safety": timedelta(days=7),
                "capacity_l": 40_000, "max_vehicles": 3},
}
RECENT_EMPTYING = timedelta(hours=24)  # „opróżniony X h temu” w powodzie pominięcia


def road_m(a, b):
    return distance_m(a[0], a[1], b[0], b[1]) * DETOUR


def next_runs(kind, now):
    """(najbliższy kurs po `now`, kolejny kurs) dla floty."""
    runs = []
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    while len(runs) < 2:
        runs += [day.replace(hour=h) for h in FLEETS[kind]["hours"] if day.replace(hour=h) > now]
        day += timedelta(days=1)
    return runs[0], runs[1]


def select_reason(kind, state, crossing, last_emptying, run_at, following):
    """Powód wzięcia punktu na kurs `run_at` albo None. Reguły, nie AI (koncepcja, sekcja 6.6)."""
    if state == "bad":
        return "do opróżnienia teraz"
    if crossing is not None and crossing < following:
        return f"85% ok. {crossing:%H:%M}, a kolejny kurs dopiero {following:%d.%m %H:%M}"
    if last_emptying is None or run_at - last_emptying >= FLEETS[kind]["safety"]:
        return f"bezpiecznik: nieopróżniany od {FLEETS[kind]['safety'].days} dni"
    return None


def skip_reason(kind, level, crossing, last_emptying, now, following):
    """Dlaczego punkt NIE jedzie na najbliższy kurs: te same dane co select_reason, odwrotna strona reguły. Nie AI."""
    if crossing is None:
        parts = [f"poziom {level}%, bez 85% w prognozie 24 h"]
    else:
        at = f"{crossing:%H:%M}" if crossing.date() == now.date() else f"{crossing:%d.%m %H:%M}"
        parts = [f"poziom {level}%, 85% dopiero ok. {at} — po kolejnym kursie ({following:%d.%m %H:%M})"]
    if last_emptying is not None and now - last_emptying < RECENT_EMPTYING:
        hours = int((now - last_emptying).total_seconds() // 3600)
        parts.append(f"opróżniony {hours} h temu" if hours else "opróżniony przed chwilą")
    elif last_emptying is not None:
        days = max(1, -((now - last_emptying - FLEETS[kind]["safety"]) // timedelta(days=1)))
        parts.append(f"bezpiecznik za {days} {'dzień' if days == 1 else 'dni'}")
    return " · ".join(parts)


def _solve(dist, demands, capacity, vehicles):
    """Jedno uruchomienie OR-Tools. demands=None: bez wymiaru pojemności. None, gdy nie ma rozwiązania."""
    manager = pywrapcp.RoutingIndexManager(len(dist), vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)
    transit = routing.RegisterTransitCallback(lambda i, j: dist[manager.IndexToNode(i)][manager.IndexToNode(j)])
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    if demands is not None:
        load = routing.RegisterUnaryTransitCallback(lambda i: demands[manager.IndexToNode(i)])
        routing.AddDimensionWithVehicleCapacity(load, 0, [capacity] * vehicles, True, "Capacity")
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(params)
    if solution is None:
        return None
    routes = []
    for v in range(vehicles):
        order, index = [], routing.Start(v)
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node:
                order.append(node)
            index = solution.Value(routing.NextVar(index))
        if order:
            path = [0, *order, 0]
            routes.append((tuple(order), float(sum(dist[a][b] for a, b in zip(path, path[1:])))))
    return tuple(routes)


@lru_cache(maxsize=512)
def solve_fleet(coords, demands=None, capacity=None, max_vehicles=1):
    """coords[0] = baza, demands[i] = litry do zabrania z punktu i (demands[0] = 0). Zwraca krotkę tras
    (kolejność indeksów, metry), po jednej na użyty pojazd. Pojazdów tyle, ile trzeba: od sumy/pojemność w górę.
    Gdy nawet max_vehicles nie wystarcza (np. punkt większy niż pojazd), trasa bez limitu pojemności. Deterministyczne."""
    if len(coords) == 1:
        return (((), 0.0),)
    dist = [[int(road_m(a, b)) for b in coords] for a in coords]
    total = sum(demands) if demands else 0
    if not demands or total <= capacity:  # mieści się w jednym pojeździe: ten sam model co bez pojemności
        return _solve(dist, None, None, 1)
    for vehicles in range(-(-total // capacity), max_vehicles + 1):
        routes = _solve(dist, list(demands), capacity, vehicles)
        if routes:
            return routes
    return _solve(dist, None, None, 1)  # ponytail: przeładowany kurs zamiast błędu; flaga, gdy flota MPO będzie znana


def solve_route(coords):
    """Jeden pojazd bez limitu pojemności (porównanie „przed i po”). Zwraca (kolejność indeksów 1..n-1, metry)."""
    return solve_fleet(coords)[0]


def plan_routes(now, states):
    """Trasy obu flot na najbliższy kurs. `states` = wynik state.point_states(now)."""
    last_emptying = dict(db.session.query(Emptying.point_id, func.max(Emptying.at))
                         .filter(Emptying.at <= now).group_by(Emptying.point_id).all())
    points = Point.live_query().order_by(Point.id).all()
    out = []
    for kind, fleet in FLEETS.items():
        run_at, following = next_runs(kind, now)
        chosen, skipped = [], []
        for p in points:
            s = states.get(p.id)
            if p.kind != kind or s is None:
                continue
            crossing = datetime.fromisoformat(s["crossing"]) if s.get("crossing") else None
            level = round(s.get("value") or 0)
            reason = select_reason(kind, s["state"], crossing, last_emptying.get(p.id), run_at, following)
            if reason:
                chosen.append((p, reason, level))
            else:
                skipped.append({"id": p.id, "name": p.name, "level": level,
                                "reason": skip_reason(kind, level, crossing, last_emptying.get(p.id), now, following)})
        coords = ((DEPOT["lat"], DEPOT["lon"]),) + tuple((p.lat, p.lon) for p, _, _ in chosen)
        demands = (0,) + tuple(round(min(100, max(0, lvl)) / 100 * CAPACITY_L[kind]) for _, _, lvl in chosen)
        routes = []
        for v, (order, meters) in enumerate(solve_fleet(coords, demands, fleet["capacity_l"], fleet["max_vehicles"]), 1):
            stops = [{"id": chosen[i - 1][0].id, "name": chosen[i - 1][0].name, "lat": coords[i][0], "lon": coords[i][1],
                      "order": n, "reason": chosen[i - 1][1], "vehicle": v} for n, i in enumerate(order, 1)]
            routes.append({"vehicle": v, "km": round(meters / 1000, 1), "stops": stops,
                           "path": [[DEPOT["lat"], DEPOT["lon"]]] + [[s["lat"], s["lon"]] for s in stops]
                           + [[DEPOT["lat"], DEPOT["lon"]]]})
        first = routes[0]
        out.append({
            "kind": kind, "label": fleet["label"], "vehicle": fleet["vehicle"],
            "run_at": run_at.isoformat(), "run_label": f"{run_at:%d.%m %H:%M}",
            "following_at": following.isoformat(), "following_label": f"{following:%d.%m %H:%M}",
            "km": first["km"], "stops": first["stops"], "path": first["path"],
            "vehicles": len(routes), "capacity_l": fleet["capacity_l"], "extra_routes": routes[1:],
            "skipped": sorted(skipped, key=lambda k: (-k["level"], k["id"])),
        })
    return out
