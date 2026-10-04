"""Oszczędności wobec planu: koszt odbioru z bieżących założeń (nie z zapisanej kolumny), pola kafla KPI i ich spójność.
Małe, ręcznie ułożone dane (pusta baza z conftest): dzielnica kontrolna (Dębniki, bez projektu) i Stare Miasto (projekt)."""
from datetime import date, datetime, timedelta

import pytest

from app import db, methodology
from app.dashboard import Filters, pickup_totals
from app.history import COST_PER_TONNE_PLN, cost_pln
from app.models import Pickup, Point
from app.simulation import DEMO_NOW

NOW = DEMO_NOW
MASS, KM = 10.0, 1.0


def _point(district, n):
    p = Point(osm_id=f"node/{district}-{n}", kind="bin", area="Rynek", lat=50.06, lon=19.94, name=f"Kosz {n}", base_rate=1.0,
              district=district, address=f"ul. Testowa {n}", live=False)
    db.session.add(p)
    db.session.flush()
    return p


def _pickup(p, at, stored_cost=999.0):
    db.session.add(Pickup(point_id=p.id, at=at, fraction="zmieszane", mass_kg=MASS, cost_pln=stored_cost, km=KM, fill_pct=80,
                          on_demand=False, far_m=10))


@pytest.fixture
def data():
    """Baza planu (1.11.2025–30.04.2026): oba kosze codziennie. Ostatnie 30 dni: kontrola codziennie, Stare Miasto co drugi
    dzień → plan 60 odbiorów i 60 km, faktycznie 45 → 15 odbiorów i 15 km mniej."""
    ctrl, sm = _point("Dębniki", 1), _point("Stare Miasto", 2)
    day = datetime(2025, 11, 1, 10)
    while day < datetime(2026, 5, 1):
        _pickup(ctrl, day)
        _pickup(sm, day)
        day += timedelta(days=1)
    for k in range(30):
        _pickup(ctrl, NOW - timedelta(days=k, hours=1))
        if k % 2 == 0:
            _pickup(sm, NOW - timedelta(days=k, hours=1))
    db.session.commit()


def test_history_cost_uses_current_assumptions_not_stored_column(monkeypatch):
    p = _point("Dębniki", 1)
    _pickup(p, NOW - timedelta(hours=1), stored_cost=999.0)
    db.session.commit()
    f = Filters(od=NOW - timedelta(days=1), do=NOW + timedelta(seconds=1))
    a = methodology.money_assumptions()
    assert pickup_totals(f, NOW)["koszt"] == pytest.approx(cost_pln(MASS, KM, a))
    monkeypatch.setenv("COST_PER_VISIT_PLN", "12")  # nowa stawka działa bez ponownego generowania historii
    assert pickup_totals(f, NOW)["koszt"] == pytest.approx(12 + KM * a["cost_per_km"] + MASS * COST_PER_TONNE_PLN / 1000)


def test_savings_tile_fields_and_consistency(client, data):
    kpi = {k["id"]: k for k in client.get("/api/dashboard/kpi").json["kpi"]}
    s, a = kpi["oszczednosci"], methodology.money_assumptions()
    assert s["odbiory_mniej"] == 15 and "kursy" not in s and s["km_mniej"] == pytest.approx(15, abs=0.1)
    assert s["plan"]["odbiory"] == 60 and s["faktycznie"] == {"odbiory": 45, "km": 45.0}
    assert s["stawki"]["odbior_zl"] == a["cost_per_visit"] and s["stawki"]["km_zl"] == a["cost_per_km"]
    assert s["wartosc"] == pytest.approx(15 * a["cost_per_visit"] + 15 * a["cost_per_km"], abs=0.01)
    assert s["skladniki"]["odbiory_zl"] + s["skladniki"]["km_zl"] == pytest.approx(s["wartosc"], abs=0.02)
    assert s["okres"]["dni"] == 30 and s["okres"]["od"] == (NOW - timedelta(days=30)).date().isoformat()
    assert s["okres"]["do"] == NOW.date().isoformat()
    assert abs(s["dziennie"] * s["okres"]["dni"] - s["wartosc"]) < 1
    assert s["miesiac"] == pytest.approx(s["dziennie"] * 30, abs=0.01) and s["rok"] == pytest.approx(s["dziennie"] * 365, abs=0.01)
    stop_min = a.get("stop_min", 3)
    assert s["godziny_ekip"] == pytest.approx(15 * stop_min / 60)
    assert s["podpis"].startswith("15 odbiorów mniej · ") and "h pracy ekip" in s["podpis"]
    assert s["kosze"] == 2 and "grupa kontrolna" in s["plan_opis"] and "1.11.2025" in s["plan_opis"]
    # decyzja 2: 12 zł jako jawne założenie z rozpisaniem (3 osoby × 45 zł/h + pojazd 105 zł/h) × 3 min
    assert s["stawki"]["odbior_rozpisanie"] == {"osoby": 3, "zl_osoba_h": 45, "pojazd_zl_h": 105, "zl_h": 240}
    assert "założenie: ok. 3 min postoju × (3 osoby × 45 zł/h + pojazd 105 zł/h) = 12 zł" in s["plan_opis"]
    assert "/metodologia#koszt-odbioru" in s["plan_opis"]
    assert kpi["wywozy"]["etykieta"] == "Odbiory" and kpi["koszt"]["etykieta"] == "Koszt odbiorów"
    assert kpi["co2"]["opis"] and "przed_wdrozeniem" in kpi["zapelnienie"]


def test_overridden_visit_rate_is_not_broken_down(client, data, monkeypatch):
    monkeypatch.setenv("COST_PER_VISIT_PLN", "15")
    s = {k["id"]: k for k in client.get("/api/dashboard/kpi").json["kpi"]}["oszczednosci"]
    assert s["stawki"]["odbior_zl"] == 15 and s["stawki"]["odbior_rozpisanie"] is None
    assert "15 zł (stawka z konfiguracji)" in s["plan_opis"]


def test_savings_tile_follows_filters(client, data):
    s = {k["id"]: k for k in client.get("/api/dashboard/kpi?dzielnica=D%C4%99bniki").json["kpi"]}["oszczednosci"]
    assert s["odbiory_mniej"] == 0 and s["kosze"] == 1  # kontrola sama w sobie: plan = rzeczywistość
    s = {k["id"]: k for k in client.get("/api/dashboard/kpi?od=2026-09-01&do=2026-09-30").json["kpi"]}["oszczednosci"]
    assert s["okres"] == {"od": "2026-09-01", "do": "2026-09-30", "dni": 30} and "1–30.09.2026" in s["podpis"]


def test_polish_formatting_helpers():
    from app.dashboard import pl_num, pl_range, plural
    assert [plural(n, "odbiór", "odbiory", "odbiorów") for n in (1, 3, 5, 12, 22, 668)] == [
        "odbiór", "odbiory", "odbiorów", "odbiorów", "odbiory", "odbiorów"]
    assert pl_num(1234.5, 1) == "1\u00a0234,5" and pl_num(33.0, 1) == "33" and pl_num(12) == "12"
    assert pl_range(date(2026, 9, 1), date(2026, 9, 30)) == "1–30.09.2026"
    assert pl_range(date(2026, 9, 3), date(2026, 10, 2)) == "3.09–2.10.2026"
