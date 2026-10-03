# Graph Report - trash-fairy  (2026-10-03)

## Corpus Check
- 48 files · ~37,428 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 620 nodes · 1555 edges · 22 communities
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 75 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f7eb3944`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_residents.py
- simulation.py
- test_forecast.py
- views.py
- models.py
- panel.js
- test_api.py
- 85% crossing time with in-hour interpolation, interval from p80/p20
- Reports and anti-spam rules (merge 15 min, reliability last 10, flag)
- Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js
- Before/after comparison on same fill increments (4 weeks)
- Trash Fairy README
- Brainstorm: przycisk dla mieszkańców, awarie, spam, wyświetlacz, program „Przyjaciele Wróżki”
- Events from data/events.json with crowd-scale multiplier (200m x1.3 / 400m x1.6 / 800m x2.0)
- Style: Planty green + gold panel, magic violet/pink for AI and button
- test_photos.py
- test_fairy.py
- api.py
- Kontekst MPO: dane do pitchu i porównania
- Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)
- OR-Tools VRP, 1 vehicle per fleet, depot MPO Nowohucka 1, straight line x1.3
- Photo analysis JSON schema (fill_level, misuse, damage, confidence)

## God Nodes (most connected - your core abstractions)
1. `import_points()` - 34 edges
2. `point_states()` - 34 edges
3. `Point` - 29 edges
4. `simulate()` - 29 edges
5. `record_press()` - 25 edges
6. `distance_m()` - 24 edges
7. `Emptying` - 24 edges
8. `now()` - 21 edges
9. `hour_floor()` - 18 edges
10. `reset()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Point details section with Chart.js chart` --implements--> `85% crossing time with in-hour interpolation, interval from p80/p20`  [INFERRED]
  app/templates/panel.html → DECYZJE.md
- `Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js` --semantically_similar_to--> `Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/KONCEPCJA.md
- `test_demo_starts_with_links_and_recommendations()` --calls--> `misuse_overview()`  [EXTRACTED]
  tests/test_photos.py → app/misuse.py
- `Stage 6: 'Wrozka podpowiada' report, Karnet, recommendations, jury mode` --references--> `Investment recommendations (compactor, bigger bin, shelter intervention)`  [INFERRED]
  ROADMAPA.md → docs/KONCEPCJA.md
- `All operational data synthetic (permanent demo bar)` --conceptually_related_to--> `Synthetic data: 8 weeks, OSM-driven fill rates, trolled buttons, frozen demo clock`  [INFERRED]
  README.md → docs/KONCEPCJA.md

