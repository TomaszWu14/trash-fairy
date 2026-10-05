# Graph Report - trash-fairy  (2026-10-05)

## Corpus Check
- 180 files · ~19,461,961 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2680 nodes · 7390 edges · 134 communities (128 shown, 6 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 747 edges (avg confidence: 0.73)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `59aab48a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- echarts.min.js
- T
- r
- H
- N
- wysypiska.py
- Forecast: weekly profile + event multiplier, 85% crossing, MAE
- methodology.py
- Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report
- Synthetic data: 8 weeks, OSM-driven fill rates, trolled buttons, frozen demo clock
- Trash Fairy README
- Brainstorm: przycisk dla mieszkańców, awarie, spam, wyświetlacz, program „Przyjaciele Wróżki”
- Photo analysis JSON schema (fill_level, misuse, damage, confidence)
- AI role: Vision, event parsing, 'Wrozka podpowiada' report
- test_photos.py
- test_fairy.py
- odbior
- Kontekst MPO: dane do pitchu i porównania
- Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)
- test_poprawki_jury.py
- devices.py
- film_pelny.py
- models.py
- history.py
- Audyt UX / UI / funkcjonalności – Trash Fairy (Etap 2)
- Trash Fairy – wdrożenie ekranu „Zgłoś kosz” (PWA dla mieszkańców)
- Etap 1 – rozpoznanie (bez zmian w kodzie)
- Trash Fairy – wdrożenie widoku C „Pokaz dla jury”
- te
- dashboard.py
- test_urzadzenia.py
- render
- import_points
- reset
- test_perspektywy.py
- test_forecast.py
- Trash Fairy – wyświetlacz e-papierowy na koszu (800×480)
- E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware)
- dyspozytor_api.py
- pathlib
- dashboard_api.py
- test_qr_rotacja.py
- test_ai_safety.py
- it
- llm.py
- e
- Filters
- test_dashboard.py
- _get
- fetch_osm.py
- comparison.py
- leaflet.js
- ft
- k
- jb
- traffic.py
- api_pl.py
- test_epapier.py
- Et
- weather.py
- residents.py
- Audyt UX, ekranów i API: Trash Fairy (Etap 1)
- test_wysypiska.py
- dashboard.js
- http.py
- crew_points.py
- build_all.py
- wysypiska_api.py
- record_press
- point_states
- now
- test_dashboard_jakosc.py
- test_residents.py
- test_dokumenty_jury.py
- urzadzenia.js
- test_kierowca_jury.py
- Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js
- fakes.py
- Handoff: sesja „symulacja jury + wariant A” (niedz. 4.10.2026, ok. 09:00)
- test_oszczednosci.py
- Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)
- jury_check.py
- Film 2:00: scenariusz (napisy + lektor, bez muzyki)
- ok
- conftest.py
- check_help.py
- help.js
- Wyniki po Fali 1 audytu i PWA kierowcy
- Top poprawek pod jury (z JURY-WYMAGANIA.md), w kolejności wykonania
- Take
- pytest
- create
- Routes: two fleets, runs 6:00/14:00, OR-Tools VRP
- database_url
- kierowca.js
- Wzorce do przeniesienia teraz (do 08:00)
- test_build_all.py
- test_open_api.py
- Jak poprowadzić demo w 3 minuty
- app.js
- qr_token
- Jury: przegląd przed oddaniem (runda r0)
- test_mieszkaniec_ekrany.py
- test_scenariusz.py
- osrm.py
- FastTake
- Screens: dispatcher panel, point details, virtual button, jury mode, crew view, methodology
- test_kierowca.py
- dyspozytor.js
- Voice
- _point
- rate.py
- Plan poprawek po jury r0 (4.10.2026, ok. 06:40)
- _bins
- cost_explanation
- Press
- data_version
- qr_seconds_left
- level
- FastVoice
- Materiały prezentacyjne (HackTribe)
- demo
- vision
- demo

## God Nodes (most connected - your core abstractions)
1. `T()` - 112 edges
2. `now()` - 92 edges
3. `_get()` - 87 edges
4. `e()` - 82 edges
5. `i()` - 79 edges
6. `import_points()` - 74 edges
7. `point_states()` - 70 edges
8. `a()` - 70 edges
9. `Point` - 65 edges
10. `u()` - 55 edges

## Surprising Connections (you probably didn't know these)
- `Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js` --semantically_similar_to--> `Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/KONCEPCJA.md
- `Flag 'check button' (<40% accurate in 7 days or 6 h overflow without press)` --implements--> `Reports and anti-spam rules (merge 15 min, reliability last 10, flag)`  [INFERRED]
  DECYZJE.md → docs/KONCEPCJA.md
- `test_success_screens_thank_and_lead_back()` --calls--> `qr_token()`  [EXTRACTED]
  tests/test_mieszkaniec_ekrany.py → app/api_pl.py
- `test_fixed_address_carries_token_only_for_demo_bin()` --calls--> `qr_token()`  [EXTRACTED]
  tests/test_qr_rotacja.py → app/api_pl.py
- `test_open311_filters_validation()` --calls--> `now()`  [EXTRACTED]
  tests/test_open_api.py → app/clock.py

## Import Cycles
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/reports.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/crew_points.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/rate.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/residents.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/routes.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/state.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/traffic.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/devices_api.py -> app/devices.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/dashboard_api.py -> app/state.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/dyspozytor_api.py -> app/state.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api_pl.py -> app/clock.py -> app/reports.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api_pl.py -> app/residents.py -> app/reports.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api_pl.py -> app/state.py -> app/reports.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/reports.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/cli.py -> app/simulation.py -> app/reports.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/dashboard_api.py -> app/clock.py -> app/reports.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/dashboard_api.py -> app/methodology.py -> app/reports.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/dashboard_api.py -> app/state.py -> app/reports.py -> app/__init__.py`

## Hyperedges (group relationships)
- **Forecast pipeline: weekly profile + events -> 85% crossing -> MAE** — decyzje_weekly_profile, decyzje_event_multiplier, decyzje_crossing_85_interval, decyzje_mae_evaluation, decyzje_forecast_on_demand, docs_koncepcja_forecast [INFERRED 0.95]

## Communities (134 total, 6 thin omitted)

### Community 0 - "echarts.min.js"
Cohesion: 0.01
Nodes (162): Aa(), Ab(), ac(), AS(), av(), az(), B1(), BA() (+154 more)

### Community 2 - "T"
Cohesion: 0.08
Nodes (102): open(), $a(), a0(), af(), bb(), bh(), bS(), bv() (+94 more)

### Community 3 - "r"
Cohesion: 0.05
Nodes (49): A2(), ak(), aN(), aO(), aU(), B(), bo(), bU() (+41 more)

### Community 4 - "H"
Cohesion: 0.12
Nodes (25): aR(), eU(), fw(), H(), ha(), I1(), If(), j() (+17 more)

### Community 5 - "N"
Cohesion: 0.06
Nodes (52): Ad(), aE(), B2(), dk(), ey(), Fh(), fR(), gk() (+44 more)

### Community 6 - "wysypiska.py"
Cohesion: 0.10
Nodes (34): DumpReport, Zgłoszenie dzikiego wysypiska (app/wysypiska.py): położenie jest treścią…, cleanup(), create(), crew_dump_points(), detail(), find_open(), from_nr() (+26 more)

### Community 7 - "Forecast: weekly profile + event multiplier, 85% crossing, MAE"
Cohesion: 0.18
Nodes (14): 85% crossing time with in-hour interpolation, interval from p80/p20, Panel shows system estimate, not simulation hidden truth, MAE 2.5 p.p. vs naive mean 7.3 p.p. on last week, no leakage, Report accuracy decided by emptying (>=75%); reliability = accurate share of last 10, start 70%, Report table: presses merged within 15 min of first press, Route point selection: full now, crosses 85% before next run, or safety (bin 3 d, shelter 7 d), State = max(level, 100 x report reliability), Weekly 7x24 profile per point: mean and p20/p80 (+6 more)

### Community 8 - "methodology.py"
Cohesion: 0.08
Nodes (38): compare(), Miary obu polityk na `weeks` tygodniach przed `cutoff` (pełna godzina)., assumptions(), city_scale(), dumping_rules(), money(), page_context(), _pl() (+30 more)

### Community 9 - "Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report"
Cohesion: 0.18
Nodes (11): 60 bins from Rynek/Plac Nowy, min 80 m apart, Flag 'check button' (<40% accurate in 7 days or 6 h overflow without press), Forecast computed on demand with per-clock-hour profile cache, History stored in forecast table (source='sim'), Real bin positions from OSM cached in data/*.geojson, OSM tiles instead of CARTO, Polling every 2 s with version number, Soft press limit: 1 per 2 s per point, 120/h per IP, ProxyFix (+3 more)

### Community 10 - "Synthetic data: 8 weeks, OSM-driven fill rates, trolled buttons, frozen demo clock"
Cohesion: 0.20
Nodes (10): Before/after comparison on same fill increments (4 weeks), Demo clock in DB with 24 h simulated future and +1 h advance, Fill rate from surroundings (1.5%/h + venues + stops, cap 8%/h), Simulation with fixed MPO schedule (6:00/14:00, shelters every 3 days), Bin overflow hours unchanged with fixed run times, Before/after comparison: fixed schedule vs Trash Fairy, Investment recommendations (compactor, bigger bin, shelter intervention), Synthetic data: 8 weeks, OSM-driven fill rates, trolled buttons, frozen demo clock (+2 more)

### Community 11 - "Trash Fairy README"
Cohesion: 0.20
Nodes (11): Staged work process with ROADMAPA/DECYZJE, Trash Fairy work rules (CLAUDE.md), Decision log (DECYZJE.md), Competition: Mr Fill, Wroclaw/Sierpc/Rzeszow sensors, Trash Fairy concept (KONCEPCJA.md), Hardware-agnostic brain for MPO, Out of scope list (section 16), Problem: Krakow street bins overflow on fixed MPO schedule (+3 more)

### Community 12 - "Brainstorm: przycisk dla mieszkańców, awarie, spam, wyświetlacz, program „Przyjaciele Wróżki”"
Cohesion: 0.22
Nodes (8): A. Cel i zakres, B. Fizyczny przycisk: sprzęt i awarie, Brainstorm: przycisk dla mieszkańców, awarie, spam, wyświetlacz, program „Przyjaciele Wróżki”, C. Wyświetlacz, D. Spam i nadużycia, E. Program dla mieszkańców: rejestracja, F. Nagrody i pieniądze, G. Prawo, RODO, ryzyka

### Community 13 - "Photo analysis JSON schema (fill_level, misuse, damage, confidence)"
Cohesion: 0.67
Nodes (4): Photo analysis JSON schema (fill_level, misuse, damage, confidence), Shelter -> bin rule (200 m, 48 h), Causal chain: overflowing shelter -> household bags in street bins, Stage 5: Claude Vision crew view, misuse, shelter->bin rule

### Community 14 - "AI role: Vision, event parsing, 'Wrozka podpowiada' report"
Cohesion: 0.33
Nodes (7): app/llm.py gateway (ask, ask_json), Decisions only by code rules, never AI, Events from data/events.json with crowd-scale multiplier (200m x1.3 / 400m x1.6 / 800m x2.0), AI role: Vision, event parsing, 'Wrozka podpowiada' report, 24 h plan and cut order, Events from Karnet Krakow via Claude + Nominatim, Stage 6: 'Wrozka podpowiada' report, Karnet, recommendations, jury mode

### Community 15 - "test_photos.py"
Cohesion: 0.09
Nodes (38): household_bag_links(), latest_analyses(), misuse_overview(), overflowing_shelters(), Nadużycia i powiązanie altana → kosz (koncepcja, sekcja 6.5) — reguły w kodzie.…, {point_id: (ostatnia analiza dowolna, ostatnia udana)} z okna 48 h przed `now`., {shelter_id: najwyższy szacunek} dla altan przepełnionych wg prognozy w…, [(bin, shelter)] dla worków domowych w promieniu 200 m od przepełnionej altany. (+30 more)

### Community 16 - "test_fairy.py"
Cohesion: 0.10
Nodes (35): build_facts(), generate(), is_fresh(), latest(), Raport „Wróżka podpowiada” (koncepcja, sekcja 8): fakty liczy kod, Claude tylko…, Wszystkie liczby do raportu — liczone w kodzie, nie przez model., Liczby z tekstu raportu, których nie ma w faktach (np. 16:11 → „16” i „11”…, Nowy raport albo LLMError (wtedy wywołujący pokazuje ostatni zapisany). (+27 more)

### Community 17 - "odbior"
Cohesion: 0.15
Nodes (17): crew_photo_required(), demo_reset(), odbior(), przycisk(), post, Pilotaż: odbiór tylko ze zdjęciem kosza (env REQUIRE_CREW_PHOTO=1; domyślnie…, Przywraca dane demo do stanu początkowego (jedna rola „Przegląd jury”, bez…, Przycisk na panelu kosza: naciśnięcie fizycznego przycisku = obecność przy… (+9 more)

### Community 18 - "Kontekst MPO: dane do pitchu i porównania"
Cohesion: 0.50
Nodes (3): Harmonogram oczyszczania 08/2026 (arkusz „Kosze”), Jak działa MPO (informacja ogólna MPO Kraków), Kontekst MPO: dane do pitchu i porównania

### Community 19 - "Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)"
Cohesion: 0.33
Nodes (5): Cel, Poza zakresem (ROADMAPA), Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A), Testy, Zakres (wariant A)

### Community 20 - "test_poprawki_jury.py"
Cohesion: 0.12
Nodes (30): gps_from_exif(), Reguła (nie AI): wynik analizy + typ zgłoszenia → status weryfikacji. Nigdy nie…, (lat, lon) z EXIF zdjęcia albo None. Telefon z włączoną lokalizacją w aparacie…, verification(), demo(), lonely_ok_bin(), pa(), fixture (+22 more)

### Community 21 - "devices.py"
Cohesion: 0.11
Nodes (27): _choice(), device_list(), battery_level(), counts_by_kind(), days_left(), detail(), districts(), _item() (+19 more)

### Community 22 - "film_pelny.py"
Cohesion: 0.16
Nodes (28): build_film(), card(), cut(), demo_photo(), duration(), ffmpeg(), fit(), log() (+20 more)

### Community 23 - "models.py"
Cohesion: 0.09
Nodes (41): Zegar demo: zamrożona sobota 13:30, przewijany o godzinę. Przewinięcie…, _retention(), _api_error(), errorhandler, API urządzeń na koszach (/api/urzadzenia). Reguły i założenia: app/devices.py.…, Stan wyświetlacza e-papierowego na koszu (docs/epapier/HANDOFF.md): wyzwalacze,…, Wydarzenia i mnożnik tłumu (koncepcja, sekcje 6.3–6.4). Etap 3: ręczna lista…, Device (+33 more)

### Community 24 - "history.py"
Cohesion: 0.14
Nodes (22): _city_point(), _education(), fraction_factor(), generate_history(), lever_since(), _live_point(), mass_kg(), _Out (+14 more)

### Community 25 - "Audyt UX / UI / funkcjonalności – Trash Fairy (Etap 2)"
Cohesion: 0.12
Nodes (15): A. Funkcjonalność i błędy, Audyt UX / UI / funkcjonalności – Trash Fairy (Etap 2), B. Hierarchia informacji i architektura, C. Mapa, D. Wygląd (UI), E. Responsywność, F. PWA (kierowca i zgłaszający), G. Stany i informacja zwrotna (+7 more)

### Community 26 - "Trash Fairy – wdrożenie ekranu „Zgłoś kosz” (PWA dla mieszkańców)"
Cohesion: 0.15
Nodes (12): Dostępność i ton, Kontrakt API (propozycja – dopasuj do istniejącego backendu), Kryteria odbioru, Mini-mapa, Przepływ i stany, Przyciski zgłoszenia (kolor + kształt + znak + słowo), PWA, Stany brzegowe (+4 more)

### Community 27 - "Etap 1 – rozpoznanie (bez zmian w kodzie)"
Cohesion: 0.29
Nodes (6): 1. Stos, 2. Mapa ekranów i przepływów, 3. Zrzuty ekranu, 4. Stany pojemnika w danych i w UI, 5. Nazewnictwo (do ujednolicenia), Etap 1 – rozpoznanie (bez zmian w kodzie)

### Community 28 - "Trash Fairy – wdrożenie widoku C „Pokaz dla jury”"
Cohesion: 0.22
Nodes (8): Dane (bez zmian logiki), Kryteria odbioru, Mapa – Leaflet, Tokeny, Trash Fairy – wdrożenie widoku C „Pokaz dla jury”, Układ (1440 px laptop, 1920×1080 projektor), Zachowanie kroków, Zawartość paczki

### Community 29 - "te"
Cohesion: 0.08
Nodes (34): al(), bE(), bF(), ca(), Cv(), dL(), dv(), fO() (+26 more)

### Community 30 - "dashboard.py"
Cohesion: 0.12
Nodes (33): accuracy(), _anomaly_col(), _anomalie(), _frakcje(), _heatmapa(), _mapa(), _by(), by_district() (+25 more)

### Community 31 - "test_urzadzenia.py"
Cohesion: 0.08
Nodes (30): cleanup_photos_command(), karnet_command(), Import punktów z data/*.geojson i wydarzeń z data/events.json, symulacja…, Początek okna symulacji w istniejącej bazie (historia punktów demo kończy się…, Usuwa pliki zdjęć starszych niż 7 dni (wyniki analiz zostają w bazie). Do crona., Pobiera wydarzenia z Karnet Kraków do data/karnet.json, importuje je i odtwarza…, seed_command(), _sim_start() (+22 more)

### Community 32 - "render"
Cohesion: 0.06
Nodes (44): Masterdane dla wszystkich urządzeń (deterministycznie). Wymaga Device…, seed_demo(), _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3… (+36 more)

### Community 33 - "import_points"
Cohesion: 0.09
Nodes (36): distance_m(), Odległość w linii prostej (haversine), w metrach., address_of(), bin_rate(), city_rate(), district_of(), fractions(), import_city_points() (+28 more)

### Community 34 - "reset"
Cohesion: 0.09
Nodes (26): advance(), _locked_reset(), maybe_auto_reset(), Reset ręczny: False, gdy reset już trwa (w tym procesie albo w innym workerze)., Auto-reset w tle: widz nie czeka ~13 s (PostgreSQL) na stronę. Jeden naraz na…, Odtwarza symulację od zera i cofa zegar do startu scenariusza (kasuje…, Reset demo, gdy od ostatniej akcji minęło IDLE. Warunkowy UPDATE: przy kilku…, reset() pod blokadą bazy (PostgreSQL): False, gdy inny worker właśnie resetuje.… (+18 more)

### Community 35 - "test_perspektywy.py"
Cohesion: 0.12
Nodes (19): _env_float(), pilot_roi(), Koszt pilotażu i zwrot wg jawnych założeń (env, do weryfikacji w pilotażu).…, _bin(), parametrize, Nowe UI „Przegląd jury”: cztery perspektywy na wspólnym API (audit/AUDYT-…, Zegar demo stoi: wszystkie akcje mają tę samą minutę. Drugie zgłoszenie po…, _report() (+11 more)

### Community 36 - "test_forecast.py"
Cohesion: 0.09
Nodes (42): events_near(), multiplier(), Mnożnik najsilniejszego wydarzenia w promieniu, aktywnego w godzinie `at` albo…, build_profiles(), _cell(), first_crossing(), forecast_quality(), point_forecasts() (+34 more)

### Community 37 - "Trash Fairy – wyświetlacz e-papierowy na koszu (800×480)"
Cohesion: 0.22
Nodes (8): Dane wejściowe renderera, Etap 1 – symulator do pokazu (zalecany na hackathon), Etap 2 – prawdziwe urządzenie (kontrakt, bez implementacji firmware), Kryteria odbioru, Siatka (px, stałe – nie zmieniać między stanami), Stany i wyzwalacze, Trash Fairy – wyświetlacz e-papierowy na koszu (800×480), Zawartość paczki

### Community 38 - "E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware)"
Cohesion: 0.29
Nodes (6): Co jeszcze przed pilotażem, Dlaczego urządzenie renderuje samo, Downlink (port 10, ≤ 12 B), E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware), QR na urządzeniu, Uplink

### Community 39 - "dyspozytor_api.py"
Cohesion: 0.11
Nodes (28): _address(), _done_ids(), _json_body(), Kosze opróżnione przez kierowcę od resetu demo (postęp trasy)., Ciało JSON jako słownik; tablica, liczba albo zły JSON → {} (walidacja pól…, add(), added_view(), _change() (+20 more)

### Community 40 - "pathlib"
Cohesion: 0.10
Nodes (16): json, pathlib, axe-core (WCAG 2.1 A/AA) na kluczowych ekranach; wynik do…, Buduje app/static/ui/icons.svg: podzbiór ikon Lucide (ISC) używanych w UI.…, Pętla jakości: przepływ kierowcy (lista → karta kosza → Jadę z nawigacją →…, Pętla jakości: przepływ mieszkańca na telefonie (390×844), zrzuty każdego kroku…, Pętla jakości: zrzuty ekranu w kolejnych rundach do audit/iteracje/ (1920×1080,…, opt() (+8 more)

### Community 41 - "dashboard_api.py"
Cohesion: 0.09
Nodes (46): anomaly_pct(), _api_error(), _before_rollout(), _change(), districts(), _dzielnice(), _jakosc(), _koszty() (+38 more)

### Community 42 - "test_qr_rotacja.py"
Cohesion: 0.14
Nodes (16): device_token(), Token urządzenia (nagłówek X-Token-Urzadzenia): HMAC numeru seryjnego, wgrywany…, demo(), fixture, Dzienny kod QR kosza (token zmienia się o północy w Krakowie), przycisk na…, Podmieniony zegar ścienny modułu api_pl (qr_token/qr_valid); zegar demo i…, _report(), test_fixed_address_carries_token_only_for_demo_bin() (+8 more)

### Community 43 - "test_ai_safety.py"
Cohesion: 0.07
Nodes (41): default_details(), details(), fetch(), _first(), import_events(), in_demo(), parse_list(), Wydarzenia z Karnet Kraków (koncepcja, sekcja 6.4). Publicznego API brak —… (+33 more)

### Community 44 - "it"
Cohesion: 0.08
Nodes (26): At(), cI(), dB(), dp(), dT(), e0(), Fb(), fi() (+18 more)

### Community 45 - "llm.py"
Cohesion: 0.13
Nodes (21): ask(), ask_json(), available(), _create(), image_block(), LLMError, model(), Exception (+13 more)

### Community 46 - "e"
Cohesion: 0.07
Nodes (40): b0(), bG(), bn(), Bp(), by(), Ch(), Ck(), cS() (+32 more)

### Community 47 - "Filters"
Cohesion: 0.10
Nodes (26): ApiError, _cached_json(), chart(), _date(), export_csv(), parse_filters(), _project(), _project_trend() (+18 more)

### Community 48 - "test_dashboard.py"
Cohesion: 0.08
Nodes (32): effect_label(), project_effect(), project_windows(), Etykieta efektu projektu, np. „−13,2% odbiorów”. Panel liczy ją z wartości przy…, (przed, po): „po” = od startu do końca (najdalej do teraz), „przed” = tyle samo…, (wartość zmiany, etykieta) z historii dzielnicy przed i po starcie projektu., _history_fingerprint(), _kpi() (+24 more)

### Community 49 - "_get"
Cohesion: 0.09
Nodes (27): dashboard(), devices_page(), dispatcher(), driver(), Mieszkaniec: skan kodu QR z panelu i „Twoje zgłoszenia”. Bez mapy i listy…, Status zgłoszenia jako oś czasu (dane z /api/zgloszenia/<nr>, odświeżane co…, Kierowca: mapa trasy i kosze po priorytecie (dane z /api/trasa, odświeżane przy…, Dyspozytor: mapa koszy na żywo, pilne kosze, ekipy i trasy, zgłoszenia na żywo… (+19 more)

### Community 50 - "fetch_osm.py"
Cohesion: 0.29
Nodes (11): classify(), fetch_city(), main(), nearest_streets(), overpass(), Pobiera punkty z OSM (Overpass API) dla obszaru demo i zapisuje cache do…, Kosze i pojemniki do selektywnej zbiórki w 6 dzielnicach →…, Kolejność z hasha osm_id (rozrzut po całej dzielnicy, deterministycznie),… (+3 more)

### Community 51 - "comparison.py"
Cohesion: 0.09
Nodes (35): fixed_selects(), following_run(), is_run(), Porównanie „przed i po” (koncepcja, sekcja 6.7): stały harmonogram MPO kontra…, Zwraca miary jednej polityki. `incs[pid][i]` = prawdziwy przyrost w godzinie…, run_policy(), plan_routes(), coords[0] = baza, demands[i] = litry do zabrania z punktu i (demands[0] = 0).… (+27 more)

### Community 52 - "leaflet.js"
Cohesion: 0.05
Nodes (34): Ae(), at(), be(), bi(), Ci(), De(), ei(), fe() (+26 more)

### Community 53 - "ft"
Cohesion: 0.10
Nodes (29): aw(), dc(), dw(), ew(), Fl(), ft(), gm(), gV() (+21 more)

### Community 54 - "k"
Cohesion: 0.06
Nodes (33): ai(), Bd(), br(), cb(), ce(), Cf(), d0(), dF() (+25 more)

### Community 55 - "jb"
Cohesion: 0.11
Nodes (19): Di(), FD(), FG(), fn(), Gg(), HC(), HD(), Hh() (+11 more)

### Community 56 - "traffic.py"
Cohesion: 0.17
Nodes (22): city_ratio(), conditions(), data(), delay_min(), drive_min(), fresh_samples(), _load_cache(), ratio() (+14 more)

### Community 57 - "api_pl.py"
Cohesion: 0.08
Nodes (42): _ai(), _ai_ok(), _crew_photo(), crew_photo_status(), _dowod(), _jade_at(), kosz_json(), _last_emptying() (+34 more)

### Community 58 - "test_epapier.py"
Cohesion: 0.15
Nodes (23): device_info(), display_state(), keys(), plural_people(), state_key zmienia się tylko przy pełnym odświeżeniu, values_key przy zmianie…, Dane urządzenia do renderera; `qr` = dzienny token kosza (kod „zgłoś” na…, (state, data) dla renderera. `states`/`routes` można podać z zewnątrz, żeby nie…, _when() (+15 more)

### Community 59 - "Et"
Cohesion: 0.27
Nodes (10): $C(), EA(), Et(), $g(), jf(), oy(), ry(), up() (+2 more)

### Community 60 - "weather.py"
Cohesion: 0.17
Nodes (19): conditions(), data(), factor(), factor_at(), _fetch(), _load_cache(), Pogoda z Open-Meteo (bez klucza) jako mnożnik tempa zapełniania w prognozie.…, {"fetched_at", "hours": {"2026-10-03T13:00": {"temp", "rain", "code"}}} albo… (+11 more)

### Community 61 - "residents.py"
Cohesion: 0.11
Nodes (28): PointAward, Uczestnik programu „Przyjaciele Wróżki”. Bez danych osobowych: pseudonim + hash…, Punkty za trafne zgłoszenie (jedna nagroda na mieszkańca, punkt i dzień)., Resident, award(), demo_resident(), devices_overview(), mark_verified() (+20 more)

### Community 62 - "Audyt UX, ekranów i API: Trash Fairy (Etap 1)"
Cohesion: 0.12
Nodes (15): 1. Inwentaryzacja, 2. Ocena ekranów, 3. Nawigacja: dziś i docelowo, 4. Docelowa struktura ekranów, 5. Docelowe API, 6. Kierunek wizualny, 7. Decyzje do akceptacji przed Etapem 2, 8. Plan wdrożenia (do zamrożenia kodu w niedzielę o 19:00) (+7 more)

### Community 63 - "test_wysypiska.py"
Cohesion: 0.14
Nodes (26): Reset scenariusza: wysypiska z poprzedniego pokazu znikają razem z plikami…, reset_demo(), png(), points(), parametrize, Dzikie wysypiska (POST/GET /api/wysypiska) i punkty mieszkanki demo…, send(), test_ai_error_or_missing_key_means_do_weryfikacji_never_500() (+18 more)

### Community 64 - "dashboard.js"
Cohesion: 0.17
Nodes (10): apply(), load(), loadProjects(), rDzielnice(), renderKpis(), rKoszty(), rNaprawy(), rProjekty() (+2 more)

### Community 65 - "http.py"
Cohesion: 0.13
Nodes (26): config(), get_json(), post_form(), Wspólny klient HTTP integracji (Open-Meteo, TomTom, Twilio): urllib ze stdlib,…, Ustawienie integracji: najpierw config aplikacji (testy je zerują), potem…, (status, json). Błąd HTTP z treścią JSON (np. Twilio 400/429) zwracamy jako…, _send(), _auth() (+18 more)

### Community 66 - "crew_points.py"
Cohesion: 0.16
Nodes (23): crew_points(), need_bin_suggestions(), Punkty zaangażowania ekipy — reguła w kodzie za potwierdzone sygnały, nie za…, Sugestie kierowców „Tu przydałby się kosz” z ostatnich WINDOW_DAYS, każda z…, Punkty ekipy trasy ROUTE z ostatnich WINDOW_DAYS: suma i pozycje (każda z…, shows_dumping(), _counts(), dumping_sites() (+15 more)

### Community 67 - "build_all.py"
Cohesion: 0.14
Nodes (22): app_shots(), b64(), build_pdf(), cells(), doc(), fetch(), grab(), ic() (+14 more)

### Community 68 - "wysypiska_api.py"
Cohesion: 0.13
Nodes (21): blad(), dojazd(), kosze(), meta(), Kosze operacyjne z poziomem; ?blisko=lat,lon sortuje po odległości i dodaje…, Przebieg po ulicach z punktu (od=lat,lon) do kosza (do=id): nawigacja…, cleared(), detail() (+13 more)

### Community 69 - "record_press"
Cohesion: 0.13
Nodes (27): low_reliability(), point_reliability(), Odsetek trafnych wśród ostatnich 10 rozstrzygniętych zgłoszeń (outcomes: od…, Flaga „sprawdź przycisk”: < 40% trafnych wśród zgłoszeń z 7 dni (min. 3…, Zapisuje naciśnięcie i dolicza je do otwartego zgłoszenia z ostatnich 15 min…, record_press(), reliability(), level_state() (+19 more)

### Community 70 - "point_states"
Cohesion: 0.14
Nodes (20): device_flags(), {point_id: powód} dla urządzeń bez sygnału od 48 h., neighbors_map(), non_fill_reports(), point_states(), {point_id: dict ze stanem} dla chwili `now` zegara demo (z cache po wersji…, Id zgłoszeń wyłącznie „uszkodzony” / „inne”: zostają zgłoszeniami (numer,…, {point_id: dict ze stanem} dla chwili `now` zegara demo. (+12 more)

### Community 71 - "now"
Cohesion: 0.14
Nodes (25): after_request, numer(), now(), device_detail(), bad_param(), BadParam, _bin(), bin_detail() (+17 more)

### Community 72 - "test_dashboard_jakosc.py"
Cohesion: 0.18
Nodes (19): Sumy odbiorów i zgłoszeń w przedziale filtrów., Otwarte zgłoszenia „Uszkodzony” (Press.kind = damaged, zgłoszenie…, repair_queue(), totals(), far_m(), Zgłoszenie historyczne (syntetyczne). Zgłoszenia na żywo to Report — panel…, ReportHistory, _hist() (+11 more)

### Community 73 - "test_residents.py"
Cohesion: 0.18
Nodes (20): Opróżnienie rozstrzyga otwarte zgłoszenia punktu: poziom >= 75% → trafne,…, resolve_reports(), Autotest wyświetlacza i przycisku: aktualizuje urządzenie, NIE tworzy…, selftest(), effective_weight(), Czy ten przycisk ma ≥3 fałszywe zgłoszenia o tej samej godzinie (±1 h) w…, Waga zgłoszenia po regułach antyspamowych (potwierdzone przez mieszkańca nie są…, troll_pattern() (+12 more)

### Community 74 - "test_dokumenty_jury.py"
Cohesion: 0.11
Nodes (9): demo(), fixture, parametrize, Strony dokumentów po poprawkach jury: koszt odbioru z jawnych składników,…, Zdjęcie odbioru o przykładowym id nie istnieje (404), więc przy nim jest tylko…, test_api_docs_no_open_link_to_example_photo(), test_documents_follow_decision_1(), test_documents_styles_only_in_doc_css() (+1 more)

### Community 75 - "urzadzenia.js"
Cohesion: 0.52
Nodes (6): apply(), fillDistricts(), load(), renderChips(), renderKpis(), renderList()

### Community 76 - "test_kierowca_jury.py"
Cohesion: 0.25
Nodes (18): first_stop(), jpeg(), oproznij(), Dowód wykonania usługi: zdjęcie kosza przy „Opróżniono”, flaga pilotażu,…, Zgłoszenia z seeda/symulacji nie mają wierszy Press: karta kosza nie może mówić…, Atrapa Claude Vision dla zdjęcia ekipy (schemat photos.SCHEMA)., Zgłoszenie z konta demo „Anna K.” (jak formularz mieszkańca z konto=demo)., test_bad_photo_is_rejected_before_emptying() (+10 more)

### Community 77 - "Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js"
Cohesion: 0.33
Nodes (6): Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js, Style: Planty green + gold panel, magic violet/pink for AI and button, Map visual encoding: shape=type, colour+symbol=state (WCAG), Flask 3.1.3, Flask-SQLAlchemy 3.1.1, gunicorn 26.2.0

### Community 78 - "fakes.py"
Cohesion: 0.28
Nodes (5): FakeOpener, Fałszywy opener dla app/http.py: odpowiedzi po fragmencie adresu, zapis…, routes: {fragment_adresu: (status, body) | Exception | callable(req) ->…, _Resp, urllib_error

### Community 79 - "Handoff: sesja „symulacja jury + wariant A” (niedz. 4.10.2026, ok. 09:00)"
Cohesion: 0.18
Nodes (10): (archiwum) W toku (workflow Etap 2b, run wf_0b1b6482-9dc), Do zrobienia po Etapie 2b, Grabie z tej sesji, Handoff: sesja „symulacja jury + wariant A” (niedz. 4.10.2026, ok. 09:00), Handoff: stan 5.10.2026 ok. 10:40 (NAJNOWSZY), Materiały prezentacyjne (zatwierdzone przez autora, robić PO zmianach w aplikacji), Stan 4.10 ok. 09:40 (sesja 336aa886), Stan 4.10 ok. 10:30 — RESTART SESJI (po to, by załadować łącznik „claude.ai ElevenLabs”) (+2 more)

### Community 80 - "test_oszczednosci.py"
Cohesion: 0.18
Nodes (13): cost_pln(), Koszt odbioru wg założeń `a` = methodology.money_assumptions(). Też dla wyrażeń…, money_assumptions(), Pickup, Odbiór historyczny (syntetyczny, app/history.py). Odbiory na żywo to Emptying —…, data(), _pickup(), _point() (+5 more)

### Community 81 - "Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)"
Cohesion: 0.25
Nodes (7): 1. Uprawnienia, 2. Ekrany i nawigacja, 3. Wygląd, 4. Widoki i stany, 5. Zależności i infrastruktura, 6. Produkt i pokaz, Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)

### Community 82 - "jury_check.py"
Cohesion: 0.18
Nodes (11): project(), Szczegóły projektu z wykresami przed i po (dane z /api/projekty/<slug>)., Flow, flows(), off_token(), probe(), Symulacja jury (audit/JURY.md): zrzuty i metryki każdego ekranu + budżety…, Jedna ścieżka jury w nowej sesji: liczy kliknięcia od strony startowej. (+3 more)

### Community 83 - "Film 2:00: scenariusz (napisy + lektor, bez muzyki)"
Cohesion: 0.50
Nodes (3): Film 2:00: scenariusz (napisy + lektor, bez muzyki), Liczby w filmie, Przebieg

### Community 84 - "ok"
Cohesion: 0.23
Nodes (9): ok(), FullTake, Napis + lektor, potem chwila ciszy; dopiero wtedy kolejna akcja (najpierw…, Kursor płynnie dojeżdża do elementu (ok. 0,7 s), kliknięcie z kółkiem, chwila…, Krok scenariusza przyciskiem „Dalej” z paska aplikacji; ładowanie nowej strony…, Szare szkielety ładowania (.skel) znikają, zanim kadr trafi do filmu., scenario_a(), scenario_b() (+1 more)

### Community 85 - "conftest.py"
Cohesion: 0.24
Nodes (10): clear_cache(), clear_cache(), Profile zależą od zawartości bazy — czyścimy po każdej nowej symulacji lub…, random, app(), cache(), client(), fixture (+2 more)

### Community 86 - "check_help.py"
Cohesion: 0.18
Nodes (10): bad_entry(), human_entry_errors(), load(), main(), Strażnik trybu „Podpowiedzi” (app/static/ui/help.js + podpowiedzi.json) na…, Serwer dev przeładowuje się po każdej zmianie pliku: kilka prób zamiast…, (7) Człowiek (webdriver=false) przy pierwszej wizycie: powitanie samo na /, a…, welcome_errors() (+2 more)

### Community 87 - "help.js"
Cohesion: 0.32
Nodes (13): apply(), closeTip(), endTour(), inject(), maybeOffer(), openTip(), place(), reflow() (+5 more)

### Community 88 - "Wyniki po Fali 1 audytu i PWA kierowcy"
Cohesion: 0.40
Nodes (4): Lighthouse (lokalnie, Chromium headless, Lighthouse 13.5), Poziomy scroll, Pozycje audytu, Wyniki po Fali 1 audytu i PWA kierowcy

### Community 89 - "Top poprawek pod jury (z JURY-WYMAGANIA.md), w kolejności wykonania"
Cohesion: 0.40
Nodes (4): P0: przed zamrożeniem kodu (największy wpływ, mały nakład), P1: mocne wzmocnienia (jeśli zostanie czas przed 19:00), P2: dopracowanie i roadmapa, Top poprawek pod jury (z JURY-WYMAGANIA.md), w kolejności wykonania

### Community 90 - "Take"
Cohesion: 0.30
Nodes (7): optional(), Jedna strona nagrywana do webm + odcinki, które zostają w filmie (ładowanie…, Czekanie bez obrazu (np. dojazd nawigacji, analiza zdjęcia) — wycinamy z filmu., Napis na ekranie; `spoken` = tekst lektora, gdy różni się od napisu (np. bez…, scenario_1(), scenario_2(), Take

### Community 91 - "pytest"
Cohesion: 0.14
Nodes (6): pytest, parametrize, Treści trybu „Podpowiedzi” (app/static/ui/podpowiedzi.json) i wejścia do…, Obszar dotyku ikonki „i” to ::before z inset −12 px: przy position: static…, test_help_icon_never_static(), test_selektory_powitania_istnieja_w_szablonach()

### Community 92 - "create"
Cohesion: 0.15
Nodes (13): ai_status(), analyze(), analyze_in_background(), _coord(), create(), post, Pola (multipart albo JSON): lat, lon, rodzaj (wiele), ilosc (1–100, brak = „nie…, client_hash() (+5 more)

### Community 93 - "Routes: two fleets, runs 6:00/14:00, OR-Tools VRP"
Cohesion: 0.67
Nodes (4): OR-Tools VRP, 1 vehicle per fleet, depot MPO Nowohucka 1, straight line x1.3, Routes: two fleets, runs 6:00/14:00, OR-Tools VRP, ortools 9.15, OSRM, multiple vehicles per fleet, time windows

### Community 95 - "database_url"
Cohesion: 0.60
Nodes (4): database_url(), DATABASE_URL z env; Coolify/Heroku podają postgres(ql)://, a my używamy…, test_database_url_defaults_to_sqlite(), test_database_url_uses_psycopg3_for_postgres()

### Community 97 - "Wzorce do przeniesienia teraz (do 08:00)"
Cohesion: 0.15
Nodes (12): 1. Prezentacja: 10 slajdów ułożonych według kryteriów (BLOKUJE, nakład M), 2. Telefon: nic nie znika bez słowa (ODBIERA PUNKTY, nakład S), 3. Ekran kierowcy: adres się zawija, nie ucina (ODBIERA PUNKTY, nakład S), 4. Jeden łańcuch kwot: „Skąd te kwoty” (ODBIERA PUNKTY, nakład S–M, razem z pracą nad KPI oszczędności), 5. Dostępność z liczbami (KOSMETYKA, nakład S), 6. README jako drzwi wejściowe (KOSMETYKA, nakład S), 7. Teksty zgodne z decyzją 1 poza plikami drugiego agenta (ODBIERA PUNKTY, nakład S), 8. Mikrokopia z HugMe dla plików drugiego agenta (KOSMETYKA, nakład S, przekazać) (+4 more)

### Community 98 - "test_build_all.py"
Cohesion: 0.20
Nodes (11): lektor_texts(), on_cut(), Teksty lektora w kolejności filmu: plansze, potem take.say w scenariuszach…, Czas t surowego nagrania → czas w filmie po wycięciu (zostają odcinki keep) i…, Strażnik osi czasu lektora: napis z surowego nagrania musi trafić w to samo…, Każdy klucz lektora użyty w pełnym filmie ma tekst, każdy tekst jest użyty i…, Każda kwestia filmu 3-minutowego („p:klucz” albo „k:NN”) ma plik nagrania., test_film_3min_ma_wszystkie_nagrania() (+3 more)

### Community 99 - "test_open_api.py"
Cohesion: 0.20
Nodes (6): demo(), fixture, _report(), test_open311_filters_validation(), test_open311_maps_status_and_service_code(), test_open_data_csv_has_bom_source_and_no_personal_fields()

### Community 104 - "qr_token"
Cohesion: 0.22
Nodes (11): qr_token(), qr_valid(), Token z kodu QR na panelu kosza, inny każdego dnia (doba w Krakowie): bez niego…, Kod z dziś albo, przez pierwszą godzinę po północy, z wczoraj. Porównanie…, app_context_processor, ui_context(), test_simulated_scan_offers_bins_with_panel_and_todays_token(), test_qr_on_bin_and_jury_link_carry_scan_token() (+3 more)

### Community 105 - "Jury: przegląd przed oddaniem (runda r0)"
Cohesion: 0.18
Nodes (10): BLOKUJE, Budżet kliknięć, Jury: przegląd przed oddaniem (runda r0), KOSMETYKA, Oceny wstępne, ODBIERA PUNKTY, Odrzucone przez sceptyka, Przegląd wizualny (+2 more)

### Community 106 - "test_mieszkaniec_ekrany.py"
Cohesion: 0.18
Nodes (4): demo(), fixture, Ekrany mieszkańca po uwagach jury (J-32, J-55, decyzja a): treści i kolejność,…, test_success_screens_thank_and_lead_back()

### Community 107 - "test_scenariusz.py"
Cohesion: 0.18
Nodes (8): demo(), fixture, Scenariusz demo w trzech wariantach (app.js: okienko losowania, TF.SCENARIOS):…, Okienko losuje kosz A/B tylko z losuj=True (ui.scenario_bins): po…, app.js TF.SCENARIOS: po wysłaniu zgłoszenia (A, B) i po statusie wysypiska (C)…, test_dispatcher_step_follows_report_in_every_variant(), test_drawn_bins_always_land_on_driver_route(), test_places_for_variant_c_are_real_krakow_points()

### Community 108 - "osrm.py"
Cohesion: 0.29
Nodes (7): _fetch(), _load(), Przebieg tras po ulicach z OSRM, tylko do rysowania na mapie. Kilometry nadal…, coords: lista [lat, lon]. Zwraca (punkty linii [lat, lon], approx)., street_path(), test_no_network_falls_back_to_straight_line(), test_street_path_cached_after_first_fetch()

### Community 109 - "FastTake"
Cohesion: 0.47
Nodes (4): FastTake, Lektor mówi, a w tym czasie kursor już klika. Przed przejściem na inną stronę i…, scenario_a(), scenario_c()

### Community 114 - "test_kierowca.py"
Cohesion: 0.29
Nodes (7): demo(), odbior(), fixture, test_far_emptying_is_saved_with_flag_and_counts_as_progress(), test_reset_clears_stop_issues(), test_stop_issue_flags_point_until_emptying(), test_stop_issue_rejects_bad_input()

### Community 115 - "dyspozytor.js"
Cohesion: 0.42
Nodes (8): feed(), load(), renderFeed(), renderFleets(), renderKpis(), renderMap(), renderUrgent(), urgentItem()

### Community 116 - "Voice"
Cohesion: 0.25
Nodes (6): env(), FileVoice, Zmienna środowiska albo wpis z .env w repo (wartości nigdy nie wypisujemy)., Lektor: tekst → mp3 z ElevenLabs (eleven_multilingual_v2), z pamięcią po…, Lektor z plików demo/lektor (teksty.json); brak nagrania = napis bez głosu i…, Voice

### Community 117 - "_point"
Cohesion: 0.25
Nodes (8): kosz(), _point(), driver_bin(), kiosk(), Panel kosza (kiosk 1280×800): kod QR z dziennym tokenem tego kosza i przyciski…, Zgłoszenie na jednym ekranie: problem → Wyślij. ?qr=<token> z kodu na panelu…, Karta kosza: zgłoszenia, „Jadę” z nawigacją w aplikacji, „Opróżniono”,…, report()

### Community 118 - "rate.py"
Cohesion: 0.36
Nodes (7): Counter, Liczniki limitów (SMS, AI, logowanie) wspólne dla wszystkich workerów…, count(), hit(), Limity wspólne dla wszystkich workerów: liczniki w bazie (tabela Counter), okno…, Liczy zdarzenie i zwraca True, gdy mieści się w limicie; przy przekroczeniu nic…, _window()

### Community 119 - "Plan poprawek po jury r0 (4.10.2026, ok. 06:40)"
Cohesion: 0.25
Nodes (7): 1. BLOKUJE, 2. ODBIERA PUNKTY (od najlepszego stosunku zysku do nakładu), 3. KOSMETYKA (tylko S), 4. Pakiety (rozłączne pliki), 5. ROADMAPA (po hackathonie, nie robimy teraz), Plan poprawek po jury r0 (4.10.2026, ok. 06:40), Zaplanowane wcześniej (decyzje autora)

### Community 120 - "_bins"
Cohesion: 0.32
Nodes (8): _bins(), Decyzja dyspozytora to nie zgłoszenie: bez nowych Report/Press, ta sama lista…, Kosz uliczny spoza trasy (najciekawszy przypadek), a gdy reguły wzięły…, _target(), test_add_puts_bin_first_on_route_and_is_idempotent(), test_dispatcher_does_not_touch_resident_statistics(), test_overview_numbers_come_from_engine(), test_undo_and_emptying_close_the_decision()

### Community 121 - "cost_explanation"
Cohesion: 0.29
Nodes (7): cost_explanation(), cost_parts(), _moved(), _pct_change(), Koszt odbiorów z sum `t` rozbity na składniki history.cost_pln: wizyty przy…, Zmiana w % słowem, bez znaku: „spadł o 6%”, „wzrósł o 2,1%”., Czemu koszt nie spada razem z liczbą odbiorów (sumy `totals` przed i po starcie…

### Community 122 - "Press"
Cohesion: 0.33
Nodes (5): Press, Pojedyncze naciśnięcie przycisku. Scalanie w zgłoszenia: app/reports.py., demo(), fixture, test_old_ips_are_forgotten()

### Community 123 - "data_version"
Cohesion: 0.33
Nodes (6): Wersja danych do pollingu wszystkich perspektyw (co 3 s): zmienia się po…, zmiany(), data_version(), _engine_version(), Zmienia się przy każdej zmianie danych, od której zależy stan: zgłoszenie,…, Klucz cache silnika: wersja danych + pogoda. Pogoda (prognoza godzin…

### Community 124 - "qr_seconds_left"
Cohesion: 0.40
Nodes (5): _local(), qr_seconds_left(), Zegar ŚCIENNY w Krakowie, nie zegar demo: kod QR to zabezpieczenie, nie może…, Sekundy do najbliższej północy w Krakowie (panel przeładowuje się wtedy z nowym…, test_token_changes_at_midnight_in_krakow()

### Community 125 - "level"
Cohesion: 0.50
Nodes (4): level(), Poziom drabinki z liczby sygnałów i liczby sygnałów w najczęstszym dniu…, parametrize, test_ladder_thresholds()

### Community 127 - "Materiały prezentacyjne (HackTribe)"
Cohesion: 0.50
Nodes (3): Film 3 min (do wysyłki), Materiały prezentacyjne (HackTribe), Pełny film (6–8 min, spokojne tempo)

### Community 128 - "demo"
Cohesion: 0.50
Nodes (4): demo(), fixture, Atrapa Claude: ustaw wynik albo wyjątek LLMError., vision()

### Community 129 - "vision"
Cohesion: 0.50
Nodes (4): no_limits(), fixture, Atrapa Claude: wynik opisu zdjęcia albo wyjątek LLMError., vision()

## Ambiguous Edges - Review These
- `psycopg[binary] 3.3.6` → `Real bin positions from OSM cached in data/*.geojson`  [AMBIGUOUS]
  DECYZJE.md · relation: conceptually_related_to

## Knowledge Gaps
- **137 isolated node(s):** `Ściągawka: trudne pytania`, `Handoff: stan 5.10.2026 ok. 10:40 (NAJNOWSZY)`, `Zrobione`, `Stan 4.10 ok. 11:00 — KONIEC (autor: „kończ co się da”)`, `Stan 4.10 ok. 10:30 — RESTART SESJI (po to, by załadować łącznik „claude.ai ElevenLabs”)` (+132 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `psycopg[binary] 3.3.6` and `Real bin positions from OSM cached in data/*.geojson`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Point` connect `models.py` to `methodology.py`, `test_photos.py`, `test_fairy.py`, `test_poprawki_jury.py`, `devices.py`, `history.py`, `dashboard.py`, `import_points`, `test_perspektywy.py`, `test_forecast.py`, `dyspozytor_api.py`, `pathlib`, `dashboard_api.py`, `test_qr_rotacja.py`, `test_ai_safety.py`, `Filters`, `test_dashboard.py`, `_get`, `comparison.py`, `api_pl.py`, `test_epapier.py`, `residents.py`, `test_wysypiska.py`, `crew_points.py`, `record_press`, `point_states`, `now`, `test_dashboard_jakosc.py`, `test_residents.py`, `test_oszczednosci.py`, `test_open_api.py`, `test_kierowca.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `import_points()` connect `import_points` to `demo`, `demo`, `methodology.py`, `test_photos.py`, `test_fairy.py`, `test_poprawki_jury.py`, `models.py`, `test_urzadzenia.py`, `reset`, `test_perspektywy.py`, `test_forecast.py`, `test_qr_rotacja.py`, `test_ai_safety.py`, `test_dashboard.py`, `comparison.py`, `traffic.py`, `test_epapier.py`, `test_wysypiska.py`, `point_states`, `test_residents.py`, `test_dokumenty_jury.py`, `test_kierowca_jury.py`, `test_open_api.py`, `test_mieszkaniec_ekrany.py`, `test_scenariusz.py`, `test_kierowca.py`, `Press`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Why does `_get()` connect `_get` to `render`, `wysypiska_api.py`, `point_states`, `dyspozytor_api.py`, `now`, `dashboard_api.py`, `wysypiska.py`, `Filters`, `odbior`, `jury_check.py`, `_point`, `devices.py`, `api_pl.py`, `data_version`, `create`, `dashboard.py`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `T()` (e.g. with `e()` and `p()`) actually correct?**
  _`T()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 65 inferred relationships involving `e()` (e.g. with `ai()` and `aR()`) actually correct?**
  _`e()` has 65 INFERRED edges - model-reasoned connections that need verification._
- **Are the 76 inferred relationships involving `i()` (e.g. with `A2()` and `aw()`) actually correct?**
  _`i()` has 76 INFERRED edges - model-reasoned connections that need verification._