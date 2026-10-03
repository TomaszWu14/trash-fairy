from app import database_url


def test_database_url_defaults_to_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert database_url().startswith("sqlite:///")


def test_database_url_uses_psycopg3_for_postgres(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@db:5432/tf")
    assert database_url() == "postgresql+psycopg://u:p@db:5432/tf"
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db:5432/tf")
    assert database_url() == "postgresql+psycopg://u:p@db:5432/tf"
