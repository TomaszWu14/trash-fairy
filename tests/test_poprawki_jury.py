"""Poprawki P0 pod jury: AI w przepływie zgłoszenia, EXIF, powód priorytetu, „uszkodzony”/„inne”, limit per IP."""
import io
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from PIL import Image

from app import clock, db, llm, photos
from app.api_pl import powod, qr_token
from app.models import Point
from app.osm_import import import_points
from app.state import neighbors_map, point_states
from tests.test_zdjecia import jpeg_with_gps


@pytest.fixture
def demo(cache, monkeypatch, tmp_path):
    monkeypatch.setattr(photos, "photo_dir", lambda: tmp_path)  # zdjęcia z testów nie lądują w instance/
    import_points(cache)
    clock.reset(weeks=2)


def lonely_ok_bin():
    """Kosz bez sąsiadów i w stanie ok: zgłoszenie zmienia tylko jego stan."""
    lonely = {pid for pid, n in neighbors_map().items() if not n}
    states = point_states(clock.now())
    pid = min((pid for pid, s in states.items() if s["state"] == "ok" and pid in lonely), key=lambda i: states[i]["value"])
    return db.session.get(Point, pid)


def send(client, p, typ="przepelniony", klient="t1", photo=None):
    body = {"kosz": p.id, "typ": typ, "qr": qr_token(p.id), "lat": p.lat, "lon": p.lon, "klient": klient}
    if photo is None:
        return client.post("/api/zgloszenia", json=body)
    return client.post("/api/zgloszenia", data={**body, "zdjecie": (io.BytesIO(photo), "kosz.jpg")},
                       content_type="multipart/form-data")


# --- #5: EXIF ---

def test_strip_metadata_removes_gps_and_camera_data():
    raw = jpeg_with_gps(50.0618, 19.9360)
    assert photos.gps_from_exif(raw) is not None
    clean = photos.strip_metadata(raw, "image/jpeg")
    assert photos.gps_from_exif(clean) is None
    with Image.open(io.BytesIO(clean)) as img:
        assert len(img.getexif()) == 0 and "exif" not in img.info and img.size == (32, 32)


