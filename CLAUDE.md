# Trash Fairy — zasady pracy agentów

Flask (app factory, blueprinty) + Flask-SQLAlchemy, SQLite lokalnie i w testach, PostgreSQL 16 na produkcji (Coolify).
Szczegóły dla ludzi: `README.md`, `CONTRIBUTING.md`. Ten plik: tylko to, czego agent nie wyczyta szybko z kodu.

## Komendy
- `pip install -r requirements.txt -r requirements-dev.txt` (venv w `.venv` – z niego korzystają hooki)
- `python -m pytest -q -n auto` – pełne testy (~3 min); `ruff check .`; `mypy` (tryb łagodny, konfiguracja w `pyproject.toml`)
- `flask --app app seed [--force]`, `flask --app app run`; z Postgresem jak na prod: `docker compose up --build`

## Reguły architektury
- Decyzje (stan, priorytet, trasa, rekomendacja) wyłącznie regułami w kodzie, nigdy przez AI.
- AI tylko przez `app/llm.py` (`ask`, `ask_json`); błąd API = komunikat + ostatni wynik z cache, nigdy 500.
- Sekrety tylko w env/`.env` (w `.gitignore`). UI po polsku, WCAG 2.1 AA, bez CDN (biblioteki w `app/static/vendor`).

## Pułapki – przeczytaj odpowiedni plik przed pracą
| Pracujesz nad… | Czytaj |
|---|---|
| modelami, zapytaniami, schematem (`_add_missing_columns`), zegarem demo, limitami w bazie | `docs/pitfalls/db.md` |
| endpointami `POST`, tokenami QR/urządzeń/telefonów, `SECRET_KEY`, limitami, danymi mieszkańców | `docs/pitfalls/auth.md` |
| widokami, API JSON, szablonami, uploadem zdjęć, PWA/service workerem, AI w przepływie | `docs/pitfalls/views.md` |
| `Dockerfile`, `app/wsgi.py`, CI, zmiennymi env, Coolify | `docs/pitfalls/deploy.md` |

Nowa pułapka z sesji → dopisz punkt do właściwego pliku (max 10 na plik; najsłabszy wylatuje).

## Duże zadania: planuj → `worker`y → reviewerzy raz
1. Główna sesja planuje i tnie zadanie na niezależne wycinki (pliki, cel, kryterium „gotowe”). Wycinki dotykające tych
   samych plików idą po kolei, nie równolegle.
2. Każdy wycinek dostaje agent `worker` (model sonnet). Główna sesja scala wyniki i uruchamia pełne testy.
3. Na końcu **raz** `security-reviewer` i `db-reviewer` (równolegle, na diffie gałęzi). Główna sesja ocenia zgłoszenia
   i poprawia te zasadne. **Bez pętli review → poprawka → review**: ponowny przegląd tylko na wyraźną prośbę człowieka.
Małe zadanie (1–2 pliki) robi główna sesja sama, bez agentów.

## Koniec gałęzi: dokument dla operatora
Zmiany w `app/` przesuwają odwołania `plik:linia` w `docs/0*.md`: przed PR `python scripts/remap_doc_lines.py origin/main`,
potem sprawdź ręcznie 2–3 przesunięte odwołania.
Przed PR wygeneruj `docs/operator/<nazwa-gałęzi>.md` (ukośniki → `-`) według `docs/operator/TEMPLATE.md`:
co zmieniono, kroki do przeklikania z oczekiwanym wynikiem, checklista (schemat na dev/test/compose/prod, env, deploy),
plan wycofania. Wpisuj prawdziwe wyniki komend, nie zapowiedzi. Potem `/end` (propozycje usprawnień harnessu).

## Harness
`.claude/hooks/guard.py` (PreToolUse) blokuje groźne akcje – blokada to sygnał, nie przeszkoda do obejścia; jeśli jest
fałszywa, powiedz człowiekowi. `.claude/hooks/check.py` (Stop) uruchamia ruff, mypy i powiązane testy na zmienionych
plikach. Testy strażnika: `bash .claude/hooks/test_guard.sh`.
