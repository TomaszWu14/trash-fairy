# Graph Report - trash-fairy  (2026-10-03)

## Corpus Check
- 110 files · ~6,528,982 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1969 nodes · 5052 edges · 95 communities (87 shown, 8 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 298 edges (avg confidence: 0.64)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dc97f4f5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- chart.umd.min.js
- o
- page_context
- views.py
- conftest.py
- panel.js
- test_zglos.py
- 85% crossing time with in-hour interpolation, interval from p80/p20
- Reports and anti-spam rules (merge 15 min, reliability last 10, flag)
- Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js
- Before/after comparison on same fill increments (4 weeks)
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
- test_karnet.py
- test_residents.py
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
- fetch_osm.py
- reset
- no
- llm.py
- zt
- generate
- tn
- an
- .isHorizontal
- details
- .configure
- test_kierowca.py
- leaflet.js
- s
- .getContext
- database_url
- traffic.py
- kierowca/sw.js
- n
- da
- weather.py
- render
- va
- .bindResponsiveEvents
- update
- sms.py
- build.py
- jn
- e
- open_api.py
- .notifyPlugins
- .draw
- rate.py
- parse
- k
- rs
- test_auth.py
- fakes.py
- test_sms.py
- fairy_refresh
- ke
- Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)
- pytest
- app
- http.py
- money
- OR-Tools VRP, 1 vehicle per fleet, depot MPO Nowohucka 1, straight line x1.3
- jury_pool
- Wyniki po Fali 1 audytu i PWA kierowcy
- bi
- si
- ri
- logout

## God Nodes (most connected - your core abstractions)
1. `an()` - 61 edges
2. `va` - 56 edges
3. `ns()` - 55 edges
4. `o()` - 51 edges
5. `import_points()` - 50 edges
6. `now()` - 49 edges
7. `s()` - 49 edges
8. `point_states()` - 47 edges
9. `a()` - 44 edges
10. `l()` - 39 edges

## Surprising Connections (you probably didn't know these)
- `Soft press limit: 1 per 2 s per point, 120/h per IP, ProxyFix` --conceptually_related_to--> `Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report`  [INFERRED]
  DECYZJE.md → docs/KONCEPCJA.md
