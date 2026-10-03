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


def create_app(config=None):
    app = Flask(__name__)
    # za reverse proxy (Coolify/Traefik): prawdziwy adres klienta do limitu naciśnięć na IP
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url()
    # sekret sesji (logowanie mieszkańców) i hashowania telefonów; na produkcji MUSI być ustawiony w env
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-trash-fairy")
    app.config.update(config or {})
    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    from . import models  # noqa: F401  rejestracja tabel
    from .api import bp as api_bp
    from .open_api import bp as open_api_bp
    from .cli import cleanup_photos_command, karnet_command, seed_command
    from .views import bp

    from . import auth
    auth.init_app(app)
    app.register_blueprint(bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(open_api_bp)

    @app.errorhandler(404)
    def not_found(_e):
        # stara naklejka z QR albo literówka: polska strona zamiast surowego „Not Found”; API dalej dostaje JSON
        if request.path.startswith("/api/"):
            return jsonify(ok=False, message="Nie znaleziono."), 404
        return render_template("404.html"), 404
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
    for table, column, ddl in [("press", "kind", "VARCHAR(10)"), ("demo_clock", "last_activity", "TIMESTAMP")]:
        if table in insp.get_table_names() and column not in {c["name"] for c in insp.get_columns(table)}:
            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
            db.session.commit()
