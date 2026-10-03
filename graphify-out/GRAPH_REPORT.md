# Graph Report - trash-fairy  (2026-10-03)

## Corpus Check
- 111 files · ~6,530,760 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1981 nodes · 5076 edges · 98 communities (87 shown, 11 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 298 edges (avg confidence: 0.64)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bbd77765`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- chart.umd.min.js
- o
- page_context
- views.py
- osm_import.py
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
- karnet.py
- residents.py
- state.py
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
- json
- reset
- no
- llm.py
- zt
- generate
- tn
- an
- va
- test_ai_safety.py
- n
- comparison.py
- leaflet.js
- .isHorizontal
- .getContext
- database_url
- traffic.py
- kierowca/sw.js
- emptying
- inRange
- weather.py
- render
- press
- ws
- auth.py
- http.py
- build.py
- jn
- e
- open_api.py
- .notifyPlugins
- now
- rate.py
- parse
- k
- rs
- u
- Cs
- test_sms.py
- fairy_refresh
- ke
- Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)
- test_zdjecia.py
- display_state
- osrm.py
- money
- ._createDescriptors
- xt
- Wyniki po Fali 1 audytu i PWA kierowcy
- bi
- si
- ri
- logout
- .buildOrUpdateControllers
- xo
- Before/after comparison on same fill increments (4 weeks)

## God Nodes (most connected - your core abstractions)
1. `an()` - 61 edges
2. `va` - 56 edges
3. `ns()` - 55 edges
4. `import_points()` - 52 edges
5. `o()` - 51 edges
6. `now()` - 49 edges
7. `s()` - 49 edges
8. `point_states()` - 47 edges
9. `a()` - 44 edges
10. `Point` - 39 edges

## Surprising Connections (you probably didn't know these)
- `Soft press limit: 1 per 2 s per point, 120/h per IP, ProxyFix` --conceptually_related_to--> `Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report`  [INFERRED]
  DECYZJE.md → docs/KONCEPCJA.md
- `Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js` --semantically_similar_to--> `Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/KONCEPCJA.md
- `test_reset_clears_stop_issues()` --calls--> `reset()`  [EXTRACTED]
  tests/test_kierowca.py → app/clock.py
- `_shape()` --calls--> `P()`  [INFERRED]
  app/epaper_render.py → docs/widok-c/map/build.py
- `test_weather_changes_only_future_hours()` --calls--> `trajectory()`  [EXTRACTED]
  tests/test_weather.py → app/forecast.py

## Import Cycles
- 3-file cycle: `app/__init__.py -> app/api.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/epaper.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/auth.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/fairy.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/forecast.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/rate.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/reports.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/residents.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/routes.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/simulation.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/sms.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/state.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/traffic.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/weather.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/karnet.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/osm_import.py -> app/__init__.py`

## Hyperedges (group relationships)
- **Routing and before/after comparison** — decyzje_route_point_selection, decyzje_ortools_vrp, decyzje_before_after_comparison, decyzje_fixed_schedule_simulation, app_templates_panel_routes_section, app_templates_panel_compare_section [INFERRED 0.85]
- **Forecast pipeline: weekly profile + events -> 85% crossing -> MAE** — decyzje_weekly_profile, decyzje_event_multiplier, decyzje_crossing_85_interval, decyzje_mae_evaluation, decyzje_forecast_on_demand, docs_koncepcja_forecast [INFERRED 0.95]

## Communities (98 total, 11 thin omitted)

### Community 0 - "chart.umd.min.js"
Cohesion: 0.03
Nodes (45): As(), beforeDatasetDraw(), beforeDatasetsDraw(), beforeLayout(), Bt(), d(), destroy(), Di() (+37 more)

### Community 1 - "o"
Cohesion: 0.08
Nodes (54): a(), aa(), ai(), ao(), at(), b(), beforeDraw(), cn() (+46 more)

### Community 2 - "page_context"
Cohesion: 0.40
Nodes (5): assumptions(), page_context(), _pl(), [(obszar, założenie, wartość)] — wartości wprost z kodu., methodology()

### Community 3 - "views.py"
Cohesion: 0.09
Nodes (36): api_docs(), button(), crew(), driver(), driver_sw(), epaper_page(), health(), jury() (+28 more)

### Community 4 - "osm_import.py"
Cohesion: 0.08
Nodes (27): clear_cache(), clear_cache(), Profile zależą od zawartości bazy — czyścimy po każdej nowej symulacji lub…, Import punktów demo z cache OSM (data/*.geojson) do bazy., clear_cache(), Po resecie demo i między testami: wersja danych może się powtórzyć na nowej…, pytest, random (+19 more)

### Community 5 - "panel.js"
Cohesion: 0.09
Nodes (35): apply(), clockAction(), dec(), describe(), esc(), eventLayer, hhmm(), KIND (+27 more)

### Community 6 - "test_zglos.py"
Cohesion: 0.08
Nodes (22): neighbors_map(), demo(), press(), props(), fixture, Test 10 z sekcji 11: naciśnięcie → stan → punkt do opróżnienia., test_changes_only_when_version_moves(), test_clock_endpoints() (+14 more)

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
Cohesion: 0.12
Nodes (24): household_bag_links(), latest_analyses(), misuse_overview(), overflowing_shelters(), {point_id: (ostatnia analiza dowolna, ostatnia udana)} z okna 48 h przed `now`., {shelter_id: najwyższy szacunek} dla altan przepełnionych wg prognozy w…, [(bin, shelter)] dla worków domowych w promieniu 200 m od przepełnionej altany., Wszystko, czego potrzebuje panel: plakietki nadużyć, flagi rozbieżności, linie… (+16 more)

### Community 16 - "test_fairy.py"
Cohesion: 0.15
Nodes (18): point_stats(), {point_id: {"days", "overflow_days", "readings", "half_full", "per_day"}} z…, (typ, etykieta, uzasadnienie, efekt) albo None — reguły z tabeli w sekcji 6.8., Lista rekomendacji, od najważniejszych. `shelter_interventions`: {shelter_id:…, recommend(), recommendations(), demo(), model() (+10 more)

### Community 17 - "api.py"
Cohesion: 0.10
Nodes (37): _analysis(), changes(), clock_advance(), clock_reset(), comparison(), current_resident(), device_selftest(), devices() (+29 more)

### Community 18 - "Kontekst MPO: dane do pitchu i porównania"
Cohesion: 0.50
Nodes (3): Harmonogram oczyszczania 08/2026 (arkusz „Kosze”), Jak działa MPO (informacja ogólna MPO Kraków), Kontekst MPO: dane do pitchu i porównania

### Community 19 - "Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)"
Cohesion: 0.33
Nodes (5): Cel, Poza zakresem (ROADMAPA), Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A), Testy, Zakres (wariant A)

### Community 20 - "pokaz.js"
Cohesion: 0.08
Nodes (38): apply(), atRisk(), CAPTION, clockAction(), cluster, DAYS, dur(), esc() (+30 more)

### Community 21 - "karnet.py"
Cohesion: 0.13
Nodes (24): default_details(), details(), fetch(), _first(), import_events(), in_demo(), parse_list(), Wydarzenia z Karnet Kraków (koncepcja, sekcja 6.4). Publicznego API brak —… (+16 more)

### Community 22 - "residents.py"
Cohesion: 0.10
Nodes (34): Device, PointAward, Press, Uczestnik programu „Przyjaciele Wróżki”. Bez danych osobowych: pseudonim + hash…, Punkty za trafne zgłoszenie (jedna nagroda na mieszkańca, punkt i dzień)., Fizyczny przycisk z wyświetlaczem e-papierowym przy punkcie (stan symulowany w…, Pojedyncze naciśnięcie przycisku. Scalanie w zgłoszenia: app/reports.py., Zgłoszenie: naciśnięcia jednego punktu w oknie 15 minut od pierwszego… (+26 more)

### Community 23 - "state.py"
Cohesion: 0.08
Nodes (53): Emptying, Opróżnienie punktu przez ekipę MPO, z poziomem zastanym przed opróżnieniem., low_reliability(), Flaga „sprawdź przycisk”: < 40% trafnych wśród zgłoszeń z 7 dni (min. 3…, Zapisuje naciśnięcie i dolicza je do otwartego zgłoszenia z ostatnich 15 min…, Opróżnienie rozstrzyga otwarte zgłoszenia punktu: poziom >= 75% → trafne,…, record_press(), resolve_reports() (+45 more)

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
Nodes (39): cleanup_photos_command(), karnet_command(), Import punktów z data/*.geojson i wydarzeń z data/events.json, symulacja…, Usuwa pliki zdjęć starszych niż 7 dni (wyniki analiz zostają w bazie). Do crona., Pobiera wydarzenia z Karnet Kraków do data/karnet.json, importuje je i odtwarza…, seed_command(), Zegar demo: zamrożona sobota 13:30, przewijany o godzinę. Przewinięcie…, Stan wyświetlacza e-papierowego na koszu (docs/epapier/HANDOFF.md): wyzwalacze,… (+31 more)

### Community 32 - "renderer/epaper_render.py"
Cohesion: 0.23
Nodes (14): _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3…, 168×168: obrys 3 px, biała ramka 8 px, kod wpisany w 152 px., Wycinek okna PARTIAL (752×88) do odświeżenia częściowego. (+6 more)

### Community 33 - "kierowca.js"
Cohesion: 0.14
Nodes (33): act(), commit(), count(), cur(), DAYS, dec(), drawMap(), esc() (+25 more)

### Community 34 - "import_points"
Cohesion: 0.10
Nodes (40): compare(), Miary obu polityk na `weeks` tygodniach przed `cutoff` (pełna godzina)., distance_m(), Odległość w linii prostej (haversine), w metrach., bin_rate(), import_points(), Bierze do n punktów najbliżej centre, pomijając te bliżej niż min_gap_m od już…, Tempo zapełniania kosza (%/h) z liczby lokali i przystanków w promieniu 100 m. (+32 more)

### Community 35 - "ns"
Cohesion: 0.05
Nodes (8): beforeUpdate(), bn(), labelColor(), labelPointStyle(), ns(), pn(), updateRangeFromParsed(), xn

### Community 36 - "test_forecast.py"
Cohesion: 0.12
Nodes (33): events_near(), multiplier(), Mnożnik najsilniejszego wydarzenia w promieniu, aktywnego w godzinie `at` albo…, build_profiles(), first_crossing(), forecast_quality(), point_forecasts(), point_series() (+25 more)

### Community 37 - "Trash Fairy – wyświetlacz e-papierowy na koszu (800×480)"
Cohesion: 0.22
Nodes (8): Dane wejściowe renderera, Etap 1 – symulator do pokazu (zalecany na hackathon), Etap 2 – prawdziwe urządzenie (kontrakt, bez implementacji firmware), Kryteria odbioru, Siatka (px, stałe – nie zmieniać między stanami), Stany i wyzwalacze, Trash Fairy – wyświetlacz e-papierowy na koszu (800×480), Zawartość paczki

### Community 38 - "E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware)"
Cohesion: 0.29
Nodes (6): Co jeszcze przed pilotażem, Dlaczego urządzenie renderuje samo, Downlink (port 10, ≤ 12 B), E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware), QR na urządzeniu, Uplink

### Community 39 - "epapier.js"
Cohesion: 0.67
Nodes (5): fullRefresh(), log(), poll(), STATE_LABEL, swapFull()

### Community 40 - "json"
Cohesion: 0.18
Nodes (11): json, pathlib, Audyt UX: zrzuty każdego ekranu na 6 szerokościach + konsola, poziomy scroll,…, classify(), main(), Pobiera punkty z OSM (Overpass API) dla obszaru demo i zapisuje cache do…, to_feature(), sys (+3 more)

### Community 41 - "reset"
Cohesion: 0.10
Nodes (21): advance(), Odtwarza symulację od zera i cofa zegar do startu scenariusza (kasuje…, reset(), DemoClock, Zegar scenariusza demo (jeden wiersz). W bazie, bo gunicorn ma kilka procesów., demo(), fixture, demo() (+13 more)

### Community 42 - "no"
Cohesion: 0.07
Nodes (11): buildLookupTable(), En, Fo(), _generate(), getDecimalForValue(), _getTimestampsForTable(), init(), initOffsets() (+3 more)

### Community 43 - "llm.py"
Cohesion: 0.15
Nodes (18): ask(), ask_json(), _create(), image_block(), LLMError, model(), Exception, Jedyna brama do AI (CLAUDE.md): ask() i ask_json(). Model i klucz z env. AI… (+10 more)

### Community 44 - "zt"
Cohesion: 0.07
Nodes (10): ce(), color(), de, Ft(), he(), It(), qs(), te() (+2 more)

### Community 45 - "generate"
Cohesion: 0.17
Nodes (12): build_facts(), generate(), Wszystkie liczby do raportu — liczone w kodzie, nie przez model., Liczby z tekstu raportu, których nie ma w faktach (np. 16:11 → „16” i „11”…, Nowy raport albo LLMError (wtedy wywołujący pokazuje ostatni zapisany)., unknown_numbers(), fence(), Opakowuje treść zewnętrzną w ogranicznik; tag zamykający w środku jest… (+4 more)

### Community 47 - "an"
Cohesion: 0.10
Nodes (3): an(), generateLabels(), onClick()

### Community 48 - "va"
Cohesion: 0.08
Nodes (21): addElements(), afterDatasetsUpdate(), afterDraw(), afterEvent(), afterUpdate(), ba, Ee(), es() (+13 more)

### Community 49 - "test_ai_safety.py"
Cohesion: 0.23
Nodes (12): demo(), fake_create(), fixture, parametrize, Prompt injection i niebezpieczne odpowiedzi AI: treści zewnętrzne to dane,…, Atrapa llm._create: zapamiętuje system i treść, zwraca przygotowaną odpowiedź…, test_ai_text_with_script_is_escaped(), test_external_text_is_fenced_and_system_forbids_instructions() (+4 more)

### Community 50 - "n"
Cohesion: 0.05
Nodes (25): Be(), bo, _calculateBarIndexPixels(), _calculateBarValuePixels(), determineDataLimits(), ea(), getBasePixel(), getPixelForValue() (+17 more)

### Community 51 - "comparison.py"
Cohesion: 0.13
Nodes (28): fixed_selects(), following_run(), is_run(), Porównanie „przed i po” (koncepcja, sekcja 6.7): stały harmonogram MPO kontra…, Zwraca miary jednej polityki. `incs[pid][i]` = prawdziwy przyrost w godzinie…, run_policy(), _cell(), plan_routes() (+20 more)

### Community 52 - "leaflet.js"
Cohesion: 0.07
Nodes (7): a(), Ci(), l(), Le(), Mi(), x(), zi()

### Community 53 - ".isHorizontal"
Cohesion: 0.13
Nodes (5): Ae(), configure(), getPixelForTick(), Xs(), Y()

### Community 54 - ".getContext"
Cohesion: 0.11
Nodes (8): Bi(), ca(), Ci(), Do(), eo(), Fi(), ls, Oe()

### Community 55 - "database_url"
Cohesion: 0.60
Nodes (4): database_url(), DATABASE_URL z env; Coolify/Heroku podają postgres(ql)://, a my używamy…, test_database_url_defaults_to_sqlite(), test_database_url_uses_psycopg3_for_postgres()

### Community 56 - "traffic.py"
Cohesion: 0.17
Nodes (20): city_ratio(), conditions(), data(), drive_min(), fresh_samples(), _load_cache(), ratio(), Ruch drogowy z TomTom Traffic Flow (TOMTOM_API_KEY) jako mnożnik czasu… (+12 more)

### Community 58 - "emptying"
Cohesion: 0.11
Nodes (23): emptying(), _nearest_point(), photo(), _photo_from_request(), _point_or_none(), Zapisuje zdjęcie z formularza i uruchamia analizę. Zwraca (analiza, komunikat…, Ekipa MPO: punkt opróżniony, poziom zastany przed opróżnieniem, opcjonalne…, Kierowca: nie da się podjechać albo problem z koszem (+ opcjonalne zdjęcie).… (+15 more)

### Community 59 - "inRange"
Cohesion: 0.09
Nodes (24): average(), dataset(), getCenterPoint(), ha, ho(), Hs, _i(), index() (+16 more)

### Community 60 - "weather.py"
Cohesion: 0.17
Nodes (19): conditions(), data(), factor(), factor_at(), _fetch(), _load_cache(), Pogoda z Open-Meteo (bez klucza) jako mnożnik tempa zapełniania w prognozie.…, {"fetched_at", "hours": {"2026-10-03T13:00": {"temp", "rain", "code"}}} albo… (+11 more)

### Community 61 - "render"
Cohesion: 0.14
Nodes (21): _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3…, 168×168: obrys 3 px, biała ramka 8 px, kod wpisany w 152 px., Wycinek okna PARTIAL (752×88) do odświeżenia częściowego. (+13 more)

### Community 62 - "press"
Cohesion: 0.12
Nodes (16): _accuracy_m(), _eta(), press(), Kiedy ten telefon może zgłosić znowu (w czasie zegara demo)., Dokładność GPS z telefonu (m), obcięta do 150 m: słaby GPS w kamienicy nie…, (ETA kursu z opóźnieniem dojazdu w korku, opóźnienie w min). Bez danych o ruchu…, _retry_at(), routes() (+8 more)

### Community 63 - "ws"
Cohesion: 0.14
Nodes (10): ct(), dt(), fs(), ge(), gs(), ms(), ps(), vs() (+2 more)

### Community 64 - "auth.py"
Cohesion: 0.23
Nodes (13): driver_run(), PWA kierowcy: tylko kurs jego floty (decyzja 2), z przebiegiem po ulicach i…, can_touch(), fleet(), home_for_role(), init_app(), is_dispatcher(), Role na pokaz (docs/PRZEGLAD.md, decyzje 1–8): publiczna, dyspozytor, kierowca… (+5 more)

### Community 65 - "http.py"
Cohesion: 0.16
Nodes (19): config(), get_json(), post_form(), Wspólny klient HTTP integracji (Open-Meteo, TomTom, Twilio): urllib ze stdlib,…, Ustawienie integracji: najpierw config aplikacji (testy je zerują), potem…, (status, json). Błąd HTTP z treścią JSON (np. Twilio 400/429) zwracamy jako…, _send(), _auth() (+11 more)

### Community 66 - "build.py"
Cohesion: 0.26
Nodes (8): dist(), geom_d(), P(), path_d(), route(), seq_path(), snap(), math

### Community 68 - "e"
Cohesion: 0.22
Nodes (14): at(), d(), e(), F(), hi(), m(), p(), q() (+6 more)

### Community 69 - "open_api.py"
Cohesion: 0.18
Nodes (18): after_request, conditions(), Pogoda (mnożnik prognozy) i ruch (mnożnik czasu przejazdu) — panel i…, _bin(), bin_detail(), bins(), conditions_view(), cors() (+10 more)

### Community 71 - "now"
Cohesion: 0.35
Nodes (14): now(), calm_bin(), Ekran e-papierowy na koszu: logika stanów (tabela wyzwalaczy + priorytety),…, Kosz bez otwartego zgłoszenia i bez opróżnienia w ostatniej godzinie., state_of(), test_calm_then_confirm_after_press(), test_emptied_holds_60_minutes_then_calm(), test_enroute_when_stale_report_is_on_route_before_run() (+6 more)

### Community 72 - "rate.py"
Cohesion: 0.27
Nodes (10): login(), None, gdy się udało; inaczej komunikat do pokazania., Counter, Liczniki limitów (SMS, AI, logowanie) wspólne dla wszystkich workerów…, count(), hit(), Limity wspólne dla wszystkich workerów: liczniki w bazie (tabela Counter), okno…, Liczy zdarzenie i zwraca True, gdy mieści się w limicie; przy przekroczeniu nic… (+2 more)

### Community 73 - "parse"
Cohesion: 0.14
Nodes (10): buildTicks(), Fn(), getLabelAndValue(), getLabelForValue(), go(), ii(), parse(), parseArrayData() (+2 more)

### Community 74 - "k"
Cohesion: 0.22
Nodes (10): G(), Jt(), k(), me(), Oe(), Qt(), Se(), $t() (+2 more)

### Community 76 - "u"
Cohesion: 0.20
Nodes (5): addBox(), reset(), start(), u(), vn()

### Community 78 - "test_sms.py"
Cohesion: 0.23
Nodes (11): FakeOpener, routes: {fragment_adresu: (status, body) | Exception | callable(req) ->…, _Resp, fixture, register(), test_gateway_failure_503_or_demo_fallback(), test_limits_per_number(), test_twilio_send_and_check() (+3 more)

### Community 79 - "fairy_refresh"
Cohesion: 0.43
Nodes (7): fairy_get(), fairy_refresh(), Nowy raport. Przy błędzie API: komunikat + ostatni raport (nigdy 500)., is_fresh(), latest(), to_dict(), available()

### Community 80 - "ke"
Cohesion: 0.25
Nodes (8): Ae(), be(), Ie(), j(), ke(), ne(), Re(), s()

### Community 81 - "Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)"
Cohesion: 0.25
Nodes (7): 1. Uprawnienia, 2. Ekrany i nawigacja, 3. Wygląd, 4. Widoki i stany, 5. Zależności i infrastruktura, 6. Produkt i pokaz, Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)

### Community 82 - "test_zdjecia.py"
Cohesion: 0.22
Nodes (9): gps_from_exif(), (lat, lon) z EXIF zdjęcia albo None. Telefon z włączoną lokalizacją w aparacie…, demo(), jpeg_with_gps(), fixture, Zdjęcia z miasta: GPS z EXIF → najbliższy kosz (do 80 m), paczka wielu plików., JPEG 32×32 z GPSInfo w EXIF (tak zapisuje aparat telefonu z włączoną…, test_batch_upload_matches_nearest_bin_by_exif() (+1 more)

### Community 83 - "display_state"
Cohesion: 0.20
Nodes (10): epaper_keys(), Stan ekranu na koszu: state_key (pełne odświeżenie) i values_key (okno…, device_info(), display_state(), keys(), plural_people(), state_key zmienia się tylko przy pełnym odświeżeniu, values_key przy zmianie…, (state, data) dla renderera. `states`/`routes` można podać z zewnątrz, żeby nie… (+2 more)

### Community 84 - "osrm.py"
Cohesion: 0.29
Nodes (7): _fetch(), _load(), Przebieg tras po ulicach z OSRM, tylko do rysowania na mapie. Kilometry nadal…, coords: lista [lat, lon]. Zwraca (punkty linii [lat, lon], approx)., street_path(), test_no_network_falls_back_to_straight_line(), test_street_path_cached_after_first_fetch()

### Community 85 - "money"
Cohesion: 0.40
Nodes (5): _env_float(), money(), money_assumptions(), Przeliczenie wyniku porównania (4 tygodnie) na miesiąc, zł i CO₂ — wg jawnych…, test_money_uses_configurable_assumptions()

### Community 86 - "._createDescriptors"
Cohesion: 0.29
Nodes (4): fe(), ks(), nn(), sn

### Community 88 - "Wyniki po Fali 1 audytu i PWA kierowcy"
Cohesion: 0.40
Nodes (4): Lighthouse (lokalnie, Chromium headless, Lighthouse 13.5), Poziomy scroll, Pozycje audytu, Wyniki po Fali 1 audytu i PWA kierowcy

### Community 89 - "bi"
Cohesion: 0.50
Nodes (4): bi(), Pi(), Ti(), u()

### Community 90 - "si"
Cohesion: 0.67
Nodes (4): Je(), ni(), oi(), si()

### Community 91 - "ri"
Cohesion: 0.67
Nodes (3): ei(), ii(), ri()

### Community 97 - "Before/after comparison on same fill increments (4 weeks)"
Cohesion: 0.29
Nodes (7): Before/after 4 weeks section, 'Wrozka podpowiada' placeholder card, Before/after comparison on same fill increments (4 weeks), Bin overflow hours unchanged with fixed run times, Before/after comparison: fixed schedule vs Trash Fairy, Investment recommendations (compactor, bigger bin, shelter intervention), Stage 6: 'Wrozka podpowiada' report, Karnet, recommendations, jury mode

## Ambiguous Edges - Review These
- `psycopg[binary] 3.3.6` → `Real bin positions from OSM cached in data/*.geojson`  [AMBIGUOUS]
  DECYZJE.md · relation: conceptually_related_to

## Knowledge Gaps
- **129 isolated node(s):** `STATE_LABEL`, `ISSUES`, `STATE_LBL`, `DAYS`, `I` (+124 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `psycopg[binary] 3.3.6` and `Real bin positions from OSM cached in data/*.geojson`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `o()` connect `o` to `chart.umd.min.js`, `ns`, `k`, `u`, `an`, `va`, `ke`, `n`, `.isHorizontal`, `.getContext`, `ws`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `import_points()` connect `import_points` to `osm_import.py`, `test_forecast.py`, `test_zglos.py`, `now`, `reset`, `test_photos.py`, `test_fairy.py`, `test_ai_safety.py`, `test_zdjecia.py`, `comparison.py`, `state.py`, `traffic.py`, `models.py`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Why does `ns()` connect `ns` to `chart.umd.min.js`, `o`, `parse`, `Cs`, `va`, `n`, `.getContext`, `.buildOrUpdateControllers`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `o()` (e.g. with `ai()` and `da()`) actually correct?**
  _`o()` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `STATE_LABEL`, `ISSUES`, `STATE_LBL` to the rest of the system?**
  _129 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `chart.umd.min.js` be split into smaller, more focused modules?**
  _Cohesion score 0.031683168316831684 - nodes in this community are weakly interconnected._