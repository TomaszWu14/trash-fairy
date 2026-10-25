# Operator: `claude/laughing-cray-me204b-przepustka-portfolio`

- **PR / commity:** brak PR (gałąź wypchnięta, PR robi główna sesja) · jeden commit „Przepustka z portfolio w bramce gościa”
- **Data:** 2026-10-25 · **Autor zmian:** agent (Claude Code)

## 1. Co zmieniono
- Gość, który przedstawił się w portfolio (ciasteczko `gosc` na `.twapp.pl`), wchodzi do dema bez formularza bramki.
- Backend dema pyta portfolio: `GET {PORTFOLIO_URL}/api/gosc` z nagłówkiem `Cookie: gosc=<token>` (timeout 2 s, bez
  przekierowań; liczy się tylko kod 200). Błąd sieci, timeout lub inny kod = formularz jak dotąd, nigdy 500.
- Po 200 powstaje rekord `DemoVisitor` „Gość z portfolio” (bez danych osobowych) i flaga sesji dema na 30 dni; wynik
  jest też w pamięci procesu ~10 min. Dema nie pyta portfolio przy każdym żądaniu.
- Demo nie wysyła własnego pusha (ani „wszedł”, ani „obejrzał N ekranów” dla gościa z portfolio); push z nazwiskiem
  wysyła portfolio przez piksel.
- Strona formularza (`ui/wizytowka.html`) nie ładuje już piksela `portfolio.twapp.pl/px/trash-fairy` (blok `pixel` w `base.html`).
- Kod: `app/portfolio_pass.py` (nowy), `app/visitor_gate.py`, `app/visitor_activity.py`; testy `tests/test_portfolio_pass.py`.
- Celowo NIE zmieniono: modelu `DemoVisitor`, retencji 90 dni, formularza, listy `/odwiedzajacy`. Endpoint `/api/gosc` w portfolio robi inny wycinek.

## 2. Kroki do przeklikania

Wymaga wdrożonego endpointu `/api/gosc` w portfolio (inna gałąź).

| # | Gdzie (URL / ekran) | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | `http://localhost:8080/health` | otwórz | `{"db": "ok", "status": "ok"}`, kod 200 |
| 2 | demo w oknie prywatnym (bez przepustki) | wejdź na `/metodologia` | formularz „przedstaw się”; w źródle strony brak `/px/` |
| 3 | `https://portfolio.twapp.pl` (to samo okno) | przedstaw się formularzem portfolio | portfolio ustawia ciasteczko `gosc` |
| 4 | `https://trashfairy.twapp.pl/metodologia` (to samo okno) | otwórz | strona bez formularza; w `/odwiedzajacy` wpis „Gość z portfolio” |
| 5 | to samo okno | kilka kliknięć po demie | licznik ekranów rośnie; z dema brak pusha ntfy |
| 6 | demo z `PORTFOLIO_PASS=0` | krok 4 | formularz dema jak dotąd |

## 3. Checklista wdrożenia

### Schemat bazy (repo nie ma Alembica – kolumny dokłada `_add_missing_columns()` przy starcie aplikacji)
- [x] Zmiana schematu w tej gałęzi: nie dotyczy
- [ ] **dev** (SQLite `trash_fairy.db`): nie dotyczy
- [x] **test** (pytest, SQLite w pamięci): `python -m pytest -q -n auto` → `587 passed in 327.01s`; `ruff check .` → All checks passed
- [ ] **compose** (Postgres 16 lokalnie): `docker compose up --build` startuje, `/health` = 200
- [ ] **prod** (Postgres w Coolify): nie dotyczy (bez zmian schematu); `/health` = 200 po Redeploy
- [ ] Ręczne kroki na bazie: nie dotyczy

### Zmienne środowiskowe
- [ ] Nowe: `PORTFOLIO_URL` – baza adresu portfolio, wymagany `https://` – domyślnie `https://portfolio.twapp.pl`
- [ ] Nowe: `PORTFOLIO_PASS` – `0` wyłącza rozpoznawanie przepustki – domyślnie `1`
- [ ] Ustawione w Coolify (opcjonalnie, domyślne wystarczą) przed Redeploy
- [x] Opisane w README, `.env.example` i `docker-compose.yml`

### Deploy (robi człowiek)
- [ ] PR zmergowany do `main`, CI zielone (ruff + pytest)
- [ ] Coolify: zakładka *Source* wskazuje właściwą gałąź → Redeploy → w logu builda właściwa gałąź i commit
- [ ] Kroki z sekcji 2 przeklikane na produkcji (po wdrożeniu `/api/gosc` w portfolio)

## 4. Plan wycofania
- **Kod:** Coolify → Deployments → Redeploy poprzedniego commita albo `git revert <sha>` + PR.
- **Baza:** bez kroków; rekordy „Gość z portfolio” znikną po 90 dniach (retencja) albo można je usunąć z `demo_visitor`.
- **Env:** szybkie wyłączenie bez zmiany kodu: `PORTFOLIO_PASS=0` i Redeploy.
- **Sygnał do wycofania:** 500 na stronach dema, opóźnienie ~2 s przy pierwszym wejściu (portfolio nie odpowiada).

## 5. Ryzyka i otwarte sprawy
- Dopóki portfolio nie ma `/api/gosc`, demo działa jak dotąd (formularz), przy każdej nowej sesji z ciasteczkiem `gosc` kosztem do 2 s oczekiwania.
- Remap `plik:linia` w `docs/0*.md` uruchomiony: żadnych odwołań do zmienionych plików, więc bez przesunięć.
- Statystyka demo: goście z portfolio mają w `/odwiedzajacy` pusty nazwisko i firmę (wpis „Gość z portfolio”).
