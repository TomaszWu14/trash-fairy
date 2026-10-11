"""Strażnicy poprawek z docs/07-ograniczenia.md: obsługa błędów i walidacja zamiast 500, jedna nagroda dziennie,
idempotentne „Jadę”, cache dashboardu widzi wysypiska."""
import json
from datetime import timedelta
from pathlib import Path

import pytest

from app import clock, db, methodology, photos, residents, state, wysypiska
from app.devices_api import device_token
from app.events import import_events
from app.models import Device, DeviceInfo, DumpReport, Emptying, Event, Point, PointAward, Project, StopIssue
from app.osm_import import import_city_points, import_points
from app.reports import record_press, resolve_reports

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def demo(cache):
    import_points(cache)
    import_city_points()
    clock.reset(weeks=1)


def a_bin():
    return Point.query.filter_by(kind="bin", live=True).order_by(Point.id).first()


def test_one_award_per_day_counts_the_day_it_is_saved(demo):
    """Zgłoszenie z 23:50 rozstrzygnięte o 6:00 następnego dnia: sprawdzenie i zapis nagrody patrzą na ten sam dzień."""
    p = a_bin()
    r = residents.register("Nocny", "600100300", "Stare Miasto")
    residents.verify(r, r.code)
    night = clock.now().replace(hour=23, minute=50) - timedelta(days=2)
    morning = night + timedelta(hours=6, minutes=10)
    db.session.add(PointAward(resident_id=r.id, point_id=p.id, at=morning - timedelta(hours=1), points=10, kind="bin"))
    record_press(p.id, night, resident_id=r.id)
    resolve_reports(Emptying(point_id=p.id, at=morning, level=100))
    db.session.commit()
    assert PointAward.query.filter_by(resident_id=r.id).count() == 1  # nagroda z tego dnia już była


def test_out_of_range_ids_and_city_points_give_404_not_500(demo, client):
    city = Point.query.filter_by(live=False).first()
    for url in ("/epapier/99999999999.png", f"/epapier/{city.id}.png", "/api/v1/bins/99999999999",
                "/api/urzadzenia/99999999999"):
        assert client.get(url).status_code == 404, url


def test_non_ascii_device_token_is_401(demo, client):
    info = DeviceInfo.query.filter_by(kind="czujnik").first()
    res = client.post("/api/odczyty", json={"numer_seryjny": info.serial, "zapelnienie": 10},
                      headers={"X-Token-Urzadzenia": "żółw".encode().decode("latin-1")})
    assert res.status_code == 401


def test_panel_without_device_row_and_sensor_without_reading(demo, client):
    panel = DeviceInfo.query.filter_by(kind="panel").first()
    db.session.delete(db.session.get(Device, panel.point_id))
    sensor = DeviceInfo.query.filter_by(kind="czujnik").first()
    sensor.last_seen = None
    db.session.commit()
    assert client.get("/api/urzadzenia").status_code == 200
    assert client.get(f"/api/urzadzenia/{sensor.point_id}").json["urzadzenie"]["online"] is False
    res = client.post("/api/odczyty", json={"numer_seryjny": panel.serial, "bateria": 80},
                      headers={"X-Token-Urzadzenia": device_token(panel.serial)})
    assert res.status_code == 201 and db.session.get(Device, panel.point_id).battery == 80


def test_city_scale_on_empty_comparison_is_zero_not_error():
    empty = {"visits": 0, "km": 0}
    out = methodology.city_scale({"fixed": {"bin": empty}, "fairy": {"bin": empty}})
    assert out["visit_cut_pct"] == 0 and out["full"]["pln_year"] == 0


def test_unknown_project_status_does_not_break_dashboard(demo, client):
    pr = Project.query.first()
    pr.status = "wstrzymany"
    db.session.commit()
    res = client.get(f"/api/projekty/{pr.slug}")
    assert res.status_code == 200 and (res.json.get("projekt") or res.json)["status_etykieta"] == "wstrzymany"


def test_bad_event_rows_are_skipped(app, tmp_path):
    ok = {"name": "Koncert", "venue": "Rynek", "lat": 50.06, "lon": 19.94, "scale": "medium",
          "start": "2026-10-03T18:00", "end": "2026-10-03T22:00"}
    bad = [ok | {"scale": "gigantyczny"}, ok | {"end": "2026-10-03T17:00"}, {"name": "bez pól"}, ok | {"lat": "x"}]
    f = tmp_path / "events.json"
    f.write_text(json.dumps([ok, *bad]), encoding="utf-8")
    import_events(f)
    assert Event.query.filter_by(source="manual").count() == 1


def test_background_analysis_of_deleted_row_does_nothing(app):
    assert photos.analyze(987654) is None
    assert wysypiska.analyze(987654) is None


def test_second_jade_adds_nothing(demo, client):
    p = a_bin()
    for _ in range(2):
        assert client.post("/api/odbiory", json={"kosz": p.id, "akcja": "jade"}).status_code == 201
    assert StopIssue.query.filter_by(point_id=p.id, kind="jade").count() == 1


def test_dashboard_cache_sees_new_dump_report(demo):
    before = state.side_version()
    db.session.add(DumpReport(at=clock.now(), wall_at=clock.now(), lat=50.06, lon=19.94, kinds=["bio"]))
    db.session.commit()
    assert state.side_version() != before


def test_project_page_handles_the_api_error_code(demo, client):
    code = client.get("/api/projekty/nie-ma-takiego").json["kod"]
    assert f"'{code}'" in (ROOT / "app/static/ui/projekt.js").read_text(encoding="utf-8")


def test_karnet_command_reports_network_error(app, monkeypatch):
    from app import karnet

    def offline(*_a, **_k):
        raise OSError("brak sieci")
    monkeypatch.setattr(karnet, "fetch", offline)
    res = app.test_cli_runner().invoke(args=["karnet"])
    assert res.exit_code == 1 and "Karnet nie odpowiada" in res.output
