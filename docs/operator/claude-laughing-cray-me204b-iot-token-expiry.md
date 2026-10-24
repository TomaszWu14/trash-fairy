# Operator: `claude/laughing-cray-me204b-iot-token-expiry`

- **PR / commity:** PR jeszcze nie utworzony · jeden commit „Wygasanie tokenów urządzeń” na `origin/main` (5614221)
- **Data:** 2026-10-24 · **Autor zmian:** agent

## 1. Co zmieniono
- Token urządzenia (nagłówek `X-Token-Urzadzenia` w `POST /api/odczyty` i pole `token` w `POST /api/kosze/<id>/przycisk`) wygasa po `DEVICE_TOKEN_TTL_DAYS` dniach (domyślnie 365). Wygasły token daje tę samą odpowiedź co zły (401 `nieznane_urzadzenie` / 403 `zly_token_panelu`).
- Nowa kolumna `device_info.token_issued_at` (prawdziwy czas UTC). Istniejące wiersze dostają przy starcie datę „teraz”, więc urządzenia w terenie nie przestają działać wcześniej niż po pełnym okresie ważności od wdrożenia. Brak daty w wierszu = token nie wygasa (do czasu uzupełnienia przy starcie).
- Nowa komenda `flask --app app renew-device-tokens [--serial NR]` ustawia datę wydania na teraz. Wartość tokenu się NIE zmienia (to wciąż HMAC numeru seryjnego z `SECRET_KEY`), więc odnowienie nie wymaga ponownego wgrywania urządzeń.
- Porównanie tokenu dalej `hmac.compare_digest`; logika w jednym miejscu: `devices_api.token_valid`.
- Celowo NIE zmieniono: formatu/wartości tokenu (zmiana wymagałaby ponownego wgrania wszystkich urządzeń). Skutek: wygaśnięcie ogranicza okno użycia tokenu bez odnowienia, ale nie unieważnia wycieku, jeśli ktoś odnowi daty (rotacja wartości = zmiana `SECRET_KEY`, co unieważnia też kody QR).

## 2. Kroki do przeklikania

| # | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | `/health` | otwórz | `{"db": "ok", "status": "ok"}`, 200 |
| 2 | `POST /api/odczyty` z poprawnym tokenem czujnika | wyślij odczyt | 201 |
| 3 | `flask --app app shell`: `DeviceInfo.query.first().token_issued_at = <rok temu minus dzień>`, commit; powtórz krok 2 | wyślij odczyt | 401 `nieznane_urzadzenie` |
| 4 | `flask --app app renew-device-tokens --serial <NR>` i krok 2 | wyślij odczyt | `Odnowiono tokeny: 1.`, potem 201 |

## 3. Checklista wdrożenia

### Schemat bazy
- [x] Zmiana schematu: `device_info.token_issued_at TIMESTAMP` (nullable, dopisana do `_add_missing_columns`, backfill `UPDATE ... WHERE token_issued_at IS NULL`)
- [x] **dev/test** (SQLite w pamięci): `python -m pytest -q -n auto` → 568 passed
- [ ] **compose** (Postgres 16): `docker compose up --build`, `/health` = 200 (nie sprawdzono w tej sesji)
- [ ] **prod**: po Redeploy brak błędu `ALTER TABLE` w logu, `/health` = 200
- [ ] Ręczne kroki na bazie: nie dotyczy

### Zmienne środowiskowe
- [ ] Nowa: `DEVICE_TOKEN_TTL_DAYS` – ważność tokenu urządzenia w dniach (opcjonalna, domyślnie 365; wartość nieliczbowa lub < 1 = 365). Opisana w `.env.example`.
- [ ] Ustawić w Coolify tylko jeśli ma być inna niż 365

### Deploy (robi człowiek)
- [ ] PR zmergowany, CI zielone
- [ ] Coolify Redeploy, kroki z sekcji 2 na produkcji
- [ ] Zapisać w kalendarzu datę wdrożenia + 365 dni: wtedy uruchomić `renew-device-tokens` (albo wcześniej)

## 4. Plan wycofania
- **Kod:** Redeploy poprzedniego commita albo `git revert`.
- **Baza:** stary kod ignoruje kolumnę `token_issued_at`, bez kroków.
- **Env:** nie dotyczy (zmienna opcjonalna).
- **Sygnał do wycofania:** 401 z `/api/odczyty` od urządzeń, które powinny działać (sprawdź `token_issued_at` i `DEVICE_TOKEN_TTL_DAYS`).

## 5. Ryzyka i otwarte sprawy
- Po wygaśnięciu bez `renew-device-tokens` wszystkie urządzenia dostaną 401 naraz (daty z backfillu są jednakowe). Warto odnowić przed terminem.
- Brak panelu admina (aplikacja nie ma logowania), odnowienie tylko przez CLI.
- Wynik komend: `ruff check .` → All checks passed; `mypy` → 25 błędów w 5 plikach, tyle samo co na `origin/main` przed zmianą; `pytest -q -n auto` → 568 passed.
