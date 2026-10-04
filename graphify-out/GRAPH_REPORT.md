# Graph Report - trash-fairy  (2026-10-04)

## Corpus Check
- 140 files · ~8,388,297 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1995 nodes · 6040 edges · 116 communities (104 shown, 12 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 983 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `52ad841d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- echarts.min.js
- r
- E
- q
- Y
- Forecast: weekly profile + event multiplier, 85% crossing, MAE
- ui.py
- Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report
- Synthetic data: 8 weeks, OSM-driven fill rates, trolled buttons, frozen demo clock
- Trash Fairy README
- Brainstorm: przycisk dla mieszkańców, awarie, spam, wyświetlacz, program „Przyjaciele Wróżki”
- Photo analysis JSON schema (fill_level, misuse, damage, confidence)
- AI role: Vision, event parsing, 'Wrozka podpowiada' report
- test_photos.py
- test_fairy.py
- zglos
- Kontekst MPO: dane do pitchu i porównania
- Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)
- test_poprawki_jury.py
- _item
- details
- models.py
- history.py
- Audyt UX / UI / funkcjonalności – Trash Fairy (Etap 2)
- Trash Fairy – wdrożenie ekranu „Zgłoś kosz” (PWA dla mieszkańców)
- Etap 1 – rozpoznanie (bez zmian w kodzie)
- Trash Fairy – wdrożenie widoku C „Pokaz dla jury”
- U
- dashboard.py
- test_urzadzenia.py
- build.py
- import_points
- reset
- test_perspektywy.py
- simulation.py
- Trash Fairy – wyświetlacz e-papierowy na koszu (800×480)
- E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware)
- ug
- przed_po.py
- dashboard_api.py
- device_token
- test_karnet.py
- i
- llm.py
- n
- ApiError
- test_dashboard.py
- get
- fetch_osm.py
- test_routes.py
- leaflet.js
- zw
- rt
- Xd
- traffic.py
- kosz_json
- now
- T
- weather.py
- render
- Audyt UX, ekranów i API: Trash Fairy (Etap 1)
- validate
- dashboard.js
- test_sms.py
- Wt
- Jr
- z
- point_states
- Xy
- open_api.py
- generate
- monthly_plan
- k
- urzadzenia.js
- Hu
- Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js
- fakes.py
- Handoff: przebudowa UI pod jury (niedz. 4.10.2026, ok. 02:30)
- ke
- Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)
- Filters
- Nagranie 2:00: scenariusz (decyzje 44–45, po przebudowie UI)
- R
- conftest.py
- bi
- ri
- Wyniki po Fali 1 audytu i PWA kierowcy
- Top poprawek pod jury (z JURY-WYMAGANIA.md), w kolejności wykonania
- si
- fu
- http.py
- Routes: two fleets, runs 6:00/14:00, OR-Tools VRP
- database_url
- kierowca.js
- jw
- ia
- je
- Jak poprowadzić demo w 3 minuty
- Gt
- GB
- Tm
- Mk
- Vu
- test_wsgi.py
- Screens: dispatcher panel, point details, virtual button, jury mode, crew view, methodology
- HS
- JB

## God Nodes (most connected - your core abstractions)
1. `E()` - 129 edges
2. `i()` - 107 edges
3. `r()` - 99 edges
4. `n()` - 86 edges
5. `a()` - 86 edges
6. `s()` - 84 edges
7. `now()` - 66 edges
8. `point_states()` - 65 edges
9. `l()` - 63 edges
10. `T()` - 60 edges

## Surprising Connections (you probably didn't know these)
- `Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js` --semantically_similar_to--> `Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/KONCEPCJA.md
- `Flag 'check button' (<40% accurate in 7 days or 6 h overflow without press)` --implements--> `Reports and anti-spam rules (merge 15 min, reliability last 10, flag)`  [INFERRED]
  DECYZJE.md → docs/KONCEPCJA.md
- `test_fixed_policy_visits_every_bin_twice_a_day()` --calls--> `run_policy()`  [EXTRACTED]
  tests/test_routes.py → app/comparison.py
- `test_weather_changes_only_future_hours()` --calls--> `trajectory()`  [EXTRACTED]
  tests/test_weather.py → app/forecast.py
- `fake_create()` --indirect_call--> `_create()`  [INFERRED]
  tests/test_ai_safety.py → app/llm.py

## Import Cycles
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/rate.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/reports.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/routes.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/state.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api_pl.py -> app/traffic.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/history.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/karnet.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/osm_import.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/simulation.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/dashboard_api.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/dashboard_api.py -> app/dashboard.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/dashboard_api.py -> app/history.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/dashboard_api.py -> app/methodology.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/dashboard_api.py -> app/state.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/devices_api.py -> app/clock.py -> app/__init__.py`

## Hyperedges (group relationships)
- **Forecast pipeline: weekly profile + events -> 85% crossing -> MAE** — decyzje_weekly_profile, decyzje_event_multiplier, decyzje_crossing_85_interval, decyzje_mae_evaluation, decyzje_forecast_on_demand, docs_koncepcja_forecast [INFERRED 0.95]

## Communities (116 total, 12 thin omitted)

### Community 0 - "echarts.min.js"
Cohesion: 0.02
Nodes (15): fg(), gE(), ir(), LN(), mu(), NS(), og(), PC() (+7 more)

### Community 2 - "r"
Cohesion: 0.11
Nodes (82): Al(), An(), ba(), bG(), bk(), bl(), bp(), Bx() (+74 more)

### Community 3 - "E"
Cohesion: 0.05
Nodes (56): az(), Cl(), Cm(), ct(), Dk(), Dl(), E(), el() (+48 more)

### Community 4 - "q"
Cohesion: 0.06
Nodes (48): Am(), ao(), aw(), Bs(), bw(), D(), eb(), ec() (+40 more)

### Community 5 - "Y"
Cohesion: 0.07
Nodes (53): at(), B(), bB(), bv(), Cf(), Cr(), Cw(), di() (+45 more)

### Community 7 - "Forecast: weekly profile + event multiplier, 85% crossing, MAE"
Cohesion: 0.18
Nodes (14): 85% crossing time with in-hour interpolation, interval from p80/p20, Panel shows system estimate, not simulation hidden truth, MAE 2.5 p.p. vs naive mean 7.3 p.p. on last week, no leakage, Report accuracy decided by emptying (>=75%); reliability = accurate share of last 10, start 70%, Report table: presses merged within 15 min of first press, Route point selection: full now, crosses 85% before next run, or safety (bin 3 d, shelter 7 d), State = max(level, 100 x report reliability), Weekly 7x24 profile per point: mean and p20/p80 (+6 more)

### Community 8 - "ui.py"
Cohesion: 0.12
Nodes (21): assumptions(), city_scale(), page_context(), _pl(), Strona Metodologia: założenia czytane wprost ze stałych w kodzie + jawne…, [(obszar, założenie, wartość)] — wartości wprost z kodu., Skalowanie wyniku koszy na cały Kraków (decyzja 43): wizyty z harmonogramu MPO…, point_stats() (+13 more)

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
Cohesion: 0.12
Nodes (25): household_bag_links(), latest_analyses(), misuse_overview(), {point_id: (ostatnia analiza dowolna, ostatnia udana)} z okna 48 h przed `now`., [(bin, shelter)] dla worków domowych w promieniu 200 m od przepełnionej altany., Wszystko, czego potrzebuje panel: plakietki nadużyć, flagi rozbieżności, linie…, analyze_in_background(), discrepancy() (+17 more)

### Community 16 - "test_fairy.py"
Cohesion: 0.16
Nodes (18): money(), Przeliczenie wyniku porównania (4 tygodnie) na miesiąc, zł i CO₂ — wg jawnych…, (typ, etykieta, uzasadnienie, efekt) albo None — reguły z tabeli w sekcji 6.8., recommend(), demo(), model(), fixture, stats() (+10 more)

### Community 17 - "zglos"
Cohesion: 0.12
Nodes (31): _accuracy(), blad(), demo_reset(), dojazd(), _json_body(), kosz(), kosze(), meta() (+23 more)

### Community 18 - "Kontekst MPO: dane do pitchu i porównania"
Cohesion: 0.50
Nodes (3): Harmonogram oczyszczania 08/2026 (arkusz „Kosze”), Jak działa MPO (informacja ogólna MPO Kraków), Kontekst MPO: dane do pitchu i porównania

### Community 19 - "Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)"
Cohesion: 0.33
Nodes (5): Cel, Poza zakresem (ROADMAPA), Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A), Testy, Zakres (wariant A)

### Community 20 - "test_poprawki_jury.py"
Cohesion: 0.10
Nodes (33): _plural(), powod(), Krótkie „dlaczego tu” przy przystanku kierowcy; ta sama kolejność co _priority.…, gps_from_exif(), Ponowne zakodowanie obrazu bez EXIF/XMP (GPS, model aparatu, czas). Orientację…, (lat, lon) z EXIF zdjęcia albo None. Telefon z włączoną lokalizacją w aparacie…, Reguła (nie AI): wynik analizy + typ zgłoszenia → status weryfikacji. Nigdy nie…, strip_metadata() (+25 more)

### Community 21 - "_item"
Cohesion: 0.10
Nodes (22): device_detail(), battery_level(), days_left(), detail(), _item(), overview(), _presses(), _query() (+14 more)

### Community 22 - "details"
Cohesion: 0.16
Nodes (14): default_details(), details(), Jawne reguły, gdy AI niedostępne: festiwale/koncerty średni tłum, wystawy i…, (szczegóły, źródło): z Claude albo z reguł domyślnych (przy braku klucza lub…, fence(), Opakowuje treść zewnętrzną w ogranicznik; tag zamykający w środku jest…, fake_create(), parametrize (+6 more)

### Community 23 - "models.py"
Cohesion: 0.07
Nodes (56): API perspektyw (panel na koszu, mieszkaniec, kierowca, demo). JSON wszędzie,…, Zegar demo: zamrożona sobota 13:30, przewijany o godzinę. Przewinięcie…, _api_error(), errorhandler, API urządzeń na koszach (/api/urzadzenia). Reguły i założenia: app/devices.py.…, Urządzenia na koszach: masterdane, bateria, odczyty i status. Reguły w kodzie,…, Stan wyświetlacza e-papierowego na koszu (docs/epapier/HANDOFF.md): wyzwalacze,…, Wydarzenia z Karnet Kraków (koncepcja, sekcja 6.4). Publicznego API brak —… (+48 more)

### Community 24 - "history.py"
Cohesion: 0.12
Nodes (25): _city_point(), _education(), fraction_factor(), generate_history(), lever_since(), _live_point(), _Out, _plain() (+17 more)

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

### Community 29 - "U"
Cohesion: 0.07
Nodes (39): Ad(), ay(), cv(), dv(), ed(), fk(), fv(), gg() (+31 more)

### Community 30 - "dashboard.py"
Cohesion: 0.14
Nodes (25): _frakcje(), _heatmapa(), _mapa(), _by(), dow_of(), hour_of(), hours_between(), month_of() (+17 more)

### Community 31 - "test_urzadzenia.py"
Cohesion: 0.07
Nodes (32): cleanup_photos_command(), karnet_command(), Import punktów z data/*.geojson i wydarzeń z data/events.json, symulacja…, Początek okna symulacji w istniejącej bazie (historia punktów demo kończy się…, Usuwa pliki zdjęć starszych niż 7 dni (wyniki analiz zostają w bazie). Do crona., Pobiera wydarzenia z Karnet Kraków do data/karnet.json, importuje je i odtwarza…, seed_command(), _sim_start() (+24 more)

### Community 32 - "build.py"
Cohesion: 0.11
Nodes (23): Kształt stanu wypełniony `fill`, znak w kolorze `glyph`. s = bok w px., _shape(), _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3… (+15 more)

### Community 33 - "import_points"
Cohesion: 0.05
Nodes (55): Raport „Wróżka podpowiada” (koncepcja, sekcja 8): fakty liczy kod, Claude tylko…, distance_m(), Odległość w linii prostej (haversine), w metrach., overflowing_shelters(), Nadużycia i powiązanie altana → kosz (koncepcja, sekcja 6.5) — reguły w kodzie.…, {shelter_id: najwyższy szacunek} dla altan przepełnionych wg prognozy w…, FairyReport, PhotoAnalysis (+47 more)

### Community 34 - "reset"
Cohesion: 0.08
Nodes (32): advance(), _locked_reset(), maybe_auto_reset(), Auto-reset w tle: widz nie czeka ~13 s (PostgreSQL) na stronę. Jeden naraz na…, Odtwarza symulację od zera i cofa zegar do startu scenariusza (kasuje…, Reset demo, gdy od ostatniej akcji minęło IDLE. Warunkowy UPDATE: przy kilku…, reset() pod blokadą bazy (PostgreSQL): False, gdy inny worker właśnie resetuje.…, Reset ręczny: False, gdy reset już trwa (w tym procesie albo w innym workerze). (+24 more)

### Community 35 - "test_perspektywy.py"
Cohesion: 0.06
Nodes (45): qr_token(), Token z kodu QR na panelu kosza: bez niego nie ma zgłoszenia (wymaganie: skan…, app_context_processor, _env_float(), pilot_roi(), Koszt pilotażu i zwrot wg jawnych założeń (env, do weryfikacji w pilotażu).…, ui_context(), accessibility() (+37 more)

### Community 36 - "simulation.py"
Cohesion: 0.06
Nodes (70): compare(), fixed_selects(), following_run(), is_run(), Porównanie „przed i po” (koncepcja, sekcja 6.7): stały harmonogram MPO kontra…, Zwraca miary jednej polityki. `incs[pid][i]` = prawdziwy przyrost w godzinie…, Miary obu polityk na `weeks` tygodniach przed `cutoff` (pełna godzina)., run_policy() (+62 more)

### Community 37 - "Trash Fairy – wyświetlacz e-papierowy na koszu (800×480)"
Cohesion: 0.22
Nodes (8): Dane wejściowe renderera, Etap 1 – symulator do pokazu (zalecany na hackathon), Etap 2 – prawdziwe urządzenie (kontrakt, bez implementacji firmware), Kryteria odbioru, Siatka (px, stałe – nie zmieniać między stanami), Stany i wyzwalacze, Trash Fairy – wyświetlacz e-papierowy na koszu (800×480), Zawartość paczki

### Community 38 - "E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware)"
Cohesion: 0.29
Nodes (6): Co jeszcze przed pilotażem, Dlaczego urządzenie renderuje samo, Downlink (port 10, ≤ 12 B), E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware), QR na urządzeniu, Uplink

### Community 39 - "ug"
Cohesion: 0.23
Nodes (14): ag(), cg(), dg(), eg(), hg(), lg(), mp(), ng() (+6 more)

### Community 41 - "dashboard_api.py"
Cohesion: 0.16
Nodes (26): _api_error(), _cached_json(), _change(), districts(), _dzielnice(), _koszty(), kpi(), _kpi_values() (+18 more)

### Community 42 - "device_token"
Cohesion: 0.50
Nodes (5): device_token(), Token urządzenia (nagłówek X-Token-Urzadzenia): HMAC numeru seryjnego, wgrywany…, _ok_device(), test_reading_requires_device_token(), test_sensor_and_panel_readings_update_device()

### Community 43 - "test_karnet.py"
Cohesion: 0.15
Nodes (18): fetch(), _first(), import_events(), in_demo(), parse_list(), Pobiera listy wydarzeń (grzecznie, z opóźnieniem) i zapisuje do cache. Zwraca…, Zastępuje wydarzenia z Karnetu (source='karnet') wydarzeniami z obszaru demo w…, [{id, name, lat, lon, type, location, start, end, text, url}] z HTML listy… (+10 more)

### Community 44 - "i"
Cohesion: 0.17
Nodes (27): ap(), Ci(), cp(), dp(), Dy(), ep(), F(), fp() (+19 more)

### Community 45 - "llm.py"
Cohesion: 0.14
Nodes (20): ask(), ask_json(), available(), _create(), image_block(), LLMError, model(), Exception (+12 more)

### Community 46 - "n"
Cohesion: 0.07
Nodes (39): A(), aA(), bn(), cA(), Cn(), cs(), dd(), ea() (+31 more)

### Community 47 - "ApiError"
Cohesion: 0.15
Nodes (19): ApiError, chart(), _date(), export_csv(), parse_filters(), Exception, get, CSV z tymi samymi filtrami co dashboard (okres, od/do, dzielnica, frakcja,… (+11 more)

### Community 48 - "test_dashboard.py"
Cohesion: 0.10
Nodes (22): Punkty silnika demo. Każde zapytanie silnika iterujące po punktach idzie przez…, devices_overview(), neighbors_map(), _history_fingerprint(), _kpi(), parametrize, Panel miasta: punkty miasta, historia syntetyczna, agregacje i API. Jedna baza…, Opróżnienie z PWA kierowcy (Emptying) wchodzi do liczników panelu od razu… (+14 more)

### Community 49 - "get"
Cohesion: 0.12
Nodes (17): dashboard(), devices_page(), driver(), driver_bin(), project(), get, Karta kosza: zgłoszenia, „Jadę” z nawigacją w aplikacji, „Opróżniono”,…, Dashboard miasta: KPI, wykresy, mapa, projekty. Dane z /api/dashboard/*… (+9 more)

### Community 50 - "fetch_osm.py"
Cohesion: 0.07
Nodes (32): address_of(), fractions(), near_label(), „Aleja Przyjaźni” → „al. Przyjaźni”, „Rynek Główny” bez zmian, reszta → „ul. X”., Adres przybliżony: „okolice ul. X” (skrót się nie odmienia), „okolice: Rynek…, Frakcje pojemnika z tagów recycling:* (kolejność jak w FRACTION_TAGS)., Altana ma kilka pojemników, więc „zmieszane” — chyba że tagi OSM wskazują…, addr:street (+ numer) z tagów punktu, inaczej ulica najbliższego lokalu z… (+24 more)

### Community 51 - "test_routes.py"
Cohesion: 0.14
Nodes (23): next_runs(), plan_routes(), Trasy na najbliższy kurs (koncepcja, sekcja 6.6): wybór punktów regułami + OR-…, (najbliższy kurs po `now`, kolejny kurs) dla floty., Powód wzięcia punktu na kurs `run_at` albo None. Reguły, nie AI (koncepcja,…, coords[0] = baza. Zwraca (kolejność indeksów punktów 1..n-1, metry). Wynik…, Trasy obu flot na najbliższy kurs. `states` = wynik state.point_states(now)., road_m() (+15 more)

### Community 52 - "leaflet.js"
Cohesion: 0.06
Nodes (11): at(), c(), Ci(), hi(), j(), Mi(), N(), q() (+3 more)

### Community 53 - "zw"
Cohesion: 0.26
Nodes (15): bi(), Ew(), hi(), Iw(), lw(), mi(), nw(), oW() (+7 more)

### Community 54 - "rt"
Cohesion: 0.13
Nodes (19): ac(), br(), cc(), ce(), da(), ee(), ez(), fa() (+11 more)

### Community 55 - "Xd"
Cohesion: 0.14
Nodes (18): BD(), Fn(), Gd(), Hd(), Hn(), ii(), it(), jn() (+10 more)

### Community 56 - "traffic.py"
Cohesion: 0.17
Nodes (22): city_ratio(), conditions(), data(), delay_min(), drive_min(), fresh_samples(), _load_cache(), ratio() (+14 more)

### Community 57 - "kosz_json"
Cohesion: 0.13
Nodes (18): _address(), _ai(), _done_ids(), _jade_at(), kosz_json(), _last_emptying(), _open_reports(), poziom_stan() (+10 more)

### Community 58 - "now"
Cohesion: 0.17
Nodes (24): now(), device_info(), display_state(), keys(), plural_people(), state_key zmienia się tylko przy pełnym odświeżeniu, values_key przy zmianie…, (state, data) dla renderera. `states`/`routes` można podać z zewnątrz, żeby nie…, _when() (+16 more)

### Community 59 - "T"
Cohesion: 0.12
Nodes (23): bf(), df(), et(), Ff(), hf(), hw(), kp(), lp() (+15 more)

### Community 60 - "weather.py"
Cohesion: 0.17
Nodes (19): conditions(), data(), factor(), factor_at(), _fetch(), _load_cache(), Pogoda z Open-Meteo (bez klucza) jako mnożnik tempa zapełniania w prognozie.…, {"fetched_at", "hours": {"2026-10-03T13:00": {"temp", "rain", "code"}}} albo… (+11 more)

### Community 61 - "render"
Cohesion: 0.16
Nodes (18): _font(), _partial(), FreeTypeFont, Image, _qr(), Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3…, 168×168: obrys 3 px, biała ramka 8 px, kod wpisany w 152 px., Wycinek okna PARTIAL (752×88) do odświeżenia częściowego. (+10 more)

### Community 62 - "Audyt UX, ekranów i API: Trash Fairy (Etap 1)"
Cohesion: 0.12
Nodes (15): 1. Inwentaryzacja, 2. Ocena ekranów, 3. Nawigacja: dziś i docelowo, 4. Docelowa struktura ekranów, 5. Docelowe API, 6. Kierunek wizualny, 7. Decyzje do akceptacji przed Etapem 2, 8. Plan wdrożenia (do zamrożenia kodu w niedzielę o 19:00) (+7 more)

### Community 63 - "validate"
Cohesion: 0.40
Nodes (5): media_type(), Typ obrazu po sygnaturze pliku (nie ufamy nazwie ani nagłówkowi od…, Zwraca typ obrazu albo komunikat błędu (None, komunikat)., validate(), test_validate_by_magic_bytes_and_size()

### Community 64 - "dashboard.js"
Cohesion: 0.20
Nodes (11): apply(), details(), load(), loadDistricts(), loadProjects(), rDzielnice(), renderKpis(), rKoszty() (+3 more)

### Community 65 - "test_sms.py"
Cohesion: 0.16
Nodes (21): config(), Ustawienie integracji: najpierw config aplikacji (testy je zerują), potem…, _auth(), check_code(), configured(), Exception, Kod SMS przy rejestracji w programie „Przyjaciele Wróżki”: Twilio Verify przez…, Każda próba wysyłki liczy się do limitu, także nieudana: bramka i tak mogła… (+13 more)

### Community 66 - "Wt"
Cohesion: 0.19
Nodes (14): au(), be(), bh(), bu(), Fh(), Ie(), Se(), vi() (+6 more)

### Community 67 - "Jr"
Cohesion: 0.18
Nodes (12): Ax(), co(), Cx(), dx(), eo(), ho(), Jr(), kx() (+4 more)

### Community 68 - "z"
Cohesion: 0.40
Nodes (5): ve(), W(), xe(), ye(), z()

### Community 69 - "point_states"
Cohesion: 0.06
Nodes (72): build_facts(), Wszystkie liczby do raportu — liczone w kodzie, nie przez model., Emptying, Opróżnienie punktu przez ekipę MPO, z poziomem zastanym przed opróżnieniem., low_reliability(), point_reliability(), Odsetek trafnych wśród ostatnich 10 rozstrzygniętych zgłoszeń (outcomes: od…, Flaga „sprawdź przycisk”: < 40% trafnych wśród zgłoszeń z 7 dni (min. 3… (+64 more)

### Community 70 - "Xy"
Cohesion: 0.33
Nodes (7): bo(), Eh(), Oh(), Ph(), Rh(), Uh(), Xy()

### Community 71 - "open_api.py"
Cohesion: 0.23
Nodes (14): after_request, _bin(), bin_detail(), bins(), conditions(), conditions_view(), cors(), _meta() (+6 more)

### Community 72 - "generate"
Cohesion: 0.24
Nodes (11): generate(), latest(), Liczby z tekstu raportu, których nie ma w faktach (np. 16:11 → „16” i „11”…, Nowy raport albo LLMError (wtedy wywołujący pokazuje ostatni zapisany)., to_dict(), unknown_numbers(), test_fairy_report_rejects_extra_fields_and_keeps_previous(), test_api_error_raises_llm_error_and_last_report_stays() (+3 more)

### Community 73 - "monthly_plan"
Cohesion: 0.27
Nodes (10): _baseline(), control_districts(), _index(), month_days(), monthly_plan(), _per_day(), plan(), {wywozy, km} wg planu w przedziale `f`. (+2 more)

### Community 74 - "k"
Cohesion: 0.40
Nodes (6): G(), k(), me(), Oe(), Se(), ze()

### Community 75 - "urzadzenia.js"
Cohesion: 0.43
Nodes (7): apply(), fillDistricts(), load(), open(), renderChips(), renderKpis(), renderList()

### Community 76 - "Hu"
Cohesion: 0.33
Nodes (6): Dt(), Ht(), Hu(), LC(), xC(), zt()

### Community 77 - "Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js"
Cohesion: 0.33
Nodes (6): Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js, Style: Planty green + gold panel, magic violet/pink for AI and button, Map visual encoding: shape=type, colour+symbol=state (WCAG), Flask 3.1.3, Flask-SQLAlchemy 3.1.1, gunicorn 26.2.0

### Community 78 - "fakes.py"
Cohesion: 0.28
Nodes (5): FakeOpener, Fałszywy opener dla app/http.py: odpowiedzi po fragmencie adresu, zapis…, routes: {fragment_adresu: (status, body) | Exception | callable(req) ->…, _Resp, urllib_error

### Community 79 - "Handoff: przebudowa UI pod jury (niedz. 4.10.2026, ok. 02:30)"
Cohesion: 0.33
Nodes (5): Decyzje autora (4.10, ok. 00:40), Do zrobienia (kolejność), Handoff: przebudowa UI pod jury (niedz. 4.10.2026, ok. 02:30), Stan, Ważne fakty i grabie

### Community 80 - "ke"
Cohesion: 0.18
Nodes (12): Ae(), be(), Ie(), Jt(), ke(), Le(), ne(), O() (+4 more)

### Community 81 - "Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)"
Cohesion: 0.25
Nodes (7): 1. Uprawnienia, 2. Ekrany i nawigacja, 3. Wygląd, 4. Widoki i stany, 5. Zależności i infrastruktura, 6. Produkt i pokaz, Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)

### Community 82 - "Filters"
Cohesion: 0.25
Nodes (7): Filters, project_effect(), project_windows(), (przed, po): „po” = od startu do końca (najdalej do teraz), „przed” = tyle samo…, (wartość zmiany, etykieta) z historii dzielnicy przed i po starcie projektu., test_fraction_masses_sum_to_total_mass(), test_projects_effects_computed_from_history()

### Community 83 - "Nagranie 2:00: scenariusz (decyzje 44–45, po przebudowie UI)"
Cohesion: 0.40
Nodes (4): Liczby w tekście i ich źródło, Nagranie 2:00: scenariusz (decyzje 44–45, po przebudowie UI), Przygotowanie (przed nagraniem), Tekst słowo w słowo

### Community 84 - "R"
Cohesion: 0.40
Nodes (5): aR(), oR(), R(), Vk(), zk()

### Community 85 - "conftest.py"
Cohesion: 0.21
Nodes (11): clear_cache(), clear_cache(), Profile zależą od zawartości bazy — czyścimy po każdej nowej symulacji lub…, clear_cache(), Po resecie demo i między testami: wersja danych może się powtórzyć na nowej…, app(), cache(), client() (+3 more)

### Community 86 - "bi"
Cohesion: 0.67
Nodes (3): bi(), Pi(), Ti()

### Community 87 - "ri"
Cohesion: 0.67
Nodes (3): ei(), ii(), ri()

### Community 88 - "Wyniki po Fali 1 audytu i PWA kierowcy"
Cohesion: 0.40
Nodes (4): Lighthouse (lokalnie, Chromium headless, Lighthouse 13.5), Poziomy scroll, Pozycje audytu, Wyniki po Fali 1 audytu i PWA kierowcy

### Community 89 - "Top poprawek pod jury (z JURY-WYMAGANIA.md), w kolejności wykonania"
Cohesion: 0.40
Nodes (4): P0: przed zamrożeniem kodu (największy wpływ, mały nakład), P1: mocne wzmocnienia (jeśli zostanie czas przed 19:00), P2: dopracowanie i roadmapa, Top poprawek pod jury (z JURY-WYMAGANIA.md), w kolejności wykonania

### Community 90 - "si"
Cohesion: 0.67
Nodes (4): Je(), ni(), oi(), si()

### Community 91 - "fu"
Cohesion: 0.67
Nodes (4): cu(), du(), fu(), pu()

### Community 92 - "http.py"
Cohesion: 0.47
Nodes (5): get_json(), post_form(), Wspólny klient HTTP integracji (Open-Meteo, TomTom, Twilio): urllib ze stdlib,…, (status, json). Błąd HTTP z treścią JSON (np. Twilio 400/429) zwracamy jako…, _send()

### Community 93 - "Routes: two fleets, runs 6:00/14:00, OR-Tools VRP"
Cohesion: 0.67
Nodes (4): OR-Tools VRP, 1 vehicle per fleet, depot MPO Nowohucka 1, straight line x1.3, Routes: two fleets, runs 6:00/14:00, OR-Tools VRP, ortools 9.15, OSRM, multiple vehicles per fleet, time windows

### Community 95 - "database_url"
Cohesion: 0.60
Nodes (4): database_url(), DATABASE_URL z env; Coolify/Heroku podają postgres(ql)://, a my używamy…, test_database_url_defaults_to_sqlite(), test_database_url_uses_psycopg3_for_postgres()

### Community 97 - "jw"
Cohesion: 0.67
Nodes (3): Fw(), jw(), qw()

### Community 98 - "ia"
Cohesion: 0.67
Nodes (3): ia(), oA(), rA()

### Community 99 - "je"
Cohesion: 0.67
Nodes (3): je(), Lh(), qe()

## Ambiguous Edges - Review These
- `psycopg[binary] 3.3.6` → `Real bin positions from OSM cached in data/*.geojson`  [AMBIGUOUS]
  DECYZJE.md · relation: conceptually_related_to

## Knowledge Gaps
- **107 isolated node(s):** `Ściągawka: trudne pytania`, `Stan`, `Do zrobienia (kolejność)`, `Decyzje autora (4.10, ok. 00:40)`, `Ważne fakty i grabie` (+102 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `psycopg[binary] 3.3.6` and `Real bin positions from OSM cached in data/*.geojson`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Point` connect `import_points` to `reset`, `test_perspektywy.py`, `simulation.py`, `point_states`, `open_api.py`, `ui.py`, `dashboard_api.py`, `ApiError`, `test_dashboard.py`, `test_fairy.py`, `Filters`, `test_routes.py`, `test_photos.py`, `test_poprawki_jury.py`, `models.py`, `history.py`, `now`, `dashboard.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `import_points()` connect `import_points` to `reset`, `test_perspektywy.py`, `simulation.py`, `point_states`, `test_photos.py`, `test_dashboard.py`, `test_fairy.py`, `fetch_osm.py`, `test_routes.py`, `test_poprawki_jury.py`, `models.py`, `traffic.py`, `now`, `test_urzadzenia.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `now()` connect `now` to `ui.py`, `test_photos.py`, `zglos`, `test_poprawki_jury.py`, `_item`, `details`, `models.py`, `reset`, `test_perspektywy.py`, `simulation.py`, `dashboard_api.py`, `device_token`, `llm.py`, `ApiError`, `test_dashboard.py`, `get`, `traffic.py`, `kosz_json`, `render`, `point_states`, `open_api.py`, `generate`, `Filters`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `E()` (e.g. with `U()` and `a()`) actually correct?**
  _`E()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 104 inferred relationships involving `i()` (e.g. with `A()` and `aA()`) actually correct?**
  _`i()` has 104 INFERRED edges - model-reasoned connections that need verification._
- **Are the 98 inferred relationships involving `r()` (e.g. with `echarts.min.js` and `A()`) actually correct?**
  _`r()` has 98 INFERRED edges - model-reasoned connections that need verification._