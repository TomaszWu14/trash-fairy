import time

import pytest

from app import clock, http, traffic
from app.osm_import import import_points
from tests.fakes import FakeOpener

# kształt odpowiedzi flowSegmentData z TomTom Traffic Flow v4
SEG = {"flowSegmentData": {"frc": "FRC2", "currentSpeed": 20, "freeFlowSpeed": 40, "currentTravelTime": 90,
                           "freeFlowTravelTime": 45, "confidence": 0.95, "roadClosure": False,
                           "coordinates": {"coordinate": [{"latitude": 50.06, "longitude": 19.92}]}}}


@pytest.fixture
def live(app, monkeypatch, tmp_path):
    app.config["TOMTOM_API_KEY"] = "test-key"
    monkeypatch.setattr(traffic, "CACHE_FILE", tmp_path / "traffic.json")
    monkeypatch.setattr(traffic, "_state", {"data": None, "next_try": 0.0})

    def use(routes):
        fake = FakeOpener(routes)
        monkeypatch.setattr(http, "opener", fake)
        return fake
    return use


def test_ratio_rule():
    assert traffic.ratio({"currentSpeed": 20, "freeFlowSpeed": 40}) == 2.0
    assert traffic.ratio({"currentSpeed": 50, "freeFlowSpeed": 40}) == 1.0     # szybciej niż swobodnie: bez korka
    assert traffic.ratio({"currentSpeed": 5, "freeFlowSpeed": 40}) == 3.0      # przycięte do 3,0
    assert traffic.ratio({"currentSpeed": 30, "freeFlowSpeed": 40, "roadClosure": True}) == 3.0


def test_all_samples_and_time_only_effect(live):
    fake = live({"tomtom.com": (200, SEG)})
    assert traffic.city_ratio() == 2.0 and len(fake.requests) == len(traffic.SAMPLES)
    assert "key=test-key" in fake.requests[0].full_url
    assert traffic.drive_min(20, 2.0) == 2 * traffic.drive_min(20) and traffic.delay_min(2.0) == 18
    traffic.city_ratio()
    assert len(fake.requests) == len(traffic.SAMPLES)  # kolejne odświeżenie najwcześniej za 10 min


def test_first_error_stops_series(live):
    fake = live({"tomtom.com": (403, {"error": "Developer Inactive"})})
    assert traffic.city_ratio() is None and len(fake.requests) == 1


def test_stale_measurements_ignored(live):
    live({"tomtom.com": (200, SEG)})
    traffic.data()
    for s in traffic._state["data"]["samples"]:
        s["measured_at"] = time.time() - traffic.MAX_AGE_S - 1
    assert traffic.city_ratio() is None and traffic.conditions() == {"available": False}


def test_routes_keep_points_and_km_but_eta_moves(client, app, live, cache):
    import_points(cache)
    clock.reset(weeks=2)
    app.config["TOMTOM_API_KEY"] = ""
    calm = client.get("/api/routes").json
    app.config["TOMTOM_API_KEY"] = "test-key"
    live({"tomtom.com": (200, SEG)})
    jam = client.get("/api/routes").json
    for a, b in zip(calm["fleets"], jam["fleets"]):
        assert [s["id"] for s in a["stops"]] == [s["id"] for s in b["stops"]] and a["km"] == b["km"]
        assert b["drive_min"] == traffic.drive_min(a["km"], 2.0) and a["drive_min"] == traffic.drive_min(a["km"])
    assert jam["traffic"] == {"ratio": 2.0, "delay_min": 18} and calm["traffic"] is None
    pid = jam["fleets"][0]["stops"][0]["id"]
    assert client.get(f"/api/zglos/{pid}").json["traffic_delay_min"] == 18
