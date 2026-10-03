import pytest

from app import clock
from app.osm_import import import_points


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


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
