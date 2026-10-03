"""Ekran e-papierowy na koszu: logika stanów (tabela wyzwalaczy + priorytety), renderer vs wzorce, okno częściowe, symulator."""
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from app import clock, db, epaper, epaper_render
from app.models import Device, Emptying, Point, Report
from app.osm_import import import_points
from app.reports import record_press

OUT = Path(__file__).resolve().parent.parent / "docs" / "epapier" / "renderer" / "out"


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def calm_bin():
    """Kosz bez otwartego zgłoszenia i bez opróżnienia w ostatniej godzinie."""
    now = clock.now()
    busy = {r.point_id for r in Report.query.filter(Report.hit.is_(None))}
    recent = {e.point_id for e in Emptying.query.filter(Emptying.at > now - epaper.EMPTIED_HOLD, Emptying.at <= now)}
    return next(p for p in Point.query.filter_by(kind="bin").order_by(Point.id) if p.id not in busy and p.id not in recent)


def state_of(point, now=None):
    return epaper.display_state(point, now or clock.now())


# --- renderer: zgodność z wzorcami z paczki (1-bit, bez tolerancji) ---

@pytest.mark.parametrize("i,state", enumerate(["calm", "confirm", "enroute", "emptied", "overflow", "fault", "night"], 1))
def test_render_matches_reference(i, state, monkeypatch):
    monkeypatch.setattr(epaper_render, "BASE_URL", "http://10.250.192.133:5050")
    ref = Image.open(OUT / f"stan-{i}-{state}.png").convert("L")
    assert ImageChops.difference(ref, epaper_render.render(state).convert("L")).getbbox() is None


def test_render_tri_matches_reference(monkeypatch):
    monkeypatch.setattr(epaper_render, "BASE_URL", "http://10.250.192.133:5050")
    ref = Image.open(OUT / "stan-8-confirm-3kolor.png").convert("RGB")
    assert ImageChops.difference(ref, epaper_render.render("confirm", tri=True).convert("RGB")).getbbox() is None


def test_value_change_touches_only_partial_window():
    a = epaper_render.render("enroute", {"fill": 62, "b": ("Przyjazd", "ok. 12 min"), "c": ("Przystanek", "34 z 53")}).convert("L")
    b = epaper_render.render("enroute", {"fill": 71, "b": ("Przyjazd", "ok. 8 min"), "c": ("Przystanek", "35 z 53")}).convert("L")
    diff = ImageChops.difference(a, b).getbbox()
    x0, y0, x1, y1 = epaper_render.PARTIAL
    assert diff is not None
    assert diff[0] >= x0 and diff[1] >= y0 and diff[2] <= x1 and diff[3] <= y1, diff


def test_state_change_needs_full_refresh_and_keys_follow():
    full_a, part_a = epaper.keys("calm", {"device": {"device_no": "1"}, "fill": 62, "b": ("x", "1"), "c": ("y", "2")})
    full_b, part_b = epaper.keys("calm", {"device": {"device_no": "1"}, "fill": 70, "b": ("x", "1"), "c": ("y", "2")})
    full_c, _ = epaper.keys("confirm", {"device": {"device_no": "1"}, "fill": 70, "b": ("x", "1"), "c": ("y", "2"), "big": "Zgłoszenie przyjęte o 13:24"})
    assert full_a == full_b and part_a != part_b  # tylko wartości → tylko okno częściowe
    assert full_c != full_b                       # nowy stan → pełne odświeżenie


# --- logika stanów: każdy wyzwalacz i priorytety ---

def test_calm_then_confirm_after_press(demo):
    p = calm_bin()
    state, data = state_of(p)
    assert state == "calm" and data["c"] == ("Zgłoszenia", "brak") and data["b"][0] == "Następny odbiór"
    record_press(p.id, clock.now(), source="button")
    state, data = state_of(p)
    assert state == "confirm" and data["big"] == f"Zgłoszenie przyjęte o {clock.now():%H:%M}" and data["c"] == ("Zgłosiły", "1 osoba")
    record_press(p.id, clock.now(), ip="2")
    assert state_of(p)[1]["c"] == ("Zgłosiły", "2 osoby")


