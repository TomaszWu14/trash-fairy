"""Dzikie wysypiska (POST/GET /api/wysypiska) i punkty mieszkanki demo (/api/mieszkaniec/punkty)."""
import io

import pytest
from PIL import Image

from app import clock, db, llm, rate, wysypiska
from app.models import DumpReport

ROD = (50.06446, 19.96446)  # ROD „Grzegórzki”, ul. Nullo (OSM way 121108759)
M = 1 / 111_320  # stopień szerokości na metr


def png():
    buf = io.BytesIO()
    Image.new("RGB", (16, 16), (90, 120, 60)).save(buf, "PNG")
    return buf.getvalue()


def send(client, lat=ROD[0], lon=ROD[1], klient="a", rodzaj=("bio",), photo=False, **extra):
    data = {"lat": str(lat), "lon": str(lon), "rodzaj": list(rodzaj), "klient": klient, **extra}
    if photo:
        data["zdjecie"] = (io.BytesIO(png()), "w.png")
    return client.post("/api/wysypiska", data=data, content_type="multipart/form-data")


@pytest.fixture
def vision(monkeypatch):
    """Atrapa Claude: wynik opisu zdjęcia albo wyjątek LLMError."""
    state = {"result": {"waste_outside_container": True, "bags": 20, "kinds": ["bio", "tworzywa"], "confidence": 0.9,
                        "reason": "Worki z odpadami zielonymi przy ogrodzeniu.", "people_or_plates": False}, "error": None}

    def fake(prompt, schema, system=None, images=(), max_tokens=0):
        if state["error"]:
            raise llm.LLMError(state["error"])
        return llm.validate(state["result"], schema)
    monkeypatch.setattr(llm, "ask_json", fake)
    return state


@pytest.fixture
def no_limits(monkeypatch):
    monkeypatch.setattr(rate, "hit", lambda *a, **k: True)


@pytest.mark.parametrize("extra, kod", [
    ({"lat": ""}, "brak_polozenia"), ({"lat": "nan"}, "brak_polozenia"), ({"lat": "52.23", "lon": "21.01"}, "poza_krakowem"),
    ({"rodzaj": ["opony"]}, "zly_rodzaj"), ({"rodzaj": []}, "zly_rodzaj"),
    ({"ilosc": "0"}, "zla_ilosc"), ({"ilosc": "101"}, "zla_ilosc"), ({"ilosc": "dużo"}, "zla_ilosc"),
])
def test_validation(client, extra, kod):
    r = send(client, **extra)
    assert r.status_code == 400 and r.json["kod"] == kod and r.json["blad"]
    assert DumpReport.query.count() == 0


@pytest.mark.parametrize("body, kod", [
    ({"lat": 10 ** 400}, "brak_polozenia"),  # float(int) → OverflowError
    ({"ilosc": float("inf")}, "zla_ilosc"), ({"ilosc": 7.9}, "zla_ilosc"), ({"ilosc": True}, "zla_ilosc"),
])
def test_validation_json_never_500(client, body, kod):
    r = client.post("/api/wysypiska", json={"lat": ROD[0], "lon": ROD[1], "rodzaj": ["bio"], "klient": "j"} | body)
    assert r.status_code == 400 and r.json["kod"] == kod
    assert DumpReport.query.count() == 0


