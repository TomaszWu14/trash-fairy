# Pułapki: deploy (Coolify) i środowiska

Czytaj przed zmianą `Dockerfile`, `docker-compose.yml`, `app/wsgi.py`, `.github/workflows/`, zmiennych env.

1. **Deploy robi człowiek**: Coolify (VPS) buduje obraz z `Dockerfile`, Redeploy ręcznie po merge do `main`. Agent nie
   wywołuje API Coolify ani nie pushuje na `main` (blokuje to `.claude/hooks/guard.py`).
2. **Coolify buduje z gałęzi ustawionej w zakładce *Source***, nie z tej, o której myślisz. Po zmianie: Save, Redeploy
   i sprawdź w logu builda nazwę gałęzi.
3. **Start kontenera = `flask seed && gunicorn ... --preload`**. `seed` pomija import, gdy baza ma punkty; `seed --force`
   kasuje dane demo. Nowa kolumna dochodzi przy starcie przez `_add_missing_columns()` (patrz `db.md`).
4. **Port z `PORT`** (domyślnie 8080; na serwerze 8000 jest zajęty). `HEALTHCHECK` woła `/health`, które sprawdza bazę:
   jeśli `/health` pada, Coolify restartuje kontener w pętli.
5. **Wymagane env na prod**: `DATABASE_URL` (Coolify daje `postgres://`, kod przepisuje na `postgresql+psycopg://`),
   `SECRET_KEY` (bez niego tokeny są przewidywalne), `PUBLIC_URL`. Opcjonalne: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`,
   `OSRM_URL`, `REQUIRE_CREW_PHOTO`, `TOMTOM_API_KEY`, `TWILIO_ACCOUNT_SID`/`_AUTH_TOKEN`/`_VERIFY_SID` (przez `http.config`).
   W repo nie ma `.env.example`: nowa zmienna = README + `docker-compose.yml` + Coolify + dokument operatora.
6. **Python 3.12 w Dockerze i CI, 3.13 lokalnie**: składnia/biblioteki z 3.13 przejdą lokalnie i padną w obrazie.
   `ruff` ma `target-version = "py312"`.
7. **Lokalnie SQLite, prod Postgres**: błędy współbieżności (pula połączeń, 2 workery gthread) widać tylko na
   `docker compose up --build`, nie w pytest. Sprawdź tam zmiany w `app/wsgi.py`, `app/clock.py`, `app/rate.py`.
8. **Zmiana tylko w `data/`** (cache OSM/OSRM/pogody) też wymaga przebudowy obrazu: `COPY data ./data` w `Dockerfile`.
9. **Smoke po deployu**: kody HTTP nie wystarczą (500 na `/telefony` widać było dopiero na zrzutach z prod). Przejdź
   ścieżkę z `docs/operator/<gałąź>.md`.
10. **CI (`ci.yml`) = ruff + pytest -n auto na PR do `main`**; check „pytest” odblokowuje auto-merge. Zielone CI ≠
    przetestowany Postgres.