def test_enroute_when_stale_report_is_on_route_before_run(demo):
    p = calm_bin()
    now = clock.now()  # 13:30, kurs koszy 14:00 → w oknie 45 min
    record_press(p.id, now - timedelta(minutes=20), source="button")  # zgłoszenie starsze niż okno scalania
    state, data = state_of(p)
    assert state == "enroute" and data["b"][0] == "Przyjazd" and data["c"][0] == "Przystanek" and " z " in data["c"][1]


def test_overflow_beats_confirm(demo):
    p = calm_bin()
    record_press(p.id, clock.now(), source="button")
    states = {p.id: {"level": 104, "value": 104, "state": "bad"}}
    state, data = epaper.display_state(p, clock.now(), states=states)
    assert state == "overflow" and data["fill"] == 100 and data["big"].startswith("Zgłoszenie przyjęte")


def test_fault_beats_everything(demo):
    p = calm_bin()
    record_press(p.id, clock.now(), source="button")
    dev = db.session.get(Device, p.id) or Device(point_id=p.id, last_heartbeat=clock.now(), battery=80)
    dev.battery = 12
    db.session.add(dev)
    db.session.commit()
    state, data = state_of(p)
    assert state == "fault" and data["fill"] is None and data["c"] == ("Bateria", "12 %")
    dev.battery = 80
    dev.last_heartbeat = clock.now() - timedelta(hours=49)
    db.session.commit()
    state, data = state_of(p)
    assert state == "fault" and "Brak sygnału od 49 h" in data["sub"]


def test_emptied_holds_60_minutes_then_calm(demo):
    p = calm_bin()
    now = clock.now()
    Report.query.filter_by(point_id=p.id).delete()
    db.session.add(Emptying(point_id=p.id, at=now - timedelta(minutes=59), level=75))
    db.session.commit()
    state, data = state_of(p)
    assert state == "emptied" and data["c"] == ("Zgłoszenia", "zamknięte") and "dziękujemy" in data["big"]
    assert state_of(p, now + timedelta(minutes=2))[0] == "calm"  # 61 min po opróżnieniu (a przed kursem 14:00 z symulacji)


def test_night_only_when_calm(demo):
    p = calm_bin()
    night = clock.now().replace(hour=23)
    state, data = state_of(p, night)
    assert state == "night" and data["big"].startswith("Odbiór jutro")
    record_press(p.id, night, source="button")
    assert state_of(p, night)[0] == "confirm"


def test_no_personal_data_on_screen(demo):
    p = calm_bin()
    record_press(p.id, clock.now(), source="button", resident_id=None)
    _, data = state_of(p)
    text = " ".join(str(v) for v in data.values())
    assert "@" not in text and "Smok" not in text and "!" not in text.replace("!", "", 0)


# --- symulator i QR ---

def test_png_etag_and_state_keys(client, demo):
    p = calm_bin()
    r = client.get(f"/epapier/{p.id}.png")
    assert r.status_code == 200 and r.mimetype == "image/png" and r.headers["Cache-Control"] == "no-cache"
    assert Image.open(__import__("io").BytesIO(r.data)).size == (800, 480)
    assert client.get(f"/epapier/{p.id}.png", headers={"If-None-Match": r.headers["ETag"]}).status_code == 304
    part = client.get(f"/epapier/{p.id}.png?part=1")
    assert Image.open(__import__("io").BytesIO(part.data)).size == (752, 88)
    s1, d1 = epaper.display_state(p, clock.now())
    record_press(p.id, clock.now(), source="button")
    s2, d2 = epaper.display_state(p, clock.now())
    assert s1 == "calm" and s2 == "confirm" and epaper.keys(s1, d1)[0] != epaper.keys(s2, d2)[0]
    assert client.get(f"/epapier/{p.id}.png", headers={"If-None-Match": r.headers["ETag"]}).status_code == 200


def test_qr_targets_redirect_to_app_pages(client, demo):
    p = calm_bin()
    assert f"/zglos/{p.id}?qr=" in client.get(f"/kosz/{p.id}/zglos").headers["Location"]
    assert client.get(f"/kosz/{p.id}/status").headers["Location"].endswith(f"/panel/{p.id}")
    assert client.get("/przyjaciele").status_code == 301
    for target, path in epaper_render.QR_TARGETS.items():
        assert path.format(base="", dev=p.id) in {f"/kosz/{p.id}/zglos", f"/kosz/{p.id}/status", "/przyjaciele"}
