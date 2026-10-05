"""Panel dyspozytora: strona, GET /api/dyspozytor i „Dodaj do kursu” (decyzja człowieka, nie zgłoszenie mieszkańca)."""
from datetime import datetime, timedelta

import pytest

from app import clock
from app.comparison import compare
from app.dyspozytor_api import _urgent
from app.models import Press, Report, StopIssue
from app.osm_import import import_points
from app.routes import DISPATCH_REASON
from app.simulation import DEMO_NOW
from app.models import Point
from app.state import current_routes, point_states


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def _bins():
    return next(f for f in current_routes(clock.now()) if f["kind"] == "bin")


def _target():
    """Kosz uliczny spoza trasy (najciekawszy przypadek), a gdy reguły wzięły wszystkie — ostatni na trasie."""
    f = _bins()
    return f["skipped"][0]["id"] if f["skipped"] else f["stops"][-1]["id"]


def test_page_has_map_tabs_and_scripts(client, demo):
    html = client.get("/dyspozytor").get_data(as_text=True)
    assert 'id="dp-map"' in html and 'role="tablist"' in html and html.count('role="tab"') == 3
    assert all(t in html for t in ("Pilne", "Ekipy i trasy", "Zgłoszenia", "pilnych", "przepełnionych", "km trasy"))
    assert html.index('id="dp-live"') < html.index('role="tabpanel"')  # aria-live poza ukrywanym panelem zakładki
    assert "ui/dyspozytor.js" in html and "vendor/leaflet/leaflet.js" in html and "ui/mapa.js" in html
    assert 'href="/dyspozytor" aria-current="page"' in html  # perspektywa zaznaczona w przełączniku


def test_overview_numbers_come_from_engine(client, demo):
    d = client.get("/api/dyspozytor").json
    k, f = d["kafle"], _bins()
    assert k["km"] == f["km"] and k["punkty"] == sum(len(r["stops"]) for r in [f, *f["extra_routes"]])
    cmp_ = compare(DEMO_NOW)
    fixed, fairy = cmp_["fixed"]["total"]["visits"], cmp_["fairy"]["total"]["visits"]
    assert k["odbiory_mniej_pct"] == round(100 * (fixed - fairy) / fixed)  # te same liczby co /metodologia
    assert {x["rodzaj"] for x in d["floty"]} == {"bin", "shelter"} and all(len(x["linia"]) >= 2 for x in d["floty"])
    assert all(p["juz"] or p["prog_o"] <= p["kurs_o"] for p in d["pilne"])  # pilne = 85% przed najbliższym kursem albo już teraz
    assert k["pilne"] == d["pilne_liczba"] and k["juz"] + k["zagrozone"] == k["pilne"]  # kafel = liczba na zakładce
    assert [p["juz"] for p in d["pilne"]] == sorted((p["juz"] for p in d["pilne"]), reverse=True)  # najpierw już ponad progiem
    assert d["zgloszenia"] and all("na koszu" not in f"{z['typ']} {z['zrodlo']}" and z["zrodlo"] for z in d["zgloszenia"])  # „Panel kosza”


def test_reported_bin_is_urgent_even_if_forecast_crosses_after_run(demo):
    """Świeże zgłoszenie mieszkańca (stan „do opróżnienia”, poziom 70%) trafia do „Pilnych” jako już ponad progiem,
    nawet gdy prognoza 85% wypada dopiero po kursie (przypadek z recenzji: Kazimierz 20)."""
    now = clock.now()
    states, fleets = point_states(now), {f["kind"]: f for f in current_routes(now)}
    late = (datetime.fromisoformat(fleets["bin"]["run_at"]) + timedelta(hours=6)).isoformat()
    pid = next(p.id for p in Point.live_query() if p.kind == "bin" and p.id in states)
    states = {**states, pid: {**states[pid], "state": "bad", "value": 70, "crossing": late, "reason": "zgłoszenie: 1× naciśnięty, waga 100%"}}
    item = next(k for k in _urgent(now, states, fleets, set()) if k["id"] == pid)
    assert item["juz"] is True and item["priorytet"] == "krytyczne" and item["powod"].startswith("zgłoszenie")
    calm = {**states, pid: {**states[pid], "state": "warn", "value": 70}}
    assert pid not in {k["id"] for k in _urgent(now, calm, fleets, set())}  # bez zgłoszenia i z 85% po kursie: nie pilny


def test_add_puts_bin_first_on_route_and_is_idempotent(client, demo):
    pid = _target()
    r = client.post("/api/dyspozytor/dodaj", json={"kosz": pid})
    assert r.status_code == 201 and r.json["dodany"] is True and "pierwszy na liście kierowcy" in r.json["komunikat"]
    rows = StopIssue.query.count()
    again = client.post("/api/dyspozytor/dodaj", json={"kosz": str(pid)})
    assert again.status_code == 200 and StopIssue.query.count() == rows  # drugi klik niczego nie dopisuje
    first = _bins()["stops"][0]
    assert first["id"] == pid and first["dispatcher"] and first["reason"] == DISPATCH_REASON
    stop = next(s for s in client.get("/api/trasa").json["przystanki"] if s["id"] == pid)
    assert stop["kolejnosc"] == 1
    assert client.get("/api/dyspozytor/dodane").json["dodane"] == [pid]
    assert client.get("/api/dyspozytor").json["dodane"] == [pid]


def test_undo_and_emptying_close_the_decision(client, demo):
    pid = _target()
    client.post("/api/dyspozytor/dodaj", json={"kosz": pid})
    assert client.post("/api/dyspozytor/cofnij", json={"kosz": pid}).status_code == 201
    assert client.post("/api/dyspozytor/cofnij", json={"kosz": pid}).status_code == 200
    assert client.get("/api/dyspozytor/dodane").json["dodane"] == []
    assert not any(s.get("dispatcher") for s in _bins()["stops"])
    client.post("/api/dyspozytor/dodaj", json={"kosz": pid})
    assert client.post("/api/odbiory", json={"akcja": "oprozniono", "kosz": pid, "poziom": 75}).status_code == 201
    assert client.get("/api/dyspozytor/dodane").json["dodane"] == []  # opróżnienie realizuje decyzję


@pytest.mark.parametrize("body,status", [({"kosz": 999999}, 404), ({"kosz": 0}, 404), ({"kosz": "abc"}, 400), ({"kosz": None}, 400),
                                         ({"kosz": True}, 400), ({"kosz": [1]}, 400), ({"kosz": "-3"}, 400), ({}, 400)])
def test_add_validates_input(client, demo, body, status):
    r = client.post("/api/dyspozytor/dodaj", json=body)
    assert r.status_code == status and r.json["kod"] in ("kosz_nie_istnieje", "zly_kosz", "nie_znaleziono")


def test_dispatcher_does_not_touch_resident_statistics(client, demo):
    """Decyzja dyspozytora to nie zgłoszenie: bez nowych Report/Press, ta sama lista Open311 i liczba zgłoszeń."""
    before = (Report.query.count(), Press.query.count(), len(client.get("/api/v1/open311/requests.json").json))
    client.post("/api/dyspozytor/dodaj", json={"kosz": _target()})
    assert (Report.query.count(), Press.query.count(), len(client.get("/api/v1/open311/requests.json").json)) == before


def test_dashboard_links_to_dispatcher_instead_of_map(client, demo):
    html = client.get("/dashboard").get_data(as_text=True)
    assert 'class="c-link-go" href="/dyspozytor"' in html and 'id="ch-mapa"' not in html and "leaflet.js" not in html
