# Wyniki po Fali 1 audytu i PWA kierowcy

Data: 3.10.2026, wieczór. Gałąź `ux-overhaul` (PR #3). Przed: `screens/`, `lighthouse/` (audyt z `UX_UI_AUDIT.md`).
Po: `after/` (183 zrzuty, ten sam skrypt `scripts/audit_screens.py`, dodane ekrany `kierowca-*` i `404-*`), `lighthouse-after/`.

## Poziomy scroll

| Ekran | Przed | Po |
|---|---|---|
| `/` widok C, 360 / 390 px | 460 px | brak |
| `/dyspozytor`, 360 / 390 px | 469 px | brak |
| `/dyspozytor`, 1024 px | **1 339 px** | brak |
| `/metodologia`, 360 px | 377 px | brak (tabela przewija się w swoim pudełku) |
| `/kierowca`, `/zglos/99999` (nowe) | — | brak |

`after/_findings.json`: `hscroll: []` na wszystkich 6 szerokościach, zero `pageerror`. Zgłoszenie → `fresh` w API: 263 ms (bez zmian).

## Lighthouse (lokalnie, Chromium headless, Lighthouse 13.5)

| Strona | Perf | A11y | Best | SEO | LCP | CLS |
|---|---|---|---|---|---|---|
| `/` widok C (desktop) | 80 → **87** | 100 → 100 | 100 → 100 | 91 → 91 | 1,5 → 1,7 s | 0,28 → **0,13** |
| `/dyspozytor` (desktop) | 80 → 79 | 97 → 97 | 100 → 100 | 91 → 91 | 2,0 → 2,1 s | 0,18 → **0,13** |
| `/zglos/18` (mobile) | 59 → **76** | 98 → 98 | 92 → 92 | 100 → 100 | 4,2 → **2,9 s** | 0,30 → 0,30 |
| `/ekipa` → `/kierowca` (mobile) | 69 → **82** | 100 → 100 | 100 → 100 | 90 → 90 | 4,4 → 4,7 s | 0,00 → 0,00 |
| `/epapier/18` (desktop) | 98 → 99 | 98 → 98 | 96 → 96 | 91 → 91 | 0,9 → 0,8 s | 0,00 → 0,05 |

Wyniki wydajności wahają się między przebiegami o ±4 pkt (panel na `main`: 75–79). Panel ma Tailwind z CDN (Fala 2, A9).

**Regresja złapana pomiarem:** po pierwszej wersji poprawek panel miał CLS 0,5 (perf 63). Przyczyna: menu z `overflow-x: auto`
dostawało pasek przewijania w trakcie ładowania fontów, nagłówek rósł o jego wysokość i całe `main` zjeżdżało. Pasek jest ukryty
(przewijalność sygnalizuje cień krawędzi), plakietka skrócona do „DEMO · SYMULACJA”, CLS 0,13. To samo w PWA kierowcy:
chip „Online” przeskakiwał do drugiego wiersza, teraz stoi tam na stałe (CLS 0,35 → 0).

## Pozycje audytu

| ID | Stan | Uwagi |
|---|---|---|
| E1, E2, E3 | ✅ zamknięte | poziomy scroll (tabela wyżej) |
| A1 | ✅ | ostrzeżenie przy QR na localhost bez `PUBLIC_URL` (widok C, panel) |
| A4 | ✅ | blokada gdy `odległość − min(dokładność GPS, 150) > 150 m`, serwer i telefon |
| A8 | ✅ | polska strona 404, API dalej JSON |
| A10 | ✅ | „Aktualizacja hh:mm:ss”, po 3 nieudanych pollach „Brak połączenia · dane z …” (tekst + trójkąt) |
| B1 | ✅ | „Najbliższe przepełnienia” nad QR, karta 1 z nazwami punktów |
| C2 | ✅ | trasy w panelu po ulicach (OSRM) |
| C5, D4, D5 | ✅ | nagłówki na telefonie, zwijana legenda, menu panelu bez ucinania na 1440 px |
| F1 | ✅ | PWA kierowcy `/kierowca` (start → trasa → przystanek → podsumowanie, offline, `POST /api/stop-issue`) |
| F4 | ✅ | ikony PNG 192/512 + maskable w obu manifestach |
| D8, E5, G3, A7 | ✅ przez F1 | zdjęcie przez własny przycisk, „następny przystanek”, „Cofnij” 5 s, postęp zapisany w telefonie |
| B3, D1–D3, C1, B4, A2, A9, I1, I3 | Fala 2 | w `ROADMAPA.md` |

Testy: `python -m pytest -q` → 170 passed.
