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


def _report(point, kind, resolved=False):
    from app import db
    from app.models import Press, Report
    now = clock.now()
    r = Report(point_id=point.id, first_at=now, last_at=now, weight=1.0, resolved_at=now if resolved else None)
    db.session.add(r)
    db.session.flush()
    db.session.add(Press(point_id=point.id, at=now, wall_at=now, kind=kind, ip="10.0.0.1", note="tajne", report_id=r.id))
    db.session.commit()
    return r


def test_open_data_csv_has_bom_source_and_no_personal_fields(client, demo):
    _report(Point.query.first(), "damaged")
    r = client.get("/api/v1/open-data/miesieczne.csv")
    text = r.get_data(as_text=True)
    assert r.headers["Access-Control-Allow-Origin"] == "*" and "max-age" in r.headers["Cache-Control"]
    assert text.startswith("﻿#") and "syntetyczne" in text.splitlines()[0].lower()
    lines = text.splitlines()
    assert lines[1] == "miesiac;dzielnica;frakcja;odbiory;masa_kg;zgloszenia"
    assert sum(int(l.split(";")[5]) for l in lines[2:]) >= 1
    assert "10.0.0.1" not in text and "tajne" not in text
    j = client.get("/api/v1/open-data/miesieczne.json").json
    assert j["meta"]["synthetic"] is True and set(j["rows"][0]) == set(lines[1].split(";"))


def test_open311_maps_status_and_service_code(client, demo):
    pts = Point.query.limit(3).all()
    a, b, c = _report(pts[0], "overflow"), _report(pts[1], None, resolved=True), _report(pts[2], "other")
    items = {i["service_request_id"]: i for i in client.get("/api/v1/open311/requests.json").json}
    assert items[f"TF-{a.id:05d}"]["service_code"] == "odpady_obok" and items[f"TF-{a.id:05d}"]["status"] == "open"
    assert items[f"TF-{b.id:05d}"]["service_code"] == "przepelniony" and items[f"TF-{b.id:05d}"]["status"] == "closed"
    assert items[f"TF-{c.id:05d}"]["service_code"] == "inne"
    one = items[f"TF-{a.id:05d}"]
    assert set(one) == {"service_request_id", "status", "service_code", "service_name", "requested_datetime",
                        "updated_datetime", "lat", "long", "address"}
    closed = client.get("/api/v1/open311/requests.json?status=closed").json
    assert closed and all(i["status"] == "closed" for i in closed)
    codes = [s["service_code"] for s in client.get("/api/v1/open311/services.json").json]
    assert codes == ["przepelniony", "odpady_obok", "uszkodzony", "inne"]


def test_open311_filters_validation(client, demo):
    for q in ("status=nowe", "start_date=wczoraj", "start_date=2026-10-05&end_date=2026-10-01"):
        r = client.get(f"/api/v1/open311/requests.json?{q}")
        assert r.status_code == 400 and r.json["kod"] == "zly_parametr" and r.json["blad"]
        assert r.headers["Access-Control-Allow-Origin"] == "*"
    day = clock.now().date().isoformat()
    assert client.get(f"/api/v1/open311/requests.json?start_date={day}&end_date={day}").status_code == 200


def test_docs_example_links_resolve(client, demo):
    spec = json.loads(client.get("/static/openapi.json").data)
    for path, ops in spec["paths"].items():
        if path.startswith("/api/v1/") and "{" not in path:
            assert client.get(path).status_code == 200, path
