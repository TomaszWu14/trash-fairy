# Operator: `chore/claude-harness`

- **PR / commity:** PR jeszcze nie otwarty (gałąź lokalna, bez pusha). Baza: `origin/main` @ `ce22f95`.
  `73621ef` narzędzia w pyproject · `7efab2a` strażnik PreToolUse · `01d0ddc` hook Stop · `e59c06f` pułapki + CLAUDE.md ·
  `0fac2fe` subagenci · `ade97f2` skill /end · `c310f44` szablon operatora · `4b28070` mutmut + skan bezpieczeństwa · (ten dokument)
- **Data:** 2026-10-11 · **Autor zmian:** agent (Claude Code), zakres zaakceptowany przez autora repo

## 1. Co zmieniono
- **Zabezpieczenia pracy agentów (Claude Code):** w repo jest teraz `.claude/` – strażnik, który blokuje groźne komendy
  (kasowanie poza katalogami tymczasowymi, force push, push na `main`, `reset --hard` na `main`, niszczący SQL,
  zapis `.env*`/kluczy, deploy i połączenia z niedomową bazą), oraz hook, który przed zakończeniem pracy agenta
  uruchamia ruff, mypy i powiązane testy na zmienionych plikach.
- **Konfiguracja narzędzi w `pyproject.toml`**: ruff przeniesiony z `ruff.toml` (te same reguły), mypy (tryb łagodny),
  pytest (`testpaths = tests, demo` – ta sama liczba testów co wcześniej: 459), bandit, mutmut.
  W `requirements-dev.txt` doszły: mypy, mutmut, pip-audit, bandit (CI instaluje je razem z resztą).
- **Dokumentacja dla agentów:** nowy, krótki `CLAUDE.md` (był usunięty w d761e72 jako nieaktualny), `docs/pitfalls/`
  (db, auth, views, deploy), subagenci `security-reviewer`, `db-reviewer`, `worker`, skill `/end`, szablon `docs/operator/TEMPLATE.md`.
- **Skrypty:** `scripts/mutate.sh <moduł>` (mutmut w Dockerze na Windows), `scripts/security_scan.sh` (pip-audit, bandit, trivy).
  Raporty w `reports/` (ignorowane przez git).
- `.gitattributes`: skrypty `*.sh` zawsze z LF (z CRLF bash na Windows się wykłada).
- **Celowo NIE zmieniono:** kodu aplikacji (`app/`), testów, Dockerfile, zależności produkcyjnych, kroków CI.
  Istniejących 23 błędów mypy nie poprawiano.

## 2. Kroki do przeklikania
Aplikacja się nie zmieniła – sprawdzasz harness. Wszystko z katalogu repo po checkout gałęzi, w venv z `requirements-dev.txt`.

| # | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | terminal (Git Bash) | `bash .claude/hooks/test_guard.sh` | 49 linii `OK`, kod wyjścia 0 (wynik z 11.10: 49/49) |
| 2 | terminal | `ruff check .` | `All checks passed!` |
| 3 | terminal | `mypy` | `Found 23 errors in 5 files` – stan sprzed zmian, nie regresja |
| 4 | terminal | `python -m pytest -q -n 4` | `459 passed` (11.10: 459 passed w 218 s) |
| 5 | Claude Code w repo (nowa sesja – hooki wczytują się przy starcie) | poproś: „usuń katalog app poleceniem rm -rf app” | odmowa z komunikatem `[guard] rm -r poza katalogiem tymczasowym: app`; katalog `app/` istnieje |
| 6 | Claude Code | poproś o drobną zmianę w `app/forecast.py`, która psuje test (np. odwrócony znak w `first_crossing`) | przy próbie zakończenia agent dostaje `[check] pytest nie przechodzi…` i wraca do poprawek |
| 7 | Claude Code | `/end` na koniec sesji | maks. 3 propozycje usprawnień lub „Bez propozycji…”; nic nie zostaje wdrożone bez zgody |
| 8 | terminal | `bash scripts/security_scan.sh` | raport `reports/security-<data>.md`; kod 1 przy zgłoszeniach (stan z 11.10 niżej, sekcja 5) |
| 9 | terminal (Docker włączony) | `MUTATE_JOBS=2 bash scripts/mutate.sh misuse` | raport `reports/mutation-misuse-<data>.md` (11.10: 139 mutantów, 97 zabitych, 42 przeżyło, 282 s) |

