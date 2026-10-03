"""Trasy na najbliższy kurs (koncepcja, sekcja 6.6): wybór punktów regułami + OR-Tools VRP.

Dwie floty, każda z jednym pojazdem, start i koniec w bazie MPO. Odległości w linii prostej × 1,3
(ulice nie są proste; OSRM w roadmapie).
"""
from datetime import datetime, timedelta
from functools import lru_cache

from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from sqlalchemy import func

from . import db
from .geo import distance_m
from .models import Emptying, Point

DEPOT = {"name": "Baza MPO, ul. Nowohucka 1", "lat": 50.0702786, "lon": 20.0056628}  # OSM way/79814148
DETOUR = 1.3
FLEETS = {
    "bin": {"label": "Kosze uliczne", "vehicle": "mały pojazd", "hours": (6, 14), "safety": timedelta(days=3)},
    "shelter": {"label": "Altany osiedlowe", "vehicle": "śmieciarka", "hours": (6,), "safety": timedelta(days=7)},
}


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


@lru_cache(maxsize=512)
def solve_route(coords):
    """coords[0] = baza. Zwraca (kolejność indeksów punktów 1..n-1, metry). Wynik deterministyczny."""
    n = len(coords)
    if n == 1:
        return (), 0.0
    dist = [[int(road_m(a, b)) for b in coords] for a in coords]
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)
    transit = routing.RegisterTransitCallback(lambda i, j: dist[manager.IndexToNode(i)][manager.IndexToNode(j)])
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(params)
    order, index = [], routing.Start(0)
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if node:
            order.append(node)
        index = solution.Value(routing.NextVar(index))
    return tuple(order), float(solution.ObjectiveValue())


def plan_routes(now, states):
    """Trasy obu flot na najbliższy kurs. `states` = wynik state.point_states(now)."""
    last_emptying = dict(db.session.query(Emptying.point_id, func.max(Emptying.at))
                         .filter(Emptying.at <= now).group_by(Emptying.point_id).all())
    points = Point.live_query().order_by(Point.id).all()
    out = []
    for kind, fleet in FLEETS.items():
        run_at, following = next_runs(kind, now)
        chosen = []
        for p in points:
            s = states.get(p.id)
            if p.kind != kind or s is None:
                continue
            crossing = datetime.fromisoformat(s["crossing"]) if s.get("crossing") else None
            reason = select_reason(kind, s["state"], crossing, last_emptying.get(p.id), run_at, following)
            if reason:
                chosen.append((p, reason))
        coords = ((DEPOT["lat"], DEPOT["lon"]),) + tuple((p.lat, p.lon) for p, _ in chosen)
        order, meters = solve_route(coords)
        stops = [{"id": chosen[i - 1][0].id, "name": chosen[i - 1][0].name, "lat": coords[i][0], "lon": coords[i][1],
                  "order": n, "reason": chosen[i - 1][1]} for n, i in enumerate(order, 1)]
        out.append({
            "kind": kind, "label": fleet["label"], "vehicle": fleet["vehicle"],
            "run_at": run_at.isoformat(), "run_label": f"{run_at:%d.%m %H:%M}",
            "following_at": following.isoformat(), "following_label": f"{following:%d.%m %H:%M}", "km": round(meters / 1000, 1), "stops": stops,
            "path": [[DEPOT["lat"], DEPOT["lon"]]] + [[s["lat"], s["lon"]] for s in stops] + [[DEPOT["lat"], DEPOT["lon"]]],
        })
    return out
