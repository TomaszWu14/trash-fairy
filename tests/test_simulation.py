from datetime import datetime

from app.models import Emptying, Forecast, Point
from app.osm_import import import_points
from app.simulation import MAX_LEVEL, simulate
from app.state import current_levels, level_state


def _history():
    return [(f.point_id, f.at, f.level) for f in Forecast.query.order_by(Forecast.point_id, Forecast.at)]


def test_simulation_is_deterministic(cache):
    import_points(cache)
    simulate(weeks=1, seed=3)
    first = _history()
    simulate(weeks=1, seed=3)
    assert _history() == first
    simulate(weeks=1, seed=4)
    assert _history() != first


def test_simulation_covers_every_point_hourly_within_bounds(cache):
    import_points(cache)
    n_levels, _ = simulate(weeks=1)
    assert n_levels == 72 * (7 * 24 + 1)
    levels = [f.level for f in Forecast.query]
    assert min(levels) >= 0 and max(levels) <= MAX_LEVEL


def test_bins_emptied_at_6_and_14(cache):
    import_points(cache)
    simulate(weeks=1)
    bin_ids = [p.id for p in Point.query.filter_by(kind="bin")]
    hours = {e.at.hour for e in Emptying.query.filter(Emptying.point_id.in_(bin_ids))}
    assert hours == {6, 14}


def test_overloaded_shelters_fill_faster(cache):
    import_points(cache)
    simulate(weeks=4)
    full = lambda p: sum(e.level >= 100 for e in Emptying.query.filter_by(point_id=p.id))
    shelters = Point.query.filter_by(kind="shelter").all()
    over = [full(p) for p in shelters if p.overloaded]
    normal = [full(p) for p in shelters if not p.overloaded]
    assert min(over) > max(normal) / 2
    assert sum(over) / len(over) > 2 * sum(normal) / len(normal)


def test_current_levels_take_last_hour(cache):
    import_points(cache)
    simulate(weeks=1, now=datetime(2026, 10, 3, 13, 30))
    last = {f.point_id: f.level for f in Forecast.query.filter_by(at=datetime(2026, 10, 3, 13))}
    assert current_levels() == last


def test_level_state_thresholds():
    assert level_state(59.9) == "ok"
    assert level_state(60) == "warn"
    assert level_state(85) == "warn"
    assert level_state(85.1) == "bad"


def test_points_api_includes_state(client, cache):
    import_points(cache)
    simulate(weeks=1)
    f = client.get("/api/points").json["features"][0]["properties"]
    assert f["state"] in ("ok", "warn", "bad")
    assert f["symbol"] in ("✓", "~", "!")
