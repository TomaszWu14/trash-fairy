import json

import pytest

from app import clock
from app.models import Point
from app.osm_import import import_points


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def test_bins_geojson_is_public_and_marked_synthetic(client, demo):
    r = client.get("/api/v1/bins.geojson")
    d = r.json
    assert r.headers["Access-Control-Allow-Origin"] == "*" and d["meta"]["synthetic"] is True
    props = d["features"][0]["properties"]
    assert {"id", "kind", "name", "level", "state", "crossing", "next_run"} <= props.keys()
    assert not {"reliability", "check_reason", "misuse", "crew_issue", "reason"} & props.keys()


def test_bin_detail_has_future_forecast_and_404(client, demo):
    pid = Point.query.first().id
    d = client.get(f"/api/v1/bins/{pid}").json
    assert d["bin"]["id"] == pid and len(d["forecast"]) >= 20
    assert all(f["low"] <= f["level"] <= f["high"] for f in d["forecast"])
    miss = client.get("/api/v1/bins/99999")
    assert miss.status_code == 404 and miss.json["ok"] is False


def test_routes_and_conditions(client, demo):
    d = client.get("/api/v1/routes").json
    assert d["depot"]["name"] and {f["kind"] for f in d["fleets"]} == {"bin", "shelter"}
    c = client.get("/api/v1/conditions").json
    assert c["weather"] == {"available": False} and c["traffic"] == {"available": False}  # integracje wyłączone w testach


def test_docs_page_lists_every_path_from_contract(client):
    spec = json.loads(client.get("/static/openapi.json").data)
    assert spec["openapi"].startswith("3.1")
    html = client.get("/api/docs").get_data(as_text=True)
    assert all(path in html for path in spec["paths"])
    assert all(op["summary"] in html for ops in spec["paths"].values() for op in ops.values())
    assert "POST" in html and "/api/odczyty" in html  # nowe API aplikacji, nie tylko otwarte /api/v1
