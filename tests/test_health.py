from unittest.mock import patch


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json == {"status": "ok", "db": "ok"}


def test_health_reports_db_down(client):
    with patch("app.views.db.session.execute", side_effect=RuntimeError("db down")):
        r = client.get("/health")
    assert r.status_code == 503
    assert r.json["db"] == "down"


def test_panel_renders_demo_banner(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "DANE DEMONSTRACYJNE" in r.get_data(as_text=True)
