from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app import db
from app.events import multiplier
from app.forecast import EST, HIGH, LOW, build_profiles, first_crossing, forecast_quality, trajectory
from app.models import Emptying, Event, Forecast, Point
from app.osm_import import import_points
from app.simulation import DEMO_NOW, hour_floor, simulate
from app.state import point_states

H = timedelta(hours=1)
SAT_6 = datetime(2026, 10, 3, 6)
RYNEK = (50.0617, 19.9373)


def flat(rate, low=None, high=None):
    """Profil z jednakowym tempem w każdej komórce."""
    cells = {(d, h): (rate, low if low is not None else rate, high if high is not None else rate)
             for d in range(7) for h in range(24)}
    return {"cells": cells, "avg": rate}


# --- test 5 z sekcji 11: znany profil → oczekiwana godzina przekroczenia ---

def test_known_profile_gives_expected_crossing_time():
    # opróżnienie o 6:00, 10%/h: poziom 10, 20, ... → 85% w połowie godziny 14:00–15:00
    traj = trajectory(flat(10), [], {SAT_6}, SAT_6, SAT_6 + 24 * H, now=SAT_6 + 3 * H)
    assert first_crossing(traj, EST) == datetime(2026, 10, 3, 14, 30)


def test_interval_from_slow_and_fast_rates():
    traj = trajectory(flat(10, low=5, high=17), [], {SAT_6}, SAT_6, SAT_6 + 24 * H, now=SAT_6)
    early, mid, late = (first_crossing(traj, i) for i in (HIGH, EST, LOW))
    assert early < mid < late


def test_no_estimate_before_first_known_emptying_and_reset_after():
    start = SAT_6 - 3 * H
    traj = trajectory(flat(10), [], {SAT_6}, start, SAT_6 + 2 * H, now=SAT_6 + 2 * H)
    assert [row[EST] for row in traj] == [None, None, None, 10, 20, 30]


def test_future_emptyings_are_not_assumed():
    traj = trajectory(flat(10), [], {SAT_6, SAT_6 + 8 * H}, SAT_6, SAT_6 + 10 * H, now=SAT_6 + 2 * H)
    assert traj[-1][EST] == 110  # opróżnienie o 14:00 jest w przyszłości — prognoza go nie zakłada


# --- mnożnik wydarzeń (sekcja 6.3) ---

def test_event_multiplier_radius_and_hour_after():
    event = SimpleNamespace(lat=RYNEK[0], lon=RYNEK[1], scale="large",
                            start=datetime(2026, 10, 3, 10), end=datetime(2026, 10, 3, 20))
    assert multiplier(datetime(2026, 10, 3, 10), [event]) == 2.0
    assert multiplier(datetime(2026, 10, 3, 20), [event]) == 2.0  # godzina po wydarzeniu
    assert multiplier(datetime(2026, 10, 3, 21), [event]) == 1.0
    assert multiplier(datetime(2026, 10, 3, 9), [event]) == 1.0


def test_events_near_uses_scale_radius():
    from app.events import events_near
    small = SimpleNamespace(lat=RYNEK[0], lon=RYNEK[1], scale="small")
    large = SimpleNamespace(lat=RYNEK[0], lon=RYNEK[1], scale="large")
    # ok. 500 m na północ od Rynku
    assert events_near(RYNEK[0] + 0.0045, RYNEK[1], [small, large]) == [large]


def test_event_raises_forecast():
    event = SimpleNamespace(lat=0, lon=0, scale="large", start=SAT_6, end=SAT_6 + 4 * H)
    calm = trajectory(flat(10), [], {SAT_6}, SAT_6, SAT_6 + 2 * H, now=SAT_6)
    busy = trajectory(flat(10), [event], {SAT_6}, SAT_6, SAT_6 + 2 * H, now=SAT_6)
    assert busy[-1][EST] == 2 * calm[-1][EST]


# --- profil z historii ---

@pytest.fixture
def point():
    p = Point(osm_id="node/1", kind="bin", area="Rynek", lat=50.06, lon=19.93, name="Kosz testowy", base_rate=2)
    db.session.add(p)
    db.session.commit()
    return p


def test_profile_counts_reset_hour_and_skips_capped(point):
    rows = [(SAT_6 - H, 50), (SAT_6, 5), (SAT_6 + H, 15), (SAT_6 + 2 * H, 120), (SAT_6 + 3 * H, 120)]
    for at, level in rows:
        db.session.add(Forecast(point_id=point.id, at=at, level=level, source="sim"))
    db.session.add(Emptying(point_id=point.id, at=SAT_6, level=50))
    db.session.commit()
    cells = build_profiles(SAT_6 + 4 * H)[point.id]["cells"]
    assert cells[(5, 6)][0] == 5  # godzina opróżnienia: przyrost od zera, nie 5 - 50
    assert cells[(5, 7)][0] == 10
    assert (5, 8) not in cells and (5, 9) not in cells  # 120% = ucięte przepełnienie


def test_profile_divides_out_event_multiplier(point):
    db.session.add(Event(name="X", venue="X", lat=point.lat, lon=point.lon, scale="large",
                         start=SAT_6, end=SAT_6 + H))
    for at, level in [(SAT_6 - H, 0), (SAT_6, 20)]:
        db.session.add(Forecast(point_id=point.id, at=at, level=level, source="sim"))
    db.session.commit()
    assert build_profiles(SAT_6 + H)[point.id]["cells"][(5, 6)][0] == 10


# --- na danych z symulatora ---

def test_forecast_beats_naive_average(cache):
    import_points(cache)
    simulate(weeks=3)
    q = forecast_quality(hour_floor(DEMO_NOW))
    assert q["mae"] < q["naive_mae"]


def test_state_does_not_read_hidden_truth(cache):
    import_points(cache)
    simulate(weeks=2)
    before = point_states(DEMO_NOW)
    hour = hour_floor(DEMO_NOW)
    Forecast.query.filter_by(source="sim", at=hour).update({"level": 0})
    db.session.commit()
    assert point_states(DEMO_NOW) == before


def test_point_series_48h_back_and_24h_ahead(cache):
    import_points(cache)
    simulate(weeks=2)
    from app import clock
    from app.forecast import THRESHOLD, point_series
    from app.simulation import hour_floor
    clock.advance(0)  # utwórz zegar
    now = clock.now()
    series = point_series(Point.query.first(), now)
    assert len(series) == 48 + 1 + 24
    assert sum(at <= hour_floor(now) for at, *_ in series) == 49
    assert THRESHOLD == 85
