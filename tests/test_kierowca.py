import pytest

from app import clock
from app.models import Emptying, Point, StopIssue
from app.osm_import import import_points
from app.state import point_states


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def odbior(client, pid, akcja, **kw):
    return client.post("/api/odbiory", json={"kosz": pid, "akcja": akcja, **kw})


def test_stop_issue_flags_point_until_emptying(client, demo):
    pid = Point.query.filter_by(kind="bin").first().id
    r = odbior(client, pid, "problem", problem="no_access", notatka="auto na kopercie")
    assert r.status_code == 201 and "Nie da się podjechać" in r.json["komunikat"]
    issue = point_states(clock.now())[pid]["crew_issue"]
    assert issue["kind"] == "no_access" and issue["note"] == "auto na kopercie"
    clock.advance(1)
    assert odbior(client, pid, "oprozniono", poziom=50).status_code == 201
    assert point_states(clock.now())[pid]["crew_issue"] is None  # opróżnienie zamyka problem


def test_stop_issue_rejects_bad_input(client, demo):
    pid = Point.query.first().id
    assert odbior(client, pid, "problem", problem="rm -rf").status_code == 400
    assert odbior(client, 99999, "problem", problem="damaged").status_code == 404
    assert StopIssue.query.count() == 0


def test_reset_clears_stop_issues(client, demo):
    odbior(client, Point.query.first().id, "problem", problem="damaged")
    clock.reset(weeks=2)
    assert StopIssue.query.count() == 0


def test_route_stops_carry_level_and_state(client, demo):
    stops = client.get("/api/trasa").json["przystanki"]
    assert stops and all({"poziom", "stan", "zgloszony"} <= s.keys() for s in stops)


def test_far_emptying_is_saved_with_flag_and_counts_as_progress(client, demo):
    a = Point.query.filter_by(kind="bin").first()
    before = client.get("/api/trasa").json["postep"]["zrobione"]
    assert odbior(client, a.id, "oprozniono", poziom=75, lat=a.lat + 0.01, lon=a.lon).status_code == 201  # bez blokady (decyzja 28)
    assert Emptying.query.filter_by(source="crew").one().far_m > 150
    assert client.get("/api/trasa").json["postep"]["zrobione"] == before + 1


# --- „dlaczego nie na trasie” i AI, które tylko obniża priorytet ---

def test_trasa_lists_skipped_bins_with_reasons(client, demo):
    d = client.get("/api/trasa").json
    on_route = {s["id"] for s in d["przystanki"]}
    assert d["pojazdy"] == 1 and d["pominiete"] and d["pominiete_liczba"] >= len(d["pominiete"])
    assert len(d["pominiete"]) <= 30 and not on_route & {k["id"] for k in d["pominiete"]}
    assert all(k["powod"].startswith(f"poziom {k['poziom']}%") for k in d["pominiete"])
    levels = [k["poziom"] for k in d["pominiete"]]
    assert levels == sorted(levels, reverse=True)
    skipped = client.get(f"/api/kosze/{d['pominiete'][0]['id']}").json["kosz"]["trasa"]
    assert skipped == {"na_trasie": False, "powod": d["pominiete"][0]["powod"]}
    stop = client.get(f"/api/kosze/{d['przystanki'][0]['id']}").json["kosz"]["trasa"]
    assert stop["na_trasie"] is True and stop["powod"]


def _photo(pid, confidence, report_id):
    from datetime import UTC, datetime
    from app import db
    from app.models import PhotoAnalysis, Press
    pa = PhotoAnalysis(point_id=pid, at=clock.now(), wall_at=datetime.now(UTC).replace(tzinfo=None), status="done",
                       source="resident", bin_visible=True, condition="w_porzadku", fill_level=0, confidence=confidence,
                       people=False, note="Kosz prawie pusty.")
    db.session.add(pa)
    db.session.flush()
    Press.query.filter_by(report_id=report_id).one().photo_id = pa.id
    db.session.commit()
    clock.touch()
    return pa


def test_ai_ok_photo_lowers_priority_but_never_rejects(client, demo):
    from app import db
    from app.api_pl import AI_DEPRIORITIZE_CONFIDENCE
    from app.models import Report
    from app.reports import record_press
    ids = [s["id"] for s in client.get("/api/trasa").json["przystanki"]][:2]
    reports = [record_press(pid, clock.now(), source="qr", kind="full") for pid in ids]
    db.session.commit()
    clock.touch()
    first = next(s for s in client.get("/api/trasa").json["przystanki"] if s["id"] in ids)["id"]  # wyżej bez zdjęcia
    other = (set(ids) - {first}).pop()
    pa = _photo(first, AI_DEPRIORITIZE_CONFIDENCE - 0.01, reports[ids.index(first)].id)
    order = [s["id"] for s in client.get("/api/trasa").json["przystanki"]]
    assert order.index(first) < order.index(other)  # pewność poniżej progu: nic się nie zmienia
    pa.confidence = 0.86
    db.session.commit()
    clock.touch()
    stops = client.get("/api/trasa").json["przystanki"]
    order = [s["id"] for s in stops]
    assert order.index(first) > order.index(other)
    k = next(s for s in stops if s["id"] == first)
    assert k["powod"] == "Zdjęcie: kosz w porządku (AI 0,86) · sprawdź przy okazji"
    assert k["zgloszenia_liczba"] == 1 and k["zgloszony"]  # zgłoszenie zostaje otwarte i policzone
    assert db.session.get(Report, reports[ids.index(first)].id).hit is None
