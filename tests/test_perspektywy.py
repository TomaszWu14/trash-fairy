"""Nowe UI „Przegląd jury”: cztery perspektywy na wspólnym API (audit/AUDYT-UX.md). Bez logowania."""
import pytest

from app import clock
from app.api_pl import qr_token
from app.models import Point
from app.osm_import import import_points


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def _bin(client, pid=18):
    return client.get(f"/api/kosze/{pid}").json["kosz"]


def _report(client, pid=18, **kw):
    k = _bin(client, pid)
    body = {"kosz": pid, "typ": "przepelniony", "qr": qr_token(pid), "lat": k["lat"], "lon": k["lon"], "klient": "t1", **kw}
    return client.post("/api/zgloszenia", json=body)


@pytest.mark.parametrize("path", ["/", "/panel/18", "/zglos", "/zglos/18", "/kierowca", "/kierowca/kosz/18", "/dashboard",
                                  "/metodologia", "/dostepnosc", "/prywatnosc", "/api/docs"])
def test_every_screen_renders_without_login(client, demo, path):
    r = client.get(path)
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert 'lang="pl"' in html and "Dane demonstracyjne" in html


@pytest.mark.parametrize("old, new", [("/telefony", "/"), ("/dyspozytor", "/dashboard"), ("/program", "/"), ("/logowanie", "/"),
                                      ("/epapier/18", "/panel/18"), ("/ekipa", "/kierowca")])
def test_old_addresses_redirect_to_new_screens(client, demo, old, new):
    r = client.get(old)
    assert r.status_code == 301 and r.headers["Location"].endswith(new)


def test_qr_on_bin_and_jury_link_carry_scan_token(client, demo):
    assert f"qr={qr_token(18)}" in client.get("/jury").headers["Location"]
    assert f"qr={qr_token(7)}" in client.get("/kosz/7/zglos").headers["Location"]
    assert f"/zglos/18?qr={qr_token(18)}" in client.get("/panel/18").get_data(as_text=True)


def test_report_needs_qr_scan_and_location_near_bin(client, demo):
    k = _bin(client)
    no_qr = client.post("/api/zgloszenia", json={"kosz": 18, "typ": "przepelniony", "lat": k["lat"], "lon": k["lon"]})
    assert no_qr.status_code == 403 and no_qr.json["kod"] == "brak_skanu_qr"
    wrong_qr = _report(client, qr=qr_token(17))
    assert wrong_qr.status_code == 403 and wrong_qr.json["kod"] == "brak_skanu_qr"
    no_geo = client.post("/api/zgloszenia", json={"kosz": 18, "typ": "przepelniony", "qr": qr_token(18)})
    assert no_geo.status_code == 403 and no_geo.json["kod"] == "brak_lokalizacji"
    far = _report(client, lat=k["lat"] + 0.01)  # ok. 1,1 km na północ
    assert far.status_code == 403 and far.json["kod"] == "za_daleko"
    bad = _report(client, typ="kot")
    assert bad.status_code == 400 and set(bad.json) == {"blad", "kod"}


def test_report_lifecycle_przyjete_w_realizacji_zrealizowane(client, demo):
    r = _report(client, komentarz="Worki obok kosza")
    assert r.status_code == 201 and r.json["numer"].startswith("TF-")
    nr = r.json["numer"]
    assert _report(client).status_code == 429  # ten sam telefon i kosz: raz na minutę
    s = client.get(f"/api/zgloszenia/{nr}").json
    assert s["status"] == "przyjete" and s["komentarz"] == "Worki obok kosza"
    kosz = _bin(client)
    assert kosz["zgloszenia_liczba"] >= 1 and kosz["zgloszenia"][0]["komentarz"] == "Worki obok kosza"

    trasa = client.get("/api/trasa").json
    assert trasa["przystanki"][0]["zgloszony"]  # zgłoszone kosze na górze listy kierowcy
    assert any(p["id"] == 18 and p["zgloszony"] for p in trasa["przystanki"])

    assert client.post("/api/odbiory", json={"kosz": 18, "akcja": "jade"}).status_code == 201
    assert client.get(f"/api/zgloszenia/{nr}").json["status"] == "w_realizacji"
    assert _bin(client)["kierowca_w_drodze"]

    done_before = client.get("/api/trasa").json["postep"]["zrobione"]
    assert client.post("/api/odbiory", json={"kosz": 18, "akcja": "oprozniono", "poziom": 100}).status_code == 201
    s = client.get(f"/api/zgloszenia/{nr}").json
    assert s["status"] == "zrealizowane" and all(k["o"] for k in s["kroki"])
    assert client.get("/api/trasa").json["postep"]["zrobione"] == done_before + 1
    assert _bin(client)["zgloszenia_liczba"] == 0


def test_driver_actions_validate_input(client, demo):
    assert client.post("/api/odbiory", json={"kosz": 18, "akcja": "oprozniono", "poziom": 33}).json["kod"] == "zly_poziom"
    assert client.post("/api/odbiory", json={"kosz": 18, "akcja": "problem", "problem": "x"}).json["kod"] == "zly_problem"
    assert client.post("/api/odbiory", json={"kosz": 18, "akcja": "lot"}).json["kod"] == "zla_akcja"
    assert client.post("/api/odbiory", json={"kosz": 99999, "akcja": "jade"}).status_code == 404
    ok = client.post("/api/odbiory", json={"kosz": 18, "akcja": "problem", "problem": "no_access", "notatka": "auto"})
    assert ok.status_code == 201


