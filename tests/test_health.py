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


def test_large_static_is_gzipped_small_and_uncompressed_clients_are_not(client):
    import gzip
    r = client.get("/static/vendor/echarts/echarts.min.js", headers={"Accept-Encoding": "gzip, br"})
    assert r.headers["Content-Encoding"] == "gzip" and r.headers["Vary"] == "Accept-Encoding"
    assert len(r.data) < 500_000 and len(gzip.decompress(r.data)) > 1_000_000
    assert "Content-Encoding" not in client.get("/static/vendor/echarts/echarts.min.js").headers
    assert "Content-Encoding" not in client.get("/health", headers={"Accept-Encoding": "gzip"}).headers  # < 1 kB
