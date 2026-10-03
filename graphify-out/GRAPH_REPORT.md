# Graph Report - trash-fairy  (2026-10-03)

## Corpus Check
- 81 files · ~3,324,025 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 982 nodes · 2300 edges · 58 communities (55 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 88 edges (avg confidence: 0.81)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e6669cd4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- residents.py
- import_points
- state.py
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
- point_states
- zglos.js
- Audyt UX / UI / funkcjonalności – Trash Fairy (Etap 2)
- Trash Fairy – wdrożenie ekranu „Zgłoś kosz” (PWA dla mieszkańców)
- Etap 1 – rozpoznanie (bez zmian w kodzie)
- Trash Fairy – wdrożenie widoku C „Pokaz dla jury”
- queue.js
- sw.js
- models.py
- build.py
- kierowca.js
- test_routes.py
- test_epapier.py
- test_forecast.py
- Trash Fairy – wyświetlacz e-papierowy na koszu (800×480)
- E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware)
- epapier.js
- osrm.py
- reset
- osm_import.py
- llm.py
- __init__.py
- generate
- epaper.py
- test_api.py
- simulation.py
- details
- reports.py
- test_kierowca.py
- karnet_command
- gps_from_exif
- unittest_mock
- database_url
- ask
- kierowca/sw.js

## God Nodes (most connected - your core abstractions)
1. `import_points()` - 44 edges
2. `now()` - 42 edges
3. `point_states()` - 40 edges
4. `Point` - 35 edges
5. `record_press()` - 32 edges
6. `simulate()` - 29 edges
7. `distance_m()` - 28 edges
8. `Emptying` - 27 edges
9. `reset()` - 22 edges
10. `hour_floor()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Point details section with Chart.js chart` --implements--> `85% crossing time with in-hour interpolation, interval from p80/p20`  [INFERRED]
  app/templates/panel.html → DECYZJE.md
- `Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js` --semantically_similar_to--> `Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/KONCEPCJA.md
- `test_events_near_uses_scale_radius()` --calls--> `events_near()`  [EXTRACTED]
  tests/test_forecast.py → app/events.py
- `fake_create()` --indirect_call--> `_create()`  [INFERRED]
  tests/test_ai_safety.py → app/llm.py
- `test_import_is_idempotent()` --calls--> `import_points()`  [EXTRACTED]
  tests/test_import.py → app/osm_import.py

## Import Cycles
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/osm_import.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/reports.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/forecast.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/routes.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/residents.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/karnet.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/epaper.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/fairy.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/simulation.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/state.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/simulation.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api.py -> app/simulation.py -> app/osm_import.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/cli.py -> app/simulation.py -> app/osm_import.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api.py -> app/clock.py -> app/reports.py -> app/__init__.py`

## Hyperedges (group relationships)
- **Main path: press -> report merge -> state -> route** — app_templates_przycisk_press_click_handler, decyzje_report_table_merging, decyzje_report_accuracy_reliability, decyzje_state_max_rule, decyzje_route_point_selection, docs_koncepcja_main_path [INFERRED 0.85]
- **Routing and before/after comparison** — decyzje_route_point_selection, decyzje_ortools_vrp, decyzje_before_after_comparison, decyzje_fixed_schedule_simulation, app_templates_panel_routes_section, app_templates_panel_compare_section [INFERRED 0.85]
- **Forecast pipeline: weekly profile + events -> 85% crossing -> MAE** — decyzje_weekly_profile, decyzje_event_multiplier, decyzje_crossing_85_interval, decyzje_mae_evaluation, decyzje_forecast_on_demand, docs_koncepcja_forecast [INFERRED 0.95]

## Communities (58 total, 3 thin omitted)

