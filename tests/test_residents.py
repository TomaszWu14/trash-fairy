from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app import clock, db, residents
from app.models import Device, Emptying, Point, PointAward, Press, Report, Resident
from app.osm_import import import_points
from app.reports import record_press, resolve_reports
from app.simulation import DEMO_NOW
from app.state import effective_weight, troll_pattern

T0 = datetime(2026, 10, 3, 13, 30)


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=1)


def make_resident(nick="Ania", phone="600100200", district="Stare Miasto"):
    r = residents.register(nick, phone, district)
    residents.verify(r, r.code)
    return r


def a_bin():
    return Point.query.filter_by(kind="bin", area="Rynek").order_by(Point.id).first()


# --- rejestracja ---

def test_one_account_per_phone_and_phone_stored_as_hash(demo):
    r = make_resident(phone="+48 600-100-200")
    assert "600100200" not in r.phone_hash and len(r.phone_hash) == 64
    with pytest.raises(residents.RegistrationError, match="jedno konto"):
        residents.register("Inny", "600 100 200", "Kazimierz")


def test_verification_code_required(demo):
    r = residents.register("Bob", "600100201", "Kazimierz")
    assert not residents.verify(r, "000000" if r.code != "000000" else "111111")
    assert residents.verify(r, r.code) and r.verified


# --- potwierdzenia i wagi ---

def test_registered_press_confirms_anonymous_report_and_raises_weight(demo):
    p, r = a_bin(), make_resident()
    report = record_press(p.id, T0)
    anonymous_weight = report.weight
    report = record_press(p.id, T0 + timedelta(minutes=3), resident_id=r.id)
    assert report.confirmed and report.weight >= max(anonymous_weight, residents.START_RELIABILITY)
    assert Press.query.filter_by(report_id=report.id).count() == 2


def test_own_repeated_press_does_not_confirm(demo):
    p, r = a_bin(), make_resident()
    record_press(p.id, T0, resident_id=r.id)
    assert not record_press(p.id, T0 + timedelta(minutes=1), resident_id=r.id).confirmed


def test_resident_reliability_from_resolved_reports(demo):
    p, r = a_bin(), make_resident()
    for i, level in enumerate([100, 25, 25, 25]):
        at = T0 - timedelta(days=4 - i)
        record_press(p.id, at, resident_id=r.id)
        resolve_reports(Emptying(point_id=p.id, at=at + timedelta(hours=1), level=level))
    db.session.commit()
    assert residents.resident_reliability(r.id) == pytest.approx(0.25)


def test_neighbors_empty_weakens_only_unconfirmed():
    report = SimpleNamespace(weight=1.0, confirmed=False, first_at=T0)
    assert effective_weight(report, [], [10, 20])[0] == pytest.approx(0.7)
    assert effective_weight(report, [], [10, 50])[0] == 1.0
    report.confirmed = True
    assert effective_weight(report, [], [10, 20]) == (1.0, ["potwierdzone przez mieszkańca"])


def test_troll_pattern_same_hour_false_reports():
    false_at_14 = [(T0.replace(hour=14) - timedelta(days=d), False) for d in (1, 2, 3)]
    assert troll_pattern(false_at_14, T0.replace(hour=15))
    assert not troll_pattern(false_at_14, T0.replace(hour=9))
    assert not troll_pattern(false_at_14[:2], T0.replace(hour=14))


# --- punkty ---

def test_points_only_for_hits_and_once_per_point_per_day(demo):
    p, r = a_bin(), make_resident()
    record_press(p.id, T0, resident_id=r.id)
    resolve_reports(Emptying(point_id=p.id, at=T0 + timedelta(minutes=20), level=25))  # fałszywe
    record_press(p.id, T0 + timedelta(hours=1), resident_id=r.id)
    resolve_reports(Emptying(point_id=p.id, at=T0 + timedelta(hours=2), level=100))  # trafne
    record_press(p.id, T0 + timedelta(hours=3), resident_id=r.id)
    resolve_reports(Emptying(point_id=p.id, at=T0 + timedelta(hours=4), level=100))  # trafne, ten sam dzień
    db.session.commit()
    awards = PointAward.query.filter_by(resident_id=r.id).all()
    assert [a.points for a in awards] == [residents.POINTS["bin"]]


def test_anonymous_presses_earn_nothing(demo):
    p = a_bin()
    record_press(p.id, T0)
    resolve_reports(Emptying(point_id=p.id, at=T0 + timedelta(minutes=20), level=100))
    db.session.commit()
    assert PointAward.query.filter_by(point_id=p.id, report_id=Report.query.order_by(Report.id.desc()).first().id).count() == 0


def test_rankings_and_badges(demo):
    rk = residents.rankings()
    assert rk["members"] == len(residents.DEMO_NICKS)
    assert rk["people"] == sorted(rk["people"], key=lambda x: -x["points"])
    r = Resident.query.filter_by(source="demo").first()
    assert residents.profile(r)["badges"][0]["name"] == "Pierwsze trafienie"


# --- urządzenia ---

def test_selftest_does_not_create_press_or_report(demo):
    p = a_bin()
    before = (Press.query.count(), Report.query.count())
    assert residents.selftest(p.id, clock.now()) is not None
    assert residents.selftest(99999, clock.now()) is None
    assert (Press.query.count(), Report.query.count()) == before
    assert db.session.get(Device, p.id).last_selftest == clock.now()


def test_device_without_heartbeat_48h_flagged(demo):
    from app.state import point_states
    p = a_bin()
    db.session.get(Device, p.id).last_heartbeat = DEMO_NOW - timedelta(hours=49)
    db.session.commit()
    s = point_states(clock.now())[p.id]
    assert s["check_button"] and "brak sygnału" in s["check_reason"]
    assert any(d["point_id"] == p.id for d in residents.devices_overview(clock.now())["offline"])
