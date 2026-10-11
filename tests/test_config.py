import pytest

from app import _require_secret_key, create_app, database_url


def test_database_url_defaults_to_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert database_url().startswith("sqlite:///")


def test_database_url_uses_psycopg3_for_postgres(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@db:5432/tf")
    assert database_url() == "postgresql+psycopg://u:p@db:5432/tf"
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db:5432/tf")
    assert database_url() == "postgresql+psycopg://u:p@db:5432/tf"



PG = "postgresql+psycopg://u:p@db:5432/tf"


@pytest.mark.parametrize("key", ["dev-only-trash-fairy", "zmien-mnie-lokalnie"])
def test_postgres_with_public_default_secret_key_fails(key):
    """Issue #25: jawny klucz z repo poza SQLite = tokeny QR i urządzeń do policzenia – start ma paść."""
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        _require_secret_key({"SQLALCHEMY_DATABASE_URI": PG, "SECRET_KEY": key})


def test_postgres_with_own_secret_key_and_sqlite_pass():
    _require_secret_key({"SQLALCHEMY_DATABASE_URI": PG, "SECRET_KEY": "x" * 64})
    _require_secret_key({"SQLALCHEMY_DATABASE_URI": "sqlite:///tf.db", "SECRET_KEY": "dev-only-trash-fairy"})


def test_create_app_on_postgres_with_public_key_in_env_fails_before_connecting(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "dev-only-trash-fairy")  # jawny klucz ustawiony wprost nadal blokuje start
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({"SQLALCHEMY_DATABASE_URI": PG})


def test_stored_secret_key_is_random_and_persists(app):
    """Bez SECRET_KEY w env (produkcja bez zmiennej w Coolify) klucz losujemy raz i trzymamy w bazie."""
    from app import stored_secret_key
    from app.models import AppSecret
    first = stored_secret_key()
    assert len(first) == 64 and first != "dev-only-trash-fairy"
    assert stored_secret_key() == first and AppSecret.query.count() == 1