### Community 0 - "residents.py"
Cohesion: 0.13
Nodes (24): Device, PointAward, Press, Uczestnik programu „Przyjaciele Wróżki”. Bez danych osobowych: pseudonim + hash…, Punkty za trafne zgłoszenie (jedna nagroda na mieszkańca, punkt i dzień)., Fizyczny przycisk z wyświetlaczem e-papierowym przy punkcie (stan symulowany w…, Pojedyncze naciśnięcie przycisku. Scalanie w zgłoszenia: app/reports.py., Resident (+16 more)

### Community 1 - "import_points"
Cohesion: 0.17
Nodes (21): import_points(), Zastępuje punkty w bazie: 60 koszy (Rynek, Kazimierz, kilka przy przeciążonych…, Dwa najspokojniejsze kosze na Kazimierzu („przy szkole”) — ktoś naciska je dla…, Zastępuje całą symulację (poziomy, opróżnienia, naciśnięcia, zgłoszenia)., simulate(), trolled_ids(), demo(), fixture (+13 more)

### Community 2 - "state.py"
Cohesion: 0.12
Nodes (28): compare(), Porównanie „przed i po” (koncepcja, sekcja 6.7): stały harmonogram MPO kontra…, Miary obu polityk na `weeks` tygodniach przed `cutoff` (pełna godzina)., events_near(), build_profiles(), _cell(), point_forecasts(), point_series() (+20 more)

### Community 3 - "views.py"
Cohesion: 0.07
Nodes (48): _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3…, 168×168: obrys 3 px, biała ramka 8 px, kod wpisany w 152 px., Wycinek okna PARTIAL (752×88) do odświeżenia częściowego. (+40 more)

### Community 4 - "conftest.py"
Cohesion: 0.24
Nodes (10): clear_cache(), clear_cache(), Profile zależą od zawartości bazy — czyścimy po każdej nowej symulacji lub…, random, app(), cache(), client(), fixture (+2 more)

### Community 5 - "panel.js"
Cohesion: 0.11
Nodes (31): apply(), clockAction(), describe(), esc(), eventLayer, hhmm(), KIND, linkLayer (+23 more)

### Community 6 - "test_zglos.py"
Cohesion: 0.20
Nodes (10): neighbors_map(), press(), Publiczny ekran „Zgłoś kosz”: dane bez wiarygodności, stany odpowiedzi API,…, test_damaged_does_not_raise_level_but_flags_point(), test_nosignal_flag_and_member_in_public_payload(), test_overflow_counts_as_full_and_is_noted(), test_press_distance_allows_gps_accuracy_but_caps_it(), test_press_returns_accepted_then_merged() (+2 more)

### Community 7 - "85% crossing time with in-hour interpolation, interval from p80/p20"
Cohesion: 0.17
Nodes (15): Routes for next run section, Decisions only by code rules, never AI, 85% crossing time with in-hour interpolation, interval from p80/p20, Panel shows system estimate, not simulation hidden truth, MAE 2.5 p.p. vs naive mean 7.3 p.p. on last week, no leakage, OR-Tools VRP, 1 vehicle per fleet, depot MPO Nowohucka 1, straight line x1.3, Route point selection: full now, crosses 85% before next run, or safety (bin 3 d, shelter 7 d), State = max(level, 100 x report reliability) (+7 more)

### Community 8 - "Reports and anti-spam rules (merge 15 min, reliability last 10, flag)"
Cohesion: 0.24
Nodes (9): 'Sytuacja teraz' summary with press->report counter, Press click handler (POST /api/press), Flag 'check button' (<40% accurate in 7 days or 6 h overflow without press), Report accuracy decided by emptying (>=75%); reliability = accurate share of last 10, start 70%, Report table: presses merged within 15 min of first press, Soft press limit: 1 per 2 s per point, 120/h per IP, ProxyFix, Main path: press -> state change -> to-empty list -> route -> AI report, Reports and anti-spam rules (merge 15 min, reliability last 10, flag) (+1 more)

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
Cohesion: 0.22
Nodes (10): Dispatcher panel template (panel.html), Point details section with Chart.js chart, Point list (text alternative to map) and legend, Virtual button page (przycisk.html), Events from data/events.json with crowd-scale multiplier (200m x1.3 / 400m x1.6 / 800m x2.0), 24 h plan and cut order, Screens: dispatcher panel, point details, virtual button, jury mode, crew view, methodology, Style: Planty green + gold panel, magic violet/pink for AI and button (+2 more)

### Community 15 - "test_photos.py"
Cohesion: 0.12
Nodes (24): household_bag_links(), latest_analyses(), misuse_overview(), {point_id: (ostatnia analiza dowolna, ostatnia udana)} z okna 48 h przed `now`., [(bin, shelter)] dla worków domowych w promieniu 200 m od przepełnionej altany., Wszystko, czego potrzebuje panel: plakietki nadużyć, flagi rozbieżności, linie…, cleanup(), discrepancy() (+16 more)

### Community 16 - "test_fairy.py"
Cohesion: 0.13
Nodes (19): _env_float(), money(), money_assumptions(), Przeliczenie wyniku porównania (4 tygodnie) na miesiąc, zł i CO₂ — wg jawnych…, (typ, etykieta, uzasadnienie, efekt) albo None — reguły z tabeli w sekcji 6.8., recommend(), demo(), model() (+11 more)

### Community 17 - "api.py"
Cohesion: 0.06
Nodes (77): _accuracy_m(), _analysis(), changes(), clock_advance(), clock_reset(), comparison(), current_resident(), device_selftest() (+69 more)

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
Cohesion: 0.17
Nodes (15): _first(), import_events(), in_demo(), parse_list(), Zastępuje wydarzenia z Karnetu (source='karnet') wydarzeniami z obszaru demo w…, [{id, name, lat, lon, type, location, start, end, text, url}] z HTML listy…, _text(), no_ai() (+7 more)

### Community 22 - "test_residents.py"
Cohesion: 0.14
Nodes (25): Emptying, Opróżnienie punktu przez ekipę MPO, z poziomem zastanym przed opróżnieniem., is_hit(), Opróżnienie rozstrzyga otwarte zgłoszenia punktu: poziom >= 75% → trafne,…, resolve_reports(), effective_weight(), Czy ten przycisk ma ≥3 fałszywe zgłoszenia o tej samej godzinie (±1 h) w…, Waga zgłoszenia po regułach antyspamowych (potwierdzone przez mieszkańca nie są… (+17 more)

### Community 23 - "point_states"
Cohesion: 0.14
Nodes (23): low_reliability(), Flaga „sprawdź przycisk”: < 40% trafnych wśród zgłoszeń z 7 dni (min. 3…, forecast_reason(), level_state(), point_states(), {point_id: dict ze stanem} dla chwili `now` zegara demo., Sygnał zgłoszenia w %; zgłoszenie tuż po opróżnieniu przy niskim poziomie liczy…, report_signal() (+15 more)

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
Cohesion: 0.13
Nodes (25): Zegar demo: zamrożona sobota 13:30, przewijany o godzinę. Przewinięcie…, import_events(), Wydarzenia i mnożnik tłumu (koncepcja, sekcje 6.3–6.4). Etap 3: ręczna lista…, Raport „Wróżka podpowiada” (koncepcja, sekcja 8): fakty liczy kod, Claude tylko…, Wydarzenia z Karnet Kraków (koncepcja, sekcja 6.4). Publicznego API brak —…, Nadużycia i powiązanie altana → kosz (koncepcja, sekcja 6.5) — reguły w kodzie.…, Event, FairyReport (+17 more)

### Community 32 - "build.py"
Cohesion: 0.11
Nodes (25): Kształt stanu wypełniony `fill`, znak w kolorze `glyph`. s = bok w px., _shape(), _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3… (+17 more)

### Community 33 - "kierowca.js"
Cohesion: 0.14
Nodes (33): act(), commit(), count(), cur(), DAYS, dec(), drawMap(), esc() (+25 more)

### Community 34 - "test_routes.py"
Cohesion: 0.15
Nodes (22): fixed_selects(), following_run(), is_run(), Zwraca miary jednej polityki. `incs[pid][i]` = prawdziwy przyrost w godzinie…, run_policy(), plan_routes(), Powód wzięcia punktu na kurs `run_at` albo None. Reguły, nie AI (koncepcja,…, coords[0] = baza. Zwraca (kolejność indeksów punktów 1..n-1, metry). Wynik… (+14 more)

### Community 35 - "test_epapier.py"
Cohesion: 0.30
Nodes (15): Zapisuje naciśnięcie i dolicza je do otwartego zgłoszenia z ostatnich 15 min…, record_press(), calm_bin(), Ekran e-papierowy na koszu: logika stanów (tabela wyzwalaczy + priorytety),…, Kosz bez otwartego zgłoszenia i bez opróżnienia w ostatniej godzinie., state_of(), test_calm_then_confirm_after_press(), test_emptied_holds_60_minutes_then_calm() (+7 more)

### Community 36 - "test_forecast.py"
Cohesion: 0.16
Nodes (21): first_crossing(), forecast_quality(), Chwila przekroczenia progu (interpolacja w obrębie godziny) w trajektorii…, MAE (p.p.) prognozy na ostatnim tygodniu przed `cutoff`, z profilem uczonym na…, Godzina po godzinie [(at, est, low, high)]. Do `now` zerujemy na opróżnieniach,…, trajectory(), Forecast, Szereg czasowy poziomu zapełnienia punktu. source='sim' — symulacja (historia +… (+13 more)

### Community 37 - "Trash Fairy – wyświetlacz e-papierowy na koszu (800×480)"
Cohesion: 0.22
Nodes (8): Dane wejściowe renderera, Etap 1 – symulator do pokazu (zalecany na hackathon), Etap 2 – prawdziwe urządzenie (kontrakt, bez implementacji firmware), Kryteria odbioru, Siatka (px, stałe – nie zmieniać między stanami), Stany i wyzwalacze, Trash Fairy – wyświetlacz e-papierowy na koszu (800×480), Zawartość paczki

### Community 38 - "E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware)"
Cohesion: 0.29
Nodes (6): Co jeszcze przed pilotażem, Dlaczego urządzenie renderuje samo, Downlink (port 10, ≤ 12 B), E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware), QR na urządzeniu, Uplink

### Community 39 - "epapier.js"
Cohesion: 0.67
Nodes (5): fullRefresh(), log(), poll(), STATE_LABEL, swapFull()

### Community 40 - "osrm.py"
Cohesion: 0.12
Nodes (16): _fetch(), _load(), Przebieg tras po ulicach z OSRM, tylko do rysowania na mapie. Kilometry nadal…, coords: lista [lat, lon]. Zwraca (punkty linii [lat, lon], approx)., street_path(), Audyt UX: zrzuty każdego ekranu na 6 szerokościach + konsola, poziomy scroll,…, classify(), main() (+8 more)

### Community 41 - "reset"
Cohesion: 0.13
Nodes (17): advance(), Odtwarza symulację od zera i cofa zegar do startu scenariusza (kasuje…, reset(), DemoClock, Zegar scenariusza demo (jeden wiersz). W bazie, bo gunicorn ma kilka procesów., demo(), fixture, demo() (+9 more)

### Community 42 - "osm_import.py"
Cohesion: 0.22
Nodes (13): distance_m(), Odległość w linii prostej (haversine), w metrach., bin_rate(), Import punktów demo z cache OSM (data/*.geojson) do bazy., Bierze do n punktów najbliżej centre, pomijając te bliżej niż min_gap_m od już…, Tempo zapełniania kosza (%/h) z liczby lokali i przystanków w promieniu 100 m., select_spaced(), test_bin_rate_grows_with_nearby_pois_and_is_capped() (+5 more)

### Community 43 - "llm.py"
Cohesion: 0.19
Nodes (15): ask_json(), available(), _create(), image_block(), LLMError, model(), Exception, Jedyna brama do AI (CLAUDE.md): ask() i ask_json(). Model i klucz z env. AI… (+7 more)

### Community 44 - "__init__.py"
Cohesion: 0.21
Nodes (12): cleanup_photos_command(), Import punktów z data/*.geojson i wydarzeń z data/events.json, symulacja…, Usuwa pliki zdjęć starszych niż 7 dni (wyniki analiz zostają w bazie). Do crona., seed_command(), _add_missing_columns(), create_app(), Bez Alembica: dokładamy nowe, opcjonalne kolumny do istniejącej bazy (np.…, load_cache() (+4 more)

### Community 45 - "generate"
Cohesion: 0.15
Nodes (13): build_facts(), generate(), Wszystkie liczby do raportu — liczone w kodzie, nie przez model., Liczby z tekstu raportu, których nie ma w faktach (np. 16:11 → „16” i „11”…, Nowy raport albo LLMError (wtedy wywołujący pokazuje ostatni zapisany)., unknown_numbers(), fence(), Opakowuje treść zewnętrzną w ogranicznik; tag zamykający w środku jest… (+5 more)

### Community 46 - "epaper.py"
Cohesion: 0.21
Nodes (11): device_info(), display_state(), keys(), plural_people(), Stan wyświetlacza e-papierowego na koszu (docs/epapier/HANDOFF.md): wyzwalacze,…, state_key zmienia się tylko przy pełnym odświeżeniu, values_key przy zmianie…, (state, data) dla renderera. `states`/`routes` można podać z zewnątrz, żeby nie…, _when() (+3 more)

### Community 47 - "test_api.py"
Cohesion: 0.29
Nodes (8): press(), props(), Test 10 z sekcji 11: naciśnięcie → stan → punkt do opróżnienia., test_changes_only_when_version_moves(), test_clock_endpoints(), test_main_path_press_turns_point_red_and_top_of_list(), test_presses_from_many_people_merge_into_one_report(), test_rate_limit_same_point_and_hourly()

### Community 48 - "simulation.py"
Cohesion: 0.24
Nodes (9): multiplier(), Mnożnik najsilniejszego wydarzenia w promieniu, aktywnego w godzinie `at` albo…, hourly_multiplier(), is_emptying_time(), rate_factor(), Generator danych syntetycznych (koncepcja, sekcja 7). Deterministyczny dla…, Mnożnik tempa w danej godzinie: profil dnia, weekend, nocne życie, wydarzenia., sim_presses() (+1 more)

### Community 49 - "details"
Cohesion: 0.24
Nodes (10): default_details(), details(), Jawne reguły, gdy AI niedostępne: festiwale/koncerty średni tłum, wystawy i…, (szczegóły, źródło): z Claude albo z reguł domyślnych (przy braku klucza lub…, fake_create(), parametrize, Atrapa llm._create: zapamiętuje system i treść, zwraca przygotowaną odpowiedź…, test_external_text_is_fenced_and_system_forbids_instructions() (+2 more)

### Community 50 - "reports.py"
Cohesion: 0.32
Nodes (7): point_reliability(), Zgłoszenia z przycisku: scalanie, rozstrzyganie, wiarygodność (koncepcja,…, Odsetek trafnych wśród ostatnich 10 rozstrzygniętych zgłoszeń (outcomes: od…, reliability(), Trafne z ostatnich 10 rozstrzygniętych zgłoszeń z naciśnięciem mieszkańca;…, resident_reliability(), test_reliability_last_10_and_default()

### Community 51 - "test_kierowca.py"
Cohesion: 0.25
Nodes (4): pytest, demo(), fixture, test_stop_issue_flags_point_until_emptying()

### Community 52 - "karnet_command"
Cohesion: 0.33
Nodes (6): karnet_command(), Pobiera wydarzenia z Karnet Kraków do data/karnet.json, importuje je i odtwarza…, fetch(), Pobiera listy wydarzeń (grzecznie, z opóźnieniem) i zapisuje do cache. Zwraca…, option, test_fetch_is_polite_and_writes_cache()

### Community 53 - "gps_from_exif"
Cohesion: 0.33
Nodes (6): gps_from_exif(), (lat, lon) z EXIF zdjęcia albo None. Telefon z włączoną lokalizacją w aparacie…, jpeg_with_gps(), JPEG 32×32 z GPSInfo w EXIF (tak zapisuje aparat telefonu z włączoną…, test_batch_upload_matches_nearest_bin_by_exif(), test_gps_from_exif_roundtrip()

### Community 55 - "database_url"
Cohesion: 0.60
Nodes (4): database_url(), DATABASE_URL z env; Coolify/Heroku podają postgres(ql)://, a my używamy…, test_database_url_defaults_to_sqlite(), test_database_url_uses_psycopg3_for_postgres()

### Community 56 - "ask"
Cohesion: 0.50
Nodes (4): ask(), Tekst → tekst (np. raport dla dyspozytora). Model dostaje gotowe liczby i…, test_llm_uses_model_from_env_and_fallbacks_only_where_supported(), test_llm_without_key_gives_message_not_exception()

## Ambiguous Edges - Review These
- `psycopg[binary] 3.3.6` → `Real bin positions from OSM cached in data/*.geojson`  [AMBIGUOUS]
  DECYZJE.md · relation: conceptually_related_to

## Knowledge Gaps
- **115 isolated node(s):** `STATE_LABEL`, `ISSUES`, `STATE_LBL`, `DAYS`, `I` (+110 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `psycopg[binary] 3.3.6` and `Real bin positions from OSM cached in data/*.geojson`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `import_points()` connect `import_points` to `test_routes.py`, `test_epapier.py`, `test_forecast.py`, `test_zglos.py`, `reset`, `osm_import.py`, `__init__.py`, `test_api.py`, `test_fairy.py`, `test_photos.py`, `test_kierowca.py`, `test_residents.py`, `models.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `Point` connect `models.py` to `residents.py`, `import_points`, `state.py`, `views.py`, `test_epapier.py`, `test_forecast.py`, `test_zglos.py`, `osm_import.py`, `epaper.py`, `test_api.py`, `simulation.py`, `api.py`, `reports.py`, `test_fairy.py`, `test_kierowca.py`, `test_photos.py`, `test_residents.py`, `point_states`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `point_states()` connect `point_states` to `import_points`, `state.py`, `test_routes.py`, `test_forecast.py`, `test_zglos.py`, `generate`, `epaper.py`, `test_fairy.py`, `api.py`, `reports.py`, `test_kierowca.py`, `test_residents.py`, `models.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **What connects `STATE_LABEL`, `ISSUES`, `STATE_LBL` to the rest of the system?**
  _115 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `residents.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._
- **Should `state.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11553030303030302 - nodes in this community are weakly interconnected._