# Graph Report - trash-fairy  (2026-10-03)

## Corpus Check
- 113 files · ~6,532,267 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1995 nodes · 5111 edges · 103 communities (91 shown, 12 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 298 edges (avg confidence: 0.64)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `29f5e642`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- chart.umd.min.js
- o
- xn
- views.py
- reset
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
- get
- Kontekst MPO: dane do pitchu i porównania
- Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)
- pokaz.js
- de
- api.py
- test_residents.py
- zglos.js
- Audyt UX / UI / funkcjonalności – Trash Fairy (Etap 2)
- Trash Fairy – wdrożenie ekranu „Zgłoś kosz” (PWA dla mieszkańców)
- Etap 1 – rozpoznanie (bez zmian w kodzie)
- Trash Fairy – wdrożenie widoku C „Pokaz dla jury”
- queue.js
- sw.js
- Point
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
- llm.py
- zt
- generate
- tn
- an
- va
- details
- n
- comparison.py
- leaflet.js
- emptying
- .getContext
- database_url
- traffic.py
- kierowca/sw.js
- photo
- updateElements
- test_weather.py
- render
- maybe_auto_reset
- .bindResponsiveEvents
- auth.py
- sms.py
- build.py
- jn
- e
- state.py
- .notifyPlugins
- now
- rate.py
- parse
- k
- rs
- u
- xt
- test_sms.py
- fairy_refresh
- ke
- Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)
- O
- epaper_keys
- osrm.py
- money
- ._createDescriptors
- snapshot
- Wyniki po Fali 1 audytu i PWA kierowcy
- .getDataset
- si
- recommendations
- http.py
- .buildOrUpdateControllers
- s
- Before/after comparison on same fill increments (4 weeks)
- ._resolveElementOptions
- beforeUpdate
- jury_pool
- analyze
- .getMinMax

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
- `_shape()` --calls--> `P()`  [INFERRED]
  app/epaper_render.py → docs/widok-c/map/build.py
- `test_weather_changes_only_future_hours()` --calls--> `trajectory()`  [EXTRACTED]
  tests/test_weather.py → app/forecast.py
- `fake_create()` --indirect_call--> `_create()`  [INFERRED]
  tests/test_ai_safety.py → app/llm.py

## Import Cycles
- 3-file cycle: `app/__init__.py -> app/api.py -> app/sms.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/auth.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/epaper.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/fairy.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/forecast.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/rate.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/reports.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/residents.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/routes.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/simulation.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/state.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/traffic.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/weather.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/simulation.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/events.py -> app/__init__.py`

## Hyperedges (group relationships)
- **Routing and before/after comparison** — decyzje_route_point_selection, decyzje_ortools_vrp, decyzje_before_after_comparison, decyzje_fixed_schedule_simulation, app_templates_panel_routes_section, app_templates_panel_compare_section [INFERRED 0.85]
- **Forecast pipeline: weekly profile + events -> 85% crossing -> MAE** — decyzje_weekly_profile, decyzje_event_multiplier, decyzje_crossing_85_interval, decyzje_mae_evaluation, decyzje_forecast_on_demand, docs_koncepcja_forecast [INFERRED 0.95]

## Communities (103 total, 12 thin omitted)

### Community 0 - "chart.umd.min.js"
Cohesion: 0.03
Nodes (46): afterUpdate(), As(), beforeDatasetDraw(), beforeDatasetsDraw(), Bt(), cn(), d(), destroy() (+38 more)

### Community 1 - "o"
Cohesion: 0.08
Nodes (51): a(), aa(), ai(), ao(), average(), da(), dataset(), draw() (+43 more)

### Community 2 - "xn"
Cohesion: 0.16
Nodes (4): bn(), pn(), xn, Ye()

### Community 3 - "views.py"
Cohesion: 0.08
Nodes (37): accessibility(), api_docs(), button(), crew(), driver(), driver_sw(), epaper_page(), health() (+29 more)

