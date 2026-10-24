"""Nagłówki bezpieczeństwa na każdej odpowiedzi (_security_headers w app/__init__.py)."""
from app import create_app

BASE = {"X-Content-Type-Options": "nosniff", "X-Frame-Options": "SAMEORIGIN",
        "Referrer-Policy": "strict-origin-when-cross-origin", "Cross-Origin-Opener-Policy": "same-origin"}


def test_headers_on_html_api_and_404(client):
    for path in ("/health", "/api/nie-ma-takiego", "/nie-ma-takiej-strony"):
        h = client.get(path).headers
        for name, value in BASE.items():
            assert h[name] == value, (path, name)
        assert "frame-ancestors 'self'" in h["Content-Security-Policy"]
        assert "camera=()" in h["Permissions-Policy"] and "geolocation=(self)" in h["Permissions-Policy"]


def test_api_json_not_cached_but_open_data_keeps_its_cache(client):
    assert client.get("/api/nie-ma-takiego").headers["Cache-Control"] == "no-store"
    assert client.get("/api/v1/routes").headers["Cache-Control"] == "public, max-age=60"


def test_pixel_portfolio_na_kazdym_ekranie(client):
    """Piksel statystyk portfolio (base.html) na ekranie startowym i w 404 – strażnik, by nie zgubić go przy zmianach layoutu."""
    pixel = '<img src="https://portfolio.twapp.pl/px/trash-fairy" alt="" width="1" height="1" hidden>'
    assert pixel in client.get("/").get_data(as_text=True)
    assert pixel in client.get("/nie-ma-takiej-strony").get_data(as_text=True)


def test_hsts_only_behind_https(client):
    assert "Strict-Transport-Security" not in client.get("/health").headers
    https_app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True,
                            "SESSION_COOKIE_SECURE": True})
    with https_app.app_context():
        h = https_app.test_client().get("/api/nie-ma-takiego").headers
    assert h["Strict-Transport-Security"] == "max-age=31536000"