def test_saved_resident_photo_has_no_exif(client, demo, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    p = lonely_ok_bin()
    assert send(client, p, photo=jpeg_with_gps(p.lat, p.lon)).status_code == 201
    from app.models import PhotoAnalysis
    pa = PhotoAnalysis.query.filter_by(source="resident").one()
    with open(pa.photo_path, "rb") as f:
        assert photos.gps_from_exif(f.read()) is None


def test_broken_image_is_rejected_without_500(client, demo):
    p = lonely_ok_bin()
    r = send(client, p, photo=b"\xff\xd8\xff\xe0" + b"\x00" * 64)
    assert r.status_code == 400 and r.json["kod"] == "zle_zdjecie"


# --- #3: AI w przepływie ---

def test_photo_without_api_key_goes_to_manual_check(client, demo, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    p = lonely_ok_bin()
    nr = send(client, p, photo=jpeg_with_gps(p.lat, p.lon)).json["numer"]
    ai = client.get(f"/api/zgloszenia/{nr}").json["ai"]
    assert ai["status"] == "do_weryfikacji" and ai["etykieta"] == "Do weryfikacji" and ai["pewnosc"] is None
    assert client.get(f"/api/kosze/{p.id}").json["kosz"]["zgloszenia"][0]["ai"]["status"] == "do_weryfikacji"


def test_report_without_photo_has_no_ai_block(client, demo):
    p = lonely_ok_bin()
    nr = send(client, p).json["numer"]
    assert client.get(f"/api/zgloszenia/{nr}").json["ai"] is None
    assert client.get(f"/api/kosze/{p.id}").json["kosz"]["zgloszenia"][0]["ai"] is None


def test_photo_with_vision_result_is_verified_by_rule(client, demo, monkeypatch):
    seen = {}

    def fake(prompt, schema, system=None, images=(), max_tokens=0):
        seen["schema"] = schema
        return {"bin_visible": True, "condition": "pelny", "fill_level": 100, "confidence": 0.86,
                "reason": "Kosz pełny, klapa się nie domyka.", "people_or_plates": True}
    monkeypatch.setattr(llm, "ask_json", fake)
    p = lonely_ok_bin()
    nr = send(client, p, photo=jpeg_with_gps(p.lat, p.lon)).json["numer"]
    ai = client.get(f"/api/zgloszenia/{nr}").json["ai"]
    assert seen["schema"] is photos.RESIDENT_SCHEMA
    assert ai == {"status": "zweryfikowane", "etykieta": "Zweryfikowane AI", "pewnosc": 0.86, "stan": "Pełny",
                  "uzasadnienie": "Kosz pełny, klapa się nie domyka.", "zdjecie_publiczne": False}


def pa(**kw):
    return SimpleNamespace(**({"status": "done", "bin_visible": True, "condition": "pelny", "confidence": 0.9,
                               "note": "Pełny.", "people": False, "wall_at": datetime.now(UTC).replace(tzinfo=None)} | kw))


@pytest.mark.parametrize("analysis, kind, status", [
    (pa(), "full", "zweryfikowane"),
    (pa(condition="odpady_obok"), "overflow", "zweryfikowane"),
    (pa(condition="uszkodzony"), "damaged", "zweryfikowane"),
    (pa(confidence=0.69), "full", "do_weryfikacji"),          # niska pewność
    (pa(bin_visible=False), "full", "do_weryfikacji"),         # nie widać kosza
    (pa(condition="w_porzadku"), "full", "do_weryfikacji"),    # niezgodne z typem
    (pa(), "other", "do_weryfikacji"),                         # „inne”: nie ma czego potwierdzać
    (pa(status="error"), "full", "do_weryfikacji"),            # błąd API / brak klucza
    (pa(status="pending"), "full", "w_toku"),
])
def test_verification_rule(analysis, kind, status):
    analysis.wall_at = datetime.now(UTC).replace(tzinfo=None)  # pa() powstaje przy zbieraniu testów: wolny przebieg > PENDING_MAX
    assert photos.verification(analysis, kind)["status"] == status


def test_people_or_plates_hide_photo():
    assert photos.verification(pa(people=True), "full")["zdjecie_publiczne"] is False
    assert photos.verification(pa(), "full")["zdjecie_publiczne"] is True
    assert photos.verification(None, "full") is None


# --- #7: powód priorytetu ---

@pytest.mark.parametrize("k, text", [
    ({"zgloszenia_liczba": 2, "poziom": 113, "prognoza": ""}, "2 zgłoszenia · 113%"),
    ({"zgloszenia_liczba": 1, "poziom": 60, "prognoza": ""}, "1 zgłoszenie · 60%"),
    ({"zgloszenia_liczba": 5, "poziom": 90, "prognoza": ""}, "5 zgłoszeń · 90%"),
    ({"zgloszenia_liczba": 0, "poziom": 96, "prognoza": "Przewidywane 85% ok. 15:10"}, "Pełny 96%"),
    ({"zgloszenia_liczba": 0, "poziom": 70, "prognoza": "Przewidywane 85% ok. 15:10"}, "Prognoza 85% ok. 15:10"),
    ({"zgloszenia_liczba": 0, "poziom": 30, "prognoza": "Bez przepełnienia w ciągu 24 h"}, "Według planu kursu · 30%"),
])
def test_powod(k, text):
    assert powod(k) == text


def test_route_stops_carry_reason_and_forecast(client, demo):
    d = client.get("/api/trasa").json
    todo = [s for s in d["przystanki"] if not s["zrobione"]]
    assert todo and all(s["powod"] and s["prognoza"] for s in todo)


# --- #8: „uszkodzony” i „inne” nie podnoszą szacunku ---

@pytest.mark.parametrize("typ", ["uszkodzony", "inne"])
def test_damaged_and_other_reports_do_not_raise_fill(client, demo, typ):
    p = lonely_ok_bin()
    before = point_states(clock.now())[p.id]
    r = send(client, p, typ=typ)
    assert r.status_code == 201 and r.json["numer"].startswith("TF-")
    s = point_states(clock.now())[p.id]
    assert s["value"] == before["value"] and s["state"] == "ok" and not s["fresh"]
    assert bool(s["damaged_at"]) == (typ == "uszkodzony")
    k = client.get(f"/api/kosze/{p.id}").json["kosz"]
    assert k["zgloszenia_liczba"] == 1 and not k["zgloszony"]
    assert client.get(f"/api/zgloszenia/{r.json['numer']}").json["status"] == "przyjete"


def test_full_report_still_raises_fill(client, demo):
    p = lonely_ok_bin()
    send(client, p, typ="przepelniony")
    assert point_states(clock.now())[p.id]["fresh"]


# --- #13: limit per IP ---

def test_rate_limit_per_ip(client, demo, monkeypatch):
    from app import api_pl
    monkeypatch.setattr(api_pl, "REPORTS_PER_IP_HOUR", 3)  # na produkcji 200 (jedno IP sali), tu mała liczba
    p = lonely_ok_bin()
    for i in range(3):
        assert send(client, p, klient=f"tel-{i}").status_code == 201
    r = send(client, p, klient="tel-31")
    assert r.status_code == 429 and r.json == {"blad": r.json["blad"], "kod": "za_duzo_zgloszen"}


def test_demo_reset_twice_in_a_row_is_refused_not_run_in_parallel(client, demo, monkeypatch):
    from app import rate
    monkeypatch.setattr(rate.time, "time", lambda: 1_000_000.0)  # okno limitu stałe: bez losowej granicy 20-sekundowego bloku
    assert client.post("/api/demo/reset").status_code == 200
    r = client.post("/api/demo/reset")
    assert r.status_code == 429 and r.json["kod"] == "reset_trwa"


def test_decompression_bomb_and_oversized_body_rejected(client, demo):
    big = Image.new("1", (9000, 9000))  # 81 MP, kilka kB po kompresji PNG
    buf = io.BytesIO()
    big.save(buf, "PNG")
    p = lonely_ok_bin()
    r = send(client, p, photo=buf.getvalue())
    assert r.status_code == 400 and r.json["kod"] == "zle_zdjecie"
    r = client.post("/api/zgloszenia", data={"zdjecie": (io.BytesIO(b"\xff\xd8\xff" + b"0" * (11 * 1024 * 1024)), "a.jpg")},
                    content_type="multipart/form-data")
    assert r.status_code == 413 and r.json["kod"] == "za_duzy_plik"


def test_pending_analysis_older_than_two_minutes_falls_back_to_manual_check():
    from datetime import UTC, datetime, timedelta
    pa = SimpleNamespace(status="pending", wall_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=3))
    assert photos.verification(pa, "full")["status"] == "do_weryfikacji"
    pa.wall_at = datetime.now(UTC).replace(tzinfo=None)
    assert photos.verification(pa, "full")["status"] == "w_toku"


def test_analysis_unexpected_error_is_recorded_not_left_pending(client, demo, monkeypatch):
    p = lonely_ok_bin()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setattr(llm, "ask_json", lambda *a, **k: (_ for _ in ()).throw(KeyError("boom")))
    nr = send(client, p, photo=jpeg_with_gps(p.lat, p.lon)).json["numer"]
    assert client.get(f"/api/zgloszenia/{nr}").json["ai"]["status"] == "do_weryfikacji"


def test_security_headers(client):
    h = client.get("/health").headers
    assert h["X-Content-Type-Options"] == "nosniff" and "frame-ancestors" in h["Content-Security-Policy"]
