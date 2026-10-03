# Top poprawek pod jury (z JURY-WYMAGANIA.md), w kolejności wykonania

Stan na niedz. 4.10, ok. 02:00. Juror: T = techniczny, M = miasto, P = produkt. Nakład: S ≤ 30 min, M ≤ 2 h, L > 2 h.
Już spełnione (nie powtarzamy): deploy, e2e 26/26, reset demo, polling, jednolite błędy, 5 frakcji, scalanie zgłoszeń, QR + 150 m,
oś czasu statusu, KPI/wykresy/mapa/projekty, filtry i drill-down, design system, puste stany, scenariusz demo, AGPL, `/metodologia`.

## P0: przed zamrożeniem kodu (największy wpływ, mały nakład)

| # | Poprawka | Juror | Nakład |
|---|---|---|---|
| 1 | `clock.reset()` nie regeneruje historii (historia nie zależy od akcji demo) → reset i auto-reset po 30 min w < 2 s zamiast ~10 s | T2, T6 | S |
| 2 | Test na PostgreSQL (prod) zapytań dashboardu (`to_char`, `extract`) przed Redeployem | T1, T3 | S |
| 3 | **AI realnie w przepływie**: zdjęcie ze zgłoszenia → Claude Vision przez `app/llm.py` (schemat JSON, walidacja) → reguły: „Zweryfikowane AI” / „Do weryfikacji”; fallback bez klucza | T21–25, M24, P27 | M |
| 4 | „Pokaż analizę AI” na karcie kosza kierowcy i w statusie zgłoszenia (wynik, pewność, uzasadnienie) | T22, AI-8 | S |
| 5 | Usuwanie EXIF (GPS, urządzenie) ze zdjęć mieszkańców przed zapisem; informacja przy dodawaniu zdjęcia „bez osób i tablic” | T36, M31–32 | S |
| 6 | Prognoza na ekranach: „85% ok. 20:20” (pole `crossing_label` silnika) na panelu kosza i karcie kierowcy | T26, AI-6 | S |
| 7 | Priorytet kierowcy wyjaśniony: chip „Dlaczego na górze: 2 zgłoszenia, 113%” | T27, AI-5, P13 | S |
| 8 | „Uszkodzony” i „Inne” nie podnoszą szacunku zapełnienia (osobna ścieżka jak dawniej) | M15, T28 | S |
| 9 | Licznik KPI przy wejściu (`TF.countUp` istnieje, nieużywany) | P8 | S |
| 10 | Karta projektu planowanego: krótki efekt („Start 11.2026”) zamiast długiego zdania | P4 | S |
| 11 | Panel kiosku offline: ostatni znany stan + „Stan z 13:42” zamiast samego komunikatu | T48 | S |
| 12 | Edukacja segregacji: na panelu „Co tu wrzucać / czego nie” wg frakcji kosza | M25 | S |
| 13 | Limit zgłoszeń per IP na godzinę (obok per telefon i kosz) | T34 | S |
| 14 | Mieszkaniec: runda 2 pętli jakości (desktop + telefon), chipy bez zawijania na starcie | P2, P9 | S |
| 15 | Lighthouse ≥ 90 (wydajność, dostępność) dla `/` i `/dashboard` + axe-core bez krytycznych | T6, P20 | M |
| 16 | `audit/PRZED-PO.html`: zrzuty przed/po każdej perspektywy | P47 | S |
| 17 | `docker-compose.yml` (app + Postgres 16, seed na starcie): uruchomienie jednym poleceniem | T17 | S |
| 18 | README: diagram architektury (Mermaid), sekcja „Co prawdziwe, co symulowane”, nowe zrzuty 4 perspektyw | T9, T46, P46–49 | S |
| 19 | `.env.example` bez `DEMO_PASSWORD` (plik zablokowany dla mnie, do zrobienia ręcznie); Coolify: usuń zmienną | T16 | S |
| 20 | Slajdy: nowa paleta i czcionka aplikacji, nowe zrzuty, slajd „ask” (pilotaż Dzielnica I, 50 koszy, 3 miesiące) | P36–45, M41 | M |
| 21 | Scenariusz wideo i `.srt` pod nowe ekrany (stary opisuje `/telefony`) | P39, P48 | S |
| 22 | Teksty HackTribe: nowe ekrany, AI, dashboard, urządzenia | P46 | S |

