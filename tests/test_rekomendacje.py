"""Rekomendacje z danych: drabinka „Miejsca podrzucania odpadów”, punkty zaangażowania ekipy i endpoint panelu.
Reguły na małych, ręcznie ułożonych danych (pusta baza z conftest)."""
from datetime import datetime, timedelta

import pytest

from app import db
from app.crew_points import PTS_DUMPING, PTS_NEED_BIN, PTS_PHOTO, crew_points, need_bin_suggestions
from app.dumping import dumping_sites, level
from app.models import PhotoAnalysis, Point, ReportHistory, StopIssue
from app.reports import record_press
from app.simulation import DEMO_NOW

NOW = DEMO_NOW  # sobota 3.10.2026
SAT = [NOW - timedelta(days=7 * k, hours=2) for k in range(1, 8)]  # kolejne soboty wstecz
LAT, LON = 50.06, 19.94


def _point(n, lat=LAT, lon=LON, district="Grzegórzki"):
    p = Point(osm_id=f"node/t-{n}", kind="bin", area="Grzegórzki", lat=lat, lon=lon, name=f"Kosz {n}", base_rate=1.0,
              district=district, address=f"ul. Testowa {n}")
    db.session.add(p)
    db.session.flush()
    return p


def _hist(p, at, kind="odpady_obok"):
    db.session.add(ReportHistory(point_id=p.id, created_at=at, resolved_at=at + timedelta(hours=3), kind=kind))


def _photo(p, at, **kw):
    pa = PhotoAnalysis(point_id=p.id, at=at, wall_at=datetime(2026, 10, 3), status="done", source="crew",
                       **({"confidence": 0.9, "misuse": [], "overflow_outside": False} | kw))
    db.session.add(pa)
    return pa


@pytest.mark.parametrize("n,top,expected", [
    (1, 1, None), (2, 1, "tablica"), (3, 3, "tablica"),  # dzień tygodnia liczy się dopiero od progu kontroli
    (4, 1, "kontrola"), (4, 2, "fotopulapka"), (5, 2, "kontrola"), (5, 3, "fotopulapka"), (6, 1, "fotopulapka"),
])
def test_ladder_thresholds(n, top, expected):
    assert level(n, top) == expected


def test_dumping_sites_sources_window_and_weekday():
    sign, camera, quiet = _point(1), _point(2, lat=LAT + 0.01), _point(3, lat=LAT + 0.02)
    _hist(sign, NOW - timedelta(days=3))
    _hist(sign, NOW - timedelta(days=40))
    _hist(sign, NOW - timedelta(days=100))  # poza oknem 90 dni
    _hist(sign, NOW - timedelta(days=5), kind="przepelniony")  # inny rodzaj zgłoszenia
    _hist(camera, SAT[0])
    _hist(camera, SAT[1])
    db.session.add(StopIssue(point_id=camera.id, at=SAT[2], kind="overflow"))  # kierowca: odpady obok kosza
    _photo(camera, SAT[3], misuse=["household_bag"])  # zdjęcie ekipy z workami domowymi
    _photo(camera, NOW - timedelta(days=2), misuse=["clothes"])  # inne nadużycie: nie jest sygnałem
    _hist(quiet, NOW - timedelta(days=1))
    db.session.commit()
    record_press(camera.id, NOW - timedelta(days=1), wall_at=datetime(2026, 10, 3, 11), kind="overflow")  # na żywo, piątek

    sites = {s["kosz_id"]: s for s in dumping_sites(NOW)}
    assert set(sites) == {sign.id, camera.id}
    assert sites[sign.id]["poziom"] == "tablica" and sites[sign.id]["sygnaly"] == 2
    c = sites[camera.id]
    assert c["sygnaly"] == 5 and c["zrodla"] == {"mieszkancy": 3, "kierowcy": 1, "zdjecia_ekip": 1} and c["zdjecia"] == 1
    assert c["dzien_tygodnia"] == "sobota" and c["dzien_sygnaly"] == 4
    assert c["poziom"] == "fotopulapka" and c["poziom_etykieta"] == "Rozważ fotopułapkę (decyzja gminy)"
    assert c["uzasadnienie"].startswith("5 sygnałów odpadów obok kosza w 90 dni") and "w sobotę" in c["uzasadnienie"]
    assert [s["kosz_id"] for s in dumping_sites(NOW)] == [camera.id, sign.id]  # najpoważniejsze pierwsze


