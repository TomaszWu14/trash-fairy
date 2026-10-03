"""Panel miasta: punkty miasta, historia syntetyczna, agregacje i API. Jedna baza na moduł (seed ~10 s)."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import func

from app import clock, comparison, create_app, db, forecast, methodology, state
from app.dashboard import Filters, pickup_totals, project_effect
from app.events import import_events
from app.history import FRACTIONS, PROJECTS, generate_history
from app.models import Emptying, Pickup, Point, Press, Project, Report, ReportHistory
from app.osm_import import import_city_points, import_points, load_cache
from app.reports import record_press
from app.simulation import DEMO_NOW, hour_floor


CONFIG = {"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True, "OSRM_URL": "", "WEATHER_URL": "",
          "TOMTOM_API_KEY": "", "TWILIO_ACCOUNT_SID": "", "TWILIO_AUTH_TOKEN": "", "TWILIO_VERIFY_SID": "",
          "SMS_DEMO_FALLBACK": "1", "DEMO_PASSWORD": "test-haslo"}
SIM_START = hour_floor(DEMO_NOW) - timedelta(weeks=8)


@pytest.fixture(scope="module")
def app():
    """Prawdziwe dane jak `flask seed`: 72 punkty demo z cache OSM, wydarzenia, punkty miasta, 8 tygodni symulacji."""
    for m in (forecast, comparison, state):
        m.clear_cache()
    app = create_app(CONFIG)
    with app.app_context():
        import_points(load_cache())
        import_events()
        import_city_points()
        clock.reset()
        yield app
    for m in (forecast, comparison, state):
        m.clear_cache()


def _history_fingerprint():
    p = db.session.query(func.count(Pickup.id), func.sum(Pickup.mass_kg), func.sum(Pickup.cost_pln),
                         func.sum(Pickup.fill_pct)).one()
    r = db.session.query(func.count(ReportHistory.id), func.min(ReportHistory.created_at),
                         func.max(ReportHistory.created_at)).one()
    snap = db.session.query(func.sum(Point.snapshot_fill)).scalar()
    effects = sorted((pr.slug, pr.effect_label) for pr in Project.query)
    return tuple(p), tuple(r), snap, effects


def test_slide_numbers_unchanged_with_city_points():
    """Liczby ze slajdów liczy silnik tylko na 72 punktach demo — punkty miasta niczego w nich nie zmieniają."""
    assert Point.live_query().count() == 72
    assert Point.query.filter(Point.live.is_(False)).count() >= 128  # razem 200–230
    r = comparison.compare(DEMO_NOW)
    assert (r["fixed"]["bin"]["empty_share"], r["fairy"]["bin"]["empty_share"]) == (57, 27)
    assert (r["fixed"]["shelter"]["overflow_hours"], r["fairy"]["shelter"]["overflow_hours"]) == (338, 0)
    assert (r["fixed"]["total"]["visits"], r["fairy"]["total"]["visits"]) == (3480, 2678)
    q = forecast.forecast_quality(hour_floor(DEMO_NOW))
    assert (q["mae"], q["naive_mae"]) == (2.4, 7.1)
    city = methodology.city_scale(r)
    assert (city["careful"]["pln_year"], city["full"]["pln_year"]) == (1_470_000, 2_780_000)


def test_city_points_after_live_with_district_fraction_address():
    live_max = db.session.query(func.max(Point.id)).filter(Point.live.is_(True)).scalar()
    city = Point.query.filter(Point.live.is_(False)).all()
    assert min(p.id for p in city) > live_max
    assert {p.district for p in city} == {"Stare Miasto", "Grzegórzki", "Krowodrza", "Podgórze", "Nowa Huta", "Dębniki"}
    assert all(p.fraction in FRACTIONS and p.address and p.snapshot_fill is not None for p in city)
    assert {p.district for p in Point.live_query()} == {"Stare Miasto", "Grzegórzki"}


def test_generator_is_deterministic():
    before = _history_fingerprint()
    generate_history(sim_start=SIM_START)
    assert _history_fingerprint() == before
    assert before[0][0] > 40_000  # 12 miesięcy odbiorów


def test_history_covers_all_points_for_twelve_months():
    """Historia obejmuje też 72 punkty demo aż do DEMO_NOW (symulacja silnika nie jest danymi panelu)."""
    live = db.session.query(Point.id).filter(Point.live.is_(True))
    last = db.session.query(func.max(Pickup.at)).filter(Pickup.point_id.in_(live)).scalar()
    assert DEMO_NOW - timedelta(hours=12) < last <= DEMO_NOW
    assert db.session.query(func.count(func.distinct(Pickup.point_id))).scalar() == Point.query.count()


def test_kpi_shape_and_synthetic_label(client):
    d = client.get("/api/dashboard/kpi").json
    assert d["meta"]["syntetyczne"] is True and d["meta"]["etykieta"] == "Ostatnie 30 dni"
    assert [k["id"] for k in d["kpi"]] == ["koszt", "wywozy", "zapelnienie", "zgloszenia", "czas_reakcji",
                                           "oszczednosci", "co2"]
    assert all(len(k["trend"]) == 12 and k["lepiej_gdy"] in ("mniej", "wiecej") for k in d["kpi"])
    kpi = {k["id"]: k for k in d["kpi"]}
    assert kpi["wywozy"]["wartosc"] > 0 and "kursy" in kpi["oszczednosci"]


def _kpi(client, query=""):
    return {k["id"]: k["wartosc"] for k in client.get(f"/api/dashboard/kpi?{query}").json["kpi"]}


@pytest.mark.parametrize("query", ["okres=kwartal", "okres=rok&frakcja=szklo", "dzielnica=Nowa%20Huta"])
def test_district_chart_sums_to_kpi(client, query):
    d = client.get(f"/api/dashboard/wykresy/dzielnice?{query}").json
    kpi = _kpi(client, query)
    cost = sum(v for s in d["serie"] for v in s["koszt"])
    assert cost == pytest.approx(kpi["koszt"], abs=0.01 * len(d["dzielnice"]) * len(d["serie"]))
    assert sum(v for s in d["serie"] for v in s["wywozy"]) == kpi["wywozy"]


def test_fraction_masses_sum_to_total_mass(client):
    d = client.get("/api/dashboard/wykresy/frakcje?okres=kwartal").json
    f = Filters(od=datetime.fromisoformat(d["meta"]["od"]), do=clock.now() + timedelta(seconds=1))
    total_t = float(pickup_totals(f, clock.now())["masa"]) / 1000
    assert sum(x["masa_t"] for x in d["frakcje"]) == pytest.approx(total_t, abs=0.005)
    assert {x["frakcja"] for x in d["frakcje"]} == set(FRACTIONS)


@pytest.mark.parametrize("query,expected", [
    ("dzielnica=Krowodrza", lambda q: q.filter(Point.district == "Krowodrza")),
    ("frakcja=szklo", lambda q: q.filter(Point.fraction == "szklo")),
    ("projekt=odbiory-na-zadanie-stare-miasto", lambda q: q.filter(Point.district == "Stare Miasto")),
])
def test_map_points_match_filters(client, query, expected):
    d = client.get(f"/api/dashboard/wykresy/mapa?{query}").json
    assert len(d["kosze"]) == expected(Point.query).count() > 0
    assert all(k["zapelnienie"] is not None and 0 <= k["zapelnienie"] <= 100 for k in d["kosze"])
    assert all(len(h) == 3 for h in d["goraco"])


def test_other_charts_shapes(client):
    k = client.get("/api/dashboard/wykresy/koszty").json
    assert len(k["miesiace"]) == len(k["rzeczywiste"]) == len(k["plan"]) == 12 and k["wdrozenie"] == "2026-05"
    pilot = k["miesiace"].index("2026-06")
    assert k["plan"][pilot] > k["rzeczywiste"][pilot]  # odbiory na żądanie: mniej kursów niż w planie
    z = client.get("/api/dashboard/wykresy/zgloszenia").json
    assert len(z["liczba"]) == len(z["czas_reakcji_h"]) == 12
    h = client.get("/api/dashboard/wykresy/heatmapa?okres=rok").json
    assert len(h["dane"]) == 7 * 24 and sum(c[2] for c in h["dane"]) == _kpi(client, "okres=rok")["zgloszenia"]


@pytest.mark.parametrize("url,status,kod", [
    ("/api/dashboard/kpi?okres=tydzien", 400, "nieznany_okres"),
    ("/api/dashboard/kpi?dzielnica=Atlantyda", 400, "nieznana_dzielnica"),
    ("/api/dashboard/kpi?frakcja=plutonium", 400, "nieznana_frakcja"),
    ("/api/dashboard/kpi?projekt=nie-ma", 400, "nieznany_projekt"),
    ("/api/dashboard/kpi?od=wczoraj", 400, "nieprawidlowa_data"),
    ("/api/dashboard/kpi?od=2026-09-10&do=2026-09-01", 400, "nieprawidlowy_zakres"),
    ("/api/dashboard/kpi?projekt=pilotaz-czujnikow-nowa-huta&dzielnica=Krowodrza", 400, "sprzeczne_filtry"),
    ("/api/dashboard/wykresy/mapa?frakcja=x", 400, "nieznana_frakcja"),
    ("/api/projekty?okres=x", 400, "nieznany_okres"),
    ("/api/dashboard/wykresy/kolowy", 404, "nieznany_wykres"),
    ("/api/projekty/nie-ma", 404, "nieznany_projekt"),
])
def test_bad_filters_give_polish_error(client, url, status, kod):
    r = client.get(url)
    assert r.status_code == status and r.json["kod"] == kod and r.json["blad"]


@pytest.mark.parametrize("query", ["dzielnica=Grzeg%C3%B3rzki&frakcja=bio", "od=2027-01-01&do=2027-01-31"])
def test_empty_result_is_zeros_not_error(client, query):
    r = client.get(f"/api/dashboard/kpi?{query}")
    assert r.status_code == 200
    kpi = {k["id"]: k for k in r.json["kpi"]}
    assert kpi["koszt"]["wartosc"] == 0 and kpi["wywozy"]["wartosc"] == 0 and kpi["zapelnienie"]["wartosc"] is None
    for name in ("frakcje", "dzielnice", "koszty", "zgloszenia", "heatmapa", "mapa"):
        assert client.get(f"/api/dashboard/wykresy/{name}?{query}").status_code == 200


def test_projects_effects_computed_from_history(client):
    d = client.get("/api/projekty").json
    assert d["meta"]["syntetyczne"] is True
    projects = {p["slug"]: p for p in d["projekty"]}
    assert set(projects) == {p["slug"] for p in PROJECTS}
    for pr in Project.query:
        assert projects[pr.slug]["efekt_wartosc"] == project_effect(pr, DEMO_NOW)[0]
        assert len(projects[pr.slug]["trend"]) == 12
    assert -25 <= projects["odbiory-na-zadanie-stare-miasto"]["efekt_wartosc"] <= -10
    assert projects["pilotaz-czujnikow-nowa-huta"]["efekt_wartosc"] < 0
    assert projects["edukacja-segregacji-podgorze"]["efekt_wartosc"] < 0
    assert projects["przyciski-zgloszen-debniki"]["efekt_wartosc"] is None
    detail = client.get("/api/projekty/pilotaz-czujnikow-nowa-huta").json["projekt"]
    pp = detail["przed_po"]
    assert pp["start"] == "2026-07" and len(pp["koszt"]) == len(pp["wywozy"]) == 12
    assert pp["podsumowanie"]["po"]["czas_reakcji"] < pp["podsumowanie"]["przed"]["czas_reakcji"]


def test_live_emptying_counts_immediately(client):
    """Opróżnienie z PWA kierowcy (Emptying) wchodzi do liczników panelu od razu (UNION z historią)."""
    before = _kpi(client)["wywozy"]

    pid = Point.live_query().filter_by(kind="bin").first().id
    assert client.post("/api/odbiory", json={"kosz": pid, "akcja": "oprozniono", "poziom": 75}).status_code == 201
    try:
        assert _kpi(client)["wywozy"] == before + 1
    finally:  # baza modułu jest wspólna: sprzątamy
        Emptying.query.filter_by(source="crew").delete()
        db.session.commit()


def test_simulated_emptying_does_not_count(client):
    """Symulowane opróżnienie (source=None, stały harmonogram silnika) nie zmienia KPI panelu."""
    before = _kpi(client)
    pid = Point.live_query().filter_by(kind="bin").first().id
    db.session.add(Emptying(point_id=pid, at=clock.now(), level=50))
    db.session.commit()
    try:
        assert _kpi(client) == before
    finally:
        Emptying.query.filter(Emptying.at == clock.now(), Emptying.source.is_(None)).delete()
        db.session.commit()


def test_live_report_counts_and_simulated_does_not(client):
    """Zgłoszenie na żywo (naciśnięcie z wall_at) zwiększa zgłoszenia; symulowane naciśnięcie (bez wall_at) — nie."""
    before = _kpi(client)["zgloszenia"]
    pids = [p.id for p in Point.live_query().filter_by(kind="bin").order_by(Point.id).limit(2)]
    record_press(pids[0], clock.now())  # jak symulacja: wall_at = None
    db.session.commit()
    assert _kpi(client)["zgloszenia"] == before
    record_press(pids[1], clock.now(), wall_at=datetime(2026, 10, 3, 11, 30))
    db.session.commit()
    try:
        assert _kpi(client)["zgloszenia"] == before + 1
    finally:
        Press.query.filter(Press.at == clock.now()).delete()
        Report.query.filter(Report.first_at == clock.now()).delete()
        db.session.commit()


def test_last_30_days_show_rollout_effect(client):
    kpi = {k["id"]: k for k in client.get("/api/dashboard/kpi").json["kpi"]}
    assert kpi["oszczednosci"]["wartosc"] > 0 and kpi["oszczednosci"]["kursy"] > 0
    sm = {k["id"]: k for k in client.get("/api/dashboard/kpi?dzielnica=Stare%20Miasto&okres=rok").json["kpi"]}
    trend = sm["czas_reakcji"]["trend"]
    assert max(trend[6:11]) < min(trend[:6])  # po wdrożeniu (05.2026) reakcja szybsza w każdym miesiącu


def test_engine_api_ignores_city_points(client):
    city = Point.query.filter(Point.live.is_(False)).first()
    assert client.get(f"/api/points/{city.id}").status_code == 404
    assert all(f["properties"]["id"] != city.id for f in client.get("/api/v1/bins.geojson").json["features"])
