"""Jakość obsługi na panelu miasta: norma 2 h, anomalie ekipy (> 150 m), trafność zgłoszeń, kolejka napraw.
Reguły na małych, ręcznie ułożonych danych (pusta baza z conftest)."""
import random
from datetime import timedelta

from app import db
from app.dashboard import Filters, accuracy, by_district, repair_queue, sla_pct, totals
from app.history import FAR_ANOMALY_SHARE, far_m
from app.models import Emptying, Pickup, Point, Press, Report, ReportHistory
from app.simulation import DEMO_NOW

NOW = DEMO_NOW
DAY = Filters(od=NOW - timedelta(days=1), do=NOW + timedelta(seconds=1))


def _point(district="Stare Miasto", n=1):
    p = Point(osm_id=f"node/{district}-{n}", kind="bin", area="Rynek", lat=50.06, lon=19.94, name=f"Kosz {n}", base_rate=1.0,
              district=district, address=f"ul. Testowa {n}")
    db.session.add(p)
    db.session.flush()
    return p


def _hist(p, created, resolved):
    db.session.add(ReportHistory(point_id=p.id, created_at=created, resolved_at=resolved, kind="przepelniony"))


def test_sla_share_counts_only_judged_reports_and_includes_exactly_two_hours():
    p = _point()
    t0 = NOW - timedelta(hours=10)
    _hist(p, t0, t0 + timedelta(hours=1, minutes=59))  # w normie
    _hist(p, t0, t0 + timedelta(hours=2))  # dokładnie 2 h: w normie
    _hist(p, t0, t0 + timedelta(hours=2, minutes=1))  # po normie
    _hist(p, NOW - timedelta(hours=3), None)  # otwarte > 2 h: norma przekroczona
    _hist(p, NOW - timedelta(minutes=30), None)  # otwarte 30 min: jeszcze nieocenione
    _hist(p, t0, NOW + timedelta(hours=1))  # zamknięte „w przyszłości” zegara = otwarte teraz, 10 h → po normie
    db.session.commit()
    t = totals(DAY, NOW)
    assert (t["zgloszenia"], t["sla_ok"], t["sla_ocenione"]) == (6, 2, 5)
    assert sla_pct(t) == 40
    assert by_district(DAY, NOW)["Stare Miasto"]["sla_ok"] == 2


def test_sla_without_judged_reports_is_none():
    p = _point()
    _hist(p, NOW - timedelta(minutes=10), None)
    db.session.commit()
    assert sla_pct(totals(DAY, NOW)) is None


def _pickup(p, far):
    db.session.add(Pickup(point_id=p.id, at=NOW - timedelta(hours=2), fraction="zmieszane", mass_kg=5, cost_pln=50, km=0.4,
                          fill_pct=80, on_demand=False, far_m=far))


def test_anomaly_threshold_is_strictly_more_than_150_m_and_counts_live_emptyings():
    sm, kr = _point(), _point("Krowodrza", 2)
    for far in (10, 150, 151, None):
        _pickup(sm, far)
    _pickup(kr, 900)
    db.session.add(Emptying(point_id=sm.id, at=NOW - timedelta(hours=1), level=75, source="crew", far_m=400))
    db.session.add(Emptying(point_id=sm.id, at=NOW - timedelta(hours=1), level=75, source=None, far_m=999))  # symulacja: nie
    db.session.commit()
    t = totals(DAY, NOW)
    assert (t["wywozy"], t["anomalie"]) == (6, 3)
    rows = by_district(DAY, NOW)
    assert (rows["Stare Miasto"]["wywozy"], rows["Stare Miasto"]["anomalie"]) == (5, 2)
    assert rows["Krowodrza"]["anomalie"] == 1


def test_anomaly_card_api(client):
    p = _point()
    _pickup(p, 151)
    _pickup(p, 20)
    db.session.commit()
    d = client.get("/api/dashboard/wykresy/anomalie").json
    assert d["prog_m"] == 150 and [(a["kosz"], a["odleglosc_m"], a["dzielnica"]) for a in d["lista"]] == [("Kosz 1", 151, "Stare Miasto")]
    j = client.get("/api/dashboard/wykresy/jakosc").json["dzielnice"]
    assert j == [{"dzielnica": "Stare Miasto", "sla_2h_pct": None, "sla_ocenione": 0, "wywozy": 2, "anomalie": 1,
                  "anomalie_pct": 50.0, "trafnosc_pct": None, "trafnosc_rozstrzygniete": 0}]