def test_crew_points_only_for_confirmed_signals():
    a, b, far = _point(1), _point(2, lat=LAT + 0.0005), _point(3, lat=LAT + 0.05)  # b ok. 56 m od a
    _photo(a, NOW - timedelta(hours=5), crew_level=75, fill_level=75)  # odbiór, zdjęcie zgodne: +1
    _photo(a, NOW - timedelta(hours=6), crew_level=75, fill_level=25)  # rozbieżność 50 p.p.: 0
    _photo(a, NOW - timedelta(hours=7), crew_level=75, fill_level=75, confidence=0.5)  # niska pewność: 0
    db.session.add(StopIssue(point_id=b.id, at=NOW - timedelta(hours=3), kind="overflow"))
    _photo(b, NOW - timedelta(hours=3, minutes=10), overflow_outside=True)  # zdjęcie pokazuje odpady obok: +3
    db.session.add(StopIssue(point_id=far.id, at=NOW - timedelta(hours=2), kind="overflow"))  # bez zdjęcia: 0
    _hist(a, NOW - timedelta(days=2), kind="przepelniony")
    _hist(a, NOW - timedelta(days=4), kind="przepelniony")  # 2 zgłoszenia mieszkańców w 30 dni przy a
    db.session.add(StopIssue(point_id=b.id, at=NOW - timedelta(hours=1), kind="need_bin", note="przystanek"))  # 56 m od a: +5
    db.session.add(StopIssue(point_id=far.id, at=NOW - timedelta(hours=1), kind="need_bin"))  # nic w 100 m: 0
    db.session.commit()

    sugg = {s["kosz_id"]: s for s in need_bin_suggestions(NOW, [])}
    assert sugg[b.id]["potwierdzona"] and "2 zgłoszenia mieszkańców" in sugg[b.id]["powod"]
    assert not sugg[far.id]["potwierdzona"] and sugg[far.id]["punkty"] == 0
    rec = [{"point_id": far.id, "type": "bigger", "label": "większy kosz"}]
    assert {s["kosz_id"]: s for s in need_bin_suggestions(NOW, rec)}[far.id]["potwierdzona"]  # rekomendacja z danych

    pts = crew_points(NOW, list(sugg.values()))
    assert pts["trasa"] == "K-07" and pts["suma"] == PTS_PHOTO + PTS_DUMPING + PTS_NEED_BIN
    assert sorted(x["rodzaj"] for x in pts["pozycje"]) == ["odbior_ze_zdjeciem", "podrzucenie_ze_zdjeciem", "sugestia_kosza"]
    assert [r["punkty"] for r in pts["zasady"]] == [1, 3, 5, 3, 2]  # +3 i +2 za dzikie wysypiska (app/wysypiska.py)


def test_click_series_is_one_signal_and_one_point_award():
    """Seria kliknięć z jednej wizyty: jeden sygnał podrzucenia i jedna pozycja punktów (nie za liczbę kliknięć)."""
    p, q = _point(1), _point(2, lat=LAT + 0.01)
    for k in range(4):  # 4× „Odpady obok kosza” w tej samej minucie
        db.session.add(StopIssue(point_id=p.id, at=NOW - timedelta(hours=2, seconds=k), kind="overflow"))
    _photo(p, NOW - timedelta(hours=2, minutes=5), misuse=["household_bag"], overflow_outside=True)  # dowód, nie sygnał
    for k in range(3):  # ta sama sugestia kosza 3 razy
        db.session.add(StopIssue(point_id=q.id, at=NOW - timedelta(hours=1, minutes=k), kind="need_bin"))
    _hist(q, NOW - timedelta(days=2), kind="przepelniony")
    _hist(q, NOW - timedelta(days=3), kind="przepelniony")
    db.session.commit()

    assert dumping_sites(NOW) == []  # 1 sygnał: poniżej progu tablicy
    sugg = need_bin_suggestions(NOW, [])
    assert [s["punkty"] for s in sugg] == [0, 0, PTS_NEED_BIN]  # punkty za pierwszą (najstarszą), lista od najnowszych
    pts = crew_points(NOW, sugg)
    assert pts["suma"] == PTS_DUMPING + PTS_NEED_BIN
    assert sorted(x["rodzaj"] for x in pts["pozycje"]) == ["podrzucenie_ze_zdjeciem", "sugestia_kosza"]


def test_endpoint_shape(client):
    p = _point(1)
    _hist(p, NOW - timedelta(days=3))
    _hist(p, NOW - timedelta(days=10))
    db.session.commit()
    r = client.get("/api/dashboard/rekomendacje")
    assert r.status_code == 200
    d = r.json
    assert set(d) == {"meta", "rekomendacje", "podrzucanie", "sugestie_ekip", "punkty_ekip"}
    assert d["meta"]["syntetyczne"] is True and d["meta"]["poziomy_podrzucania"] == {"fotopulapka": 0, "kontrola": 0, "tablica": 1}
    assert d["podrzucanie"][0]["kosz_id"] == p.id and d["punkty_ekip"]["suma"] == 0
    assert client.get("/api/dashboard/rekomendacje?dzielnica=Krowodrza").status_code == 400  # nieznana w tej bazie
