# Operator: `claude/laughing-cray-me204b-visitor-activity`

- **PR / commity:** PR (draft) z tej gałęzi · „Monitoring gości v2: firmy na liście i aktywność gościa” + „README: wyraźny link do demo”
- **Data:** 2026-10-23 · **Autor zmian:** agent (Claude Code)

## 1. Co zmieniono
- **Alarm „uwaga, ta firma”:** `NTFY_WATCH_COMPANIES` (frazy po przecinku, tylko w env). Gość, którego firma zawiera
  frazę (bez wielkości liter, polskich znaków i nadmiarowych spacji; fraza min. 2 znaki), daje push z priorytetem
  `urgent`, ikoną syreny, tytułem `UWAGA firma z listy: Trash Fairy` i treścią z „⚠️ ” na początku. Bez trafienia – jak dotąd.
- **Aktywność gościa:** po wejściu przez bramkę sesja (podpisane ciasteczko) niesie id wpisu. Każdy udany GET strony
  HTML (bez `/api/`, `/static/`, `/health`, `/odwiedzajacy`, `/wizytowka`, bez 404/500) zwiększa `page_views`,
  ustawia `last_seen_at` i liczy sekcję (pierwszy segment ścieżki, `/` → `start`, max 20 sekcji). Hook:
  `after_app_request` w `app/visitor_gate.py` → `app/visitor_activity.py`. Błąd licznika = ostrzeżenie w logu, strona bez zmian.
- **Lista `/odwiedzajacy` (HTML i CSV):** nowe kolumny „Ekrany”, „Czas” (`ok. N min` = ostatnie wejście − wpis, albo „—”)
  i „Najczęściej” (3 sekcje).
- **Push „zaangażowany gość”:** gdy `page_views` = `NTFY_ENGAGED_VIEWS` (domyślnie 10, `0` = wyłączone) – jeden push
  `Gosc oglada demo: Trash Fairy`, ikona oczu, priorytet `default` (`urgent` dla firmy z listy).
- **Klauzula RODO** (formularz `ui/wizytowka.html` i `/prywatnosc`): dopisane zdanie o zapisie obejrzanych ekranów (bez IP).
- Przy okazji: bramka sprawdza wyjątki (statyki, API) przed odczytem sesji, więc statyki dla anonimowych nie dostają `Vary: Cookie`.
- Celowo NIE zmieniono: retencji 90 dni (nowe pola kasują się razem z wpisem), limitu 300 zapisów/h, treści zwykłego pusha.
  Goście z flagą sprzed wdrożenia (bez id) nie są liczeni – do czasu ponownego wpisu (najwyżej 30 dni).

## 2. Kroki do przeklikania

| # | Gdzie (URL / ekran) | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | `http://localhost:8080/health` | otwórz | `{"db": "ok", "status": "ok"}`, kod 200 |
| 2 | Coolify → env | ustaw `NTFY_WATCH_COMPANIES` na frazę testową (np. `testfirma`), `NTFY_ENGAGED_VIEWS=3`, Redeploy | start bez błędu `ALTER TABLE` w logu |
| 3 | `/metodologia` (karta prywatna) | wpis z firmą `TestFirma sp. z o.o.` | push „UWAGA firma z listy”, pilny, treść zaczyna się od ⚠️ |
| 4 | ta sama karta | otwórz jeszcze 2 ekrany (np. `/dostepnosc`, `/`) | po 3. ekranie push „Gosc oglada demo” (jeden, kolejne ekrany go nie powtarzają) |
| 5 | `/odwiedzajacy?token=…` | otwórz | przy wpisie: Ekrany 3, Czas „ok. N min”, Najczęściej np. `dostepnosc, metodologia, start` |
| 6 | `/odwiedzajacy?token=…&format=csv` | pobierz | kolumny `ekrany,czas,najczesciej` |
| 7 | nowa karta prywatna | wpis z inną firmą | zwykły push „Nowy gosc” (priorytet wysoki, dzwonek) |
| 8 | formularz i `/prywatnosc` | przeczytaj klauzulę | zdanie „Zapisuję też, ile i jakie ekrany…” |
| 9 | Coolify → env | przywróć docelowe `NTFY_WATCH_COMPANIES` i `NTFY_ENGAGED_VIEWS` (albo usuń = 10) | — |

## 3. Checklista wdrożenia

### Schemat bazy (repo nie ma Alembica – kolumny dokłada `_add_missing_columns()` przy starcie aplikacji)
- [x] Zmiana schematu w tej gałęzi: tak – `demo_visitor.page_views INTEGER NOT NULL DEFAULT 0`,
      `demo_visitor.last_seen_at TIMESTAMP`, `demo_visitor.sections TEXT`
- [x] **dev** (SQLite): test `test_kolumny_dokladane_do_starej_bazy` tworzy starą tabelę bez kolumn i sprawdza, że
      `_add_missing_columns()` je dokłada
- [x] **test** (pytest, SQLite w pamięci): `python -m pytest -q -n auto` → `563 passed in 165.81s`; `ruff check .` → All checks passed;
      Bandit (`-c pyproject.toml -r app -ll -ii`) → bez zgłoszeń
- [ ] **compose** (Postgres 16 lokalnie): `docker compose up --build` startuje, `/health` = 200
- [ ] **prod** (Postgres w Coolify): po Redeploy log startu bez błędu `ALTER TABLE`, `/health` = 200, kolumny istnieją
      (`\d demo_visitor` w konsoli bazy Coolify)
- [ ] Ręczne kroki na bazie: nie dotyczy

### Zmienne środowiskowe
- [ ] Nowe: `NTFY_WATCH_COMPANIES` – frazy po przecinku (prawdziwe nazwy firm **tylko** w Coolify, nie w repo) – `firma1, firma2`; puste = brak alarmów
- [ ] Nowe: `NTFY_ENGAGED_VIEWS` – próg ekranów dla jednego pusha – `10` (domyślnie); `0` = wyłączone; niepoprawna wartość = 10
- [ ] Ustawione w Coolify (Environment Variables) przed Redeploy
- [x] Opisane w README, `.env.example` i `docker-compose.yml`

### Deploy (robi człowiek)
- [ ] PR zmergowany do `main`, CI zielone (ruff + pytest + security)
- [ ] Coolify: zakładka *Source* wskazuje właściwą gałąź → Redeploy → w logu builda właściwa gałąź i commit
- [ ] Kroki z sekcji 2 przeklikane na produkcji

## 4. Plan wycofania
- **Kod:** Coolify → Deployments → Redeploy poprzedniego commita (`d575735`, merge #65) albo `git revert <sha>` + PR.
- **Baza:** stary kod ignoruje nowe kolumny (`page_views` ma DEFAULT 0, reszta NULL) → bez kroków.
- **Env:** wyłączenie pushy bez deployu: `NTFY_ENGAGED_VIEWS=0`, puste `NTFY_WATCH_COMPANIES`, Redeploy.
- **Sygnał do wycofania:** 500 na stronach HTML po wejściu przez bramkę, w logu powtarzające się
  `aktywność gościa: nie zapisano wejścia`, wyraźnie wolniejsze strony.

## 5. Ryzyka i otwarte sprawy
- Każdy ekran gościa to jeden dodatkowy `UPDATE` + `commit` (blokuje wiersz tego gościa do commitu, inni goście bez wpływu).
- Sekcje to tylko pierwszy segment ścieżki, więc np. `/kosz/12/zglos` liczy się jako `kosz`.
- Semgrep (p/owasp-top-ten) nie dał się uruchomić lokalnie (proxy blokuje semgrep.dev) – sprawdzi go CI. Bandit lokalnie czysty.