### Community 4 - "reset"
Cohesion: 0.05
Nodes (43): Odtwarza symulację od zera i cofa zegar do startu scenariusza (kasuje…, reset(), clear_cache(), clear_cache(), Profile zależą od zawartości bazy — czyścimy po każdej nowej symulacji lub…, Reset scenariusza: usuwa analizy (i pliki), dodaje gotowe analizy przy koszach…, seed_demo(), clear_cache() (+35 more)

### Community 5 - "panel.js"
Cohesion: 0.09
Nodes (35): apply(), clockAction(), dec(), describe(), esc(), eventLayer, hhmm(), KIND (+27 more)

### Community 6 - "test_zglos.py"
Cohesion: 0.06
Nodes (34): city_scale(), Skalowanie wyniku koszy na cały Kraków (decyzja 43): wizyty z harmonogramu MPO…, gps_from_exif(), (lat, lon) z EXIF zdjęcia albo None. Telefon z włączoną lokalizacją w aparacie…, neighbors_map(), demo(), press(), props() (+26 more)

### Community 7 - "85% crossing time with in-hour interpolation, interval from p80/p20"
Cohesion: 0.16
Nodes (16): Point details section with Chart.js chart, Routes for next run section, Decisions only by code rules, never AI, 85% crossing time with in-hour interpolation, interval from p80/p20, Panel shows system estimate, not simulation hidden truth, MAE 2.5 p.p. vs naive mean 7.3 p.p. on last week, no leakage, OR-Tools VRP, 1 vehicle per fleet, depot MPO Nowohucka 1, straight line x1.3, Route point selection: full now, crosses 85% before next run, or safety (bin 3 d, shelter 7 d) (+8 more)

### Community 8 - "Reports and anti-spam rules (merge 15 min, reliability last 10, flag)"
Cohesion: 0.25
Nodes (8): 'Sytuacja teraz' summary with press->report counter, Flag 'check button' (<40% accurate in 7 days or 6 h overflow without press), Report accuracy decided by emptying (>=75%); reliability = accurate share of last 10, start 70%, Report table: presses merged within 15 min of first press, Soft press limit: 1 per 2 s per point, 120/h per IP, ProxyFix, Main path: press -> state change -> to-empty list -> route -> AI report, Reports and anti-spam rules (merge 15 min, reliability last 10, flag), Test plan (~10 pytest tests, Claude mocked)

### Community 9 - "Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js"
Cohesion: 0.15
Nodes (13): Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js, 60 bins from Rynek/Plac Nowy, min 80 m apart, Forecast computed on demand with per-clock-hour profile cache, History stored in forecast table (source='sim'), Real bin positions from OSM cached in data/*.geojson, OSM tiles instead of CARTO, Polling every 2 s with version number, Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report (+5 more)

### Community 10 - "Synthetic data: 8 weeks, OSM-driven fill rates, trolled buttons, frozen demo clock"
Cohesion: 0.22
Nodes (9): Demo clock header (advance +1 h, reset), Dispatcher panel template (panel.html), Demo clock in DB with 24 h simulated future and +1 h advance, Fill rate from surroundings (1.5%/h + venues + stops, cap 8%/h), Simulation with fixed MPO schedule (6:00/14:00, shelters every 3 days), Screens: dispatcher panel, point details, virtual button, jury mode, crew view, methodology, Synthetic data: 8 weeks, OSM-driven fill rates, trolled buttons, frozen demo clock, All operational data synthetic (permanent demo bar) (+1 more)

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
Nodes (6): Point list (text alternative to map) and legend, Events from data/events.json with crowd-scale multiplier (200m x1.3 / 400m x1.6 / 800m x2.0), 24 h plan and cut order, Events from Karnet Krakow via Claude + Nominatim, Style: Planty green + gold panel, magic violet/pink for AI and button, Map visual encoding: shape=type, colour+symbol=state (WCAG)

### Community 15 - "test_photos.py"
Cohesion: 0.11
Nodes (28): _analysis(), household_bag_links(), latest_analyses(), misuse_overview(), overflowing_shelters(), Nadużycia i powiązanie altana → kosz (koncepcja, sekcja 6.5) — reguły w kodzie.…, {point_id: (ostatnia analiza dowolna, ostatnia udana)} z okna 48 h przed `now`., {shelter_id: najwyższy szacunek} dla altan przepełnionych wg prognozy w… (+20 more)

### Community 16 - "test_fairy.py"
Cohesion: 0.20
Nodes (13): (typ, etykieta, uzasadnienie, efekt) albo None — reguły z tabeli w sekcji 6.8., recommend(), demo(), model(), fixture, stats(), test_bigger_bin_between_20_and_50_percent_days(), test_compactor_when_overflowing_most_days_despite_twice_daily() (+5 more)

### Community 17 - "get"
Cohesion: 0.20
Nodes (14): _accuracy_m(), current_resident(), devices(), display(), me(), photo_file(), _point_or_none(), press() (+6 more)

### Community 18 - "Kontekst MPO: dane do pitchu i porównania"
Cohesion: 0.50
Nodes (3): Harmonogram oczyszczania 08/2026 (arkusz „Kosze”), Jak działa MPO (informacja ogólna MPO Kraków), Kontekst MPO: dane do pitchu i porównania

### Community 19 - "Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)"
Cohesion: 0.33
Nodes (5): Cel, Poza zakresem (ROADMAPA), Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A), Testy, Zakres (wariant A)

### Community 20 - "pokaz.js"
Cohesion: 0.08
Nodes (38): apply(), atRisk(), CAPTION, clockAction(), cluster, DAYS, dur(), esc() (+30 more)

### Community 21 - "de"
Cohesion: 0.20
Nodes (4): ce(), de, he(), qs()

### Community 22 - "api.py"
Cohesion: 0.10
Nodes (35): rankings_view(), residents_verify(), Device, FairyReport, PointAward, Press, Raport „Wróżka podpowiada”: fakty policzone w kodzie + tekst od Claude (cache…, Uczestnik programu „Przyjaciele Wróżki”. Bez danych osobowych: pseudonim + hash… (+27 more)

### Community 23 - "test_residents.py"
Cohesion: 0.07
Nodes (55): advance(), Zegar demo: zamrożona sobota 13:30, przewijany o godzinę. Przewinięcie…, DemoClock, Emptying, Zegar scenariusza demo (jeden wiersz). W bazie, bo gunicorn ma kilka procesów., Opróżnienie punktu przez ekipę MPO, z poziomem zastanym przed opróżnieniem., is_hit(), low_reliability() (+47 more)

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

### Community 31 - "Point"
Cohesion: 0.05
Nodes (71): _nearest_point(), cleanup_photos_command(), karnet_command(), Import punktów z data/*.geojson i wydarzeń z data/events.json, symulacja…, Usuwa pliki zdjęć starszych niż 7 dni (wyniki analiz zostają w bazie). Do crona., Pobiera wydarzenia z Karnet Kraków do data/karnet.json, importuje je i odtwarza…, seed_command(), import_events() (+63 more)

### Community 32 - "renderer/epaper_render.py"
Cohesion: 0.23
Nodes (14): _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3…, 168×168: obrys 3 px, biała ramka 8 px, kod wpisany w 152 px., Wycinek okna PARTIAL (752×88) do odświeżenia częściowego. (+6 more)

### Community 33 - "kierowca.js"
Cohesion: 0.14
Nodes (33): act(), commit(), count(), cur(), DAYS, dec(), drawMap(), esc() (+25 more)

### Community 34 - "import_points"
Cohesion: 0.13
Nodes (30): comparison(), compare(), Miary obu polityk na `weeks` tygodniach przed `cutoff` (pełna godzina)., import_points(), Zastępuje punkty w bazie: 60 koszy (Rynek, Kazimierz, kilka przy przeciążonych…, hour_floor(), hourly_multiplier(), is_emptying_time() (+22 more)

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

### Community 40 - "fetch_osm.py"
Cohesion: 0.24
Nodes (7): Audyt UX: zrzuty każdego ekranu na 6 szerokościach + konsola, poziomy scroll,…, classify(), main(), Pobiera punkty z OSM (Overpass API) dla obszaru demo i zapisuje cache do…, to_feature(), sys, urllib_parse

### Community 41 - ".getDatasetMeta"
Cohesion: 0.21
Nodes (3): afterDatasetsUpdate(), generateLabels(), onClick()

### Community 42 - "no"
Cohesion: 0.05
Nodes (22): beforeDraw(), beforeLayout(), buildLookupTable(), ei(), En, Fo(), _generate(), getDecimalForValue() (+14 more)

### Community 43 - "llm.py"
Cohesion: 0.18
Nodes (15): ask(), ask_json(), _create(), LLMError, model(), Exception, Jedyna brama do AI (CLAUDE.md): ask() i ask_json(). Model i klucz z env. AI…, Tekst → tekst (np. raport dla dyspozytora). Model dostaje gotowe liczby i… (+7 more)

### Community 44 - "zt"
Cohesion: 0.10
Nodes (9): color(), It(), kt(), mt(), qt(), _t(), te(), wt() (+1 more)

### Community 45 - "generate"
Cohesion: 0.20
Nodes (10): generate(), Liczby z tekstu raportu, których nie ma w faktach (np. 16:11 → „16” i „11”…, Nowy raport albo LLMError (wtedy wywołujący pokazuje ostatni zapisany)., unknown_numbers(), fence(), Opakowuje treść zewnętrzną w ogranicznik; tag zamykający w środku jest…, test_fairy_report_rejects_extra_fields_and_keeps_previous(), test_fence_neutralises_closing_tag_and_truncates() (+2 more)

### Community 48 - "va"
Cohesion: 0.06
Nodes (20): Ae(), afterDraw(), afterEvent(), ba, Bi(), es(), f(), Ie() (+12 more)

### Community 49 - "details"
Cohesion: 0.22
Nodes (11): default_details(), details(), Jawne reguły, gdy AI niedostępne: festiwale/koncerty średni tłum, wystawy i…, (szczegóły, źródło): z Claude albo z reguł domyślnych (przy braku klucza lub…, fake_create(), parametrize, Atrapa llm._create: zapamiętuje system i treść, zwraca przygotowaną odpowiedź…, test_ai_text_with_script_is_escaped() (+3 more)

### Community 50 - "n"
Cohesion: 0.06
Nodes (22): Be(), ca(), _calculateBarIndexPixels(), determineDataLimits(), getLabelAndValue(), getLabelForValue(), getPixelForValue(), _getRuler() (+14 more)

### Community 51 - "comparison.py"
Cohesion: 0.12
Nodes (31): Status zgłoszenia dla „Śledź status”: przyjęte → zaplanowane → opróżnione., zglos_status(), fixed_selects(), following_run(), is_run(), Porównanie „przed i po” (koncepcja, sekcja 6.7): stały harmonogram MPO kontra…, Zwraca miary jednej polityki. `incs[pid][i]` = prawdziwy przyrost w godzinie…, run_policy() (+23 more)

### Community 52 - "leaflet.js"
Cohesion: 0.06
Nodes (13): a(), bi(), Ci(), ei(), ii(), l(), Mi(), Pi() (+5 more)

### Community 53 - "emptying"
Cohesion: 0.19
Nodes (13): clock_advance(), clock_reset(), device_selftest(), emptying(), logout(), post, Ekipa MPO: punkt opróżniony, poziom zastany przed opróżnieniem, opcjonalne…, Kierowca: nie da się podjechać albo problem z koszem (+ opcjonalne zdjęcie).… (+5 more)

### Community 54 - ".getContext"
Cohesion: 0.13
Nodes (5): Ci(), Do(), eo(), ls, Oe()

### Community 55 - "database_url"
Cohesion: 0.60
Nodes (4): database_url(), DATABASE_URL z env; Coolify/Heroku podają postgres(ql)://, a my używamy…, test_database_url_defaults_to_sqlite(), test_database_url_uses_psycopg3_for_postgres()

### Community 56 - "traffic.py"
Cohesion: 0.14
Nodes (25): _eta(), (ETA kursu z opóźnieniem dojazdu w korku, opóźnienie w min). Bez danych o ruchu…, routes(), city_ratio(), conditions(), data(), delay_min(), drive_min() (+17 more)

### Community 58 - "photo"
Cohesion: 0.18
Nodes (13): photo(), _photo_from_request(), Zapisuje zdjęcie z formularza i uruchamia analizę. Zwraca (analiza, komunikat…, Zdjęcie bez opróżnienia. Bez `point_id` kosz dobieramy z GPS w EXIF (zdjęcia z…, analyze_in_background(), media_type(), photo_dir(), Analiza nie blokuje ekipy na telefonie. W testach (TESTING) liczymy od razu,… (+5 more)

### Community 59 - "updateElements"
Cohesion: 0.25
Nodes (3): _calculateBarValuePixels(), getBasePixel(), updateElements()

### Community 60 - "test_weather.py"
Cohesion: 0.16
Nodes (18): conditions(), data(), factor(), factor_at(), _fetch(), _load_cache(), {"fetched_at", "hours": {"2026-10-03T13:00": {"temp", "rain", "code"}}} albo…, Funkcja at → mnożnik dla prognozy (jedno pobranie danych na całe wyliczenie). (+10 more)

### Community 61 - "render"
Cohesion: 0.15
Nodes (20): _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3…, 168×168: obrys 3 px, biała ramka 8 px, kod wpisany w 152 px., Wycinek okna PARTIAL (752×88) do odświeżenia częściowego. (+12 more)

### Community 62 - "maybe_auto_reset"
Cohesion: 0.33
Nodes (6): maybe_auto_reset(), Akcja w demo (zgłoszenie, opróżnienie, problem): przesuwa start odliczania do…, Reset demo, gdy od ostatniej akcji minęło IDLE. Warunkowy UPDATE: przy kilku…, touch(), _wall(), test_auto_reset_after_idle()

### Community 63 - ".bindResponsiveEvents"
Cohesion: 0.16
Nodes (9): ct(), fs(), ge(), gs(), ms(), ps(), vs(), ws (+1 more)

### Community 64 - "auth.py"
Cohesion: 0.22
Nodes (12): driver_run(), PWA kierowcy: tylko kurs jego floty (decyzja 2), z przebiegiem po ulicach i…, can_touch(), fleet(), home_for_role(), init_app(), Role na pokaz (docs/PRZEGLAD.md, decyzje 1–8): publiczna, dyspozytor, kierowca…, Rola z sesji; poza żądaniem HTTP (wątek analizy, testy wywołujące funkcje… (+4 more)

### Community 65 - "sms.py"
Cohesion: 0.21
Nodes (15): residents_register(), config(), Ustawienie integracji: najpierw config aplikacji (testy je zerują), potem…, _auth(), check_code(), configured(), Exception, Kod SMS przy rejestracji w programie „Przyjaciele Wróżki”: Twilio Verify przez… (+7 more)

### Community 66 - "build.py"
Cohesion: 0.23
Nodes (9): login(), dist(), geom_d(), P(), path_d(), route(), seq_path(), snap() (+1 more)

### Community 68 - "e"
Cohesion: 0.22
Nodes (14): at(), d(), e(), F(), hi(), m(), p(), q() (+6 more)

### Community 69 - "state.py"
Cohesion: 0.07
Nodes (46): after_request, conditions(), Dane kosza dla publicznego ekranu zgłoszenia. Bez danych wewnętrznych…, Pogoda (mnożnik prognozy) i ruch (mnożnik czasu przejazdu) — panel i…, zglos_public(), device_info(), display_state(), plural_people() (+38 more)

### Community 70 - ".notifyPlugins"
Cohesion: 0.22
Nodes (4): dt(), ke(), kn(), wn()

### Community 71 - "now"
Cohesion: 0.29
Nodes (16): now(), calm_bin(), demo(), fixture, Ekran e-papierowy na koszu: logika stanów (tabela wyzwalaczy + priorytety),…, Kosz bez otwartego zgłoszenia i bez opróżnienia w ostatniej godzinie., state_of(), test_calm_then_confirm_after_press() (+8 more)

### Community 72 - "rate.py"
Cohesion: 0.27
Nodes (10): login(), None, gdy się udało; inaczej komunikat do pokazania., Counter, Liczniki limitów (SMS, AI, logowanie) wspólne dla wszystkich workerów…, count(), hit(), Limity wspólne dla wszystkich workerów: liczniki w bazie (tabela Counter), okno…, Liczy zdarzenie i zwraca True, gdy mieści się w limicie; przy przekroczeniu nic… (+2 more)

### Community 73 - "parse"
Cohesion: 0.20
Nodes (5): buildTicks(), go(), init(), parse(), po()

### Community 74 - "k"
Cohesion: 0.40
Nodes (6): G(), k(), me(), Oe(), Se(), ze()

### Community 76 - "u"
Cohesion: 0.20
Nodes (6): addBox(), configure(), reset(), start(), u(), vn()

### Community 77 - "xt"
Cohesion: 0.15
Nodes (3): Cs, os(), xt

### Community 78 - "test_sms.py"
Cohesion: 0.19
Nodes (13): FakeOpener, Fałszywy opener dla app/http.py: odpowiedzi po fragmencie adresu, zapis…, routes: {fragment_adresu: (status, body) | Exception | callable(req) ->…, _Resp, fixture, register(), test_gateway_failure_503_or_demo_fallback(), test_limits_per_number() (+5 more)

### Community 79 - "fairy_refresh"
Cohesion: 0.43
Nodes (7): fairy_get(), fairy_refresh(), Nowy raport. Przy błędzie API: komunikat + ostatni raport (nigdy 500)., is_fresh(), latest(), to_dict(), available()

### Community 80 - "ke"
Cohesion: 0.25
Nodes (8): Ae(), be(), Ie(), j(), ke(), ne(), Re(), s()

### Community 81 - "Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)"
Cohesion: 0.25
Nodes (7): 1. Uprawnienia, 2. Ekrany i nawigacja, 3. Wygląd, 4. Widoki i stany, 5. Zależności i infrastruktura, 6. Produkt i pokaz, Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)

### Community 82 - "O"
Cohesion: 0.22
Nodes (9): Ee(), Ft(), Le(), Jt(), Le(), O(), Qt(), $t() (+1 more)

### Community 83 - "epaper_keys"
Cohesion: 0.40
Nodes (5): epaper_keys(), Stan ekranu na koszu: state_key (pełne odświeżenie) i values_key (okno…, keys(), state_key zmienia się tylko przy pełnym odświeżeniu, values_key przy zmianie…, test_state_change_needs_full_refresh_and_keys_follow()

### Community 84 - "osrm.py"
Cohesion: 0.25
Nodes (8): _fetch(), _load(), Przebieg tras po ulicach z OSRM, tylko do rysowania na mapie. Kilometry nadal…, coords: lista [lat, lon]. Zwraca (punkty linii [lat, lon], approx)., street_path(), test_no_network_falls_back_to_straight_line(), test_street_path_cached_after_first_fetch(), urllib_request

### Community 85 - "money"
Cohesion: 0.40
Nodes (5): _env_float(), money(), money_assumptions(), Przeliczenie wyniku porównania (4 tygodnie) na miesiąc, zł i CO₂ — wg jawnych…, test_money_uses_configurable_assumptions()

### Community 87 - "snapshot"
Cohesion: 0.31
Nodes (9): changes(), point_detail(), points(), public_view(), _r(), Wersja danych dla pollingu (app/state.data_version); ta sama służy za klucz…, snapshot(), version() (+1 more)

### Community 88 - "Wyniki po Fali 1 audytu i PWA kierowcy"
Cohesion: 0.40
Nodes (4): Lighthouse (lokalnie, Chromium headless, Lighthouse 13.5), Poziomy scroll, Pozycje audytu, Wyniki po Fali 1 audytu i PWA kierowcy

### Community 90 - "si"
Cohesion: 0.67
Nodes (4): Je(), ni(), oi(), si()

### Community 91 - "recommendations"
Cohesion: 0.33
Nodes (6): recommendations_list(), point_stats(), {point_id: {"days", "overflow_days", "readings", "half_full", "per_day"}} z…, Lista rekomendacji, od najważniejszych. `shelter_interventions`: {shelter_id:…, recommendations(), test_recommendations_use_crew_readings_and_shelter_rule_first()

### Community 92 - "http.py"
Cohesion: 0.47
Nodes (5): get_json(), post_form(), Wspólny klient HTTP integracji (Open-Meteo, TomTom, Twilio): urllib ze stdlib,…, (status, json). Błąd HTTP z treścią JSON (np. Twilio 400/429) zwracamy jako…, _send()

### Community 95 - ".buildOrUpdateControllers"
Cohesion: 0.19
Nodes (4): addElements(), Mn(), removeBox(), stop()

### Community 96 - "s"
Cohesion: 0.10
Nodes (16): at(), b(), bo, et(), g(), H(), label(), m() (+8 more)

### Community 97 - "Before/after comparison on same fill increments (4 weeks)"
Cohesion: 0.29
Nodes (7): Before/after 4 weeks section, 'Wrozka podpowiada' placeholder card, Before/after comparison on same fill increments (4 weeks), Bin overflow hours unchanged with fixed run times, Before/after comparison: fixed schedule vs Trash Fairy, Investment recommendations (compactor, bigger bin, shelter intervention), Stage 6: 'Wrozka podpowiada' report, Karnet, recommendations, jury mode

### Community 100 - "jury_pool"
Cohesion: 0.40
Nodes (5): jury(), jury_pool(), Kod QR w panelu prowadzi tutaj: losowy kosz przy Rynku, żeby jury naciskało…, start_url PWA bez kosza: wybór kosza (najbliższe wg GPS w JS, zapas: pula przy…, report_pick()

### Community 101 - "analyze"
Cohesion: 0.50
Nodes (4): image_block(), analyze(), Wywołuje Claude Vision i zapisuje wynik albo komunikat błędu — nigdy nie rzuca…, test_invalid_photo_reply_keeps_last_good_result()

## Ambiguous Edges - Review These
- `psycopg[binary] 3.3.6` → `Real bin positions from OSM cached in data/*.geojson`  [AMBIGUOUS]
  DECYZJE.md · relation: conceptually_related_to

## Knowledge Gaps
- **129 isolated node(s):** `STATE_LABEL`, `ISSUES`, `STATE_LBL`, `DAYS`, `I` (+124 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `psycopg[binary] 3.3.6` and `Real bin positions from OSM cached in data/*.geojson`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `import_points()` connect `import_points` to `reset`, `test_forecast.py`, `test_zglos.py`, `now`, `test_photos.py`, `test_fairy.py`, `comparison.py`, `test_residents.py`, `traffic.py`, `Point`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Why does `ns()` connect `ns` to `chart.umd.min.js`, `o`, `xn`, `beforeUpdate`, `._resolveElementOptions`, `.getMinMax`, `parse`, `xt`, `va`, `n`, `.getContext`, `.getDataset`, `updateElements`, `.buildOrUpdateControllers`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `o()` connect `o` to `chart.umd.min.js`, `s`, `xn`, `no`, `k`, `u`, `va`, `ke`, `n`, `O`, `.getDataset`, `.bindResponsiveEvents`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `o()` (e.g. with `ai()` and `da()`) actually correct?**
  _`o()` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `STATE_LABEL`, `ISSUES`, `STATE_LBL` to the rest of the system?**
  _129 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `chart.umd.min.js` be split into smaller, more focused modules?**
  _Cohesion score 0.030566280566280565 - nodes in this community are weakly interconnected._