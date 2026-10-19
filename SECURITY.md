# Bezpieczeństwo

## Zgłaszanie podatności

Podatności zgłaszaj **prywatnie**, nie przez publiczne issue ani PR (repozytorium jest publiczne):
GitHub **Security → Report a vulnerability** —
<https://github.com/TomaszWu14/trash-fairy/security/advisories/new>.

Podaj: adres strony lub endpointu, kroki odtworzenia, skutek oraz SHA commita (jeśli go znasz).
Nie dołączaj prawdziwych danych osobowych. Odpowiedź otrzymasz najczęściej do 7 dni.

Testy w dobrej wierze są mile widziane wyłącznie na lokalnej kopii lub instancji demo (dane syntetyczne),
bez ataków odmowy usługi.

## Zakres

Wspierana jest gałąź domyślna `main` i wdrożenie zbudowane z niej. Poprawki nie są przenoszone
do starszych commitów.

## Automatyczne kontrole (CI)

| Narzędzie | Co sprawdza | Kiedy | Blokuje? |
|---|---|---|---|
| **gitleaks** (przypięta wersja + sha256) | sekrety w historii gita | PR (tylko jego commity), push do `main`, co tydzień i ręcznie (cała historia) — `security.yml` | tak |
| **Bandit** | SAST kodu `app/`, ważność i pewność medium+ | jak wyżej | tak |
| **Semgrep** `p/owasp-top-ten` | `app/`: Python, JS (`app/static/ui`), szablony (bez `app/static/vendor`) | jak wyżej, wynik także jako artefakt SARIF | tak |
| **pip-audit** | znane podatności w `requirements.txt` i `requirements-dev.txt` | jak wyżej | tak |
| **Trivy** `fs` | podatności, sekrety, konfiguracja (`Dockerfile`), HIGH/CRITICAL z dostępną poprawką | jak wyżej | tak |
| **ruff + pytest** | lint i testy, w tym nagłówków bezpieczeństwa | `ci.yml` | tak |
| **Dependabot** | cotygodniowe PR-y: pip, GitHub Actions, obraz Docker | `.github/dependabot.yml` | — |

Fałszywe alarmy oznaczamy w kodzie z powodem: Bandit `# nosec BXXX`, Semgrep `nosemgrep`
(komentarz z powodem obok). Wyjątki Trivy: `.trivyignore` (ID, uzasadnienie, data przeglądu).
Lokalnie: `bash scripts/security_scan.sh` (pip-audit, Bandit, Trivy obrazu).

## Wbudowane zabezpieczenia aplikacji

- Nagłówki na każdej odpowiedzi (`_security_headers` w `app/__init__.py`): `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: SAMEORIGIN` i `Content-Security-Policy: frame-ancestors 'self'` (osadzanie w ramce tylko
  na tej samej stronie), `Referrer-Policy: strict-origin-when-cross-origin`,
  `Permissions-Policy` (bez kamery, mikrofonu, płatności i USB; geolokalizacja tylko dla tej strony),
  `Cross-Origin-Opener-Policy: same-origin`, `Cache-Control: no-store` na odpowiedziach JSON (o ile endpoint
  nie ustawił własnego). **HSTS** tylko za HTTPS — gdy `PUBLIC_URL` zaczyna się od `https://` (ta sama flaga
  co `Secure` ciasteczka sesji).
- Zapis chronią tokeny HMAC z `SECRET_KEY` i limity w bazie (szczegóły: `docs/pitfalls/auth.md`).
- Sekrety tylko w zmiennych środowiskowych / `.env` (poza repozytorium).

## Znane ograniczenia

- Pełna polityka CSP (skrypty, style) nie jest jeszcze włączona — szablony mają skrypty i style inline.
- Kontener działa jako root (wyjątek `DS-0002` w `.trivyignore`, do decyzji właściciela).
