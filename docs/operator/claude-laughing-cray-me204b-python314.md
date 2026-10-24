# Operator: `claude/laughing-cray-me204b-python314`

- **PR / commity:** PR do uzupełnienia · `ci: also run tests on Python 3.14`
- **Data:** 2026-10-22 · **Autor zmian:** agent

## 1. Co zmieniono
- W `ci.yml` doszedł osobny job „pytest (Python 3.14)”: te same testy (`python -m pytest -q -n auto`) na Pythonie 3.14.
- Job „pytest” (Python 3.12, jak w Dockerfile; ruff + testy) zostaje bez zmian, więc nazwa wymaganego checka się nie zmienia.
- Lokalnie (Python 3.14.6, świeży venv, zależności z `requirements*.txt`): `ruff check .` → All checks passed,
  `python -m pytest -q -n auto` → 494 passed in 193 s.
- Celowo NIE zmieniono: wersji Pythona w `Dockerfile`, `target-version` w ruff, odznaki „python 3.12” w README.

## 2. Kroki do przeklikania
| # | Gdzie (URL / ekran) | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | PR → zakładka Checks | otwórz | zielone „pytest” i „pytest (Python 3.14)” |

## 3. Checklista wdrożenia

### Schemat bazy (repo nie ma Alembica – kolumny dokłada `_add_missing_columns()` przy starcie aplikacji)
- [x] Zmiana schematu w tej gałęzi: nie dotyczy
- [x] **dev** (SQLite `trash_fairy.db`): nie dotyczy
- [x] **test** (pytest, SQLite w pamięci): Python 3.14.6 → 494 passed
- [x] **compose** (Postgres 16 lokalnie): nie dotyczy
- [x] **prod** (Postgres w Coolify): nie dotyczy
- [x] Ręczne kroki na bazie: nie dotyczy

### Zmienne środowiskowe
- [x] Nowe / zmienione: nie dotyczy
- [x] Ustawione w Coolify: nie dotyczy
- [x] Opisane w README / `docker-compose.yml`: nie dotyczy

### Deploy (robi człowiek)
- [ ] PR zmergowany do `main`, CI zielone (oba joby)
- [x] Coolify: nie dotyczy (obraz bez zmian)
- [ ] Krok 1 z sekcji 2 sprawdzony

## 4. Plan wycofania
- **Kod:** `git revert <sha>` + PR.
- **Baza:** nie dotyczy
- **Env:** nie dotyczy
- **Sygnał do wycofania:** job 3.14 czerwony bez winy kodu (np. brak kół zależności dla 3.14).

## 5. Ryzyka i otwarte sprawy
- Job 3.14 nie jest wymagany; jeśli ma blokować merge, trzeba go dodać w Settings → Branches (decyzja właściciela).
