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
