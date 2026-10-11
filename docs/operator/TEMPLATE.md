# Operator: `<nazwa-gałęzi>`

> Szablon. Kopia: `docs/operator/<nazwa-gałęzi>.md` (ukośniki w nazwie gałęzi → `-`). Wypełnia agent na koniec gałęzi;
> sekcje, które nie dotyczą zmiany, zostają z wpisem „nie dotyczy” (nie usuwaj ich).

- **PR / commity:** `<#numer>` · `<git log origin/main..HEAD --oneline>`
- **Data:** `<RRRR-MM-DD>` · **Autor zmian:** `<agent / człowiek>`

## 1. Co zmieniono
Dla człowieka, bez żargonu, 3–6 punktów: co działa inaczej i gdzie to widać. Na końcu: czego celowo NIE zmieniono.

## 2. Kroki do przeklikania
Każdy krok: gdzie wejść → co kliknąć/wpisać → oczekiwany wynik. Najpierw lokalnie (`flask --app app run` albo
`docker compose up --build`), potem na produkcji po deployu.

| # | Gdzie (URL / ekran) | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | `http://localhost:8080/health` | otwórz | `{"db": "ok", "status": "ok"}`, kod 200 (503 = baza nie odpowiada) |
| 2 | `<ekran>` | `<akcja>` | `<co widać>` |

## 3. Checklista wdrożenia

### Schemat bazy (repo nie ma Alembica – kolumny dokłada `_add_missing_columns()` przy starcie aplikacji)
- [ ] Zmiana schematu w tej gałęzi: `<tak: tabela.kolumna DDL / nie dotyczy>`
- [ ] **dev** (SQLite `trash_fairy.db`): aplikacja uruchomiona po zmianie, kolumna istnieje
      (`sqlite3 trash_fairy.db ".schema <tabela>"`)
- [ ] **test** (pytest, SQLite w pamięci): `python -m pytest -q -n auto` zielone → `<wynik>`
- [ ] **compose** (Postgres 16 lokalnie): `docker compose up --build` startuje, `/health` = 200
- [ ] **prod** (Postgres w Coolify): po Redeploy log startu bez błędu `ALTER TABLE`, `/health` = 200,
      kolumna istnieje (sprawdza człowiek w konsoli bazy Coolify)
- [ ] Ręczne kroki na bazie (zmiana typu/nazwy/usunięcie kolumny, `seed --force`): `<opis / nie dotyczy>`

### Zmienne środowiskowe
- [ ] Nowe / zmienione: `<NAZWA – po co – wartość przykładowa / nie dotyczy>`
- [ ] Ustawione w Coolify (Environment Variables) przed Redeploy
- [ ] Opisane w README / `docker-compose.yml`

### Deploy (robi człowiek)
- [ ] PR zmergowany do `main`, CI zielone (ruff + pytest)
- [ ] Coolify: zakładka *Source* wskazuje właściwą gałąź → Redeploy → w logu builda właściwa gałąź i commit
- [ ] Kroki z sekcji 2 przeklikane na produkcji

## 4. Plan wycofania
- **Kod:** Coolify → Deployments → Redeploy poprzedniego commita `<sha>` albo `git revert <sha>` + PR.
- **Baza:** `<czy stary kod działa z nowym schematem? dodana kolumna jest ignorowana przez stary kod → bez kroków /
  inaczej: dokładne kroki>`
- **Env:** `<które zmienne przywrócić / nie dotyczy>`
- **Sygnał do wycofania:** `<np. /health ≠ 200, 500 w logach, błąd w kroku 2.x>`

## 5. Ryzyka i otwarte sprawy
`<konkretne punkty / brak>`
