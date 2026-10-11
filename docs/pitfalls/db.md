# Pułapki: baza danych

Czytaj przed zmianą `app/models.py`, zapytań SQLAlchemy, `app/__init__.py` (schemat) lub `app/clock.py`.

1. **Nie ma Alembica.** Schemat to `db.create_all()` + `_add_missing_columns()` w `app/__init__.py`. Nowa kolumna w modelu
   = dopisz krotkę `(tabela, kolumna, DDL)` do tej listy, inaczej istniejąca baza na produkcji (Postgres) jej nie dostanie,
   a testy (świeża SQLite w pamięci) przejdą. Zmiana typu, zmiana nazwy i usunięcie kolumny nie są obsługiwane: to ręczna operacja.
2. **Nowa kolumna NOT NULL musi mieć `DEFAULT`** w DDL (`"BOOLEAN NOT NULL DEFAULT TRUE"`), bo `ALTER TABLE ADD COLUMN`
   na niepustej tabeli bez wartości domyślnej nie przejdzie na Postgresie.
3. **DDL musi działać w SQLite i Postgresie** (lokalnie/testy vs prod). Bez `ALTER COLUMN`, bez typów tylko z Postgresa.
   Sprawdź na `docker compose up --build` (Postgres 16), nie tylko pytestem.
4. **Gunicorn `--preload` + połączenie otwarte w procesie głównym = wspólne gniazdo Postgresa w workerach** → 500 tylko
   pod równoległym ruchem (incydent `/telefony`, commit 8afcb9a). Niczego nie wołaj na bazie po
   `db.session.remove(); db.engine.dispose()` w `app/wsgi.py` i tego nie usuwaj.
5. **Stan wspólny dla workerów trzymaj w bazie, nie w pamięci procesu.** Limity: `rate.hit()` (tabela `Counter`),
   reset demo: warunkowy `UPDATE` + `pg_advisory_lock(RESET_LOCK_ID)` w `app/clock.py`. Zmienna modułu = inna wartość
   na każdym z 2 workerów (np. wersja danych z czasem pogody → migotanie ekranów pollingu).
6. **Zegar demo stoi** (`app/clock.py`): akcje na żywo dostają tę samą minutę. Porównania `>=`/`<` na `at` mylą stare zdarzenie
   z nowym. Status licz z `resolved_at`, nie z „pierwszego zdarzenia po”.
7. **Symulowane naciśnięcia nie mają `report_id`.** Filtruj wykluczaniem (`report_id.isnot(None)`), nie zakładaj, że każde
   `Press` należy do zgłoszenia.
8. **N+1 w pętlach po punktach**: zbieraj id i pytaj raz (`Press.report_id.in_(...)` w `app/api_kierowca.py`), nie
   `query` w pętli po 72 punktach przy pollingu co kilka sekund.
9. **`flask seed --force` kasuje dane demo** i liczy 8 tygodni symulacji od nowa. Na produkcji tylko świadomie (deploy, patrz `deploy.md`).
10. **IP zgłoszeń żyją 24 h** (`app/privacy.py`, `forget_old_ips()` przy starcie). Nowa kolumna z danymi osobowymi =
    dopisz ją do czyszczenia i do `docs/` o prywatności.
