from datetime import timedelta

import pytest

from app import clock, rate
from app.models import DemoClock, Point, Press
from app.osm_import import import_points
from tests.conftest import login


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def test_login_roles_and_bad_password(client):
    assert login(client, "dyspozytor", "zle").status_code == 400
    r = login(client, "driver_bin")
    assert r.status_code == 302 and r.headers["Location"].endswith("/kierowca")
    with client.session_transaction() as s:
        assert s["role"] == "driver" and s["fleet"] == "bin" and s.permanent
    client.post("/wyloguj")
    with client.session_transaction() as s:
        assert "role" not in s


def test_login_rate_limit_after_five_failures(client):
    for _ in range(5):
        login(client, "dyspozytor", "zle")
    r = login(client, "dyspozytor")  # dobre hasło, ale za dużo prób z tego IP
    assert r.status_code == 400 and "Za dużo" in r.get_data(as_text=True)


def test_login_disabled_without_password(app, client):
    app.config["DEMO_PASSWORD"] = ""
    assert "wyłączone" in login(client).get_data(as_text=True)


def test_dispatcher_only_endpoints(client, demo):
    for url in ("/api/clock/reset", "/api/fairy", "/api/photo"):
        assert client.post(url).status_code == 401, url
    login(client, "driver_bin")
    assert client.post("/api/clock/reset").status_code == 403
    assert client.post("/api/clock/advance").status_code == 200  # Przewiń jest publiczne (decyzja 4)


def test_driver_only_own_fleet(client, demo):
    bin_id = Point.query.filter_by(kind="bin").first().id
    shelter_id = Point.query.filter_by(kind="shelter").first().id
    assert client.post("/api/emptying", data={"point_id": bin_id, "level": 50}).status_code == 401
    login(client, "driver_bin")
    assert client.post("/api/emptying", data={"point_id": bin_id, "level": 50}).status_code == 200
    r = client.post("/api/stop-issue", data={"point_id": shelter_id, "kind": "no_access"})
    assert r.status_code == 403 and "floty" in r.json["message"]
    kurs = client.get("/api/kierowca/kurs").json
    assert kurs["fleet"]["kind"] == "bin" and "geometry" in kurs["fleet"]


def test_public_view_hides_dispatcher_fields(client, demo):
    hidden = {"reliability", "check_reason", "misuse", "crew_issue", "photo_note", "photo_error"}
    pid = Point.query.first().id
    for props in [f["properties"] for f in client.get("/api/changes").json["features"]] + [client.get(f"/api/points/{pid}").json]:
        assert not hidden & props.keys()
    login(client)
    assert "reliability" in client.get("/api/changes").json["features"][0]["properties"]


def test_rate_counter_is_shared_and_limited(app):
    assert all(rate.hit("t", 3, 3600) for _ in range(3))
    assert not rate.hit("t", 3, 3600) and rate.count("t", 3600) == 3


def test_auto_reset_after_idle(client, demo):
    client.post("/api/clock/advance")
    c = DemoClock.query.get(1)
    assert c.now > clock.DEMO_NOW and c.last_activity is not None
    assert not clock.maybe_auto_reset()  # świeża aktywność: bez resetu
    c.last_activity -= clock.IDLE + timedelta(minutes=1)
    from app import db
    db.session.commit()
    client.get("/api/changes")
    assert clock.now() == clock.DEMO_NOW and DemoClock.query.get(1).last_activity is None
    assert Press.query.filter(Press.wall_at.isnot(None)).count() == 0


def test_epaper_png_etag_304(client, demo):
    pid = Point.query.first().id
    first = client.get(f"/epapier/{pid}.png")
    again = client.get(f"/epapier/{pid}.png", headers={"If-None-Match": first.headers["ETag"]})
    assert first.status_code == 200 and again.status_code == 304
