import importlib
import sys


def test_preload_leaves_no_open_db_connections(tmp_path, monkeypatch):
    """--preload: proces główny nie może zostawić połączeń w puli, bo po forku workery dzieliłyby gniazdo bazy."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'w.db'}")
    sys.modules.pop("app.wsgi", None)
    wsgi = importlib.import_module("app.wsgi")
    from app import db
    with wsgi.app.app_context():
        assert db.engine.pool.checkedin() == 0
        assert db.engine.pool.checkedout() == 0
    sys.modules.pop("app.wsgi", None)
