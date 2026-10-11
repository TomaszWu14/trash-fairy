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


def test_create_app_on_postgres_without_secret_key_fails_before_connecting(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({"SQLALCHEMY_DATABASE_URI": PG})
