from app.models import Emptying, Forecast, Point, Press, Report
from app.osm_import import import_points
from app.simulation import DEMO_NOW, FUTURE_HOURS, MAX_LEVEL, simulate, trolled_ids
from app.state import point_states


def _history():
    return [(f.point_id, f.at, f.level) for f in Forecast.query.order_by(Forecast.point_id, Forecast.at)]


def _presses():
    return [(p.point_id, p.at) for p in Press.query.order_by(Press.point_id, Press.at)]


def test_simulation_is_deterministic(cache):
    import_points(cache)
    simulate(weeks=1, seed=3)
    first, first_presses = _history(), _presses()
    simulate(weeks=1, seed=3)
    assert _history() == first
    assert _presses() == first_presses
    simulate(weeks=1, seed=4)
    assert _history() != first


def test_simulation_covers_every_point_hourly_within_bounds(cache):
    import_points(cache)
    stats = simulate(weeks=1)
    assert stats["levels"] == 72 * (7 * 24 + 1 + FUTURE_HOURS)
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


def test_simulated_presses_only_in_the_past_and_future_reports_open(cache):
    import_points(cache)
    simulate(weeks=2)
    assert Press.query.count() > 0
    assert Press.query.filter(Press.at >= DEMO_NOW).count() == 0
    assert Report.query.filter(Report.resolved_at > DEMO_NOW).count() == 0


def test_trolled_buttons_get_check_flag(cache):
    import_points(cache)
    simulate(weeks=2)
    states = point_states(DEMO_NOW)
    trolled = trolled_ids(Point.query.all())
    assert len(trolled) == 2
    for pid in trolled:
        assert states[pid]["check_button"]
        assert "trafnych" in states[pid]["check_reason"]