def test_bad_photo_and_json_body(client):
    r = client.post("/api/wysypiska", data={"lat": ROD[0], "lon": ROD[1], "rodzaj": "bio", "klient": "x",
                                            "zdjecie": (io.BytesIO(b"to nie obraz"), "x.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 400 and r.json["kod"] == "zle_zdjecie"
    ok = client.post("/api/wysypiska", json={"lat": ROD[0], "lon": ROD[1], "rodzaj": ["gabaryty"], "ilosc": "nie_wiem", "klient": "y"})
    assert ok.status_code == 201 and ok.json["numer"] == "WD-00001" and ok.json["status"] == "do_weryfikacji"
    assert DumpReport.query.one().qty is None


def test_rate_limit_per_phone(client):
    assert send(client, klient="a").status_code == 201
    r = send(client, klient="a", lat=ROD[0] + 0.01)
    assert r.status_code == 429 and r.json["kod"] == "za_czesto"


def test_duplicate_within_50_m_joins_and_confirms(client, no_limits):
    a = send(client, klient="a", ilosc="20")
    b = send(client, klient="b", lat=ROD[0] + 30 * M, rodzaj=["tworzywa"])
    assert b.json["numer"] == a.json["numer"] and b.json["dolaczone"] and b.json["status"] == "potwierdzone"
    same_phone = send(client, klient="b", lat=ROD[0] + 20 * M)
    g = db.session.get(DumpReport, 1)
    assert same_phone.json["dolaczone"] and g.confirmations == 2  # ten sam telefon nie potwierdza drugi raz
    far = send(client, klient="c", lat=ROD[0] + 80 * M)
    assert far.json["numer"] != a.json["numer"] and not far.json["dolaczone"]
    d = client.get(f"/api/wysypiska/{a.json['numer']}").json["wysypisko"]
    assert d["rodzaje"] == ["Bio", "Tworzywa sztuczne"] and d["ilosc"] == 20 and d["zgloszen"] == 3


def test_cleared_dump_does_not_absorb_new_report_and_is_final(client, no_limits):
    a = send(client).json["numer"]
    ok = client.post(f"/api/wysypiska/{a}/uprzatnieto")
    assert ok.status_code == 200 and client.get(f"/api/wysypiska/{a}").json["wysypisko"]["status"] == "uprzatniete"
    assert client.post(f"/api/wysypiska/{a}/uprzatnieto").status_code == 409
    again = send(client, klient="b").json
    assert again["numer"] != a and not again["dolaczone"]
    assert client.get("/api/wysypiska/WD-99999").status_code == 404
    assert client.post("/api/wysypiska/xyz/uprzatnieto").json["kod"] == "wysypisko_nie_istnieje"


@pytest.mark.parametrize("n, poziom", [(1, None), (2, "tablica"), (4, "kontrola"), (6, "fotopulapka")])
def test_ladder_counts_dumps_within_100_m_in_90_days(client, no_limits, n, poziom):
    for i in range(n):  # każde kolejne wysypisko po uprzątnięciu poprzedniego, w promieniu 100 m
        nr = send(client, klient=f"k{i}", lat=ROD[0] + (i % 3) * 30 * M).json["numer"]
        client.post(f"/api/wysypiska/{nr}/uprzatnieto")
    send(client, klient="obok", lat=ROD[0] + 500 * M)  # inne miejsce
    d = client.get("/api/wysypiska").json
    top = d["miejsca"][0]
    assert len(top["wysypiska"]) == n and top["poziom"] == poziom and len(d["miejsca"]) == 2
    assert top["etykieta"] == ({"tablica": "Tablica informacyjna i edukacja", "kontrola": "Kontrola Straży Miejskiej",
                                "fotopulapka": "Rozważ fotopułapkę (decyzja gminy)"}.get(poziom))


def test_ai_rule_sets_status_and_hides_photo_with_people(client, no_limits, vision):
    ok = send(client, photo=True).json
    assert ok["status"] == "zweryfikowane" and "pewność 90%" in ok["uzasadnienie"]
    item = client.get("/api/wysypiska").json["wysypiska"][0]
    assert item["zdjecie"] and item["ai"]["worki"] == 20 and "komentarz" not in item
    assert client.get(item["zdjecie"]).status_code == 200
    vision["result"] = vision["result"] | {"confidence": 0.5}
    low = send(client, klient="b", lat=ROD[0] + 300 * M, photo=True).json
    assert low["status"] == "do_weryfikacji"
    vision["result"] = vision["result"] | {"confidence": 0.95, "people_or_plates": True}
    people = send(client, klient="c", lat=ROD[0] + 600 * M, photo=True).json
    assert people["status"] == "zweryfikowane"
    shown = {x["numer"]: x for x in client.get("/api/wysypiska").json["wysypiska"]}[people["numer"]]
    assert shown["zdjecie"] is None and shown["ai"]["zdjecie_publiczne"] is False
    assert client.get(f"/api/wysypiska/{people['numer']}/zdjecie").status_code == 404


def test_ai_error_or_missing_key_means_do_weryfikacji_never_500(client, no_limits, vision, monkeypatch):
    vision["error"] = "Analiza AI niedostępna (błąd API 529)."
    r = send(client, photo=True)
    assert r.status_code == 201 and r.json["status"] == "do_weryfikacji" and "niedostępna" in r.json["uzasadnienie"]
    monkeypatch.undo()  # prawdziwe llm.ask_json bez klucza
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(rate, "hit", lambda *a, **k: True)
    r = send(client, klient="b", lat=ROD[0] + 300 * M, photo=True)
    assert r.status_code == 201 and r.json["status"] == "do_weryfikacji"
    assert db.session.get(DumpReport, 2).ai["status"] == "error"


def points(client):
    return client.get("/api/mieszkaniec/punkty").json


def test_resident_points_only_after_verification_with_photo(client, no_limits, vision):
    vision["result"] = vision["result"] | {"confidence": 0.4}  # AI niepewna: zdjęcie nie weryfikuje
    a = send(client, konto="demo", photo=True).json["numer"]
    send(client, konto="demo", klient="b", lat=ROD[0] + 300 * M)  # bez zdjęcia
    p = points(client)
    assert p["punkty"] == 0 and {x["powod"] for x in p["ostatnie"]} == {
        "Czeka na weryfikację", "Bez zdjęcia: punkty są tylko za zgłoszenia ze zdjęciem"}
    client.post(f"/api/wysypiska/{a}/uprzatnieto")  # weryfikacja przez ekipę
    p = points(client)
    assert p["punkty"] == 20 and p["odznaki"][-1]["nazwa"] == "Czujne oko"
    send(client, klient="obcy", lat=ROD[0] + 310 * M)  # drugie niezależne zgłoszenie potwierdza wysypisko bez zdjęcia…
    assert points(client)["punkty"] == 20  # …ale punkty są tylko za zgłoszenia ze zdjęciem


def test_crew_report_is_not_resident_and_gives_crew_points(client, no_limits, vision):
    send(client, zrodlo="ekipa", konto="demo", photo=True)
    assert points(client)["punkty"] == 0
    nr = client.get("/api/wysypiska").json["wysypiska"][0]["numer"]
    client.post(f"/api/wysypiska/{nr}/uprzatnieto")
    items = wysypiska.crew_dump_points(clock.now())
    assert sorted(x["punkty"] for x in items) == [2, 3] and all(x["kosz_id"] is None for x in items)
    from app.crew_points import crew_points  # suma trasy obejmuje też wysypiska
    assert crew_points(clock.now(), [])["suma"] == 5


def test_resident_daily_limit(client, no_limits, vision):
    for i in range(4):
        assert send(client, konto="demo", klient=f"k{i}", lat=ROD[0] + i * 300 * M, photo=True).json["status"] == "zweryfikowane"
    p = points(client)
    assert p["punkty"] == 60 and sum(x["powod"].startswith("Limit 3") for x in p["ostatnie"]) == 1


def test_same_account_does_not_self_confirm_and_confirmation_gives_no_points(client, no_limits, vision):
    vision["result"] = vision["result"] | {"confidence": 0.4}  # zdjęcie nie weryfikuje
    send(client, konto="demo", klient="tel-1", photo=True)
    send(client, konto="demo", klient="laptop-1", lat=ROD[0] + 20 * M)  # to samo konto, inny „telefon”
    assert db.session.get(DumpReport, 1).confirmations == 1 and points(client)["punkty"] == 0
    other = send(client, klient="obcy", lat=ROD[0] + 30 * M).json  # anonimowe drugie zgłoszenie: „Potwierdzone”…
    assert other["status"] == "potwierdzone" and points(client)["punkty"] == 0  # …ale id telefonu da się podrobić


def test_joining_verified_dump_needs_own_verified_photo(client, no_limits, vision):
    send(client, klient="obcy", photo=True)  # cudze wysypisko „Zweryfikowane AI”
    vision["result"] = vision["result"] | {"waste_outside_container": False, "confidence": 0.1}
    mine = send(client, konto="demo", klient="a2", lat=ROD[0] + 20 * M, photo=True).json
    assert mine["dolaczone"] and mine["status"] == "zweryfikowane"
    p = points(client)
    assert p["punkty"] == 0 and p["ostatnie"][0]["powod"].startswith("Dołączone do wcześniejszego")


def test_self_cleared_dump_gives_no_points(client, no_limits, vision):
    vision["result"] = vision["result"] | {"confidence": 0.4}
    a = send(client, konto="demo", klient="tel-1", photo=True).json["numer"]
    assert client.post(f"/api/wysypiska/{a}/uprzatnieto", json={"klient": "tel-1"}).status_code == 200
    p = points(client)
    assert p["punkty"] == 0 and p["ostatnie"][0]["powod"].startswith("Uprzątnięte z telefonu")


def test_photo_without_waste_is_not_public(client, no_limits, vision):
    vision["result"] = vision["result"] | {"waste_outside_container": False, "confidence": 0.9}
    nr = send(client, photo=True).json["numer"]
    assert client.get("/api/wysypiska").json["wysypiska"][0]["zdjecie"] is None
    assert client.get(f"/api/wysypiska/{nr}/zdjecie").status_code == 404


def test_points_endpoint_has_rewards_as_proposal(client):
    p = points(client)
    assert p["mieszkaniec"] == "Anna K." and p["punkty"] == 0 and p["ostatnie"] == []
    assert p["uwaga"] == "Katalog nagród to propozycja do ustalenia z miastem; partnerów jeszcze nie ma."
    assert [n["prog"] for n in p["nagrody"]] == sorted(n["prog"] for n in p["nagrody"])
    assert not any("zł" in n["nazwa"] for n in p["nagrody"])


def test_bin_report_from_resident_ui_earns_points_after_hit(client, cache):
    from app.api_pl import qr_token
    from app.models import Point
    from app.osm_import import import_points
    import_points(cache)
    clock.reset(weeks=1)
    p = Point.query.filter_by(kind="bin").first()
    assert client.post("/api/zgloszenia", json={"kosz": p.id, "typ": "przepelniony", "qr": qr_token(p.id), "klient": "t",
                                                "konto": "demo"}).status_code == 201
    assert points(client)["punkty"] == 0  # punkty dopiero za trafne zgłoszenie
    client.post("/api/odbiory", json={"kosz": p.id, "akcja": "oprozniono", "poziom": 100})
    got = points(client)
    assert got["punkty"] == 10 and got["ostatnie"][0]["powod"].startswith("Trafne zgłoszenie kosza")


def test_demo_account_does_not_confirm_or_weigh_bin_report(client, cache):
    from app.api_pl import qr_token
    from app.models import Point, Press, Report
    from app.osm_import import import_points
    from app.reports import record_press
    import_points(cache)
    clock.reset(weeks=1)
    p = Point.query.filter_by(kind="bin").first()
    first = record_press(p.id, clock.now())  # anonimowy przycisk panelu
    weight = first.weight
    assert client.post("/api/zgloszenia", json={"kosz": p.id, "typ": "przepelniony", "qr": qr_token(p.id), "klient": "t",
                                                "konto": "demo"}).status_code == 201
    r = db.session.get(Report, first.id)
    assert r.presses == 2 and r.confirmed is False and r.weight == weight  # konto demo tylko do punktów
    assert Press.query.order_by(Press.id.desc()).first().resident_id is not None


def test_reset_clears_dumps(client):
    send(client)
    wysypiska.reset_demo()
    assert DumpReport.query.count() == 0


@pytest.mark.parametrize("path", ["/wysypisko", "/wysypisko?ekipa=1", "/wysypisko/WD-00001", "/zglos"])
def test_pages_render(client, path):
    r = client.get(path)
    assert r.status_code == 200
    if path.startswith("/wysypisko"):
        assert "Zgłoś dzikie wysypisko" in r.get_data(as_text=True) or "WD-00001" in r.get_data(as_text=True)
