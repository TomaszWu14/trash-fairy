# Graph Report - trash-fairy  (2026-10-03)

## Corpus Check
- Corpus is ~15,676 words - fits in a single context window. You may not need a graph.

## Summary
- 364 nodes · 925 edges · 15 communities
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 135 edges (avg confidence: 0.93)
- Token cost: 118,876 input · 0 output

## Community Hubs (Navigation)
- API i snapshot panelu
- Import OSM i model punktów
- Prognoza i wydarzenia
- Trasy i porównanie
- Aplikacja Flask i widoki
- Panel dyspozytora (JS)
- Testy API i health
- Decyzje: prognoza i trasy
- Przycisk, zgłoszenia, stan
- Stack i dane OSM
- Symulacja i zegar demo
- Koncepcja i zasady pracy
- Pobieranie z Overpass
- Rola AI (etapy 5–6)
- Ekrany i styl UI

## God Nodes (most connected - your core abstractions)
1. `Point` - 41 edges
2. `simulate()` - 35 edges
3. `point_states()` - 29 edges
4. `import_points()` - 27 edges
5. `Emptying` - 26 edges
6. `Report` - 20 edges
7. `Event` - 19 edges
8. `build_profiles()` - 17 edges
9. `Press` - 16 edges
10. `record_press()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `test_button_page()` --uses--> `Point`  [INFERRED]
  tests/test_api.py → app/models.py
- `Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js` --semantically_similar_to--> `Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report`  [INFERRED] [semantically similar]
  CLAUDE.md → docs/KONCEPCJA.md
- `Point details section with Chart.js chart` --implements--> `85% crossing time with in-hour interpolation, interval from p80/p20`  [INFERRED]
  app/templates/panel.html → DECYZJE.md
- `test_changes_only_when_version_moves()` --uses--> `Point`  [INFERRED]
  tests/test_api.py → app/models.py
- `test_clock_endpoints()` --uses--> `Point`  [INFERRED]
  tests/test_api.py → app/models.py

## Import Cycles
- 3-file cycle: `app/__init__.py -> app/api.py -> app/forecast.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/cli.py -> app/osm_import.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/state.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/clock.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/events.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/reports.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/routes.py -> app/__init__.py`
- 3-file cycle: `app/__init__.py -> app/api.py -> app/simulation.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api.py -> app/comparison.py -> app/forecast.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api.py -> app/state.py -> app/forecast.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api.py -> app/forecast.py -> app/events.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api.py -> app/forecast.py -> app/simulation.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/reports.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/cli.py -> app/clock.py -> app/simulation.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api.py -> app/state.py -> app/reports.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api.py -> app/state.py -> app/simulation.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api.py -> app/comparison.py -> app/events.py -> app/__init__.py`
- 4-file cycle: `app/__init__.py -> app/api.py -> app/comparison.py -> app/routes.py -> app/__init__.py`

## Hyperedges (group relationships)
- **Main path: press -> report merge -> state -> route** — app_templates_przycisk_press_click_handler, decyzje_report_table_merging, decyzje_report_accuracy_reliability, decyzje_state_max_rule, decyzje_route_point_selection, docs_koncepcja_main_path [INFERRED 0.85]
- **Forecast pipeline: weekly profile + events -> 85% crossing -> MAE** — decyzje_weekly_profile, decyzje_event_multiplier, decyzje_crossing_85_interval, decyzje_mae_evaluation, decyzje_forecast_on_demand, docs_koncepcja_forecast [INFERRED 0.95]
- **Routing and before/after comparison** — decyzje_route_point_selection, decyzje_ortools_vrp, decyzje_before_after_comparison, decyzje_fixed_schedule_simulation, app_templates_panel_routes_section, app_templates_panel_compare_section [INFERRED 0.85]

## Communities (15 total, 0 thin omitted)

### Community 0 - "API i snapshot panelu"
Cohesion: 0.08
Nodes (45): changes(), clock_advance(), clock_reset(), comparison(), point_detail(), points(), press(), _r() (+37 more)

### Community 1 - "Import OSM i model punktów"
Cohesion: 0.09
Nodes (28): seed_command(), distance_m(), Point, bin_rate(), import_points(), load_cache(), select_spaced(), hour_floor() (+20 more)

### Community 2 - "Prognoza i wydarzenia"
Cohesion: 0.11
Nodes (23): events_near(), import_events(), multiplier(), build_profiles(), first_crossing(), forecast_quality(), point_forecasts(), point_series() (+15 more)

### Community 3 - "Trasy i porównanie"
Cohesion: 0.10
Nodes (25): compare(), fixed_selects(), following_run(), is_run(), run_policy(), _cell(), next_runs(), plan_routes() (+17 more)

### Community 4 - "Aplikacja Flask i widoki"
Cohesion: 0.10
Nodes (13): clear_cache(), clear_cache(), create_app(), database_url(), button(), health(), panel(), app() (+5 more)

### Community 5 - "Panel dyspozytora (JS)"
Cohesion: 0.15
Nodes (22): apply(), clockAction(), describe(), esc(), eventLayer, hhmm(), KIND, loadRoutes() (+14 more)

### Community 6 - "Testy API i health"
Cohesion: 0.15
Nodes (9): demo(), press(), props(), test_button_page(), test_changes_only_when_version_moves(), test_clock_endpoints(), test_main_path_press_turns_point_red_and_top_of_list(), test_presses_from_many_people_merge_into_one_report() (+1 more)

### Community 7 - "Decyzje: prognoza i trasy"
Cohesion: 0.18
Nodes (6): Routes for next run section, Forecast: weekly profile + event multiplier, 85% crossing, MAE, Routes: two fleets, runs 6:00/14:00, OR-Tools VRP, ortools 9.15, OSRM, multiple vehicles per fleet, time windows, Route-aware forecast (future emptyings in trajectory)

### Community 8 - "Przycisk, zgłoszenia, stan"
Cohesion: 0.19
Nodes (7): Point list (text alternative to map) and legend, 'Sytuacja teraz' summary with press->report counter, Press click handler (POST /api/press), Main path: press -> state change -> to-empty list -> route -> AI report, Point state = max(forecast, report x reliability), thresholds 60/85, Reports and anti-spam rules (merge 15 min, reliability last 10, flag), Test plan (~10 pytest tests, Claude mocked)

### Community 9 - "Stack i dane OSM"
Cohesion: 0.15
Nodes (7): Stack: Flask + SQLAlchemy + Postgres/SQLite + Leaflet + Chart.js, Architecture: Flask app factory, tables point/press/emptying/photo_analysis/event/forecast/route/report, OpenStreetMap data, ODbL 1.0, Flask 3.1.3, Flask-SQLAlchemy 3.1.1, gunicorn 26.2.0, psycopg[binary] 3.3.6

### Community 10 - "Symulacja i zegar demo"
Cohesion: 0.18
Nodes (6): Before/after 4 weeks section, Demo clock header (advance +1 h, reset), Before/after comparison: fixed schedule vs Trash Fairy, Investment recommendations (compactor, bigger bin, shelter intervention), Synthetic data: 8 weeks, OSM-driven fill rates, trolled buttons, frozen demo clock, Authorization for demo clock endpoints /api/clock/*

### Community 11 - "Koncepcja i zasady pracy"
Cohesion: 0.20
Nodes (8): Trash Fairy work rules (CLAUDE.md), Decision log (DECYZJE.md), Competition: Mr Fill, Wroclaw/Sierpc/Rzeszow sensors, Trash Fairy concept (KONCEPCJA.md), Out of scope list (section 16), Problem: Krakow street bins overflow on fixed MPO schedule, Trash Fairy README, Roadmap (ROADMAPA.md)

### Community 12 - "Pobieranie z Overpass"
Cohesion: 0.22
Nodes (3): classify(), main(), to_feature()

### Community 13 - "Rola AI (etapy 5–6)"
Cohesion: 0.24
Nodes (9): 'Wrozka podpowiada' placeholder card, app/llm.py gateway (ask, ask_json), AI role: Vision, event parsing, 'Wrozka podpowiada' report, Events from Karnet Krakow via Claude + Nominatim, Photo analysis JSON schema (fill_level, misuse, damage, confidence), Shelter -> bin rule (200 m, 48 h), Causal chain: overflowing shelter -> household bags in street bins, Stage 5: Claude Vision crew view, misuse, shelter->bin rule (+1 more)

### Community 14 - "Ekrany i styl UI"
Cohesion: 0.33
Nodes (6): Dispatcher panel template (panel.html), Point details section with Chart.js chart, Virtual button page (przycisk.html), Screens: dispatcher panel, point details, virtual button, jury mode, crew view, methodology, Style: Planty green + gold panel, magic violet/pink for AI and button, All operational data synthetic (permanent demo bar)

## Ambiguous Edges - Review These
- `Real bin positions from OSM cached in data/*.geojson` → `psycopg[binary] 3.3.6`  [AMBIGUOUS]
  DECYZJE.md · relation: conceptually_related_to

## Knowledge Gaps
- **24 isolated node(s):** `map`, `KIND`, `markers`, `eventLayer`, `routeLayers` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 110 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Real bin positions from OSM cached in data/*.geojson` and `psycopg[binary] 3.3.6`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Point` connect `Import OSM i model punktów` to `API i snapshot panelu`, `Prognoza i wydarzenia`, `Trasy i porównanie`, `Aplikacja Flask i widoki`, `Testy API i health`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `simulate()` connect `Import OSM i model punktów` to `API i snapshot panelu`, `Prognoza i wydarzenia`, `Trasy i porównanie`, `Aplikacja Flask i widoki`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `point_states()` connect `API i snapshot panelu` to `Import OSM i model punktów`, `Prognoza i wydarzenia`, `Trasy i porównanie`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `Point` (e.g. with `point_detail()` and `press()`) actually correct?**
  _`Point` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `simulate()` (e.g. with `Emptying` and `Event`) actually correct?**
  _`simulate()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `point_states()` (e.g. with `Emptying` and `Press`) actually correct?**
  _`point_states()` has 3 INFERRED edges - model-reasoned connections that need verification._