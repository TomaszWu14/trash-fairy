from datetime import datetime, timedelta

import pytest

from app.comparison import compare, run_policy
from app.geo import distance_m
from app.osm_import import import_points
from app.routes import DEPOT, DETOUR, next_runs, plan_routes, road_m, select_reason, solve_route
from app.simulation import DEMO_NOW, simulate
from app.state import point_states

RUN = datetime(2026, 10, 3, 14)
FOLLOWING = datetime(2026, 10, 4, 6)


# --- test 6 z sekcji 11: wybór punktów do trasy ---

def test_selects_full_point():
    assert select_reason("bin", "bad", None, RUN - timedelta(hours=8), RUN, FOLLOWING) == "do opróżnienia teraz"


def test_selects_point_crossing_before_following_run():
    reason = select_reason("bin", "warn", datetime(2026, 10, 3, 22, 15), RUN - timedelta(hours=8), RUN, FOLLOWING)
    assert reason.startswith("85% ok. 22:15")


def test_skips_point_crossing_after_following_run():
    assert select_reason("bin", "ok", FOLLOWING + timedelta(hours=1), RUN - timedelta(hours=8), RUN, FOLLOWING) is None
    assert select_reason("bin", "ok", None, RUN - timedelta(hours=8), RUN, FOLLOWING) is None


def test_safety_3_days_for_bins_and_7_for_shelters():
    assert select_reason("bin", "ok", None, RUN - timedelta(days=3), RUN, FOLLOWING).startswith("bezpiecznik")
    assert select_reason("bin", "ok", None, RUN - timedelta(days=2, hours=23), RUN, FOLLOWING) is None
    assert select_reason("shelter", "ok", None, RUN - timedelta(days=6), RUN, FOLLOWING) is None
    assert select_reason("shelter", "ok", None, RUN - timedelta(days=7), RUN, FOLLOWING).startswith("bezpiecznik")


def test_next_runs_per_fleet():
    now = datetime(2026, 10, 3, 13, 30)
    assert next_runs("bin", now) == (datetime(2026, 10, 3, 14), datetime(2026, 10, 4, 6))
    assert next_runs("shelter", now) == (datetime(2026, 10, 4, 6), datetime(2026, 10, 5, 6))


# --- test 7 z sekcji 11: trasa odwiedza każdy wybrany punkt dokładnie raz ---

def test_route_visits_each_point_once_from_depot():
    coords = ((DEPOT["lat"], DEPOT["lon"]),) + tuple((50.05 + 0.002 * i, 19.93 + 0.003 * (i % 4)) for i in range(15))
    order, meters = solve_route(coords)
    assert sorted(order) == list(range(1, 16))
    path = [coords[0]] + [coords[i] for i in order] + [coords[0]]
    assert meters == pytest.approx(sum(int(road_m(a, b)) for a, b in zip(path, path[1:])))


def test_distances_use_detour_factor():
    a, b = (50.06, 19.93), (50.07, 19.95)
    assert road_m(a, b) == pytest.approx(distance_m(*a, *b) * DETOUR)


def test_empty_route():
    assert solve_route(((DEPOT["lat"], DEPOT["lon"]),)) == ((), 0.0)


def test_plan_routes_on_demo_data(cache):
    import_points(cache)
    simulate(weeks=2)
    fleets = plan_routes(DEMO_NOW, point_states(DEMO_NOW))
    assert [f["kind"] for f in fleets] == ["bin", "shelter"]
    for f in fleets:
        ids = [s["id"] for s in f["stops"]]
        assert len(ids) == len(set(ids))
        assert f["path"][0] == f["path"][-1] == [DEPOT["lat"], DEPOT["lon"]]
        assert all(s["reason"] for s in f["stops"])


# --- porównanie „przed i po” ---

def test_comparison_is_deterministic_and_saves_visits(cache):
    import_points(cache)
    simulate(weeks=6)
    first = compare(DEMO_NOW, weeks=2)
    compare.cache_clear()
    assert compare(DEMO_NOW, weeks=2) == first
    assert first["fairy"]["bin"]["visits"] < first["fixed"]["bin"]["visits"]
    assert first["fairy"]["total"]["overflow_hours"] <= first["fixed"]["total"]["overflow_hours"]


def test_fixed_policy_visits_every_bin_twice_a_day():
    from types import SimpleNamespace
    points = [SimpleNamespace(id=i, kind="bin", lat=50.06, lon=19.93 + i * 0.001) for i in range(3)]
    start = datetime(2026, 9, 1)
    hours = [start + timedelta(hours=h) for h in range(48)]
    incs = {p.id: [1.0] * 48 for p in points}
    stats = run_policy("fixed", points, hours, incs, {}, {p.id: [] for p in points})
    assert stats["bin"]["visits"] == 3 * 4 and stats["bin"]["runs"] == 4