- `Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js` --semantically_similar_to--> `Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/KONCEPCJA.md
- `test_report_older_than_current_hour_is_not_fresh()` --calls--> `advance()`  [EXTRACTED]
  tests/test_fairy.py → app/clock.py
- `test_weather_changes_only_future_hours()` --calls--> `trajectory()`  [EXTRACTED]
  tests/test_weather.py → app/forecast.py
- `fake_create()` --indirect_call--> `_create()`  [INFERRED]
  tests/test_ai_safety.py → app/llm.py

## Import Cycles
- 3-file cycle: `app/__init__.py -> app/api.py -> app/rate.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/simulation.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/simulation.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/forecast.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/residents.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/osm_import.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/auth.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/epaper.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/fairy.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/reports.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/routes.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/sms.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/state.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/traffic.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/weather.py -> app/__init__.py`

## Hyperedges (group relationships)
- **Routing and before/after comparison** — decyzje_route_point_selection, decyzje_ortools_vrp, decyzje_before_after_comparison, decyzje_fixed_schedule_simulation, app_templates_panel_routes_section, app_templates_panel_compare_section [INFERRED 0.85]
- **Forecast pipeline: weekly profile + events -> 85% crossing -> MAE** — decyzje_weekly_profile, decyzje_event_multiplier, decyzje_crossing_85_interval, decyzje_mae_evaluation, decyzje_forecast_on_demand, docs_koncepcja_forecast [INFERRED 0.95]

## Communities (95 total, 8 thin omitted)

### Community 0 - "chart.umd.min.js"
Cohesion: 0.04
Nodes (39): afterUpdate(), at(), b(), Bt(), cn(), d(), destroy(), Di() (+31 more)

### Community 1 - "o"
Cohesion: 0.07
Nodes (56): a(), aa(), afterDatasetsUpdate(), ai(), ao(), As(), average(), Bi() (+48 more)

### Community 2 - "page_context"
Cohesion: 0.40
Nodes (5): assumptions(), page_context(), _pl(), [(obszar, założenie, wartość)] — wartości wprost z kodu., methodology()

### Community 3 - "views.py"
Cohesion: 0.11
Nodes (28): api_docs(), button(), crew(), driver(), driver_sw(), epaper_page(), health(), panel() (+20 more)

### Community 4 - "conftest.py"
Cohesion: 0.31
Nodes (8): random, cache(), client(), fixture, Klient zalogowany jako dyspozytor (zapisy, AI, Reset)., Mały, sztuczny odpowiednik data/*.geojson (bez sieci)., _scatter(), staff()

### Community 5 - "panel.js"
Cohesion: 0.10
Nodes (35): apply(), clockAction(), dec(), describe(), esc(), eventLayer, hhmm(), KIND (+27 more)

### Community 6 - "test_zglos.py"
Cohesion: 0.05
Nodes (35): _fetch(), _load(), coords: lista [lat, lon]. Zwraca (punkty linii [lat, lon], approx)., street_path(), neighbors_map(), demo(), press(), props() (+27 more)

### Community 7 - "85% crossing time with in-hour interpolation, interval from p80/p20"
Cohesion: 0.22
Nodes (11): Point details section with Chart.js chart, Decisions only by code rules, never AI, 85% crossing time with in-hour interpolation, interval from p80/p20, Panel shows system estimate, not simulation hidden truth, MAE 2.5 p.p. vs naive mean 7.3 p.p. on last week, no leakage, Route point selection: full now, crosses 85% before next run, or safety (bin 3 d, shelter 7 d), State = max(level, 100 x report reliability), Weekly 7x24 profile per point: mean and p20/p80 (+3 more)

### Community 8 - "Reports and anti-spam rules (merge 15 min, reliability last 10, flag)"
Cohesion: 0.33
Nodes (6): 'Sytuacja teraz' summary with press->report counter, Report accuracy decided by emptying (>=75%); reliability = accurate share of last 10, start 70%, Report table: presses merged within 15 min of first press, Main path: press -> state change -> to-empty list -> route -> AI report, Reports and anti-spam rules (merge 15 min, reliability last 10, flag), Test plan (~10 pytest tests, Claude mocked)

### Community 9 - "Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js"
Cohesion: 0.15
Nodes (13): Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js, 60 bins from Rynek/Plac Nowy, min 80 m apart, Forecast computed on demand with per-clock-hour profile cache, History stored in forecast table (source='sim'), Real bin positions from OSM cached in data/*.geojson, OSM tiles instead of CARTO, Polling every 2 s with version number, Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report (+5 more)

### Community 10 - "Before/after comparison on same fill increments (4 weeks)"
Cohesion: 0.18
Nodes (11): Before/after 4 weeks section, Demo clock header (advance +1 h, reset), Before/after comparison on same fill increments (4 weeks), Demo clock in DB with 24 h simulated future and +1 h advance, Fill rate from surroundings (1.5%/h + venues + stops, cap 8%/h), Simulation with fixed MPO schedule (6:00/14:00, shelters every 3 days), Bin overflow hours unchanged with fixed run times, Before/after comparison: fixed schedule vs Trash Fairy (+3 more)

### Community 11 - "Trash Fairy README"
Cohesion: 0.20
Nodes (11): Staged work process with ROADMAPA/DECYZJE, Trash Fairy work rules (CLAUDE.md), Decision log (DECYZJE.md), Competition: Mr Fill, Wroclaw/Sierpc/Rzeszow sensors, Trash Fairy concept (KONCEPCJA.md), Hardware-agnostic brain for MPO, Out of scope list (section 16), Problem: Krakow street bins overflow on fixed MPO schedule (+3 more)

### Community 12 - "Brainstorm: przycisk dla mieszkańców, awarie, spam, wyświetlacz, program „Przyjaciele Wróżki”"
Cohesion: 0.22
Nodes (8): A. Cel i zakres, B. Fizyczny przycisk: sprzęt i awarie, Brainstorm: przycisk dla mieszkańców, awarie, spam, wyświetlacz, program „Przyjaciele Wróżki”, C. Wyświetlacz, D. Spam i nadużycia, E. Program dla mieszkańców: rejestracja, F. Nagrody i pieniądze, G. Prawo, RODO, ryzyka

### Community 13 - "AI role: Vision, event parsing, 'Wrozka podpowiada' report"
Cohesion: 0.28
Nodes (9): 'Wrozka podpowiada' placeholder card, app/llm.py gateway (ask, ask_json), AI role: Vision, event parsing, 'Wrozka podpowiada' report, Events from Karnet Krakow via Claude + Nominatim, Photo analysis JSON schema (fill_level, misuse, damage, confidence), Shelter -> bin rule (200 m, 48 h), Causal chain: overflowing shelter -> household bags in street bins, Stage 5: Claude Vision crew view, misuse, shelter->bin rule (+1 more)

### Community 14 - "Events from data/events.json with crowd-scale multiplier (200m x1.3 / 400m x1.6 / 800m x2.0)"
Cohesion: 0.20
Nodes (10): Dispatcher panel template (panel.html), Point list (text alternative to map) and legend, Flag 'check button' (<40% accurate in 7 days or 6 h overflow without press), Events from data/events.json with crowd-scale multiplier (200m x1.3 / 400m x1.6 / 800m x2.0), Soft press limit: 1 per 2 s per point, 120/h per IP, ProxyFix, 24 h plan and cut order, Screens: dispatcher panel, point details, virtual button, jury mode, crew view, methodology, Style: Planty green + gold panel, magic violet/pink for AI and button (+2 more)

### Community 15 - "test_photos.py"
Cohesion: 0.09
Nodes (33): household_bag_links(), latest_analyses(), misuse_overview(), overflowing_shelters(), Nadużycia i powiązanie altana → kosz (koncepcja, sekcja 6.5) — reguły w kodzie.…, {point_id: (ostatnia analiza dowolna, ostatnia udana)} z okna 48 h przed `now`., {shelter_id: najwyższy szacunek} dla altan przepełnionych wg prognozy w…, [(bin, shelter)] dla worków domowych w promieniu 200 m od przepełnionej altany. (+25 more)

### Community 16 - "test_fairy.py"
Cohesion: 0.18
Nodes (14): (typ, etykieta, uzasadnienie, efekt) albo None — reguły z tabeli w sekcji 6.8., recommend(), demo(), model(), fixture, stats(), test_bigger_bin_between_20_and_50_percent_days(), test_compactor_when_overflowing_most_days_despite_twice_daily() (+6 more)

### Community 17 - "api.py"
Cohesion: 0.05
Nodes (82): _accuracy_m(), _analysis(), changes(), clock_advance(), clock_reset(), comparison(), current_resident(), device_selftest() (+74 more)

### Community 18 - "Kontekst MPO: dane do pitchu i porównania"
Cohesion: 0.50
Nodes (3): Harmonogram oczyszczania 08/2026 (arkusz „Kosze”), Jak działa MPO (informacja ogólna MPO Kraków), Kontekst MPO: dane do pitchu i porównania

### Community 19 - "Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)"
Cohesion: 0.33
Nodes (5): Cel, Poza zakresem (ROADMAPA), Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A), Testy, Zakres (wariant A)

### Community 20 - "pokaz.js"
Cohesion: 0.09
Nodes (38): apply(), atRisk(), CAPTION, clockAction(), cluster, DAYS, dur(), esc() (+30 more)

### Community 21 - "test_karnet.py"
Cohesion: 0.15
Nodes (17): fetch(), _first(), import_events(), in_demo(), parse_list(), Pobiera listy wydarzeń (grzecznie, z opóźnieniem) i zapisuje do cache. Zwraca…, Zastępuje wydarzenia z Karnetu (source='karnet') wydarzeniami z obszaru demo w…, [{id, name, lat, lon, type, location, start, end, text, url}] z HTML listy… (+9 more)

### Community 22 - "test_residents.py"
Cohesion: 0.07
Nodes (52): PointAward, Press, Uczestnik programu „Przyjaciele Wróżki”. Bez danych osobowych: pseudonim + hash…, Punkty za trafne zgłoszenie (jedna nagroda na mieszkańca, punkt i dzień)., Pojedyncze naciśnięcie przycisku. Scalanie w zgłoszenia: app/reports.py., Zgłoszenie: naciśnięcia jednego punktu w oknie 15 minut od pierwszego…, Report, Resident (+44 more)

### Community 23 - "state.py"
Cohesion: 0.06
Nodes (68): device_info(), display_state(), keys(), plural_people(), Stan wyświetlacza e-papierowego na koszu (docs/epapier/HANDOFF.md): wyzwalacze,…, state_key zmienia się tylko przy pełnym odświeżeniu, values_key przy zmianie…, (state, data) dla renderera. `states`/`routes` można podać z zewnątrz, żeby nie…, _when() (+60 more)

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
Nodes (52): cleanup_photos_command(), karnet_command(), Import punktów z data/*.geojson i wydarzeń z data/events.json, symulacja…, Usuwa pliki zdjęć starszych niż 7 dni (wyniki analiz zostają w bazie). Do crona., Pobiera wydarzenia z Karnet Kraków do data/karnet.json, importuje je i odtwarza…, seed_command(), Zegar demo: zamrożona sobota 13:30, przewijany o godzinę. Przewinięcie…, import_events() (+44 more)

### Community 32 - "renderer/epaper_render.py"
Cohesion: 0.23
Nodes (14): _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3…, 168×168: obrys 3 px, biała ramka 8 px, kod wpisany w 152 px., Wycinek okna PARTIAL (752×88) do odświeżenia częściowego. (+6 more)

### Community 33 - "kierowca.js"
Cohesion: 0.14
Nodes (33): act(), commit(), count(), cur(), DAYS, dec(), drawMap(), esc() (+25 more)

### Community 34 - "import_points"
Cohesion: 0.06
Nodes (66): compare(), fixed_selects(), following_run(), is_run(), Porównanie „przed i po” (koncepcja, sekcja 6.7): stały harmonogram MPO kontra…, Zwraca miary jednej polityki. `incs[pid][i]` = prawdziwy przyrost w godzinie…, Miary obu polityk na `weeks` tygodniach przed `cutoff` (pełna godzina)., run_policy() (+58 more)

### Community 35 - "ns"
Cohesion: 0.05
Nodes (9): bn(), initialize(), labelColor(), labelPointStyle(), ns(), pn(), rt(), updateRangeFromParsed() (+1 more)

### Community 36 - "test_forecast.py"
Cohesion: 0.12
Nodes (36): events_near(), multiplier(), Mnożnik najsilniejszego wydarzenia w promieniu, aktywnego w godzinie `at` albo…, build_profiles(), first_crossing(), forecast_quality(), point_forecasts(), point_series() (+28 more)

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
Cohesion: 0.24
Nodes (7): Audyt UX: zrzuty każdego ekranu na 6 szerokościach + konsola, poziomy scroll,…, classify(), main(), Pobiera punkty z OSM (Overpass API) dla obszaru demo i zapisuje cache do…, to_feature(), sys, urllib_parse

### Community 41 - "reset"
Cohesion: 0.12
Nodes (16): advance(), Odtwarza symulację od zera i cofa zegar do startu scenariusza (kasuje…, reset(), Reset scenariusza: usuwa analizy (i pliki), dodaje gotowe analizy przy koszach…, seed_demo(), demo(), fixture, demo() (+8 more)

### Community 42 - "no"
Cohesion: 0.06
Nodes (18): beforeLayout(), buildLookupTable(), ei(), En, Fo(), _generate(), getDecimalForValue(), _getTimestampsForTable() (+10 more)

### Community 43 - "llm.py"
Cohesion: 0.17
Nodes (16): ask(), ask_json(), _create(), image_block(), LLMError, model(), Exception, Jedyna brama do AI (CLAUDE.md): ask() i ask_json(). Model i klucz z env. AI… (+8 more)

### Community 44 - "zt"
Cohesion: 0.06
Nodes (11): ce(), color(), de, Ft(), he(), It(), qs(), te() (+3 more)

### Community 45 - "generate"
Cohesion: 0.20
Nodes (10): generate(), Liczby z tekstu raportu, których nie ma w faktach (np. 16:11 → „16” i „11”…, Nowy raport albo LLMError (wtedy wywołujący pokazuje ostatni zapisany)., unknown_numbers(), fence(), Opakowuje treść zewnętrzną w ogranicznik; tag zamykający w środku jest…, test_ai_text_with_script_is_escaped(), test_fence_neutralises_closing_tag_and_truncates() (+2 more)

### Community 46 - "tn"
Cohesion: 0.07
Nodes (8): addElements(), Cs, fe(), ks(), nn(), os(), sn, tn

### Community 47 - "an"
Cohesion: 0.09
Nodes (4): an(), Mn(), onClick(), reset()

### Community 48 - ".isHorizontal"
Cohesion: 0.09
Nodes (11): Ae(), ba, Ee(), la(), Le(), Oi(), Si(), tt() (+3 more)

### Community 49 - "details"
Cohesion: 0.22
Nodes (11): default_details(), details(), Jawne reguły, gdy AI niedostępne: festiwale/koncerty średni tłum, wystawy i…, (szczegóły, źródło): z Claude albo z reguł domyślnych (przy braku klucza lub…, fake_create(), parametrize, Atrapa llm._create: zapamiętuje system i treść, zwraca przygotowaną odpowiedź…, test_external_text_is_fenced_and_system_forbids_instructions() (+3 more)

### Community 50 - ".configure"
Cohesion: 0.07
Nodes (13): addBox(), beforeUpdate(), bo, configure(), determineDataLimits(), et(), getValueForPixel(), j() (+5 more)

### Community 51 - "test_kierowca.py"
Cohesion: 0.29
Nodes (4): demo(), fixture, test_driver_pwa_page_sw_and_manifest(), test_stop_issue_flags_point_until_emptying()

### Community 52 - "leaflet.js"
Cohesion: 0.07
Nodes (7): a(), Ci(), l(), Le(), Mi(), x(), zi()

### Community 53 - "s"
Cohesion: 0.14
Nodes (19): ca(), _calculateBarIndexPixels(), _calculateBarValuePixels(), draw(), getBasePixel(), getLabelAndValue(), getLabelForValue(), getPixelForTick() (+11 more)

### Community 54 - ".getContext"
Cohesion: 0.12
Nodes (3): Ci(), eo(), ls

### Community 55 - "database_url"
Cohesion: 0.60
Nodes (4): database_url(), DATABASE_URL z env; Coolify/Heroku podają postgres(ql)://, a my używamy…, test_database_url_defaults_to_sqlite(), test_database_url_uses_psycopg3_for_postgres()

### Community 56 - "traffic.py"
Cohesion: 0.16
Nodes (23): routes(), city_ratio(), conditions(), data(), delay_min(), drive_min(), fresh_samples(), _load_cache() (+15 more)

### Community 58 - "n"
Cohesion: 0.11
Nodes (13): Be(), Do(), Fn(), getMaxOverflow(), n(), ne(), numeric(), Oe() (+5 more)

### Community 59 - "da"
Cohesion: 0.10
Nodes (13): beforeDatasetDraw(), beforeDatasetsDraw(), beforeDraw(), da(), ea(), ha, Ie(), na() (+5 more)

### Community 60 - "weather.py"
Cohesion: 0.17
Nodes (19): conditions(), data(), factor(), factor_at(), _fetch(), _load_cache(), Pogoda z Open-Meteo (bez klucza) jako mnożnik tempa zapełniania w prognozie.…, {"fetched_at", "hours": {"2026-10-03T13:00": {"temp", "rain", "code"}}} albo… (+11 more)

### Community 61 - "render"
Cohesion: 0.16
Nodes (18): _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3…, 168×168: obrys 3 px, biała ramka 8 px, kod wpisany w 152 px., Wycinek okna PARTIAL (752×88) do odświeżenia częściowego. (+10 more)

### Community 63 - ".bindResponsiveEvents"
Cohesion: 0.14
Nodes (10): ct(), dt(), fs(), ge(), gs(), ms(), ps(), vs() (+2 more)

### Community 64 - "update"
Cohesion: 0.18
Nodes (14): es(), f(), g(), generateLabels(), ki(), m(), p(), Qi() (+6 more)

### Community 65 - "sms.py"
Cohesion: 0.21
Nodes (14): config(), Ustawienie integracji: najpierw config aplikacji (testy je zerują), potem…, _auth(), check_code(), configured(), Exception, Kod SMS przy rejestracji w programie „Przyjaciele Wróżki”: Twilio Verify przez…, Każda próba wysyłki liczy się do limitu, także nieudana: bramka i tak mogła… (+6 more)

### Community 66 - "build.py"
Cohesion: 0.19
Nodes (11): Kształt stanu wypełniony `fill`, znak w kolorze `glyph`. s = bok w px., _shape(), login(), dist(), geom_d(), P(), path_d(), route() (+3 more)

### Community 68 - "e"
Cohesion: 0.22
Nodes (14): at(), d(), e(), F(), hi(), m(), p(), q() (+6 more)

### Community 69 - "open_api.py"
Cohesion: 0.28
Nodes (12): after_request, conditions(), Pogoda (mnożnik prognozy) i ruch (mnożnik czasu przejazdu) — panel i…, _bin(), bin_detail(), bins(), conditions_view(), cors() (+4 more)

### Community 72 - "rate.py"
Cohesion: 0.27
Nodes (10): login(), None, gdy się udało; inaczej komunikat do pokazania., Counter, Liczniki limitów (SMS, AI, logowanie) wspólne dla wszystkich workerów…, count(), hit(), Limity wspólne dla wszystkich workerów: liczniki w bazie (tabela Counter), okno…, Liczy zdarzenie i zwraca True, gdy mieści się w limicie; przy przekroczeniu nic… (+2 more)

### Community 73 - "parse"
Cohesion: 0.20
Nodes (5): buildTicks(), go(), init(), parse(), po()

### Community 74 - "k"
Cohesion: 0.22
Nodes (10): G(), Jt(), k(), me(), Oe(), Qt(), Se(), $t() (+2 more)

### Community 76 - "test_auth.py"
Cohesion: 0.39
Nodes (7): login(), test_dispatcher_only_endpoints(), test_driver_only_own_fleet(), test_login_disabled_without_password(), test_login_rate_limit_after_five_failures(), test_login_roles_and_bad_password(), test_public_view_hides_dispatcher_fields()

### Community 77 - "fakes.py"
Cohesion: 0.28
Nodes (5): FakeOpener, Fałszywy opener dla app/http.py: odpowiedzi po fragmencie adresu, zapis…, routes: {fragment_adresu: (status, body) | Exception | callable(req) ->…, _Resp, urllib_error

### Community 78 - "test_sms.py"
Cohesion: 0.47
Nodes (8): fixture, register(), test_gateway_failure_503_or_demo_fallback(), test_limits_per_number(), test_twilio_send_and_check(), test_without_gateway_demo_code_on_screen(), test_wrong_code_and_retry_for_unverified_number(), twilio()

### Community 79 - "fairy_refresh"
Cohesion: 0.36
Nodes (8): fairy_get(), fairy_refresh(), Nowy raport. Przy błędzie API: komunikat + ostatni raport (nigdy 500)., is_fresh(), latest(), to_dict(), available(), test_fairy_report_rejects_extra_fields_and_keeps_previous()

### Community 80 - "ke"
Cohesion: 0.25
Nodes (8): Ae(), be(), Ie(), j(), ke(), ne(), Re(), s()

### Community 81 - "Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)"
Cohesion: 0.25
Nodes (7): 1. Uprawnienia, 2. Ekrany i nawigacja, 3. Wygląd, 4. Widoki i stany, 5. Zależności i infrastruktura, 6. Produkt i pokaz, Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)

### Community 82 - "pytest"
Cohesion: 0.25
Nodes (3): pytest, demo(), fixture

### Community 83 - "app"
Cohesion: 0.33
Nodes (6): clear_cache(), clear_cache(), Profile zależą od zawartości bazy — czyścimy po każdej nowej symulacji lub…, clear_cache(), Po resecie demo i między testami: wersja danych może się powtórzyć na nowej…, app()

### Community 84 - "http.py"
Cohesion: 0.47
Nodes (5): get_json(), post_form(), Wspólny klient HTTP integracji (Open-Meteo, TomTom, Twilio): urllib ze stdlib,…, (status, json). Błąd HTTP z treścią JSON (np. Twilio 400/429) zwracamy jako…, _send()

### Community 85 - "money"
Cohesion: 0.40
Nodes (5): _env_float(), money(), money_assumptions(), Przeliczenie wyniku porównania (4 tygodnie) na miesiąc, zł i CO₂ — wg jawnych…, test_money_uses_configurable_assumptions()

### Community 86 - "OR-Tools VRP, 1 vehicle per fleet, depot MPO Nowohucka 1, straight line x1.3"
Cohesion: 0.50
Nodes (5): Routes for next run section, OR-Tools VRP, 1 vehicle per fleet, depot MPO Nowohucka 1, straight line x1.3, Routes: two fleets, runs 6:00/14:00, OR-Tools VRP, ortools 9.15, OSRM, multiple vehicles per fleet, time windows

### Community 87 - "jury_pool"
Cohesion: 0.40
Nodes (5): jury(), jury_pool(), Kod QR w panelu prowadzi tutaj: losowy kosz przy Rynku, żeby jury naciskało…, start_url PWA bez kosza: wybór kosza (najbliższe wg GPS w JS, zapas: pula przy…, report_pick()

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

## Ambiguous Edges - Review These
- `psycopg[binary] 3.3.6` → `Real bin positions from OSM cached in data/*.geojson`  [AMBIGUOUS]
  DECYZJE.md · relation: conceptually_related_to

## Knowledge Gaps
- **129 isolated node(s):** `STATE_LABEL`, `ISSUES`, `STATE_LBL`, `DAYS`, `I` (+124 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `psycopg[binary] 3.3.6` and `Real bin positions from OSM cached in data/*.geojson`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `ns()` connect `ns` to `chart.umd.min.js`, `o`, `.draw`, `parse`, `no`, `tn`, `an`, `s`, `.getContext`, `n`, `va`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `import_points()` connect `import_points` to `test_forecast.py`, `test_zglos.py`, `reset`, `test_auth.py`, `test_photos.py`, `test_fairy.py`, `pytest`, `test_kierowca.py`, `test_residents.py`, `state.py`, `traffic.py`, `models.py`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Why does `an()` connect `an` to `chart.umd.min.js`, `update`, `o`, `.notifyPlugins`, `zt`, `.configure`, `.getContext`, `da`, `.bindResponsiveEvents`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `o()` (e.g. with `ai()` and `da()`) actually correct?**
  _`o()` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `STATE_LABEL`, `ISSUES`, `STATE_LBL` to the rest of the system?**
  _129 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `chart.umd.min.js` be split into smaller, more focused modules?**
  _Cohesion score 0.03833943833943834 - nodes in this community are weakly interconnected._