## Import Cycles
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/karnet.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/osm_import.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/simulation.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/forecast.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/fairy.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/state.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/reports.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/photos.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/residents.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/routes.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/simulation.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/photos.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/reports.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/residents.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/simulation.py -> app/__init__.py`

## Hyperedges (group relationships)
- **Main path: press -> report merge -> state -> route** — app_templates_przycisk_press_click_handler, decyzje_report_table_merging, decyzje_report_accuracy_reliability, decyzje_state_max_rule, decyzje_route_point_selection, docs_koncepcja_main_path [INFERRED 0.85]
- **Routing and before/after comparison** — decyzje_route_point_selection, decyzje_ortools_vrp, decyzje_before_after_comparison, decyzje_fixed_schedule_simulation, app_templates_panel_routes_section, app_templates_panel_compare_section [INFERRED 0.85]
- **Forecast pipeline: weekly profile + events -> 85% crossing -> MAE** — decyzje_weekly_profile, decyzje_event_multiplier, decyzje_crossing_85_interval, decyzje_mae_evaluation, decyzje_forecast_on_demand, docs_koncepcja_forecast [INFERRED 0.95]

## Communities (22 total, 0 thin omitted)

### Community 0 - "test_residents.py"
Cohesion: 0.05
Nodes (86): Device, Emptying, PointAward, Press, Uczestnik programu „Przyjaciele Wróżki”. Bez danych osobowych: pseudonim + hash…, Punkty za trafne zgłoszenie (jedna nagroda na mieszkańca, punkt i dzień)., Fizyczny przycisk z wyświetlaczem e-papierowym przy punkcie (stan symulowany w…, Pojedyncze naciśnięcie przycisku. Scalanie w zgłoszenia: app/reports.py. (+78 more)

### Community 1 - "simulation.py"
Cohesion: 0.06
Nodes (62): distance_m(), Odległość w linii prostej (haversine), w metrach., Point, Kosz uliczny (kind='bin') albo altana osiedlowa (kind='shelter')., bin_rate(), import_points(), Import punktów demo z cache OSM (data/*.geojson) do bazy., Bierze do n punktów najbliżej centre, pomijając te bliżej niż min_gap_m od już… (+54 more)

### Community 2 - "test_forecast.py"
Cohesion: 0.07
Nodes (60): clear_cache(), compare(), fixed_selects(), following_run(), is_run(), Porównanie „przed i po” (koncepcja, sekcja 6.7): stały harmonogram MPO kontra…, Zwraca miary jednej polityki. `incs[pid][i]` = prawdziwy przyrost w godzinie…, Miary obu polityk na `weeks` tygodniach przed `cutoff` (pełna godzina). (+52 more)

### Community 3 - "views.py"
Cohesion: 0.13
Nodes (21): assumptions(), _env_float(), money(), money_assumptions(), Strona Metodologia: założenia czytane wprost ze stałych w kodzie + jawne…, [(obszar, założenie, wartość)] — wartości wprost z kodu., Przeliczenie wyniku porównania (4 tygodnie) na miesiąc, zł i CO₂ — wg jawnych…, button() (+13 more)

### Community 4 - "models.py"
Cohesion: 0.05
Nodes (67): cleanup_photos_command(), karnet_command(), Import punktów z data/*.geojson i wydarzeń z data/events.json, symulacja…, Usuwa pliki zdjęć starszych niż 7 dni (wyniki analiz zostają w bazie). Do crona., Pobiera wydarzenia z Karnet Kraków do data/karnet.json, importuje je i odtwarza…, seed_command(), advance(), Zegar demo: zamrożona sobota 13:30, przewijany o godzinę. Przewinięcie… (+59 more)

### Community 5 - "panel.js"
Cohesion: 0.12
Nodes (30): apply(), clockAction(), describe(), esc(), eventLayer, hhmm(), KIND, linkLayer (+22 more)

### Community 6 - "test_api.py"
Cohesion: 0.15
Nodes (12): neighbors_map(), demo(), press(), props(), fixture, Test 10 z sekcji 11: naciśnięcie → stan → punkt do opróżnienia., test_changes_only_when_version_moves(), test_clock_endpoints() (+4 more)

### Community 7 - "85% crossing time with in-hour interpolation, interval from p80/p20"
Cohesion: 0.24
Nodes (10): Decisions only by code rules, never AI, 85% crossing time with in-hour interpolation, interval from p80/p20, Panel shows system estimate, not simulation hidden truth, MAE 2.5 p.p. vs naive mean 7.3 p.p. on last week, no leakage, Route point selection: full now, crosses 85% before next run, or safety (bin 3 d, shelter 7 d), State = max(level, 100 x report reliability), Weekly 7x24 profile per point: mean and p20/p80, Forecast: weekly profile + event multiplier, 85% crossing, MAE (+2 more)

### Community 8 - "Reports and anti-spam rules (merge 15 min, reliability last 10, flag)"
Cohesion: 0.22
Nodes (10): Point list (text alternative to map) and legend, 'Sytuacja teraz' summary with press->report counter, Press click handler (POST /api/press), Flag 'check button' (<40% accurate in 7 days or 6 h overflow without press), Report accuracy decided by emptying (>=75%); reliability = accurate share of last 10, start 70%, Report table: presses merged within 15 min of first press, Soft press limit: 1 per 2 s per point, 120/h per IP, ProxyFix, Main path: press -> state change -> to-empty list -> route -> AI report (+2 more)

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

### Community 13 - "Events from data/events.json with crowd-scale multiplier (200m x1.3 / 400m x1.6 / 800m x2.0)"
Cohesion: 0.33
Nodes (7): 'Wrozka podpowiada' placeholder card, app/llm.py gateway (ask, ask_json), Events from data/events.json with crowd-scale multiplier (200m x1.3 / 400m x1.6 / 800m x2.0), AI role: Vision, event parsing, 'Wrozka podpowiada' report, 24 h plan and cut order, Events from Karnet Krakow via Claude + Nominatim, Stage 6: 'Wrozka podpowiada' report, Karnet, recommendations, jury mode

### Community 14 - "Style: Planty green + gold panel, magic violet/pink for AI and button"
Cohesion: 0.33
Nodes (7): Dispatcher panel template (panel.html), Point details section with Chart.js chart, Virtual button page (przycisk.html), Screens: dispatcher panel, point details, virtual button, jury mode, crew view, methodology, Style: Planty green + gold panel, magic violet/pink for AI and button, Map visual encoding: shape=type, colour+symbol=state (WCAG), All operational data synthetic (permanent demo bar)

### Community 15 - "test_photos.py"
Cohesion: 0.05
Nodes (53): ask(), ask_json(), available(), _create(), image_block(), LLMError, model(), Exception (+45 more)

### Community 16 - "test_fairy.py"
Cohesion: 0.09
Nodes (34): fairy_get(), fairy_refresh(), Nowy raport. Przy błędzie API: komunikat + ostatni raport (nigdy 500)., build_facts(), generate(), is_fresh(), latest(), Raport „Wróżka podpowiada” (koncepcja, sekcja 8): fakty liczy kod, Claude tylko… (+26 more)

### Community 17 - "api.py"
Cohesion: 0.11
Nodes (43): _analysis(), changes(), clock_advance(), clock_reset(), comparison(), current_resident(), device_selftest(), devices() (+35 more)

### Community 18 - "Kontekst MPO: dane do pitchu i porównania"
Cohesion: 0.50
Nodes (3): Harmonogram oczyszczania 08/2026 (arkusz „Kosze”), Jak działa MPO (informacja ogólna MPO Kraków), Kontekst MPO: dane do pitchu i porównania

### Community 19 - "Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)"
Cohesion: 0.33
Nodes (5): Cel, Poza zakresem (ROADMAPA), Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A), Testy, Zakres (wariant A)

### Community 20 - "OR-Tools VRP, 1 vehicle per fleet, depot MPO Nowohucka 1, straight line x1.3"
Cohesion: 0.50
Nodes (5): Routes for next run section, OR-Tools VRP, 1 vehicle per fleet, depot MPO Nowohucka 1, straight line x1.3, Routes: two fleets, runs 6:00/14:00, OR-Tools VRP, ortools 9.15, OSRM, multiple vehicles per fleet, time windows

### Community 21 - "Photo analysis JSON schema (fill_level, misuse, damage, confidence)"
Cohesion: 0.67
Nodes (4): Photo analysis JSON schema (fill_level, misuse, damage, confidence), Shelter -> bin rule (200 m, 48 h), Causal chain: overflowing shelter -> household bags in street bins, Stage 5: Claude Vision crew view, misuse, shelter->bin rule

## Ambiguous Edges - Review These
- `psycopg[binary] 3.3.6` → `Real bin positions from OSM cached in data/*.geojson`  [AMBIGUOUS]
  DECYZJE.md · relation: conceptually_related_to

## Knowledge Gaps
- **39 isolated node(s):** `map`, `KIND`, `markers`, `eventLayer`, `linkLayer` (+34 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `psycopg[binary] 3.3.6` and `Real bin positions from OSM cached in data/*.geojson`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `import_points()` connect `simulation.py` to `test_residents.py`, `test_forecast.py`, `models.py`, `test_api.py`, `test_photos.py`, `test_fairy.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `Point` connect `simulation.py` to `test_residents.py`, `test_forecast.py`, `views.py`, `models.py`, `test_api.py`, `test_photos.py`, `test_fairy.py`, `api.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `point_states()` connect `test_residents.py` to `simulation.py`, `test_forecast.py`, `test_api.py`, `test_fairy.py`, `api.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **What connects `map`, `KIND`, `markers` to the rest of the system?**
  _39 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_residents.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05165965404394577 - nodes in this community are weakly interconnected._
- **Should `simulation.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06436487638533675 - nodes in this community are weakly interconnected._