# Jak współtworzyć Trash Fairy

## Uruchomienie lokalnie

Najprościej przez Dockera (aplikacja + PostgreSQL 16, seed startuje sam):

```bash
docker compose up --build                            # http://localhost:8080
```

Bez Dockera (SQLite):

```bash
python -m venv .venv && . .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
flask --app app seed                                 # punkty z data/*.geojson + 8 tygodni symulacji
flask --app app run                                  # http://localhost:5000
python -m pytest -q -n auto                          # wszystkie testy, równolegle
ruff check .                                         # lint (reguły w ruff.toml), to samo w CI
```

AI jest opcjonalne (`ANTHROPIC_API_KEY` w `.env`) — bez klucza aplikacja działa
w pełni, a zdjęcia trafiają „Do weryfikacji”. Pozostałe zmienne środowiskowe opisuje README.

## Zgłaszanie błędów i pomysłów

Załóż issue z szablonu **Zgłoszenie błędu** albo **Propozycja zmiany**. Podaj perspektywę
(mieszkaniec, kierowca, dyspozytor, dashboard, panel kosza), adres strony i kroki do odtworzenia.
Nie wklejaj danych osobowych ani zdjęć z twarzami czy tablicami rejestracyjnymi.

## Gałęzie i commity

- Gałąź od `main`, nazwa z numerem issue: `fix/14-filtr-dashboardu`, `feat/23-web-push`,
  `docs/28-zmienne-srodowiskowe`.
- Commity w konwencji [Conventional Commits](https://www.conventionalcommits.org/),
  po angielsku: `fix:`, `feat:`, `docs:`, `test:`, `refactor:`, `chore:`.
  Przykład: `fix: keep dashboard filters after reload`.
- Każdy bugfix ma test regresji.

## Pull request

- Opis według szablonu: **Co się zmienia**, **Dlaczego**, **Jak sprawdzić**, `Closes #<numer>`.
- CI (`ruff check .` i `pytest`) musi być zielone.
- Decyzje (stan kosza, priorytet, trasa, rekomendacja) liczą reguły w kodzie; AI tylko opisuje
  i rozpoznaje, wyłącznie przez `app/llm.py`. Uzasadnienie większej zmiany: 2–3 zdania w `DECYZJE.md`.
- Zmiany w interfejsie: UI po polsku, WCAG 2.1 AA (stan to kolor + ikona + tekst), sprawdź
  klawiaturę i widok 390 px (`python scripts/axe_check.py <ścieżka do axe.min.js>`).
- Dane demo są syntetyczne i oznaczone „Dane demonstracyjne” — nie dodawaj prawdziwych danych osobowych.
- Jedna sprawa = jeden PR.
