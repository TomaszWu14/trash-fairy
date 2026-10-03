"""Publiczny ekran „Zgłoś kosz”: dane bez wiarygodności, stany odpowiedzi API, /jury na nowy ekran."""
from unittest.mock import patch

import pytest

from app import api, clock
from app.models import Point, Press
from app.osm_import import import_points


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def press(client, pid, ip="10.0.0.1", **extra):
    return client.post("/api/press", json={"point_id": pid, "source": "qr", "kind": "full", **extra}, environ_base={"REMOTE_ADDR": ip})


def test_public_bin_has_no_internal_fields(client, demo):
    pid = Point.query.filter_by(kind="bin").first().id
    d = client.get(f"/api/zglos/{pid}").json
    assert {"name", "address", "fill_pct", "next_pickup", "neighbors", "button_offline", "clock_label"} <= d.keys()
    assert "reliability" not in d and "reason" not in d
    assert all(n["distance_m"] <= api.NEIGHBOR_PUBLIC_M for n in d["neighbors"])


def test_report_screen_and_jury_redirect(client, demo):
    pid = Point.query.filter_by(kind="bin").first().id
    html = client.get(f"/zglos/{pid}").get_data(as_text=True)
    assert 'id="sheet"' in html and "manifest.webmanifest" in html
    assert client.get("/zglos").status_code == 200
    r = client.get("/jury")
    assert r.status_code == 302 and "/zglos/" in r.headers["Location"]


def test_press_returns_accepted_then_merged(client, demo):
    pid = Point.query.filter_by(kind="bin").first().id
    a = press(client, pid, ip="10.0.0.1").json
    assert a["ok"] and a["status"] in ("accepted", "merged") and a["eta"] and a["accepted_at"]
    b = press(client, pid, ip="10.0.0.2").json
    assert b["status"] == "merged" and b["merged_with_at"] == a["accepted_at"] and b["others_count"] >= 1
    assert Press.query.filter_by(point_id=pid, kind="full").count() == 2


def test_press_too_far_and_limit_payloads(client, demo):
    p = Point.query.filter_by(kind="bin").first()
    far = press(client, p.id, lat=p.lat + 0.01, lon=p.lon)
    assert far.status_code == 403 and far.json["reason"] == "too_far" and far.json["distance_m"] > 150
    assert press(client, p.id).status_code == 200
    again = press(client, p.id)  # ten sam punkt w ciągu 2 s
    assert again.status_code == 429 and len(again.json["retry_at"]) == 5


def test_status_endpoint(client, demo):
    pid = Point.query.filter_by(kind="bin").first().id
    rid = press(client, pid).json["report_id"]
    st = client.get(f"/api/zglos/status/{rid}").json
    assert st["accepted_at"] and st["emptied_at"] is None and "run_label" in st


def test_damaged_does_not_raise_level_but_flags_point(client, demo):
    from app.state import neighbors_map
    lonely = {pid for pid, n in neighbors_map().items() if not n}
    calm = min((f["properties"] for f in client.get("/api/points").json["features"]
                if f["properties"]["state"] == "ok" and f["properties"]["id"] in lonely), key=lambda p: p["value"])
    r = press(client, calm["id"], kind="damaged")
    assert r.status_code == 200 and r.json["status"] == "accepted" and r.json["report_id"] is None
    p = next(f["properties"] for f in client.get("/api/points").json["features"] if f["properties"]["id"] == calm["id"])
    assert p["state"] == "ok" and not p["fresh"] and p["damaged_at"]


def test_overflow_counts_as_full_and_is_noted(client, demo):
    pid = Point.query.filter_by(kind="bin").first().id
    assert press(client, pid, kind="overflow").json["ok"]
    p = next(f["properties"] for f in client.get("/api/points").json["features"] if f["properties"]["id"] == pid)
    assert p["fresh"] and p["overflow_reported"]


def test_nosignal_flag_and_member_in_public_payload(client, demo):
    from datetime import timedelta
    from app import db
    from app.models import Device, Resident
    from app.residents import HEARTBEAT_LOST
    pid = Point.query.filter_by(kind="bin").first().id
    dev = Device.query.filter_by(point_id=pid).first()
    if dev is None:
        dev = Device(point_id=pid, last_heartbeat=clock.now(), battery=80, last_selftest=clock.now())
        db.session.add(dev)
    dev.last_heartbeat = clock.now() - HEARTBEAT_LOST - timedelta(hours=1)
    db.session.commit()
    assert client.get(f"/api/zglos/{pid}").json["button_offline"] is True
    res = Resident(nick="Smok", phone_hash="x" * 64, district="Stare Miasto", verified=True)
    db.session.add(res)
    db.session.commit()
    with client.session_transaction() as sess:
        sess["resident_id"] = res.id
    assert client.get(f"/api/zglos/{pid}").json["member"] == {"nick": "Smok", "district": "Stare Miasto"}


def test_service_worker_scope_and_manifest(client):
    r = client.get("/zglos/sw.js")
    assert r.status_code == 200 and r.headers["Service-Worker-Allowed"] == "/zglos"
    m = client.get("/static/zglos/manifest.webmanifest").json
    assert m["start_url"] == "/zglos" and m["display"] == "standalone" and m["theme_color"] == "#0E1222"
