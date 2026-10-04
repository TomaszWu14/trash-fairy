"""Zgłoszenie mieszkańca (POST /api/zgloszenia) i reguły stanu dla rodzajów zgłoszeń."""
from datetime import UTC, datetime

import pytest

from app import clock, db
from app.api_pl import qr_token
from app.models import Point, Press
from app.osm_import import import_points
from app.state import point_states


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def report(client, p, klient="t1", **extra):
    body = {"kosz": p.id, "typ": "przepelniony", "qr": qr_token(p.id), "lat": p.lat, "lon": p.lon, "klient": klient, **extra}
    return client.post("/api/zgloszenia", json=body)


def a_bin():
    return Point.query.filter_by(kind="bin").first()


def test_reports_from_two_phones_merge(client, demo):
    p = a_bin()
    a = report(client, p, klient="a")
    assert a.status_code == 201
    b = report(client, p, klient="b")
    assert b.status_code == 201 and b.json["dolaczone"] and b.json["numer"] == a.json["numer"]
    assert Press.query.filter_by(point_id=p.id, kind="full").count() == 2


def test_report_gate_is_bin_token_not_location(client, demo):
    p = a_bin()
    far = report(client, p, klient="a", lat=p.lat + 0.0036)  # ~400 m: położenia nie sprawdzamy, ważny token wystarcza
    assert far.status_code == 201, far.json
    other_bin = report(client, p, klient="b", qr=qr_token(p.id + 1))  # kod z innego kosza nie przechodzi
    assert other_bin.status_code == 403 and other_bin.json["kod"] == "brak_skanu_qr"


def test_overflow_counts_as_full_and_is_noted(client, demo):
    p = a_bin()
    assert report(client, p, typ="odpady_obok").status_code == 201
    s = point_states(clock.now())[p.id]
    assert s["fresh"] and s["overflow_reported"]


def test_damaged_press_does_not_raise_level_but_flags_point(demo):
    from app.state import neighbors_map
    lonely = {pid for pid, n in neighbors_map().items() if not n}
    states = point_states(clock.now())
    pid = min((pid for pid, s in states.items() if s["state"] == "ok" and pid in lonely), key=lambda i: states[i]["value"])
    db.session.add(Press(point_id=pid, at=clock.now(), wall_at=datetime.now(UTC).replace(tzinfo=None), source="qr", kind="damaged"))
    db.session.commit()
    s = point_states(clock.now())[pid]
    assert s["state"] == "ok" and not s["fresh"] and s["damaged_at"]


def test_404_is_polish_html_and_api_stays_json(client):
    page = client.get("/nie-ma-takiej-strony")
    assert page.status_code == 404 and "lang=\"pl\"" in page.get_data(as_text=True)
    api_r = client.get("/api/nie-ma")
    assert api_r.status_code == 404 and set(api_r.json) == {"blad", "kod"}
