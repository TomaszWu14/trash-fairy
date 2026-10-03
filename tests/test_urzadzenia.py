"""Urządzenia na koszach: reguły baterii i statusu, seed deterministyczny, API z filtrami i błędami."""
from datetime import datetime, timedelta

import pytest

from app import clock, create_app, db, devices, forecast, comparison, state
from app.events import import_events
from app.models import DeviceInfo
from app.osm_import import import_city_points, import_points, load_cache
from app.simulation import DEMO_NOW

CONFIG = {"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True, "OSRM_URL": "", "WEATHER_URL": "",
          "TOMTOM_API_KEY": "", "TWILIO_ACCOUNT_SID": "", "TWILIO_AUTH_TOKEN": "", "TWILIO_VERIFY_SID": "",
          "SMS_DEMO_FALLBACK": "1"}


@pytest.fixture(scope="module")
def app():
    for m in (forecast, comparison, state):
        m.clear_cache()
    app = create_app(CONFIG)
    with app.app_context():
        import_points(load_cache())
        import_events()
        import_city_points()
        clock.reset()
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_battery_and_days_left_rules():
    t0 = datetime(2026, 7, 1)
    assert devices.sensor_battery(t0, t0, 1.0, 730) == 100
    assert devices.sensor_battery(t0, t0 + timedelta(days=365), 1.0, 730) == 50
    assert devices.sensor_battery(t0, t0 + timedelta(days=100), 10.0, 730) == 0  # nigdy ujemna
    assert devices.days_left(50, 730) == 365
    assert devices.days_left(20, 730, 6.2) == 23
    assert devices.days_left(0, 365) == 0


@pytest.mark.parametrize("battery,left,online,selftest,expected", [
    (90, 300, True, True, "ok"),
    (40, 30, True, True, "wymiana_30"),
    (40, 31, True, True, "ok"),
    (14, 5, True, True, "bateria_krytyczna"),
    (15, 5, True, True, "wymiana_30"),
    (90, 300, True, False, "autotest"),
    (5, 1, False, False, "brak_sygnalu"),  # brak sygnału ma pierwszeństwo
])
def test_status_thresholds(battery, left, online, selftest, expected):
    assert devices.status(battery, left, online, selftest) == expected


def test_seed_is_deterministic_and_covers_both_kinds():
    snap = lambda: sorted((i.point_id, i.kind, i.serial, i.installed_at, i.firmware, round(i.drain, 6), i.last_seen)
                          for i in DeviceInfo.query)
    first = snap()
    devices.seed_demo(DEMO_NOW)
    assert snap() == first
    kinds = {k for _, k, *_ in first}
    assert kinds == {"panel", "czujnik"}
    assert all(s.startswith("TF-EP-") if k == "panel" else s.startswith("TF-US-") for _, k, s, *_ in first)
    sensors = DeviceInfo.query.filter_by(kind="czujnik").all()
    assert sensors and all(datetime(2026, 7, 1) <= s.installed_at < datetime(2026, 8, 1) for s in sensors)


def test_list_kpi_and_urgency_order(client):
    d = client.get("/api/urzadzenia").get_json()
    assert d["meta"]["syntetyczne"] is True
    items, k = d["urzadzenia"], d["kpi"]
    assert k["lacznie"] == len(items) == sum(k["wg_typu"].values())
    assert k["aktywne"] + k["bez_sygnalu"] == k["lacznie"]
    ranks = [devices.STATUS[i["status"]][1] for i in items]
    assert ranks == sorted(ranks) and items[0]["status"] != "ok"
    found = {i["status"] for i in items}
    assert {"brak_sygnalu", "bateria_krytyczna", "autotest", "wymiana_30", "ok"} <= found
    assert all(len(i["odczyty_dni"]) == 7 and i["odczyty_7d"] == sum(i["odczyty_dni"]) for i in items)
    panel = next(i for i in items if i["typ"] == "panel")
    from app.models import Device
    assert panel["bateria_pct"] == db.session.get(Device, panel["id"]).battery  # spójne z Device


def test_filters(client):
    d = client.get("/api/urzadzenia?typ=czujnik&dzielnica=Nowa Huta&status=wymiana_30").get_json()
    assert d["urzadzenia"] and all(i["typ"] == "czujnik" and i["status"] == "wymiana_30" for i in d["urzadzenia"])
    assert d["kpi"]["wg_typu"] == {"czujnik": d["kpi"]["lacznie"]}
    assert sum(s["liczba"] for s in d["statusy"]) == d["kpi"]["lacznie"]


@pytest.mark.parametrize("q,kod", [("typ=lodowka", "nieznany_typ"), ("dzielnica=Atlantyda", "nieznana_dzielnica"),
                                   ("status=zepsute", "nieznany_status")])
def test_bad_filter_is_400(client, q, kod):
    r = client.get(f"/api/urzadzenia?{q}")
    assert r.status_code == 400 and r.get_json()["kod"] == kod and r.get_json()["blad"]


def test_detail_and_404(client):
    pid = DeviceInfo.query.filter_by(kind="czujnik").first().point_id
    d = client.get(f"/api/urzadzenia/{pid}").get_json()["urzadzenie"]
    assert d["kosz"]["pojemnosc_l"] and d["urzadzenie"]["numer_seryjny"].startswith("TF-US-")
    assert d["urzadzenie"]["zywotnosc_baterii_dni"] == 730 and len(d["seria"]["dni"]) == 7
    r = client.get("/api/urzadzenia/999999")
    assert r.status_code == 404 and r.get_json() == {"blad": "Przy koszu 999999 nie ma urządzenia.", "kod": "nieznane_urzadzenie"}


def test_page_renders(client):
    r = client.get("/dashboard/urzadzenia")
    assert r.status_code == 200 and "Urządzenia" in r.get_data(as_text=True)
    assert 'href="/dashboard/urzadzenia"' in client.get("/dashboard").get_data(as_text=True)