## P1: mocne wzmocnienia (jeśli zostanie czas przed 19:00)

| # | Poprawka | Juror | Nakład |
|---|---|---|---|
| 23 | Endpoint IoT `POST /api/odczyty` (token urządzenia, walidacja zakresu) zasilający moduł urządzeń; symulator w demo | T39, M43 | M |
| 24 | Eksport CSV/Excel zgłoszeń, odbiorów i trasy (`/api/eksport/*.csv`) + przycisk w dashboardzie | T40, M30, M45 | M |
| 25 | `/api/docs` opisuje też nowe API (kosze, zgłoszenia, odbiory, trasa, dashboard, urządzenia) | T44 | S |
| 26 | Klastrowanie punktów na mapie dashboardu (markercluster już w vendor) | T30 | S |
| 27 | Indeksy na polach filtrów (`pickup.at`, `point.district`, `pickup.fraction`) – sprawdzić i dodać | T29 | S |
| 28 | Szacunek kosztów wdrożenia i ROI jako jawne założenia w `/metodologia` (koszt panelu/czujnika, hosting, utrzymanie vs oszczędności) | M8–9, P30 | M |
| 29 | Rynek i model biznesowy na `/metodologia` lub slajdzie: SaaS za kosz/miesiąc + wdrożenie, liczba gmin w Polsce | P24–25 | S |
| 30 | Plan pilotażu krok po kroku (dzielnica, 50 koszy, 3 miesiące, wymagania od miasta) w README/ROADMAPA | M41, P33 | S |
| 31 | ROADMAPA.md 3/6/12 miesięcy (czujniki, ML, integracje, EN/UA, rozmycie twarzy) | T45, M50, P34 | S |
| 32 | Strefa czasowa Europe/Warsaw w formatowaniu dat (JS `timeZone`) | T49 | S |
| 33 | Maskotka „wróżki” w ilustracji startu i favicon (spójna marka) | P3 | M |
| 34 | Konfiguracja dzielnic i frakcji w danych (`data/*.json`), nie w kodzie | T47, M49 | M |
| 35 | Prywatność: hosting w UE (Hetzner), retencja zgłoszeń, AI bez danych osobowych | M31–34 | S |
| 36 | Dashboard: wskaźnik „realizacja zgłoszeń w czasie ≤ 2 h” (norma MPO) dla kontroli operatora | M20 | M |
| 37 | Porównanie dzielnic: tryb „na kosz” (koszt na kosz), nie tylko suma | M47 | S |
| 38 | Kiosk: dyskretna informacja „Panel tylko do odczytu, bez danych osobowych” w stopce | M38 | S |
| 39 | Komunikat sukcesu bez obietnicy terminu + „średnio reagujemy w X h” liczone z danych | M29 | S |
| 40 | CI: uruchamianie `scripts/e2e_demo.py` w GitHub Actions (Playwright) obok pytest | T18 | M |
| 41 | Sprzątanie martwego kodu: `residents.py`/`sms.py`/`fairy.py` poza UI → ROADMAPA albo usunięcie; stare `docs/` paczki | T15 | M |
| 42 | Skan sekretów (gitleaks) i wynik w README | T31 | S |
| 43 | Ściągawka odpowiedzi na trudne pytania (stack, AI, RODO, koszty, skalowanie, konkurencja) w `DEMO.md` | T50, P43 | S |

## P2: dopracowanie i roadmapa

| # | Poprawka | Juror | Nakład |
|---|---|---|---|
| 44 | Alembic zamiast `_add_missing_columns` (migracje odtwarzalne) | T13 | M |
| 45 | Sentry/logi strukturalne | T42 | M |
| 46 | Wersja EN interfejsu mieszkańca (turyści) | M28 | L |
| 47 | Rozmycie twarzy/tablic na zdjęciach (AI) | M32 | L |
| 48 | Tryb ciemny dashboardu | P | M |
| 49 | Web Push o zmianie statusu zgłoszenia | P17 | L |
| 50 | Oznaczanie wydarzeń miejskich jako obszarów zwiększonego ruchu w UI (silnik już używa Karnetu) | M18 | M |
| 51 | Open data: zagregowane miesięczne CSV pod `/api/v1/open-data` | M36 | S |
| 52 | Runbook i backupy bazy (Coolify) | M40 | S |
| 53 | Integracja z miejskim systemem zgłoszeń (np. eksport do formatu Open311) | M30 | L |
