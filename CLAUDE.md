# Trash Fairy — zasady pracy (HackYeah 2026, Smart City)

Koncepcja (przed wydarzeniem, bez kodu): `docs/KONCEPCJA.md`. Cały kod powstaje podczas HackYeah 3–4.10.2026.

## Proces
- Pracujemy etapami. Przed etapem plan w 6–8 punktach i akceptacja; po etapie: jak to sprawdzić.
- Wszystko spoza bieżącego etapu → `ROADMAPA.md`, nie implementujemy.
- Po każdym większym kroku 2–3 zdania w `DECYZJE.md`: CO, DLACZEGO, JAKA alternatywa odrzucona.
- Commit po polsku + push po każdym ukończonym i przetestowanym kroku. Nie commitujemy niedziałającego kodu.
- `pytest` musi przechodzić przed commitem.

## Reguły architektury
- Decyzje (stan, priorytet, trasa, rekomendacja) **wyłącznie regułami w kodzie**, nigdy przez AI.
- AI tylko przez `app/llm.py` (`ask`, `ask_json`); model i klucz z env (`ANTHROPIC_MODEL`, `ANTHROPIC_API_KEY`).
  Błąd API = komunikat + ostatni wynik z cache, nigdy 500.
- Sekrety tylko w `.env` (w `.gitignore`); `.env.example` jako wzór.

## Stack
Python 3.12 (Docker) / 3.13 (lokalny venv), Flask (app factory, blueprinty), Flask-SQLAlchemy,
PostgreSQL na produkcji (`DATABASE_URL`), SQLite lokalnie, Gunicorn, Dockerfile (port 8000), `/health` sprawdza bazę.
Frontend: Jinja + Tailwind + DaisyUI z CDN, Leaflet (z atrybucją OSM), Chart.js. Bez builda.
UI po polsku, WCAG 2.1 AA, kolor nigdy jedynym nośnikiem informacji. Styl: koncepcja, sekcja 9.

## Komendy
- `python scripts/fetch_osm.py` — odśwież cache OSM w `data/*.geojson` (zwykle niepotrzebne, cache jest w repo)
- `flask --app app seed [--force]` — import punktów + 8 tygodni symulacji
- `flask --app app run` — serwer lokalny
- `python -m pytest -q` — testy
