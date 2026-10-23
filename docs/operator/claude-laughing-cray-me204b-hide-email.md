# Operator: `claude/laughing-cray-me204b-hide-email`

- **PR / commity:** draft PR (numer w opisie) · jeden commit „Ukrycie adresu e-mail właściciela przed botami”
- **Data:** 2026-10-23 · **Autor zmian:** agent

## 1. Co zmieniono
- W klauzuli RODO bramki gościa (`/wizytowka`, szablon `ui/wizytowka.html`) i w `/prywatnosc` adres kontaktowy jest pisany jako `tomasz.wierzbowski [at] op.pl` (bez znaku `@`), żeby boty zbierające adresy go nie wyciągnęły.
- W tych szablonach nie było `mailto:`, więc nic nie usuwano.
- Nowy test sprawdza, że wyrenderowane strony nie zawierają pełnego adresu, a zawierają zapis z „[at]”.
- Celowo nie zmieniono: żadnej innej treści, konfiguracji ani wysyłki maili. `git grep` po pełnym adresie nic już nie zwraca.

## 2. Kroki do przeklikania

| # | Gdzie (URL / ekran) | Co zrobić | Oczekiwany wynik |
|---|---|---|---|
| 1 | `http://localhost:8080/health` | otwórz | `{"db": "ok", "status": "ok"}`, 200 |
| 2 | `/prywatnosc` | otwórz, znajdź „Administrator” | `tomasz.wierzbowski [at] op.pl`, bez linku |
| 3 | `/metodologia` (okno prywatne, bramka włączona) | przeczytaj klauzulę pod formularzem | „kontakt: tomasz.wierzbowski [at] op.pl” |

## 3. Checklista wdrożenia

### Schemat bazy
- [x] Zmiana schematu w tej gałęzi: nie dotyczy
- [x] **test** (pytest, SQLite w pamięci): `python -m pytest -q -n auto` (wynik w opisie PR)
- [ ] **dev / compose / prod**: nie dotyczy (brak zmian schematu)

### Zmienne środowiskowe
- [x] Nowe / zmienione: nie dotyczy

### Deploy (robi człowiek)
- [ ] PR zmergowany do `main`, CI zielone (ruff + pytest)
- [ ] Coolify: Redeploy właściwej gałęzi i commita
- [ ] Kroki z sekcji 2 przeklikane na produkcji

## 4. Plan wycofania
- **Kod:** Coolify → Redeploy poprzedniego commita albo `git revert` + PR.
- **Baza:** nie dotyczy.
- **Env:** nie dotyczy.
- **Sygnał do wycofania:** błąd renderu `/prywatnosc` lub `/metodologia`.

## 5. Ryzyka i otwarte sprawy
- Zapis „[at]” nie jest klikalny; użytkownik przepisuje adres ręcznie (zamierzone).
