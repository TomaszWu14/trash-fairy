import gzip
import os

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()


def database_url():
    """DATABASE_URL z env; Coolify/Heroku podają postgres(ql)://, a my używamy sterownika psycopg 3."""
    url = os.environ.get("DATABASE_URL", "sqlite:///trash_fairy.db")
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


_GZIP_TYPES = ("text/", "application/javascript", "application/json", "application/geo+json", "image/svg+xml")
_gzip_cache = {}  # statyki: (ścieżka, ETag) → skompresowane bajty; echarts 1 MB → ok. 330 kB liczone raz na proces


def _gzip(resp):
    """Kompresja gzip tekstu ≥ 1 kB (Gunicorn i proxy Coolify nie kompresują). Lighthouse: echarts blokował dashboard."""
    if (resp.status_code != 200 or "gzip" not in request.headers.get("Accept-Encoding", "")
            or resp.headers.get("Content-Encoding") or not (resp.mimetype or "").startswith(_GZIP_TYPES)
            or resp.is_streamed and not resp.direct_passthrough):
        return resp
    resp.direct_passthrough = False
    data = resp.get_data()
    if len(data) < 1024:
        return resp
    key = (request.path, resp.headers.get("ETag")) if request.path.startswith("/static/") else None
    body = _gzip_cache.get(key) if key else None
    if body is None:
        body = gzip.compress(data, compresslevel=6)
        if key:
            _gzip_cache[key] = body
    resp.set_data(body)
    resp.headers["Content-Encoding"] = "gzip"
    resp.headers["Vary"] = "Accept-Encoding"
    return resp


def create_app(config=None):
    app = Flask(__name__)
    # za reverse proxy (Coolify/Traefik): prawdziwy adres klienta do limitu naciśnięć na IP
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url()
    # sekret podpisu tokenów QR (api_pl) i hashowania telefonów; na produkcji MUSI być ustawiony w env
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-trash-fairy")
    app.config.update(config or {})
    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    from . import models  # noqa: F401  rejestracja tabel
    from .dashboard_api import bp as dashboard_bp
    from .devices_api import bp as devices_bp
    from .open_api import bp as open_api_bp
    from .cli import cleanup_photos_command, karnet_command, seed_command
    from .ui import bp as ui_bp
    from .api_pl import bp as api_pl_bp
    from .views import bp

    app.register_blueprint(ui_bp)
    app.register_blueprint(api_pl_bp)
    app.register_blueprint(bp)
    app.register_blueprint(open_api_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(devices_bp)

    @app.errorhandler(404)
    def not_found(_e):
        # stara naklejka z QR albo literówka: polska strona zamiast surowego „Not Found”; API dalej dostaje JSON
        if request.path.startswith("/api/"):
            return jsonify(blad="Nie ma takiego zasobu.", kod="nie_znaleziono"), 404
        return render_template("ui/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        if request.path.startswith("/api/"):
            return jsonify(blad="Coś poszło nie tak po naszej stronie. Spróbuj za chwilę.", kod="blad_serwera"), 500
        return render_template("ui/404.html", error=True), 500

    app.after_request(_gzip)
    app.cli.add_command(seed_command)
    app.cli.add_command(cleanup_photos_command)
    app.cli.add_command(karnet_command)
    with app.app_context():
        db.create_all()
        _add_missing_columns()
        from .privacy import forget_old_ips
        forget_old_ips()  # IP zgłoszeń starsze niż 24 h (decyzja 32)
    return app


def _add_missing_columns():
    """Bez Alembica: dokładamy nowe, opcjonalne kolumny do istniejącej bazy (np. press.kind z ekranu /zglos)."""
    from sqlalchemy import inspect, text
    insp = inspect(db.engine)
    for table, column, ddl in [("press", "kind", "VARCHAR(10)"), ("demo_clock", "last_activity", "TIMESTAMP"),
                               ("emptying", "source", "VARCHAR(10)"), ("emptying", "far_m", "INTEGER"),
                               ("press", "note", "VARCHAR(280)"), ("press", "photo_id", "INTEGER"),
                               ("point", "live", "BOOLEAN NOT NULL DEFAULT TRUE"), ("point", "district", "VARCHAR(30)"),
                               ("point", "fraction", "VARCHAR(20) NOT NULL DEFAULT 'zmieszane'"),
                               ("point", "address", "VARCHAR(160)"), ("point", "snapshot_fill", "INTEGER"),
                               ("photo_analysis", "bin_visible", "BOOLEAN"), ("photo_analysis", "condition", "VARCHAR(20)"),
                               ("photo_analysis", "people", "BOOLEAN")]:
        if table in insp.get_table_names() and column not in {c["name"] for c in insp.get_columns(table)}:
            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
            db.session.commit()
    if "point" in insp.get_table_names():  # stara baza: dzielnica 72 punktów demo z obszaru (jak w osm_import.district_of)
        db.session.execute(text("UPDATE point SET district = CASE WHEN area = 'Grzegórzki' THEN 'Grzegórzki' "
                                "ELSE 'Stare Miasto' END WHERE district IS NULL"))
        db.session.commit()
