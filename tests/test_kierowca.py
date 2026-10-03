import pytest

from app import clock
from app.models import Point, StopIssue
from app.osm_import import import_points
from app.state import point_states


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def test_stop_issue_flags_point_until_emptying(client, demo):
    pid = Point.query.filter_by(kind="bin").first().id
    r = client.post("/api/stop-issue", data={"point_id": pid, "kind": "no_access", "note": "auto na kopercie"})
    assert r.status_code == 200 and "nie da się podjechać" in r.json["message"]
    issue = point_states(clock.now())[pid]["crew_issue"]
    assert issue["kind"] == "no_access" and issue["note"] == "auto na kopercie"
    client.post("/api/clock/advance")
    assert client.post("/api/emptying", data={"point_id": pid, "level": 50}).status_code == 200
    assert point_states(clock.now())[pid]["crew_issue"] is None  # opróżnienie zamyka problem


def test_stop_issue_rejects_bad_input(client, demo):
    pid = Point.query.first().id
    assert client.post("/api/stop-issue", data={"point_id": pid, "kind": "rm -rf"}).status_code == 400
    assert client.post("/api/stop-issue", data={"point_id": 99999, "kind": "damaged"}).status_code == 404
    assert StopIssue.query.count() == 0


def test_reset_clears_stop_issues(client, demo):
    client.post("/api/stop-issue", data={"point_id": Point.query.first().id, "kind": "damaged"})
    clock.reset(weeks=2)
    assert StopIssue.query.count() == 0


def test_routes_stops_carry_level_and_state(client, demo):
    d = client.get("/api/routes").json
    assert d["now"]
    stops = [s for f in d["fleets"] for s in f["stops"]]
    assert stops and all({"level", "state", "fresh"} <= s.keys() for s in stops)


def test_driver_pwa_page_sw_and_manifest(client):
    html = client.get("/kierowca").get_data(as_text=True)
    assert "kierowca/manifest.webmanifest" in html and "kierowca.js" in html
    sw = client.get("/kierowca/sw.js")
    assert sw.headers["Service-Worker-Allowed"] == "/kierowca"
    m = client.get("/static/kierowca/manifest.webmanifest").get_json(force=True)
    assert m["scope"] == "/kierowca" and {"192x192", "512x512"} <= {i["sizes"] for i in m["icons"]}
    assert any(i["purpose"] == "maskable" for i in m["icons"])