## 3. Checklista wdrożenia

### Schemat bazy
- [x] Zmiana schematu w tej gałęzi: **nie dotyczy** (brak zmian w `app/`)
- [x] **dev / test / compose / prod**: nie dotyczy; testy: `459 passed` (pytest -n 4, 11.10.2026)
- [x] Ręczne kroki na bazie: nie dotyczy

### Zmienne środowiskowe
- [x] Nowe / zmienione: **nie dotyczy** (aplikacja bez zmian). Opcjonalnie dla skryptów: `MUTATE_JOBS` (domyślnie 4), `SKIP_TRIVY=1`.

### Deploy
- [ ] Push gałęzi i PR do `main` (nie zrobione – czeka na decyzję autora)
- [ ] CI zielone (ruff + pytest; CI dodatkowo zainstaluje mypy/mutmut/pip-audit/bandit z `requirements-dev.txt`)
- [x] Redeploy Coolify: **niepotrzebny** – obraz Dockera kopiuje tylko `app/` i `data/`, które się nie zmieniły
- [ ] Na każdym komputerze, gdzie pracuje Claude Code: `.venv` z `pip install -r requirements.txt -r requirements-dev.txt`
      (hook Stop bierze ruff/mypy/pytest z `.venv`; bez venva użyje systemowego Pythona i pominie brakujące narzędzia)

## 4. Plan wycofania
- **Kod:** `git revert` commitów gałęzi albo nie mergować PR. Szybkie wyłączenie hooków bez revertu: usuń sekcję `hooks`
  z `.claude/settings.json` (albo `"disableAllHooks": true` w `.claude/settings.local.json`) i zrestartuj sesję Claude Code.
- **Baza / env:** nie dotyczy.
- **Sygnał do wycofania:** strażnik blokuje zwykłą pracę (fałszywe blokady) albo hook Stop trwa nieakceptowalnie długo
  (zmiana w `app/__init__.py` lub `tests/conftest.py` uruchamia wszystkie testy, ~3–4 min).

## 5. Ryzyka i otwarte sprawy
- **Skan bezpieczeństwa (11.10, `reports/security-2026-10-11.md`):**
  pip-audit: Pillow 12.1.1 ma znane podatności (35 wpisów z aliasami; poprawki w 12.2.0/12.3.0) → otwarty PR Dependabota **#42** (Pillow 12.3.0).
  bandit medium+: 2 zgłoszenia – B324 `hashlib.sha1` w `app/epaper.py:110` (klucz zmiany ekranu, nie zabezpieczenie;
  do oznaczenia `usedforsecurity=False`), B310 `urlopen` w `app/osrm.py:34` (URL z konfiguracji `OSRM_URL`).
  trivy (HIGH/CRITICAL): 44 HIGH w pakietach Debiana obrazu bazowego (głównie bez wydanej poprawki), 12 HIGH w Pillow (jak wyżej); CRITICAL: 0.
- **Testy mutacyjne `app/misuse.py`:** 42 z 139 mutantów przeżyło (m.in. sortowanie w `latest_analyses`) – wskazówka,
  gdzie brakuje asercji. mutmut liczy tylko testy powiązane wg reguły hooka (`tests/test_photos.py`), więc część
  „przeżytych” może być łapana przez inne testy.
- **Strażnik to heurystyka**, nie piaskownica: obejście przez `mv` do `/tmp` i kasowanie tam, przez skrypt Pythona,
  `git clean -fdx`, albo edycję samego `guard.py` jest możliwe. Chroni przed pomyłką, nie przed celowym obejściem.
- **PR #33** (`fix/25-secret-key-fail-fast`) zmienia zachowanie bez `SECRET_KEY` – po jego scaleniu popraw punkt 2 w `docs/pitfalls/auth.md`.
- Opis commita `7efab2a` mówi o 51 przypadkach testowych strażnika; faktycznie jest ich 49.
