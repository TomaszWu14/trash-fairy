from datetime import datetime, timedelta

import pytest

from app import clock, db
from app.models import Emptying, Forecast, Point, Report
from app.reports import low_reliability, record_press, reliability, resolve_reports
from app.simulation import DEMO_NOW
from app.state import level_state, point_states

T0 = datetime(2026, 10, 3, 13, 30)


@pytest.fixture
def point():
    p = Point(osm_id="node/1", kind="bin", area="Rynek", lat=50.06, lon=19.93, name="Kosz testowy", base_rate=2)
    db.session.add(p)
    db.session.commit()
    return p


def set_level(point, at, level):
    db.session.add(Forecast(point_id=point.id, at=at.replace(minute=0), level=level, source="sim"))
    db.session.commit()


# --- test 2 z sekcji 11: scalanie ---

def test_30_presses_in_15_minutes_make_one_report(point):
    for i in range(30):
        record_press(point.id, T0 + timedelta(seconds=29 * i))  # ostatnie po 14 min 1 s
    assert Report.query.count() == 1
    assert Report.query.one().presses == 30


def test_press_after_15_minutes_from_first_starts_new_report(point):
    record_press(point.id, T0)
    record_press(point.id, T0 + timedelta(minutes=10))
    record_press(point.id, T0 + timedelta(minutes=16))  # okno liczone od pierwszego naciśnięcia
    assert Report.query.count() == 2


# --- test 3 z sekcji 11: wiarygodność i flaga ---

def test_reliability_last_10_and_default():
    assert reliability([]) == 0.7
    assert reliability([False] * 7 + [True] * 3) == pytest.approx(0.3)
    assert reliability([False] * 5 + [True] * 10) == 1.0  # liczy się tylko ostatnie 10


def test_7_false_of_10_gives_30_percent_and_flag():
    resolved = [(T0 - timedelta(hours=10 * i), i < 3) for i in range(10)]
    assert reliability([hit for _, hit in sorted(resolved)]) == pytest.approx(0.3)
    assert low_reliability(resolved, T0)


def test_no_flag_for_old_or_few_reports():
    assert not low_reliability([(T0 - timedelta(days=8), False)] * 10, T0)  # starsze niż 7 dni
    assert not low_reliability([(T0, False)] * 2, T0)  # za mało zgłoszeń


def test_emptying_resolves_reports_and_new_report_uses_reliability(point):
    for i in range(10):
        at = T0 - timedelta(days=5) + timedelta(hours=8 * i)
        record_press(point.id, at)
        resolve_reports(Emptying(point_id=point.id, at=at + timedelta(hours=1), level=100 if i < 3 else 25))
    db.session.commit()
    assert Report.query.filter_by(hit=True).count() == 3
    assert record_press(point.id, T0).weight == pytest.approx(0.3)


# --- test 4 z sekcji 11: progi stanu ---

def test_level_state_thresholds():
    assert level_state(59.9) == "ok"
    assert level_state(60) == "warn"
    assert level_state(85) == "warn"
    assert level_state(85.1) == "bad"
    assert level_state(10, fresh_strong_report=True) == "bad"


def test_fresh_report_turns_point_red_with_reason(point):
    set_level(point, T0, 20)
    record_press(point.id, T0)
    s = point_states(T0)[point.id]
    assert s["state"] == "bad" and s["fresh"]
    assert "zgłoszenie" in s["reason"]
    # po 20 min zgłoszenie nie jest już świeże: zostaje sygnał 100 × 0,7 = 70% → żółty
    later = point_states(T0 + timedelta(minutes=20))[point.id]
    assert not later["fresh"] and later["state"] == "warn" and later["value"] == 70


def test_report_right_after_emptying_at_low_level_is_weak(point):
    db.session.add(Emptying(point_id=point.id, at=T0 - timedelta(minutes=30), level=75))
    set_level(point, T0, 5)
    record_press(point.id, T0)
    s = point_states(T0)[point.id]
    assert s["value"] == 35 and s["state"] == "ok"
    assert "słaby sygnał" in s["reason"]


def test_emptying_clears_report_signal(point):
    set_level(point, T0, 20)
    record_press(point.id, T0)
    resolve_reports(Emptying(point_id=point.id, at=T0 + timedelta(minutes=5), level=25))
    db.session.commit()
    s = point_states(T0 + timedelta(minutes=6))[point.id]
    assert s["state"] == "ok" and s["reason"] == "poziom 20%"
    assert Report.query.one().hit is False


def test_long_overflow_without_presses_flags_button(point):
    for h in range(6):
        set_level(point, T0 - timedelta(hours=h), 110)
    s = point_states(T0)[point.id]
    assert s["check_button"] and "nikt nie nacisnął" in s["check_reason"]
    record_press(point.id, T0 - timedelta(hours=2))
    assert not point_states(T0)[point.id]["check_button"]


# --- zegar demo ---

def test_clock_advance_resolves_reports_on_scheduled_emptying(point):
    clock.reset(weeks=1)
    db.session.query(Report).delete()
    db.session.query(Emptying).delete()
    db.session.add(Emptying(point_id=point.id, at=datetime(2026, 10, 3, 14), level=100))
    db.session.commit()
    record_press(point.id, clock.now())
    assert clock.advance(1) == DEMO_NOW + timedelta(hours=1)
    assert Report.query.one().hit is True


def test_clock_cannot_go_past_simulation(point):
    clock.reset(weeks=1)
    for _ in range(30):
        clock.advance(1)
    assert clock.now() == clock.MAX_NOW

