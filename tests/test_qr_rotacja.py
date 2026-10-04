"""Dzienny kod QR kosza (token zmienia się o północy w Krakowie), przycisk na panelu z tokenem urządzenia, mieszkaniec bez mapy."""
import types
from datetime import datetime

import pytest

from app import api_pl, clock, db, epaper, rate
from app.api_pl import WARSAW, qr_seconds_left, qr_token, qr_valid
from app.devices_api import device_token
from app.osm_import import import_points

NOON = datetime(2026, 10, 4, 12, 0, tzinfo=WARSAW).timestamp()
DAY = 86400


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


@pytest.fixture
def wall(monkeypatch):
    """Podmieniony zegar ścienny modułu api_pl (qr_token/qr_valid); zegar demo i limity zostają prawdziwe."""
    now = [NOON]
    monkeypatch.setattr(api_pl, "time", types.SimpleNamespace(time=lambda: now[0]))
    return now


def _report(client, qr, pid=18):
    return client.post("/api/zgloszenia", json={"kosz": pid, "typ": "przepelniony", "qr": qr, "klient": f"t-{qr}"})


def test_token_changes_at_midnight_in_krakow():
    morning = datetime(2026, 10, 4, 0, 0, 1, tzinfo=WARSAW).timestamp()
    evening = datetime(2026, 10, 4, 23, 59, 59, tzinfo=WARSAW).timestamp()
    assert qr_token(18, morning) == qr_token(18, evening)  # cała doba ten sam kod
    assert qr_token(18, evening) != qr_token(18, evening + 2)  # po północy nowy
    assert qr_token(18, NOON) != qr_token(17, NOON)  # każdy kosz ma swój
    assert qr_seconds_left(evening) == 1 and qr_seconds_left(NOON) == 12 * 3600


def test_yesterdays_code_works_only_in_first_hour_after_midnight(client, demo, wall):
    yesterday = qr_token(18, NOON - DAY)
    wall[0] = datetime(2026, 10, 4, 0, 30, tzinfo=WARSAW).timestamp()
    assert qr_valid(18, yesterday)
    wall[0] = datetime(2026, 10, 4, 1, 0, 1, tzinfo=WARSAW).timestamp()
    assert not qr_valid(18, yesterday) and qr_valid(18, qr_token(18, wall[0]))


def test_report_accepts_todays_code_and_rejects_old_photo(client, demo, wall):
    wall[0] = NOON + DAY  # jutro w południe: wczorajsze zdjęcie kodu już nie działa
    old = _report(client, qr_token(18, NOON))
    assert old.status_code == 403 and old.json["kod"] == "brak_skanu_qr" and "nieaktualny" in old.json["blad"]
    assert _report(client, qr_token(18, NOON), pid=17).status_code == 403  # kod z innego kosza
    assert _report(client, "kod-ż").status_code == 403  # znaki spoza ASCII: 403, nie 500
    ok = _report(client, qr_token(18, wall[0]))
    assert ok.status_code == 201 and ok.json["numer"].startswith("TF-")  # bez lat/lon: położenia nie sprawdzamy


def test_fixed_address_carries_token_only_for_demo_bin(client, demo):
    assert client.get("/kosz/7/zglos").headers["Location"].endswith("/zglos/7")
    assert f"/zglos/18?qr={qr_token(18)}" in client.get("/kosz/18/zglos").headers["Location"]
    page = client.get("/zglos/7").get_data(as_text=True)
    assert "Kod QR kosza: brak skanu" in page
    assert "Kod QR kosza: nieaktualny" in client.get("/zglos/7?qr=stary").get_data(as_text=True)


def test_panel_shows_daily_code_and_reloads_after_midnight(client, demo):
    html = client.get("/panel/18").get_data(as_text=True)
    assert f"/zglos/18?qr={qr_token(18)}" in html and 'data-qr-left="' in html
    assert "Kod zmienia się codziennie" in html and "tylko do odczytu" not in html
    assert f'data-token="{device_token("TF-EP-000018")}"' in html


def test_panel_button_needs_device_token(client, demo, monkeypatch):
    monkeypatch.setattr(rate, "time", types.SimpleNamespace(time=lambda: NOON))  # jedno okno limitu: test nie miga na granicy minuty
    before = client.get("/api/kosze/18").json["kosz"]["zgloszenia_liczba"]
    bad = client.post("/api/kosze/18/przycisk", json={"typ": "przepelniony", "token": device_token("TF-EP-000017")})
    assert bad.status_code == 403 and set(bad.json) == {"blad", "kod"}
    assert client.post("/api/kosze/18/przycisk", json={"typ": "kot", "token": device_token("TF-EP-000018")}).status_code == 400
    ok = client.post("/api/kosze/18/przycisk", json={"typ": "odpady_obok", "token": device_token("TF-EP-000018")})
    assert ok.status_code == 201 and ok.json["komunikat"]
    k = client.get("/api/kosze/18").json["kosz"]
    assert k["zgloszenia_liczba"] == before + 1 and k["zgloszenia"][0]["typ"] == "Odpady obok kosza"
    for _ in range(2):
        client.post("/api/kosze/18/przycisk", json={"typ": "inne", "token": device_token("TF-EP-000018")})
    limit = client.post("/api/kosze/18/przycisk", json={"typ": "inne", "token": device_token("TF-EP-000018")})
    assert limit.status_code == 429  # najwyżej 3 na minutę z jednego kosza


def test_resident_start_has_no_map_and_no_other_bins(client, demo):
    html = client.get("/zglos").get_data(as_text=True)
    assert "m-map" not in html and "leaflet" not in html and "Kosze w pobliżu" not in html and "/zglos/7" not in html
    assert 'id="m-mine"' in html and "Twoje zgłoszenia" in html


def test_epaper_report_qr_carries_daily_token(demo):
    from app.models import Point
    p = db.session.get(Point, 18)
    state, data = epaper.display_state(p, clock.now())
    assert data["device"]["qr"] == qr_token(18)
    other = {**data, "device": {**data["device"], "qr": "inny"}}
    assert epaper.keys(state, data)[0] != epaper.keys(state, other)[0]  # nowy kod = pełne odświeżenie ekranu
