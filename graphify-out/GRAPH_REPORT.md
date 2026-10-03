# Graph Report - trash-fairy  (2026-10-03)

## Corpus Check
- 114 files · ~6,533,374 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2008 nodes · 5136 edges · 98 communities (85 shown, 13 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 299 edges (avg confidence: 0.64)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d59d8ba8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- chart.umd.min.js
- o
- xn
- views.py
- test_auth.py
- panel.js
- test_zglos.py
- 85% crossing time with in-hour interpolation, interval from p80/p20
- Reports and anti-spam rules (merge 15 min, reliability last 10, flag)
- Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js
- Synthetic data: 8 weeks, OSM-driven fill rates, trolled buttons, frozen demo clock
- Trash Fairy README
- Brainstorm: przycisk dla mieszkańców, awarie, spam, wyświetlacz, program „Przyjaciele Wróżki”
- AI role: Vision, event parsing, 'Wrozka podpowiada' report
- Events from data/events.json with crowd-scale multiplier (200m x1.3 / 400m x1.6 / 800m x2.0)
- test_photos.py
- test_fairy.py
- api.py
- Kontekst MPO: dane do pitchu i porównania
- Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)
- pokaz.js
- .add
- residents.py
- test_residents.py
- zglos.js
- Audyt UX / UI / funkcjonalności – Trash Fairy (Etap 2)
- Trash Fairy – wdrożenie ekranu „Zgłoś kosz” (PWA dla mieszkańców)
- Etap 1 – rozpoznanie (bez zmian w kodzie)
- Trash Fairy – wdrożenie widoku C „Pokaz dla jury”
- queue.js
- sw.js
- models.py
- renderer/epaper_render.py
- kierowca.js
- import_points
- ns
- test_forecast.py
- Trash Fairy – wyświetlacz e-papierowy na koszu (800×480)
- E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware)
- epapier.js
- fetch_osm.py
- .getDatasetMeta
- no
- test_karnet.py
- zt
- forecast.py
- tn
- an
- va
- compare
- updateElements
- test_routes.py
- leaflet.js
- pytest
- .getContext
- database_url
- traffic.py
- kierowca/sw.js
- open_api.py
- n
- test_weather.py
- render
- clock.py
- .bindResponsiveEvents
- auth.py
- sms.py
- build.py
- jn
- e
- state.py
- .constructor
- now
- rate.py
- xt
- k
- rs
- u
- Cs
- fakes.py
- test_sms.py
- ke
- Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)
- O
- test_zdjecia.py
- xo
- conftest.py
- bi
- Wyniki po Fali 1 audytu i PWA kierowcy
- si
- http.py
- .buildOrUpdateControllers
- s
- Before/after comparison on same fill increments (4 weeks)
- ._setStyle
- beforeUpdate
- jury_pool

## God Nodes (most connected - your core abstractions)
1. `an()` - 61 edges
2. `va` - 56 edges
3. `ns()` - 55 edges
4. `import_points()` - 52 edges
5. `o()` - 51 edges
6. `now()` - 50 edges
7. `s()` - 49 edges
8. `point_states()` - 48 edges
9. `a()` - 44 edges
10. `Point` - 39 edges

## Surprising Connections (you probably didn't know these)
- `Soft press limit: 1 per 2 s per point, 120/h per IP, ProxyFix` --conceptually_related_to--> `Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report`  [INFERRED]
  DECYZJE.md → docs/KONCEPCJA.md
