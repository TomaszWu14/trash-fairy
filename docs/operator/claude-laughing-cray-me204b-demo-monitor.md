# Operator: `claude/laughing-cray-me204b-demo-monitor`

- **PR / commity:** PR do uzupełnienia · `ci: add scheduled demo monitor`
- **Data:** 2026-10-22 · **Autor zmian:** agent

## 1. Co zmieniono
- Nowy workflow `.github/workflows/demo-monitor.yml`: co 6 godzin (i ręcznie: Actions → Monitor demo → Run workflow)
  sprawdza, czy https://trashfairy.twapp.pl/ zwraca 200, a `/health` zwraca 200 i `{"status": "ok"}`.
- curl ma limit 30 s i 3 ponowienia co 20 s, więc chwilowy restart kontenera nie daje fałszywego alarmu.
- Awaria → issue „Demo nie odpowiada” z etykietą `demo` (etykieta zakłada się sama); kolejne awarie dopisują komentarz
  do otwartego issue. Pierwsze udane sprawdzenie zamyka issue.
- Uprawnienia: `contents: read`, `issues: write`, tylko `GITHUB_TOKEN`.
- Celowo NIE zmieniono: aplikacji, `ci.yml`, ustawień repo.

## 2. Kroki do przeklikania
| # | Gdzie (URL / ekran) | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | GitHub → Actions → Monitor demo | po merge: Run workflow | przebieg zielony, w podsumowaniu „Demo działa.” |
| 2 | GitHub → Issues, etykieta `demo` | po awarii demo | jedno otwarte issue „Demo nie odpowiada”, zamknięte po powrocie demo |

## 3. Checklista wdrożenia

### Schemat bazy (repo nie ma Alembica – kolumny dokłada `_add_missing_columns()` przy starcie aplikacji)
- [x] Zmiana schematu w tej gałęzi: nie dotyczy
- [x] **dev** (SQLite `trash_fairy.db`): nie dotyczy
- [x] **test** (pytest, SQLite w pamięci): nie dotyczy (zmiana tylko w workflow); `actionlint` bez błędów, skrypt sprawdzenia
      uruchomiony lokalnie na serwerze testowym (działa → `ok=true`, brak serwera → `ok=false` z raportem)
- [x] **compose** (Postgres 16 lokalnie): nie dotyczy
- [x] **prod** (Postgres w Coolify): nie dotyczy
- [x] Ręczne kroki na bazie: nie dotyczy

### Zmienne środowiskowe
- [x] Nowe / zmienione: nie dotyczy
- [x] Ustawione w Coolify: nie dotyczy
- [x] Opisane w README / `docker-compose.yml`: nie dotyczy

### Deploy (robi człowiek)
- [ ] PR zmergowany do `main`, CI zielone (ruff + pytest)
- [x] Coolify: nie dotyczy (workflow działa w GitHub Actions, nie w obrazie)
- [ ] Krok 1 z sekcji 2 przeklikany po merge

## 4. Plan wycofania
- **Kod:** `git revert <sha>` + PR albo Actions → Monitor demo → ⋯ → Disable workflow.
- **Baza:** nie dotyczy
- **Env:** nie dotyczy
- **Sygnał do wycofania:** fałszywe alarmy (issue otwierane, gdy demo działa).

## 5. Ryzyka i otwarte sprawy
- Harmonogram w GitHub wyłącza się sam po 60 dniach bez commitów w repo (publiczne repo) — wtedy włączyć go ponownie w Actions.
- Monitor nie sprawdza treści ekranów (pułapka deploy #9) — tylko czy serwer i baza odpowiadają.
