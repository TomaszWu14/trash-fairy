import pytest

from app import clock
from app.models import Point
from app.osm_import import import_points


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def test_phones_page_has_three_live_frames(client, demo):
    html = client.get("/telefony").get_data(as_text=True)
    assert html.count("<iframe") == 3 and "/epapier/18" in html and "/zglos/18?jury=1&amp;theme=light" in html
    assert "/kierowca?podglad=1" in html and 'lang="en"' in html
    assert 'id="reset"' not in html  # „Zacznij od nowa” tylko dla dyspozytora


def test_driver_preview_is_public_but_read_only(client, demo):
    assert client.get("/kierowca?podglad=1").status_code == 200
    kurs = client.get("/api/kierowca/kurs?podglad=1").json
    assert kurs["fleet"]["kind"] == "bin" and kurs["login"] is None
    assert client.get("/api/kierowca/kurs").status_code == 401
    bin_id = Point.query.filter_by(kind="bin").first().id
    assert client.post("/api/emptying", data={"point_id": bin_id, "level": 50}).status_code == 401


def test_theme_param_sets_data_theme(client, demo):
    assert 'data-theme="dark"' in client.get("/kierowca?podglad=1&theme=dark").get_data(as_text=True)
    assert "data-theme" not in client.get("/zglos/18").get_data(as_text=True)


def test_jury_bin_counts_per_phone_not_per_ip(client, demo):
    def press(cid):
        return client.post("/api/press", json={"point_id": 18, "source": "qr", "kind": "full", "jury": True, "client_id": cid},
                           environ_base={"REMOTE_ADDR": "10.9.9.9"})
    a, b = press("telefon-a"), press("telefon-b")  # ta sama sieć sali, dwa telefony w ciągu 2 s
    assert a.status_code == 200 and b.status_code == 200 and b.json["status"] == "merged"
    assert press("telefon-a").status_code == 429  # ten sam telefon od razu ponownie


def test_menu_by_role(client, demo):
    from tests.conftest import login
    html = client.get("/telefony").get_data(as_text=True)
    assert "Panel (podgląd)" in html and "Zaloguj" in html and "/zdjecia" not in html
    login(client)
    html = client.get("/telefony").get_data(as_text=True)
    assert "/zdjecia" in html and "Wyloguj" in html and 'id="reset"' in html


def test_accessibility_and_privacy_pages(client):
    assert "częściowo zgodna" in client.get("/dostepnosc").get_data(as_text=True)
    html = client.get("/prywatnosc").get_data(as_text=True)
    assert "24 godziny" in html and "nie zapisujemy" in html


def test_old_ips_are_forgotten(app, demo):
    from datetime import datetime, timedelta
    from app import db
    from app.models import Press
    from app.privacy import forget_old_ips
    now = datetime(2026, 10, 3, 12)
    db.session.add_all([Press(point_id=18, at=now, ip="1.1.1.1", wall_at=now - timedelta(hours=25), source="qr"),
                        Press(point_id=18, at=now, ip="2.2.2.2", wall_at=now - timedelta(hours=1), source="qr")])
    db.session.commit()
    assert forget_old_ips(now) == 1
    assert {p.ip for p in Press.query.filter(Press.wall_at.isnot(None))} == {None, "2.2.2.2"}