- `Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js` --semantically_similar_to--> `Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/KONCEPCJA.md
- `_shape()` --calls--> `P()`  [INFERRED]
  app/epaper_render.py → docs/widok-c/map/build.py
- `test_events_near_uses_scale_radius()` --calls--> `events_near()`  [EXTRACTED]
  tests/test_forecast.py → app/events.py
- `test_weather_changes_only_future_hours()` --calls--> `trajectory()`  [EXTRACTED]
  tests/test_weather.py → app/forecast.py

## Import Cycles
- 3-file cycle: `app/__init__.py -> app/api.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/residents.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/auth.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/epaper.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/fairy.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/forecast.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/rate.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/reports.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/routes.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/simulation.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/sms.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/state.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/traffic.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/weather.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/osm_import.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/__init__.py`

## Hyperedges (group relationships)
- **Routing and before/after comparison** — decyzje_route_point_selection, decyzje_ortools_vrp, decyzje_before_after_comparison, decyzje_fixed_schedule_simulation, app_templates_panel_routes_section, app_templates_panel_compare_section [INFERRED 0.85]
- **Forecast pipeline: weekly profile + events -> 85% crossing -> MAE** — decyzje_weekly_profile, decyzje_event_multiplier, decyzje_crossing_85_interval, decyzje_mae_evaluation, decyzje_forecast_on_demand, docs_koncepcja_forecast [INFERRED 0.95]

## Communities (98 total, 13 thin omitted)

### Community 0 - "chart.umd.min.js"
Cohesion: 0.03
Nodes (43): As(), beforeDatasetDraw(), beforeDatasetsDraw(), Bt(), cn(), ct(), d(), destroy() (+35 more)

### Community 1 - "o"
Cohesion: 0.09
Nodes (47): a(), aa(), ai(), ao(), average(), da(), dataset(), draw() (+39 more)

### Community 2 - "xn"
Cohesion: 0.13
Nodes (5): bn(), pn(), un(), xn, Ye()

### Community 3 - "views.py"
Cohesion: 0.08
Nodes (38): accessibility(), api_docs(), button(), crew(), driver(), driver_sw(), epaper_page(), health() (+30 more)

### Community 4 - "test_auth.py"
Cohesion: 0.15
Nodes (14): login(), demo(), fixture, test_dispatcher_only_endpoints(), test_driver_only_own_fleet(), test_login_disabled_without_password(), test_login_rate_limit_after_five_failures(), test_login_roles_and_bad_password() (+6 more)

### Community 5 - "panel.js"
Cohesion: 0.08
Nodes (39): apply(), askedPoint, clockAction(), dec(), describe(), esc(), eventLayer, hhmm() (+31 more)

### Community 6 - "test_zglos.py"
Cohesion: 0.06
Nodes (32): city_scale(), Skalowanie wyniku koszy na cały Kraków (decyzja 43): wizyty z harmonogramu MPO…, _fetch(), _load(), Przebieg tras po ulicach z OSRM, tylko do rysowania na mapie. Kilometry nadal…, coords: lista [lat, lon]. Zwraca (punkty linii [lat, lon], approx)., street_path(), neighbors_map() (+24 more)

### Community 7 - "85% crossing time with in-hour interpolation, interval from p80/p20"
Cohesion: 0.16
Nodes (16): Point details section with Chart.js chart, Routes for next run section, Decisions only by code rules, never AI, 85% crossing time with in-hour interpolation, interval from p80/p20, Panel shows system estimate, not simulation hidden truth, MAE 2.5 p.p. vs naive mean 7.3 p.p. on last week, no leakage, OR-Tools VRP, 1 vehicle per fleet, depot MPO Nowohucka 1, straight line x1.3, Route point selection: full now, crosses 85% before next run, or safety (bin 3 d, shelter 7 d) (+8 more)

### Community 8 - "Reports and anti-spam rules (merge 15 min, reliability last 10, flag)"
Cohesion: 0.33
Nodes (6): 'Sytuacja teraz' summary with press->report counter, Report accuracy decided by emptying (>=75%); reliability = accurate share of last 10, start 70%, Report table: presses merged within 15 min of first press, Main path: press -> state change -> to-empty list -> route -> AI report, Reports and anti-spam rules (merge 15 min, reliability last 10, flag), Test plan (~10 pytest tests, Claude mocked)

### Community 9 - "Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js"
Cohesion: 0.15
Nodes (13): Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js, 60 bins from Rynek/Plac Nowy, min 80 m apart, Forecast computed on demand with per-clock-hour profile cache, History stored in forecast table (source='sim'), Real bin positions from OSM cached in data/*.geojson, OSM tiles instead of CARTO, Polling every 2 s with version number, Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report (+5 more)

### Community 10 - "Synthetic data: 8 weeks, OSM-driven fill rates, trolled buttons, frozen demo clock"
Cohesion: 0.18
Nodes (11): Demo clock header (advance +1 h, reset), Dispatcher panel template (panel.html), Demo clock in DB with 24 h simulated future and +1 h advance, Fill rate from surroundings (1.5%/h + venues + stops, cap 8%/h), Simulation with fixed MPO schedule (6:00/14:00, shelters every 3 days), Screens: dispatcher panel, point details, virtual button, jury mode, crew view, methodology, Style: Planty green + gold panel, magic violet/pink for AI and button, Synthetic data: 8 weeks, OSM-driven fill rates, trolled buttons, frozen demo clock (+3 more)

### Community 11 - "Trash Fairy README"
Cohesion: 0.20
Nodes (11): Staged work process with ROADMAPA/DECYZJE, Trash Fairy work rules (CLAUDE.md), Decision log (DECYZJE.md), Competition: Mr Fill, Wroclaw/Sierpc/Rzeszow sensors, Trash Fairy concept (KONCEPCJA.md), Hardware-agnostic brain for MPO, Out of scope list (section 16), Problem: Krakow street bins overflow on fixed MPO schedule (+3 more)

### Community 12 - "Brainstorm: przycisk dla mieszkańców, awarie, spam, wyświetlacz, program „Przyjaciele Wróżki”"
Cohesion: 0.22
Nodes (8): A. Cel i zakres, B. Fizyczny przycisk: sprzęt i awarie, Brainstorm: przycisk dla mieszkańców, awarie, spam, wyświetlacz, program „Przyjaciele Wróżki”, C. Wyświetlacz, D. Spam i nadużycia, E. Program dla mieszkańców: rejestracja, F. Nagrody i pieniądze, G. Prawo, RODO, ryzyka

### Community 13 - "AI role: Vision, event parsing, 'Wrozka podpowiada' report"
Cohesion: 0.40
Nodes (6): app/llm.py gateway (ask, ask_json), AI role: Vision, event parsing, 'Wrozka podpowiada' report, Photo analysis JSON schema (fill_level, misuse, damage, confidence), Shelter -> bin rule (200 m, 48 h), Causal chain: overflowing shelter -> household bags in street bins, Stage 5: Claude Vision crew view, misuse, shelter->bin rule

### Community 14 - "Events from data/events.json with crowd-scale multiplier (200m x1.3 / 400m x1.6 / 800m x2.0)"
Cohesion: 0.33
Nodes (6): Point list (text alternative to map) and legend, Flag 'check button' (<40% accurate in 7 days or 6 h overflow without press), Events from data/events.json with crowd-scale multiplier (200m x1.3 / 400m x1.6 / 800m x2.0), Soft press limit: 1 per 2 s per point, 120/h per IP, ProxyFix, 24 h plan and cut order, Events from Karnet Krakow via Claude + Nominatim

### Community 15 - "test_photos.py"
Cohesion: 0.07
Nodes (44): image_block(), household_bag_links(), latest_analyses(), misuse_overview(), overflowing_shelters(), Nadużycia i powiązanie altana → kosz (koncepcja, sekcja 6.5) — reguły w kodzie.…, {point_id: (ostatnia analiza dowolna, ostatnia udana)} z okna 48 h przed `now`., {shelter_id: najwyższy szacunek} dla altan przepełnionych wg prognozy w… (+36 more)

### Community 16 - "test_fairy.py"
Cohesion: 0.11
Nodes (23): Liczby z tekstu raportu, których nie ma w faktach (np. 16:11 → „16” i „11”…, unknown_numbers(), _env_float(), money(), money_assumptions(), Przeliczenie wyniku porównania (4 tygodnie) na miesiąc, zł i CO₂ — wg jawnych…, (typ, etykieta, uzasadnienie, efekt) albo None — reguły z tabeli w sekcji 6.8., recommend() (+15 more)

### Community 17 - "api.py"
Cohesion: 0.08
Nodes (55): _accuracy_m(), changes(), clock_advance(), clock_reset(), comparison(), current_resident(), device_selftest(), devices() (+47 more)

### Community 18 - "Kontekst MPO: dane do pitchu i porównania"
Cohesion: 0.50
Nodes (3): Harmonogram oczyszczania 08/2026 (arkusz „Kosze”), Jak działa MPO (informacja ogólna MPO Kraków), Kontekst MPO: dane do pitchu i porównania

### Community 19 - "Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)"
Cohesion: 0.33
Nodes (5): Cel, Poza zakresem (ROADMAPA), Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A), Testy, Zakres (wariant A)

### Community 20 - "pokaz.js"
Cohesion: 0.08
Nodes (38): apply(), atRisk(), CAPTION, clockAction(), cluster, DAYS, dur(), esc() (+30 more)

### Community 21 - ".add"
Cohesion: 0.09
Nodes (10): ei(), En, Fo(), ia(), je(), qe(), qs(), ti() (+2 more)

### Community 22 - "residents.py"
Cohesion: 0.11
Nodes (26): PointAward, Uczestnik programu „Przyjaciele Wróżki”. Bez danych osobowych: pseudonim + hash…, Punkty za trafne zgłoszenie (jedna nagroda na mieszkańca, punkt i dzień)., Zgłoszenie: naciśnięcia jednego punktu w oknie 15 minut od pierwszego…, Report, Resident, award(), devices_overview() (+18 more)

### Community 23 - "test_residents.py"
Cohesion: 0.09
Nodes (46): Emptying, Opróżnienie punktu przez ekipę MPO, z poziomem zastanym przed opróżnieniem., low_reliability(), point_reliability(), Odsetek trafnych wśród ostatnich 10 rozstrzygniętych zgłoszeń (outcomes: od…, Flaga „sprawdź przycisk”: < 40% trafnych wśród zgłoszeń z 7 dni (min. 3…, Zapisuje naciśnięcie i dolicza je do otwartego zgłoszenia z ostatnich 15 min…, Opróżnienie rozstrzyga otwarte zgłoszenia punktu: poziom >= 75% → trafne,… (+38 more)

### Community 24 - "zglos.js"
Cohesion: 0.15
Nodes (30): bind(), clientId, dequeue(), distM(), doneHtml(), esc(), extras(), flushQueue() (+22 more)

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

### Community 29 - "queue.js"
Cohesion: 0.67
Nodes (3): tfDb(), tfQueue, tfTx()

### Community 31 - "models.py"
Cohesion: 0.07
Nodes (51): cleanup_photos_command(), karnet_command(), Import punktów z data/*.geojson i wydarzeń z data/events.json, symulacja…, Usuwa pliki zdjęć starszych niż 7 dni (wyniki analiz zostają w bazie). Do crona., Pobiera wydarzenia z Karnet Kraków do data/karnet.json, importuje je i odtwarza…, seed_command(), clear_cache(), Porównanie „przed i po” (koncepcja, sekcja 6.7): stały harmonogram MPO kontra… (+43 more)

### Community 32 - "renderer/epaper_render.py"
Cohesion: 0.23
Nodes (14): _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3…, 168×168: obrys 3 px, biała ramka 8 px, kod wpisany w 152 px., Wycinek okna PARTIAL (752×88) do odświeżenia częściowego. (+6 more)

### Community 33 - "kierowca.js"
Cohesion: 0.13
Nodes (33): act(), commit(), count(), cur(), DAYS, dec(), drawMap(), esc() (+25 more)

### Community 34 - "import_points"
Cohesion: 0.12
Nodes (27): import_points(), Zastępuje punkty w bazie: 60 koszy (Rynek, Kazimierz, kilka przy przeciążonych…, is_emptying_time(), Dwa najspokojniejsze kosze na Kazimierzu („przy szkole”) — ktoś naciska je dla…, Zastępuje całą symulację (poziomy, opróżnienia, naciśnięcia, zgłoszenia)., sim_presses(), simulate(), trolled_ids() (+19 more)

### Community 35 - "ns"
Cohesion: 0.10
Nodes (4): at(), ns(), rt(), updateRangeFromParsed()

### Community 36 - "test_forecast.py"
Cohesion: 0.20
Nodes (17): multiplier(), Mnożnik najsilniejszego wydarzenia w promieniu, aktywnego w godzinie `at` albo…, first_crossing(), Chwila przekroczenia progu (interpolacja w obrębie godziny) w trajektorii…, Godzina po godzinie [(at, est, low, high)]. Do `now` zerujemy na opróżnieniach,…, trajectory(), flat(), point() (+9 more)

### Community 37 - "Trash Fairy – wyświetlacz e-papierowy na koszu (800×480)"
Cohesion: 0.22
Nodes (8): Dane wejściowe renderera, Etap 1 – symulator do pokazu (zalecany na hackathon), Etap 2 – prawdziwe urządzenie (kontrakt, bez implementacji firmware), Kryteria odbioru, Siatka (px, stałe – nie zmieniać między stanami), Stany i wyzwalacze, Trash Fairy – wyświetlacz e-papierowy na koszu (800×480), Zawartość paczki

### Community 38 - "E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware)"
Cohesion: 0.29
Nodes (6): Co jeszcze przed pilotażem, Dlaczego urządzenie renderuje samo, Downlink (port 10, ≤ 12 B), E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware), QR na urządzeniu, Uplink

### Community 39 - "epapier.js"
Cohesion: 0.67
Nodes (5): fullRefresh(), log(), poll(), STATE_LABEL, swapFull()

### Community 40 - "fetch_osm.py"
Cohesion: 0.20
Nodes (7): Audyt UX: zrzuty każdego ekranu na 6 szerokościach + konsola, poziomy scroll,…, classify(), main(), Pobiera punkty z OSM (Overpass API) dla obszaru demo i zapisuje cache do…, to_feature(), Smoke test pokazu (decyzja 37): 10 przepływów w prawdziwej przeglądarce, kod…, sys

### Community 42 - "no"
Cohesion: 0.08
Nodes (12): beforeDraw(), beforeLayout(), buildLookupTable(), _generate(), getDecimalForValue(), _getTimestampsForTable(), initOffsets(), lt() (+4 more)

### Community 43 - "test_karnet.py"
Cohesion: 0.06
Nodes (44): default_details(), details(), fetch(), _first(), import_events(), in_demo(), parse_list(), Pobiera listy wydarzeń (grzecznie, z opóźnieniem) i zapisuje do cache. Zwraca… (+36 more)

### Community 44 - "zt"
Cohesion: 0.08
Nodes (11): ce(), color(), de, he(), It(), kt(), qt(), _t() (+3 more)

### Community 45 - "forecast.py"
Cohesion: 0.14
Nodes (22): events_near(), build_profiles(), clear_cache(), forecast_quality(), point_forecasts(), point_series(), Prognoza zapełnienia (koncepcja, sekcja 6.3): statystyka i reguły, bez AI.…, {point_id: {"est", "crossing", "early", "late", "recent"}} dla chwili `now`… (+14 more)

### Community 48 - "va"
Cohesion: 0.06
Nodes (24): afterDraw(), afterEvent(), afterUpdate(), ba, Bi(), Ee(), es(), f() (+16 more)

### Community 49 - "compare"
Cohesion: 0.12
Nodes (17): compare(), fixed_selects(), following_run(), is_run(), Zwraca miary jednej polityki. `incs[pid][i]` = prawdziwy przyrost w godzinie…, Miary obu polityk na `weeks` tygodniach przed `cutoff` (pełna godzina)., run_policy(), _cell() (+9 more)

### Community 50 - "updateElements"
Cohesion: 0.08
Nodes (24): Ae(), buildTicks(), ca(), _calculateBarIndexPixels(), _calculateBarValuePixels(), Fn(), getBasePixel(), getLabelAndValue() (+16 more)

### Community 51 - "test_routes.py"
Cohesion: 0.12
Nodes (26): distance_m(), Odległość w linii prostej (haversine), w metrach., bin_rate(), Bierze do n punktów najbliżej centre, pomijając te bliżej niż min_gap_m od już…, Tempo zapełniania kosza (%/h) z liczby lokali i przystanków w promieniu 100 m., select_spaced(), Trasy na najbliższy kurs (koncepcja, sekcja 6.6): wybór punktów regułami + OR-…, Powód wzięcia punktu na kurs `run_at` albo None. Reguły, nie AI (koncepcja,… (+18 more)

### Community 52 - "leaflet.js"
Cohesion: 0.07
Nodes (9): a(), Ci(), ei(), ii(), l(), Mi(), ri(), x() (+1 more)

### Community 53 - "pytest"
Cohesion: 0.12
Nodes (6): pytest, demo(), fixture, demo(), fixture, test_menu_by_role()

### Community 54 - ".getContext"
Cohesion: 0.10
Nodes (10): Ci(), Do(), eo(), ho(), inXRange(), inYRange(), ls, Oe() (+2 more)

### Community 55 - "database_url"
Cohesion: 0.60
Nodes (4): database_url(), DATABASE_URL z env; Coolify/Heroku podają postgres(ql)://, a my używamy…, test_database_url_defaults_to_sqlite(), test_database_url_uses_psycopg3_for_postgres()

### Community 56 - "traffic.py"
Cohesion: 0.17
Nodes (20): _eta(), (ETA kursu z opóźnieniem dojazdu w korku, opóźnienie w min). Bez danych o ruchu…, city_ratio(), conditions(), data(), delay_min(), drive_min(), fresh_samples() (+12 more)

### Community 58 - "open_api.py"
Cohesion: 0.28
Nodes (12): after_request, conditions(), Pogoda (mnożnik prognozy) i ruch (mnożnik czasu przejazdu) — panel i…, _bin(), bin_detail(), bins(), conditions_view(), cors() (+4 more)

### Community 59 - "n"
Cohesion: 0.06
Nodes (16): Be(), bo, determineDataLimits(), ea(), et(), getValueForPixel(), ha, ko (+8 more)

### Community 60 - "test_weather.py"
Cohesion: 0.17
Nodes (15): conditions(), data(), factor(), _load_cache(), {"fetched_at", "hours": {"2026-10-03T13:00": {"temp", "rain", "code"}}} albo…, Pogoda dla godziny zegara demo: tekst do panelu i otwartego API., _row(), live() (+7 more)

### Community 61 - "render"
Cohesion: 0.15
Nodes (20): _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3…, 168×168: obrys 3 px, biała ramka 8 px, kod wpisany w 152 px., Wycinek okna PARTIAL (752×88) do odświeżenia częściowego. (+12 more)

### Community 62 - "clock.py"
Cohesion: 0.16
Nodes (17): advance(), maybe_auto_reset(), Zegar demo: zamrożona sobota 13:30, przewijany o godzinę. Przewinięcie…, Akcja w demo (zgłoszenie, opróżnienie, problem): przesuwa start odliczania do…, Reset demo, gdy od ostatniej akcji minęło IDLE. Warunkowy UPDATE: przy kilku…, Odtwarza symulację od zera i cofa zegar do startu scenariusza (kasuje…, reset(), touch() (+9 more)

### Community 63 - ".bindResponsiveEvents"
Cohesion: 0.21
Nodes (4): fs(), ps(), vs(), ws

### Community 64 - "auth.py"
Cohesion: 0.16
Nodes (17): _analysis(), point_detail(), public_view(), _r(), can_touch(), fleet(), home_for_role(), init_app() (+9 more)

### Community 65 - "sms.py"
Cohesion: 0.20
Nodes (15): config(), post_form(), Ustawienie integracji: najpierw config aplikacji (testy je zerują), potem…, _auth(), check_code(), configured(), Exception, Kod SMS przy rejestracji w programie „Przyjaciele Wróżki”: Twilio Verify przez… (+7 more)

### Community 66 - "build.py"
Cohesion: 0.26
Nodes (8): dist(), geom_d(), P(), path_d(), route(), seq_path(), snap(), math

### Community 68 - "e"
Cohesion: 0.22
Nodes (14): at(), d(), e(), F(), hi(), m(), p(), q() (+6 more)

### Community 69 - "state.py"
Cohesion: 0.08
Nodes (38): crew_progress(), driver_run(), PWA kierowcy: tylko kurs jego floty (decyzja 2), z przebiegiem po ulicach i…, Postęp kierowcy floty od resetu demo (decyzja 30): opróżnienia, problemy,…, routes(), device_info(), display_state(), plural_people() (+30 more)

### Community 70 - ".constructor"
Cohesion: 0.27
Nodes (4): dt(), ke(), kn(), wn()

### Community 71 - "now"
Cohesion: 0.12
Nodes (33): fairy_get(), fairy_refresh(), Nowy raport. Przy błędzie API: komunikat + ostatni raport (nigdy 500)., now(), keys(), state_key zmienia się tylko przy pełnym odświeżeniu, values_key przy zmianie…, generate(), is_fresh() (+25 more)

### Community 72 - "rate.py"
Cohesion: 0.27
Nodes (10): login(), None, gdy się udało; inaczej komunikat do pokazania., Counter, Liczniki limitów (SMS, AI, logowanie) wspólne dla wszystkich workerów…, count(), hit(), Limity wspólne dla wszystkich workerów: liczniki w bazie (tabela Counter), okno…, Liczy zdarzenie i zwraca True, gdy mieści się w limicie; przy przekroczeniu nic… (+2 more)

### Community 74 - "k"
Cohesion: 0.40
Nodes (6): G(), k(), me(), Oe(), Se(), ze()

### Community 76 - "u"
Cohesion: 0.20
Nodes (6): addBox(), configure(), reset(), start(), u(), vn()

### Community 78 - "fakes.py"
Cohesion: 0.28
Nodes (5): FakeOpener, Fałszywy opener dla app/http.py: odpowiedzi po fragmencie adresu, zapis…, routes: {fragment_adresu: (status, body) | Exception | callable(req) ->…, _Resp, urllib_error

### Community 79 - "test_sms.py"
Cohesion: 0.47
Nodes (8): fixture, register(), test_gateway_failure_503_or_demo_fallback(), test_limits_per_number(), test_twilio_send_and_check(), test_without_gateway_demo_code_on_screen(), test_wrong_code_and_retry_for_unverified_number(), twilio()

### Community 80 - "ke"
Cohesion: 0.25
Nodes (8): Ae(), be(), Ie(), j(), ke(), ne(), Re(), s()

### Community 81 - "Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)"
Cohesion: 0.25
Nodes (7): 1. Uprawnienia, 2. Ekrany i nawigacja, 3. Wygląd, 4. Widoki i stany, 5. Zależności i infrastruktura, 6. Produkt i pokaz, Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)

### Community 82 - "O"
Cohesion: 0.29
Nodes (7): Ft(), Jt(), Le(), O(), Qt(), $t(), te()

### Community 83 - "test_zdjecia.py"
Cohesion: 0.28
Nodes (7): demo(), jpeg_with_gps(), fixture, Zdjęcia z miasta: GPS z EXIF → najbliższy kosz (do 80 m), paczka wielu plików., JPEG 32×32 z GPSInfo w EXIF (tak zapisuje aparat telefonu z włączoną…, test_batch_upload_matches_nearest_bin_by_exif(), test_gps_from_exif_roundtrip()

### Community 85 - "conftest.py"
Cohesion: 0.36
Nodes (7): cache(), client(), fixture, Klient zalogowany jako dyspozytor (zapisy, AI, Reset)., Mały, sztuczny odpowiednik data/*.geojson (bez sieci)., _scatter(), staff()

### Community 86 - "bi"
Cohesion: 0.50
Nodes (4): bi(), Pi(), Ti(), u()

### Community 88 - "Wyniki po Fali 1 audytu i PWA kierowcy"
Cohesion: 0.40
Nodes (4): Lighthouse (lokalnie, Chromium headless, Lighthouse 13.5), Poziomy scroll, Pozycje audytu, Wyniki po Fali 1 audytu i PWA kierowcy

### Community 90 - "si"
Cohesion: 0.67
Nodes (4): Je(), ni(), oi(), si()

### Community 92 - "http.py"
Cohesion: 0.18
Nodes (11): get_json(), Wspólny klient HTTP integracji (Open-Meteo, TomTom, Twilio): urllib ze stdlib,…, (status, json). Błąd HTTP z treścią JSON (np. Twilio 400/429) zwracamy jako…, _send(), ratio(), Korek z odpowiedzi flowSegmentData: swobodna / teraz, 1,0–3,0; zamknięta droga…, _refresh(), _fetch() (+3 more)

### Community 96 - "s"
Cohesion: 0.13
Nodes (15): b(), g(), init(), label(), m(), mt(), nn(), on() (+7 more)

### Community 97 - "Before/after comparison on same fill increments (4 weeks)"
Cohesion: 0.29
Nodes (7): Before/after 4 weeks section, 'Wrozka podpowiada' placeholder card, Before/after comparison on same fill increments (4 weeks), Bin overflow hours unchanged with fixed run times, Before/after comparison: fixed schedule vs Trash Fairy, Investment recommendations (compactor, bigger bin, shelter intervention), Stage 6: 'Wrozka podpowiada' report, Karnet, recommendations, jury mode

### Community 100 - "jury_pool"
Cohesion: 0.40
Nodes (5): jury(), jury_pool(), Kod QR w panelu prowadzi tutaj: losowy kosz przy Rynku, żeby jury naciskało…, start_url PWA bez kosza: wybór kosza (najbliższe wg GPS w JS, zapas: pula przy…, report_pick()

## Ambiguous Edges - Review These
- `psycopg[binary] 3.3.6` → `Real bin positions from OSM cached in data/*.geojson`  [AMBIGUOUS]
  DECYZJE.md · relation: conceptually_related_to

## Knowledge Gaps
- **131 isolated node(s):** `STATE_LABEL`, `ISSUES`, `STATE_LBL`, `DAYS`, `I` (+126 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `psycopg[binary] 3.3.6` and `Real bin positions from OSM cached in data/*.geojson`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `import_points()` connect `import_points` to `test_auth.py`, `test_forecast.py`, `test_zglos.py`, `now`, `forecast.py`, `test_photos.py`, `test_fairy.py`, `compare`, `test_routes.py`, `test_zdjecia.py`, `pytest`, `test_residents.py`, `traffic.py`, `models.py`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `point_states()` connect `state.py` to `auth.py`, `import_points`, `test_forecast.py`, `test_auth.py`, `test_zglos.py`, `forecast.py`, `test_fairy.py`, `api.py`, `test_routes.py`, `test_residents.py`, `open_api.py`, `models.py`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Why does `ns()` connect `ns` to `chart.umd.min.js`, `o`, `xn`, `beforeUpdate`, `._setStyle`, `no`, `Cs`, `va`, `updateElements`, `.buildOrUpdateControllers`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `o()` (e.g. with `ai()` and `da()`) actually correct?**
  _`o()` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `STATE_LABEL`, `ISSUES`, `STATE_LBL` to the rest of the system?**
  _131 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `chart.umd.min.js` be split into smaller, more focused modules?**
  _Cohesion score 0.03058103975535168 - nodes in this community are weakly interconnected._