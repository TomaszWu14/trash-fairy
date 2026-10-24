# Operator: `claude/laughing-cray-me204b-archiwum-audit`

- **PR / commity:** PR do uzupełnienia · `docs: move audit notes to docs/archiwum/audit`
- **Data:** 2026-10-22 · **Autor zmian:** agent

## 1. Co zmieniono
- Notatki robocze z audytu (`audit/`: AUDYT-UX, JURY, PLAN-POPRAWEK, POPRAWKI-JURY, WZORCE, wyniki Lighthouse/axe, metryki
  jury) przeniesione do `docs/archiwum/audit/` (`git mv`, historia plików zostaje). Katalog główny repo jest krótszy.
- Zaktualizowane wszystkie odwołania: `DECYZJE.md`, docstringi w `app/api_wspolne.py`, `app/ui.py`, `app/views.py`,
  `tests/test_perspektywy.py`, tekst na stronie `/dostepnosc`, wewnętrzne odwołania w przeniesionych plikach,
  ścieżki wyjściowe skryptów `scripts/{axe_check,iter_shots,iter_flow_*,jury_check,po_shots,przed_po}.py` i wpisy w `.gitignore`.
- Celowo NIE zmieniono: `docs/audit/` (inny, wcześniejszy audyt UX/UI — zostaje na miejscu), linków do historii
  GitHub (`tree/ce22f95/audit`), które nadal wskazują stan sprzed usunięcia zrzutów.

## 2. Kroki do przeklikania
| # | Gdzie (URL / ekran) | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | GitHub → katalog główny repo | otwórz | brak katalogu `audit/`, jest `docs/archiwum/audit/` |
| 2 | `http://localhost:5000/dostepnosc` | przewiń do akapitu o motywach | „zrzutach ekranu (docs/archiwum/audit/ w repozytorium)” |

## 3. Checklista wdrożenia

### Schemat bazy (repo nie ma Alembica – kolumny dokłada `_add_missing_columns()` przy starcie aplikacji)
- [x] Zmiana schematu w tej gałęzi: nie dotyczy
- [x] **dev** (SQLite `trash_fairy.db`): nie dotyczy
- [x] **test** (pytest, SQLite w pamięci): `python -m pytest -q -n auto` → 494 passed; `ruff check .` → All checks passed
- [x] **compose** (Postgres 16 lokalnie): nie dotyczy
- [x] **prod** (Postgres w Coolify): nie dotyczy
- [x] Ręczne kroki na bazie: nie dotyczy

### Zmienne środowiskowe
- [x] Nowe / zmienione: nie dotyczy
- [x] Ustawione w Coolify: nie dotyczy
- [x] Opisane w README / `docker-compose.yml`: nie dotyczy

### Deploy (robi człowiek)
- [ ] PR zmergowany do `main`, CI zielone (ruff + pytest)
- [ ] Coolify → Redeploy (zmienia się tylko tekst na `/dostepnosc`; bez Redeploy prod pokazuje starą ścieżkę)
- [ ] Krok 2 z sekcji 2 przeklikany na produkcji

## 4. Plan wycofania
- **Kod:** `git revert <sha>` + PR.
- **Baza:** nie dotyczy
- **Env:** nie dotyczy
- **Sygnał do wycofania:** martwy link do `audit/` zgłoszony przez czytelnika.

## 5. Ryzyka i otwarte sprawy
- Sprawdzenie linków (skrypt: każde odwołanie `docs/archiwum/audit/...` w plikach z `git ls-files` musi istnieć albo być
  ignorowanym wynikiem skryptu): brak starych odwołań `audit/`; nie istnieją tylko `PRZED-PO.html` i `zrzuty/po/` —
  to pliki generowane przez `scripts/przed_po.py`/`po_shots.py`, których nie było w repo już przed tą zmianą.
