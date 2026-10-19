# Operator: `claude/security-baseline`

- **PR / commity:** PR do uzupełnienia po otwarciu · `git log origin/main..HEAD --oneline` (commity tej gałęzi)
- **Data:** 2026-10-19 · **Autor zmian:** agent (Claude Code)

## 1. Co zmieniono
- Nowy workflow `.github/workflows/security.yml`: gitleaks (sekrety), Bandit i Semgrep (SAST), pip-audit
  (zależności), Trivy (zależności, sekrety, `Dockerfile`). Czerwony wynik blokuje PR.
- Każda odpowiedź ma dodatkowe nagłówki: `X-Frame-Options: SAMEORIGIN`, `Permissions-Policy`,
  `Cross-Origin-Opener-Policy: same-origin`; odpowiedzi JSON bez własnego `Cache-Control` dostają `no-store`;
  HSTS (`max-age=31536000`) tylko gdy `PUBLIC_URL` zaczyna się od `https://`.
- `SECURITY.md` (zgłaszanie podatności przez GitHub), sekcja „Bezpieczeństwo” w README, Dependabot dla obrazu Docker,
  `ci.yml` z tokenem tylko do odczytu.
- Celowo NIE zmieniono: pełnej CSP (skrypty/style inline), użytkownika w kontenerze (root), logiki aplikacji.

## 2. Kroki do przeklikania

| # | Gdzie (URL / ekran) | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | `http://localhost:8080/health` | otwórz | `{"db": "ok", "status": "ok"}`, kod 200 (503 = baza nie odpowiada) |
| 2 | `curl -sI http://localhost:8080/` | sprawdź nagłówki | `X-Frame-Options: SAMEORIGIN`, `Permissions-Policy: camera=(), …`, `Cross-Origin-Opener-Policy: same-origin`; bez HSTS lokalnie |
| 3 | `/zglos` → zgłoszenie wysypiska | „Użyj mojego położenia” i dodanie zdjęcia | przeglądarka pyta o położenie; wybór zdjęcia/aparatu działa |
| 4 | prod: `curl -sI https://<domena>/api/v1/routes` | po deployu | `Strict-Transport-Security: max-age=31536000`, `Cache-Control: public, max-age=60` (open data bez zmian) |

## 3. Checklista wdrożenia

### Schemat bazy (repo nie ma Alembica – kolumny dokłada `_add_missing_columns()` przy starcie aplikacji)
- [x] Zmiana schematu w tej gałęzi: nie dotyczy
- [ ] **dev** (SQLite `trash_fairy.db`): nie dotyczy
- [x] **test** (pytest, SQLite w pamięci): `python -m pytest -q -n auto` → 494 passed, ruff czysto
- [ ] **compose** (Postgres 16 lokalnie): `docker compose up --build` startuje, `/health` = 200
- [ ] **prod** (Postgres w Coolify): po Redeploy `/health` = 200
- [x] Ręczne kroki na bazie: nie dotyczy

### Zmienne środowiskowe
- [x] Nowe / zmienione: nie dotyczy (HSTS korzysta z istniejącego `PUBLIC_URL`)
- [x] Ustawione w Coolify: nie dotyczy
- [x] Opisane w README / `docker-compose.yml`: nie dotyczy

### Deploy (robi człowiek)
- [ ] PR zmergowany do `main`, CI zielone (ruff + pytest + Security)
- [ ] Coolify: zakładka *Source* wskazuje właściwą gałąź → Redeploy → w logu builda właściwa gałąź i commit
- [ ] Kroki z sekcji 2 przeklikane na produkcji
- [ ] GitHub *Settings → Code security*: włączone *Private vulnerability reporting* (link w `SECURITY.md`)

## 4. Plan wycofania
- **Kod:** Coolify → Deployments → Redeploy poprzedniego commita albo `git revert <sha>` + PR.
- **Baza:** bez zmian schematu — bez kroków.
- **Env:** nie dotyczy.
- **Sygnał do wycofania:** geolokalizacja zablokowana, PWA przestaje się aktualizować.
  Uwaga: HSTS przeglądarki pamiętają rok — wycofanie kodu go nie cofa (domena i tak działa po HTTPS).

## 5. Ryzyka i otwarte sprawy
- Klucz stanu e-papieru liczony teraz SHA-256 zamiast SHA-1 (Semgrep): po deployu każdy ekran raz odświeży się w całości.
- Pełna CSP i kontener bez roota (wyjątek `DS-0002` w `.trivyignore`) — do decyzji właściciela.
