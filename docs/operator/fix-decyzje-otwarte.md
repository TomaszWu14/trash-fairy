# Operator: `fix/decyzje-otwarte`

## 1. Co zmieniono
Decyzje autora z 11.10.2026 dla otwartych problemów z `docs/07-ograniczenia.md`:
1. Jedna definicja „pełny”: progi silnika tras (≥ 60% „zapełnia się”, > 85% „pełny”) wszędzie — ekrany, dyspozytor, kierowca, legendy, podpowiedzi.
2. Progi baterii w `app/devices.py`: 15% krytyczny, 35% ostrzeżenie; martwy próg 20% usunięty.
3. Rozbieżność poziomu od ekipy i zdjęcia (> 25 p.p.) na liście „Do sprawdzenia” w szczegółach anomalii dashboardu.
4. Blokada wiersza kosza przy scalaniu naciśnięć (PostgreSQL `FOR UPDATE`), atomowy licznik potwierdzeń wysypiska.
5. Identyfikator telefonu z podpisanego ciasteczka sesji (`phone_id`); pole „klient” z żądania ignorowane.
6. Dyspozytor: linki do statusu zgłoszenia, wysypiska i karty kosza.

## 2. Kroki do przeklikania
| # | Gdzie (URL / ekran) | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | `/health` | otwórz | `{"db": "ok", "status": "ok"}`, kod 200 |
| 2 | `/kierowca` | legenda mapy | „< 60% · 60–85% · > 85%” |
| 3 | `/dyspozytor` → Zgłoszenia | kliknij „Szczegóły TF-…” | otwiera się status zgłoszenia |
| 4 | `/dyspozytor` → Pilne | kliknij „Karta kosza” | karta kosza kierowcy |
| 5 | `/zglos/18?qr=…` (przez kod QR z `/panel/18`) | wyślij „Przepełniony” dwa razy w minutę | drugi raz: „To zgłoszenie już dotarło…” (429) |
| 6 | `/dashboard` → Anomalie ekipy → Szczegóły | otwórz | pod listą odległości sekcja „Do sprawdzenia: poziom od ekipy różni się od zdjęcia…” |
| 7 | `/prywatnosc` | tabela danych | „ciasteczko sesji podpisane przez serwer… do 31 dni” |

## 3. Checklista wdrożenia
### Schemat bazy
- [x] Zmiana schematu w tej gałęzi: nie dotyczy
- [x] **test** (pytest, SQLite w pamięci): `python -m pytest -q -n 3` → 488 passed
- [ ] **compose** (Postgres 16): `docker compose up --build` — nie uruchamiane na tej gałęzi (blokada `FOR UPDATE` działa tylko na PostgreSQL; logikę sprawdził przegląd db-reviewer)
- [ ] **prod**: po Redeploy `/health` = 200
### Zmienne środowiskowe
- [ ] `PUBLIC_URL` na produkcji zaczyna się od `https://` — teraz włącza też flagę `Secure` ciasteczka sesji (opisane w `.env.example`, `docs/pitfalls/deploy.md`)
### Deploy (robi człowiek)
- [ ] PR zmergowany do `main`, CI zielone (ruff + pytest)
- [ ] Coolify: Redeploy z `main`
- [ ] Kroki z sekcji 2 przeklikane na produkcji

## 4. Plan wycofania
Revert commita scalającego PR (`git revert <sha>`) i Redeploy. Brak zmian schematu i danych do cofania; ciasteczko sesji
bez wpływu na dane.

## 5. Ryzyka i otwarte sprawy
- Po wdrożeniu zmienia się wygląd kolorów: kosze 50–59% i 80–85% zmieniają stan na ekranach (zgodnie z decyzją).
- Telefon, który wyczyści ciasteczka, dostaje nowy identyfikator (zostaje limit IP i dzienny kod QR).
- Wspólne konto demo „Anna K.” ma jawny wyjątek przy samouprzątnięciu (scenariusz C) — opis w `docs/07`.