def test_history_far_m_mostly_small_with_small_anomaly_share():
    rng = random.Random("2026:far")
    draws = [far_m(rng) for _ in range(20_000)]
    share = sum(d > 150 for d in draws) / len(draws)
    assert abs(share - FAR_ANOMALY_SHARE) < 0.005
    assert sorted(draws)[len(draws) // 2] < 20  # mediana: rozrzut GPS przy koszu
    assert draws[:50] == [far_m(r) for r in [random.Random("2026:far")] for _ in range(50)]  # deterministycznie


def _report(p, first_at, hit, resolved_at=None, kind=None, note=None):
    r = Report(point_id=p.id, first_at=first_at, last_at=first_at, presses=1, weight=0.7, hit=hit, resolved_at=resolved_at)
    db.session.add(r)
    db.session.flush()
    db.session.add(Press(point_id=p.id, at=first_at, report_id=r.id, kind=kind, note=note, wall_at=first_at))
    return r


def test_accuracy_per_district_counts_resolved_fill_reports_only():
    sm, gr = _point(), _point("Grzegórzki", 2)
    t = NOW - timedelta(hours=5)
    for hit in (True, True, True, False):
        _report(sm, t, hit, resolved_at=t + timedelta(hours=1))
    _report(sm, t, None)  # otwarte
    _report(sm, t, False, resolved_at=t + timedelta(hours=1), kind="damaged")  # „uszkodzony”: nie o zapełnieniu
    _report(sm, t, True, resolved_at=NOW + timedelta(hours=2))  # rozstrzygnięte dopiero w przyszłości zegara
    _report(gr, t, False, resolved_at=t + timedelta(hours=1), kind="overflow")
    db.session.commit()
    assert accuracy(DAY, NOW) == {"Stare Miasto": (3, 4), "Grzegórzki": (0, 1)}
    assert accuracy(Filters(od=DAY.od, do=DAY.do, district="Grzegórzki"), NOW) == {"Grzegórzki": (0, 1)}


def test_repair_queue_status_and_term(client):
    p, q = _point(), _point("Krowodrza", 2)
    late = _report(p, NOW - timedelta(hours=25), None, kind="damaged", note="Urwana pokrywa")
    db.session.add(Press(point_id=p.id, at=NOW - timedelta(hours=24), report_id=late.id, kind="damaged", note="Dalej urwana"))
    _report(q, NOW - timedelta(hours=1), None, kind="damaged")
    _report(p, NOW - timedelta(hours=3), True, resolved_at=NOW - timedelta(hours=2), kind="damaged")  # rozstrzygnięte
    _report(p, NOW - timedelta(hours=2), None, kind="full")  # nie uszkodzenie
    _report(p, NOW + timedelta(hours=1), None, kind="damaged")  # w przyszłości zegara demo
    db.session.commit()
    items = repair_queue(NOW)
    assert [(i["point"].id, i["late"], i["due"], i["presses"], i["note"]) for i in items] == [
        (p.id, True, NOW - timedelta(hours=1), 2, "Urwana pokrywa"), (q.id, False, NOW + timedelta(hours=23), 1, None)]
    d = client.get("/api/naprawy").json
    assert d["meta"]["sla_h"] == 24
    first, second = d["naprawy"]
    assert (first["status"], first["po_terminie"], first["termin"], first["komentarz"]) == (
        "po terminie", True, (NOW - timedelta(hours=1)).isoformat(), "Urwana pokrywa")
    assert first["adres"] == "ul. Testowa 1" and first["zgloszono"] == (NOW - timedelta(hours=25)).isoformat()
    assert (second["status"], second["komentarz"], second["dzielnica"]) == ("w terminie", "", "Krowodrza")
    assert [x["kosz_id"] for x in client.get("/api/naprawy?dzielnica=Krowodrza").json["naprawy"]] == [q.id]


def test_repair_queue_bad_filter_and_empty(client):
    r = client.get("/api/naprawy?dzielnica=Atlantyda")
    assert r.status_code == 400 and r.json["kod"] == "nieznana_dzielnica" and r.json["blad"]
    assert client.get("/api/naprawy").json["naprawy"] == []
