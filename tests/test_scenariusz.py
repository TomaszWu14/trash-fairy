"""Scenariusz demo w trzech wariantach (app.js: okienko losowania, TF.SCENARIOS): dane do losowania i przebieg C po stronie API."""
import io
import json
import pathlib
import re

import pytest
from PIL import Image

from app import clock, llm, rate, wysypiska
from app.api_pl import qr_token
from app.osm_import import import_points
from app.ui import SCENARIO_PLACES

DEMO_PHOTO = pathlib.Path(__file__).resolve().parent.parent / "app/static/ui/demo/wysypisko-przyklad.jpg"


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def test_places_for_variant_c_are_real_krakow_points():
    assert len(SCENARIO_PLACES) >= 4 and SCENARIO_PLACES[0]["lat"] == 50.06446  # /?scenariusz=C&miejsce=0: ROD „Grzegórzki”
    assert all(p["nazwa"] and wysypiska.in_krakow(p["lat"], p["lon"]) for p in SCENARIO_PLACES)
    assert len({(p["lat"], p["lon"]) for p in SCENARIO_PLACES}) == len(SCENARIO_PLACES)


def test_start_page_has_one_hero_action_three_variants_and_places(client, demo):
    html = client.get("/").get_data(as_text=True)
    hero = html[html.index('class="hero-cta"'):html.index('class="proof"')]
    assert "data-start-scenario" in hero and "data-reset-demo" not in hero  # reset niżej, w karcie scenariusza
    assert all(f"Wariant {v}" in html for v in "ABC") and "sześć kroków" not in html
    places = json.loads(re.search(r'id="sc-miejsca">(.*?)</script>', html).group(1))
    assert places == SCENARIO_PLACES


def test_drawn_bins_always_land_on_driver_route(client, demo, monkeypatch):
    """Okienko losuje kosz A/B tylko z losuj=True (ui.scenario_bins): po „Przepełniony” na panelu każdy z nich jest na trasie.
    Naciskamy wszystkie naraz: reguły trasy są per kosz (waga z historii własnego przycisku, poziomy sąsiadów z prognozy)."""
    monkeypatch.setattr(rate, "hit", lambda *a, **k: True)
    html = client.get("/").get_data(as_text=True)
    bins = json.loads(re.search(r'id="sc-kosze">(.*?)</script>', html).group(1))
    drawn = [b["id"] for b in bins if b["losuj"]]
    assert len(drawn) >= 3 and any(b["id"] == 7 for b in bins)  # preset ?kosz=7 (e2e wariantu B) jest na liście
    tokens = {k: re.search(r'data-token="([^"]+)"', client.get(f"/panel/{k}").get_data(as_text=True)).group(1) for k in drawn}
    for k, token in tokens.items():
        assert client.post(f"/api/kosze/{k}/przycisk", json={"typ": "przepelniony", "token": token}).status_code == 201
    off = {k: client.get(f"/api/kosze/{k}").json["kosz"]["trasa"] for k in drawn}
    assert all(t["na_trasie"] for t in off.values()), {k: t["powod"] for k, t in off.items() if not t["na_trasie"]}


def test_bins_to_draw_are_street_bins_with_panel_and_daily_qr(client, demo):
    """Kosze uliczne z GET /api/kosze: każdy ma panel z przyciskami i kod QR z tokenem dnia."""
    bins = [k for k in client.get("/api/kosze").json["kosze"] if k["rodzaj"] == "kosz uliczny"]
    assert len(bins) >= 20 and any(k["id"] == 18 for k in bins)
    for k in bins[::10]:
        html = client.get(f"/panel/{k['id']}").get_data(as_text=True)
        assert f"/zglos/{k['id']}?qr={qr_token(k['id'])}" in html and 'data-token="' in html
        assert "Kosz nr" not in html  # numer jest w nazwie (H1), bez dubla w rogu panelu


def test_404_has_h1_and_no_bin_list(client, demo):
    r = client.get("/nie-ma-takiej")
    html = r.get_data(as_text=True)
    assert r.status_code == 404 and "<h1>Nie znaleźliśmy tej strony</h1>" in html and "Kosze w pobliżu" not in html


def test_variant_c_demo_photo_and_crew_clearing_give_resident_points(client, monkeypatch):
    """Przykładowe zdjęcie przechodzi walidację; „Uprzątnięte” z identyfikatora ekipy (tf-ekipa) daje punkty zgłaszającej,
    a z jej własnego telefonu nie (samopotwierdzenie)."""
    monkeypatch.setattr(rate, "hit", lambda *a, **k: True)
    monkeypatch.setattr(llm, "ask_json", lambda *a, **k: (_ for _ in ()).throw(llm.LLMError("brak klucza")))  # AI niedostępna
    Image.open(DEMO_PHOTO).verify()
    place = SCENARIO_PLACES[0]

    def send(klient, dlat=0.0):
        data = {"lat": str(place["lat"] + dlat), "lon": str(place["lon"]), "rodzaj": ["bio", "tworzywa"], "ilosc": "20",
                "klient": klient, "konto": "demo", "zdjecie": (io.BytesIO(DEMO_PHOTO.read_bytes()), "przyklad-demo-wysypisko.jpg")}
        r = client.post("/api/wysypiska", data=data, content_type="multipart/form-data")
        assert r.status_code == 201 and r.json["zdjecie"], r.json
        return r.json["numer"]

    own = send("telefon-anny")
    client.post(f"/api/wysypiska/{own}/uprzatnieto", json={"klient": "telefon-anny"})
    assert client.get("/api/mieszkaniec/punkty").json["punkty"] == 0
    other = send("telefon-anny", dlat=0.01)  # inne miejsce (ok. 1 km dalej), nie dołącza do pierwszego
    assert client.post(f"/api/wysypiska/{other}/uprzatnieto", json={"klient": "ekipa-mpo"}).status_code == 200
    assert client.get("/api/mieszkaniec/punkty").json["punkty"] > 0


def test_dispatcher_step_follows_report_in_every_variant():
    """app.js TF.SCENARIOS: po wysłaniu zgłoszenia (A, B) i po statusie wysypiska (C) krok w panelu dyspozytora;
    pasek „Krok X z N” liczy z tej samej tablicy, więc wystarczy kolejność kroków."""
    js = (pathlib.Path(__file__).resolve().parent.parent / "app/static/ui/app.js").read_text(encoding="utf-8")
    body = js[js.index("TF.SCENARIOS = {"):js.index("const steps = () =>")]
    a, b, c = (body[body.index(f"{v}: {{ nazwa"):] for v in "ABC")
    a, b = a[:a.index("B: { nazwa")], b[:b.index("C: { nazwa")]
    assert a.index("'Panel kosza pokazuje zgłoszenie'") < a.index("DISPATCH,") < a.index("ON_LIST")
    assert b.index("'Mieszkaniec naciska przycisk przy koszu'") < b.index("DISPATCH,") < b.index("ON_LIST")
    assert c.index("'Zgłoszenie ma numer i status'") < c.index("/dyspozytor?zakladka=zgloszenia") < c.index("'Ekipa MPO sprząta'")
    assert "const DISPATCH = { url: () => '/dyspozytor?zakladka=zgloszenia', t: 'Dyspozytor widzi zgłoszenie'" in js
