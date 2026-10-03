from unittest.mock import patch

import pytest

from app import api, clock
from app.models import Point
from app.osm_import import import_points


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def press(client, point_id, ip="10.0.0.1"):
    return client.post("/api/press", json={"point_id": point_id}, environ_base={"REMOTE_ADDR": ip})


def props(client, point_id):
    fc = client.get("/api/points").json
    return next(f["properties"] for f in fc["features"] if f["properties"]["id"] == point_id)


def test_main_path_press_turns_point_red_and_top_of_list(client, demo):
    """Test 10 z sekcji 11: naciśnięcie → stan → punkt do opróżnienia."""
    from app.state import neighbors_map
    lonely = {pid for pid, n in neighbors_map().items() if not n}  # bez sąsiadów w 100 m → bez kary za puste otoczenie
    calm = min((f["properties"] for f in client.get("/api/points").json["features"]
                if f["properties"]["state"] == "ok" and f["properties"]["reliability"] >= 70
                and f["properties"]["id"] in lonely),
               key=lambda p: p["value"])
    r = press(client, calm["id"])
    assert r.status_code == 200 and r.json["message"] == "Wróżka już leci!"
    p = props(client, calm["id"])
    assert p["state"] == "bad" and p["fresh"]
    summary = client.get("/api/points").json["summary"]
    assert summary["live_presses"] == 1 and summary["live_reports"] == 1


def test_presses_from_many_people_merge_into_one_report(client, demo):
    pid = Point.query.filter_by(kind="bin").first().id
    for i in range(5):
        assert press(client, pid, ip=f"10.0.0.{i + 10}").status_code == 200
    s = client.get("/api/points").json["summary"]
    assert s["live_presses"] == 5
    assert s["live_reports"] <= 1  # 0, jeśli dołączyły do zgłoszenia z symulacji sprzed 15 min


def test_rate_limit_same_point_and_hourly(client, demo):
    pid = Point.query.first().id
    assert press(client, pid).status_code == 200
    assert press(client, pid).status_code == 429  # ten sam punkt w ciągu 2 s
    with patch.object(api, "PER_IP_HOUR", 1):
        assert press(client, pid + 1).status_code == 429


def test_press_unknown_point_is_404(client, demo):
    assert client.post("/api/press", json={"point_id": 99999}).status_code == 404
    assert client.post("/api/press", json={"point_id": "abc"}).status_code == 404


def test_changes_only_when_version_moves(client, demo):
    v = client.get("/api/points").json["version"]
    assert client.get(f"/api/changes?since={v}").json == {"changed": False}
    press(client, Point.query.first().id)
    assert client.get(f"/api/changes?since={v}").json["changed"] is True


def test_clock_endpoints(client, demo):
    data = client.post("/api/clock/advance").json
    assert data["clock"]["label"].endswith("14:30")
    press(client, Point.query.first().id)
    data = client.post("/api/clock/reset").json
    assert data["clock"]["label"].endswith("13:30")
    assert data["summary"]["live_presses"] == 0


def test_button_page(client, demo):
    r = client.get(f"/przycisk/{Point.query.first().id}")
    assert r.status_code == 200 and "PEŁNY?" in r.get_data(as_text=True)
    assert client.get("/przycisk/99999").status_code == 404
