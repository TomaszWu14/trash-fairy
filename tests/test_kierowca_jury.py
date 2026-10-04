"""Dowód wykonania usługi: zdjęcie kosza przy „Opróżniono”, flaga pilotażu, kontrakt dowodu dla mieszkańca, „Tu przydałby się kosz”."""
import io

import pytest
from PIL import Image

from app import clock, db, llm, residents
from app.api_pl import numer
from app.models import Emptying, PhotoAnalysis, Press, Report, StopIssue
from app.osm_import import import_points
from app.reports import record_press


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def vision(monkeypatch, people=False, confidence=0.9, fill=100):
    """Atrapa Claude Vision dla zdjęcia ekipy (schemat photos.SCHEMA)."""
    monkeypatch.setattr(llm, "ask_json", lambda *a, **k: {
        "fill_level": fill, "overflow_outside": False, "misuse": [], "damage": False, "confidence": confidence,
        "note": "Kosz opróżniony.", "people_or_plates": people})


def jpeg():
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (90, 120, 90)).save(buf, "JPEG")
    return buf.getvalue()


def oproznij(client, pid, poziom=100, photo=True):
    data = {"kosz": str(pid), "akcja": "oprozniono", "poziom": str(poziom), "lat": "50.06", "lon": "19.94"}
    if photo:
        data["zdjecie"] = (io.BytesIO(jpeg()), "kosz.jpg")
    return client.post("/api/odbiory", data=data, content_type="multipart/form-data")


def zgloszenie_demo(pid):
    """Zgłoszenie z konta demo „Anna K.” (jak formularz mieszkańca z konto=demo)."""
    r = record_press(pid, clock.now(), source="qr", kind="full")
    Press.query.filter_by(report_id=r.id).first().resident_id = residents.demo_resident().id
    db.session.commit()
    clock.touch()
    return numer(r.id)


def first_stop(client):
    return client.get("/api/trasa").json["przystanki"][0]["id"]


def test_emptying_with_photo_saves_crew_photo_and_shows_status(client, demo, monkeypatch):
    vision(monkeypatch)
    pid = first_stop(client)
    r = oproznij(client, pid)
    assert r.status_code == 201, r.json
    assert r.json["zdjecie"]["status"] == "potwierdzone"  # w testach analiza od razu (TESTING)
    pa = PhotoAnalysis.query.filter_by(point_id=pid, source="crew").one()
    assert pa.crew_level == 100 and pa.people is False
    assert Emptying.query.filter_by(point_id=pid, source="crew").count() == 1
    k = client.get(f"/api/kosze/{pid}").json["kosz"]
    assert k["zdjecie_odbioru"]["etykieta"] == "Potwierdzone zdjęciem" and k["wymaga_zdjecia"] is False


def test_discrepant_photo_is_left_for_verification(client, demo, monkeypatch):
    vision(monkeypatch, fill=25)  # ekipa kliknęła 100%, zdjęcie pokazuje 25%: reguła nie potwierdza
    pid = first_stop(client)
    assert oproznij(client, pid).json["zdjecie"]["etykieta"] == "Do weryfikacji"


def test_bad_photo_is_rejected_before_emptying(client, demo):
    pid = first_stop(client)
    r = client.post("/api/odbiory", data={"kosz": str(pid), "akcja": "oprozniono", "poziom": "100",
                                          "zdjecie": (io.BytesIO(b"to nie obraz"), "x.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 400 and r.json["kod"] == "zle_zdjecie"
    assert Emptying.query.filter_by(point_id=pid, source="crew").count() == 0


def test_pilot_flag_requires_photo(client, demo, app, monkeypatch):
    vision(monkeypatch)
    pid = first_stop(client)
    assert oproznij(client, pid, photo=False).status_code == 201  # domyślnie zdjęcie opcjonalne
    app.config["REQUIRE_CREW_PHOTO"] = "1"
    pid2 = client.get("/api/trasa").json["przystanki"][0]["id"]
    r = oproznij(client, pid2, photo=False)
    assert r.status_code == 400 and r.json["blad"] == "W pilotażu odbiór wymaga zdjęcia kosza."
    assert client.get(f"/api/kosze/{pid2}").json["kosz"]["wymaga_zdjecia"] is True
    assert oproznij(client, pid2).status_code == 201


def test_report_contract_dowod_and_punkty(client, demo, monkeypatch):
    vision(monkeypatch)
    pid = first_stop(client)
    nr = zgloszenie_demo(pid)
    d = client.get(f"/api/zgloszenia/{nr}").json
    assert d["dowod"] is None
    assert d["punkty"] == {"za_trafne": residents.POINTS["bin"], "przyznane": False}
    oproznij(client, pid)
    d = client.get(f"/api/zgloszenia/{nr}").json
    assert d["status"] == "zrealizowane"
    assert d["dowod"]["etykieta"] == "Zrealizowane, potwierdzone zdjęciem ekipy" and d["dowod"]["potwierdzone"] is True
    assert d["punkty"]["przyznane"] is True  # opróżnienie przy 100% = trafne zgłoszenie, punkty dla konta demo
    img = client.get(d["dowod"]["zdjecie"])
    assert img.status_code == 200 and img.mimetype == "image/jpeg"


def test_report_done_without_crew_photo(client, demo):
    pid = first_stop(client)
    nr = zgloszenie_demo(pid)
    oproznij(client, pid, photo=False)
    assert client.get(f"/api/zgloszenia/{nr}").json["dowod"] == {
        "etykieta": "Zrealizowane, bez zdjęcia ekipy", "potwierdzone": False, "zdjecie": None}


def test_photo_with_people_is_never_public(client, demo, monkeypatch):
    vision(monkeypatch, people=True)
    pid = first_stop(client)
    nr = zgloszenie_demo(pid)
    oproznij(client, pid)
    d = client.get(f"/api/zgloszenia/{nr}").json["dowod"]
    assert d["potwierdzone"] is True and d["zdjecie"] is None  # odbiór potwierdzony, zdjęcie nie wychodzi do mieszkańca
    pa = PhotoAnalysis.query.filter_by(point_id=pid, source="crew").one()
    assert client.get(f"/api/odbiory/zdjecie/{pa.id}").status_code == 404
    assert client.get("/api/odbiory/zdjecie/999999").status_code == 404


def test_need_bin_suggestion(client, demo):
    pid = first_stop(client)
    r = client.post("/api/odbiory", json={"kosz": pid, "akcja": "problem", "problem": "need_bin", "lat": 50.06, "lon": 19.94})
    assert r.status_code == 201 and "przydałby się kosz" in r.json["komunikat"]
    assert StopIssue.query.filter_by(point_id=pid, kind="need_bin").count() == 1


def test_report_without_press_rows_is_listed_on_bin_card(client, demo):
    """Zgłoszenia z seeda/symulacji nie mają wierszy Press: karta kosza nie może mówić „brak zgłoszeń” przy liczbie > 0."""
    pid = first_stop(client)
    now = clock.now()
    db.session.add(Report(point_id=pid, first_at=now, last_at=now, presses=3, weight=1.0))
    db.session.commit()
    k = client.get(f"/api/kosze/{pid}").json["kosz"]
    bez_press = [z for z in k["zgloszenia"] if z.get("osob") == 3]
    assert k["zgloszenia_liczba"] >= 3 and len(bez_press) == 1
    assert bez_press[0]["typ"] == "Przycisk na koszu" and bez_press[0]["komentarz"] is None
