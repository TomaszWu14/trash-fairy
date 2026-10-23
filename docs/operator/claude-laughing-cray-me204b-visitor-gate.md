# Operator: `claude/laughing-cray-me204b-visitor-gate`

- **PR / commity:** draft PR (numer w opisie) · jeden commit „Bramka odwiedzających przed wersją demonstracyjną”
- **Data:** 2026-10-23 · **Autor zmian:** agent

## 1. Co zmieniono
- Pierwsze wejście na stronę HTML demo pokazuje formularz „Zanim wejdziesz do wersji demonstracyjnej, przedstaw się, proszę.” (imię, nazwisko, firma, zgoda RODO, ukryta pułapka na boty). Po wysłaniu użytkownik trafia na stronę, którą chciał otworzyć.
- Klauzula RODO pod formularzem i krótki akapit w `/prywatnosc`.
- Nowa tabela `demo_visitor` (imię, nazwisko, firma, czas); bez IP i user-agenta; wpisy starsze niż 90 dni kasuje każdy kolejny zapis.
- Po wpisaniu: ciasteczko sesji ważne 30 dni (HttpOnly, SameSite=Lax, Secure przy https).
- Lista dla właściciela: `/odwiedzajacy?token=…` (HTML) i `&format=csv` (z ochroną przed formułami). Bez `VISITORS_TOKEN` w env adres zwraca 404.
- Włącznik `DEMO_VISITOR_GATE` (domyślnie włączony; `0` wyłącza; w testach domyślnie wyłączony).
- NIE blokowane: `/api/*`, `/static/*` (PWA, service worker), `/health`, `/epapier/*`, `/przycisk/*`, `/kosz/*` (QR), `/prywatnosc`, `/dostepnosc`.
- Celowo nie zmieniono: reszty UI, API, istniejących tabel.

## 2. Kroki do przeklikania

| # | Gdzie (URL / ekran) | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | `http://localhost:8080/health` | otwórz | `{"db": "ok", "status": "ok"}`, 200 (bez formularza) |
| 2 | `/metodologia` (okno prywatne) | otwórz | formularz „przedstaw się”, klauzula RODO pod nim |
| 3 | ten sam formularz | wyślij puste pola / bez zgody | komunikat błędu u góry (role=alert) i przy polach |
| 4 | ten sam formularz | wypełnij imię, nazwisko, firmę, zaznacz zgodę | przekierowanie na `/metodologia`; kolejne strony bez formularza |
| 5 | `/api/docs`, `/prywatnosc` | otwórz w nowym oknie prywatnym | bez formularza |
| 6 | `/odwiedzajacy` | otwórz | 404 (bez `VISITORS_TOKEN` albo z błędnym tokenem) |
| 7 | `/odwiedzajacy?token=<VISITORS_TOKEN>` | otwórz, potem `&format=csv` | tabela z wpisem z kroku 4; CSV do pobrania |

## 3. Checklista wdrożenia

### Schemat bazy (repo nie ma Alembica – kolumny dokłada `_add_missing_columns()` przy starcie aplikacji)
- [x] Zmiana schematu w tej gałęzi: tak, NOWA TABELA `demo_visitor` (tworzy ją `db.create_all()` przy starcie na SQLite i Postgresie; `_add_missing_columns` nie jest potrzebne)
- [ ] **dev** (SQLite `trash_fairy.db`): aplikacja uruchomiona, tabela istnieje (`sqlite3 trash_fairy.db ".schema demo_visitor"`)
- [x] **test** (pytest, SQLite w pamięci): `python -m pytest -q -n auto` → 512 passed; `ruff check .` czysto
- [ ] **compose** (Postgres 16 lokalnie): `docker compose up --build` startuje, `/health` = 200 (nie uruchamiano w tej sesji)
- [ ] **prod** (Postgres w Coolify): po Redeploy log startu bez błędu, `/health` = 200, tabela `demo_visitor` istnieje (sprawdza człowiek)
- [x] Ręczne kroki na bazie: nie dotyczy

### Zmienne środowiskowe
- [ ] Nowe: `VISITORS_TOKEN` – długi losowy token do listy `/odwiedzajacy` (bez niego lista nie istnieje); `DEMO_VISITOR_GATE` – `1` (domyślnie) / `0`
- [ ] Ustawione w Coolify (Environment Variables) przed Redeploy
- [x] Opisane w README i `docker-compose.yml`

### Deploy (robi człowiek)
- [ ] PR zmergowany do `main`, CI zielone (ruff + pytest)
- [ ] Coolify: zakładka *Source* wskazuje właściwą gałąź → Redeploy → w logu builda właściwa gałąź i commit
- [ ] Kroki z sekcji 2 przeklikane na produkcji

## 4. Plan wycofania
- **Kod:** Coolify → Deployments → Redeploy poprzedniego commita albo `git revert` + PR.
- **Baza:** stary kod ignoruje tabelę `demo_visitor`; bez kroków (opcjonalnie `DROP TABLE demo_visitor`).
- **Env:** szybkie wyłączenie bez deployu kodu: `DEMO_VISITOR_GATE=0` i Redeploy.
- **Sygnał do wycofania:** brak dostępu do demo mimo wypełnienia formularza (ciasteczka), `/health` ≠ 200, 500 w logach.

## 5. Ryzyka i otwarte sprawy
- Bramka dotyczy każdego GET HTML, także crawlerów i podglądów linków (zobaczą formularz zamiast strony); skrypty e2e/lokalne wymagają `DEMO_VISITOR_GATE=0`.
- Imię/nazwisko/firma nie są weryfikowane (to miękka kontrola). Brak CSRF na formularzu jest świadomy (zapis nie daje uprawnień), globalny limit 300 wpisów/h.
- Token w `?token=` może trafić do logów proxy; alternatywa: nagłówek `X-Visitors-Token`.
