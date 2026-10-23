# Operator: `claude/laughing-cray-me204b-visitor-notify`

- **PR / commity:** PR (draft) z tej gałęzi · jeden commit „Powiadomienie push (ntfy) o nowym gościu demo”
- **Data:** 2026-10-23 · **Autor zmian:** agent (Claude Code)

## 1. Co zmieniono
- Po każdym **udanym** wpisie w bramce odwiedzających (`/wizytowka`) właściciel dostaje push na telefon (aplikacja ntfy):
  treść `Imię Nazwisko (Firma) wszedł do Trash Fairy`, tytuł `Nowy gosc: Trash Fairy`, priorytet wysoki, ikona dzwonka.
- Wysyłka w wątku w tle (timeout 5 s) – gość nie czeka; błąd sieci/serwera ntfy to tylko ostrzeżenie w logu.
- Brak powiadomienia przy błędach walidacji, wypełnionym honeypocie i przekroczonym limicie 300 zapisów/h.
- Kod: `app/visitor_notify.py`; w `app/visitor_gate.py` jedno wywołanie po `commit()`.
- Klauzula RODO w formularzu (`ui/wizytowka.html`) i na `/prywatnosc` mówi teraz o powiadomieniu przez ntfy.
- Celowo NIE zmieniono: modelu `DemoVisitor`, retencji 90 dni, limitu, listy `/odwiedzajacy`. Aplikacja nie ma wersji EN klauzuli.

## 2. Kroki do przeklikania

| # | Gdzie (URL / ekran) | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | `http://localhost:8080/health` | otwórz | `{"db": "ok", "status": "ok"}`, kod 200 |
| 2 | telefon, aplikacja ntfy | zasubskrybuj temat z `NTFY_URL` (długi, losowy) | temat widoczny na liście |
| 3 | `/metodologia` (nowa karta prywatna) | formularz: imię, nazwisko, firma, zgoda → Wejdź | przekierowanie do `/metodologia`; w ciągu kilku sekund push „… wszedł do Trash Fairy” |
| 4 | formularz | wyślij bez zgody | komunikat błędu, **brak** pusha |
| 5 | Coolify → logi | ustaw celowo zły `NTFY_URL` (np. nieistniejący host), krok 3 | gość wchodzi normalnie; w logu `ntfy: nie wysłano powiadomienia o gościu` |
| 6 | `/prywatnosc` i formularz | przeczytaj sekcję o odwiedzających | zdanie o powiadomieniu przez usługę push ntfy |

## 3. Checklista wdrożenia

### Schemat bazy (repo nie ma Alembica – kolumny dokłada `_add_missing_columns()` przy starcie aplikacji)
- [x] Zmiana schematu w tej gałęzi: nie dotyczy
- [ ] **dev** (SQLite `trash_fairy.db`): nie dotyczy
- [x] **test** (pytest, SQLite w pamięci): `python -m pytest -q -n auto` → `525 passed in 115.42s`; `ruff check .` → All checks passed; Bandit (`-r app -ll -ii`) → bez zgłoszeń
- [ ] **compose** (Postgres 16 lokalnie): `docker compose up --build` startuje, `/health` = 200
- [ ] **prod** (Postgres w Coolify): nie dotyczy (bez zmian schematu); `/health` = 200 po Redeploy
- [ ] Ręczne kroki na bazie: nie dotyczy

### Zmienne środowiskowe
- [ ] Nowe: `NTFY_URL` – pełny URL tematu ntfy, tylko `https://`/`http://` (inny schemat = pominięte z ostrzeżeniem) – `https://ntfy.sh/<długi-losowy-temat>`; puste = brak powiadomień
- [ ] Nowe: `NTFY_TOKEN` – opcjonalny token (nagłówek `Authorization: Bearer`) dla serwera ntfy z kontrolą dostępu
- [ ] Ustawione w Coolify (Environment Variables) przed Redeploy
- [x] Opisane w README, `.env.example` i `docker-compose.yml`

### Deploy (robi człowiek)
- [ ] PR zmergowany do `main`, CI zielone (ruff + pytest + security)
- [ ] Coolify: zakładka *Source* wskazuje właściwą gałąź → Redeploy → w logu builda właściwa gałąź i commit
- [ ] Kroki z sekcji 2 przeklikane na produkcji

## 4. Plan wycofania
- **Kod:** Coolify → Deployments → Redeploy poprzedniego commita (`a7147dc`, merge #64) albo `git revert <sha>` + PR.
- **Baza:** bez kroków (schemat bez zmian).
- **Env:** szybkie wyłączenie bez deployu kodu: usuń/wyczyść `NTFY_URL` i Redeploy.
- **Sygnał do wycofania:** 500 albo wyraźne opóźnienie po wysłaniu formularza, spam powiadomień.

## 5. Ryzyka i otwarte sprawy
- Temat na publicznym `ntfy.sh` jest jawny dla każdego, kto zna nazwę: użyj długiej, losowej nazwy albo własnego serwera z `NTFY_TOKEN`.
- Dane gościa (imię, nazwisko, firma) trafiają do zewnętrznej usługi ntfy – klauzula RODO to już mówi; przy własnym serwerze poza UE rozważ dopisek o transferze.
- Semgrep (p/owasp-top-ten) nie dał się uruchomić lokalnie (proxy blokuje semgrep.dev) – sprawdzi go CI. Bandit lokalnie czysty.