def test_jade_does_not_flag_bin_as_crew_problem(client, demo):
    from app.state import point_states
    client.post("/api/odbiory", json={"kosz": 18, "akcja": "jade"})
    assert point_states(clock.now())[18]["crew_issue"] is None


def test_api_errors_share_one_format(client, demo):
    for r in (client.get("/api/kosze/99999"), client.get("/api/zgloszenia/TF-99999"), client.get("/api/nie-ma"),
              client.get("/api/kosze?blisko=abc")):
        assert r.status_code in (400, 404) and set(r.json) == {"blad", "kod"}


def test_nearest_bins_sorted_by_distance(client, demo):
    p = Point.query.get(18)
    d = client.get(f"/api/kosze?blisko={p.lat},{p.lon}").json["kosze"]
    assert d[0]["id"] == 18 and d[0]["odleglosc_m"] == 0
    assert [k["odleglosc_m"] for k in d] == sorted(k["odleglosc_m"] for k in d)


def test_demo_reset_restores_start(client, demo):
    from app.models import Press
    _report(client)
    client.post("/api/odbiory", json={"kosz": 18, "akcja": "jade"})
    assert Press.query.filter(Press.wall_at.isnot(None)).count() == 1
    assert client.post("/api/demo/reset").status_code == 200
    assert Press.query.filter(Press.wall_at.isnot(None)).count() == 0  # zgłoszenia z pokazu znikają
    assert not _bin(client)["kierowca_w_drodze"]


def test_changes_version_moves_after_report(client, demo):
    v = client.get("/api/zmiany").json["wersja"]
    _report(client)
    assert client.get("/api/zmiany").json["wersja"] != v


def test_pilot_roi_from_careful_variant_and_env(monkeypatch):
    from app.methodology import pilot_roi
    city = {"careful": {"pln_month": 100_000.0, "bins": 2000}}  # 50 zł na kosz miesięcznie
    monkeypatch.setenv("COST_PANEL_PLN", "995")
    roi = pilot_roi(city)
    assert roi["saving_month"] == 2500 and roi["qr"]["net_month"] == 2200
    assert roi["panel"]["setup"] == 50 * 1000 and roi["panel"]["payback_months"] == round(50_000 / 2200, 1)
    monkeypatch.setenv("COST_HOSTING_MONTH_PLN", "3000")
    assert pilot_roi(city)["qr"]["payback_months"] is None  # hosting droższy niż oszczędność: brak zwrotu, nie liczba ujemna


def test_methodology_shows_pilot_and_ai_role(client, demo):
    html = client.get("/metodologia").get_data(as_text=True)
    assert 'id="pilotaz"' in html and "Zweryfikowane AI" in html and "EXIF" in html


def test_second_scenario_run_without_reset_starts_as_przyjete(client, demo):
    """Zegar demo stoi: wszystkie akcje mają tę samą minutę. Drugie zgłoszenie po odbiorze nie może być od razu zrealizowane."""
    nr1 = _report(client).json["numer"]
    client.post("/api/odbiory", json={"kosz": 18, "akcja": "jade"})
    client.post("/api/odbiory", json={"kosz": 18, "akcja": "oprozniono", "poziom": 100})
    assert client.get(f"/api/zgloszenia/{nr1}").json["status"] == "zrealizowane"
    nr2 = _report(client, klient="t2").json["numer"]
    s = client.get(f"/api/zgloszenia/{nr2}").json
    assert nr2 != nr1 and s["status"] == "przyjete" and not _bin(client)["kierowca_w_drodze"]


@pytest.mark.parametrize("bad", [{"lat": "nan"}, {"lat": "inf"}, {"dokladnosc": "nan", "lat": 0, "lon": 0}, {"typ": ["x"]},
                                 {"komentarz": 5}])
def test_report_input_cannot_bypass_geofence_or_crash(client, demo, bad):
    r = _report(client, **bad)
    assert r.status_code in (400, 403) or (r.status_code == 201 and "komentarz" in bad)


def test_non_object_json_and_huge_ids_and_extreme_dates_are_4xx(client, demo):
    assert client.post("/api/zgloszenia", json=[1]).status_code == 404  # brak kosza, nie 500
    assert client.post("/api/odbiory", json="x").status_code == 404
    assert client.post("/api/odbiory", json={"kosz": 18, "akcja": "problem", "problem": ["a"]}).status_code == 400
    assert client.get("/api/kosze/99999999999999999999").status_code == 404
    assert client.get("/api/zgloszenia/TF-99999999999999999999").status_code == 404
    assert client.get("/api/kosze?blisko=inf,0").status_code == 400
    for q in ("do=0001-01-01", "od=0001-01-01", "do=9999-12-31"):
        assert client.get(f"/api/dashboard/kpi?{q}").json["kod"] == "nieprawidlowa_data"
