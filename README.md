# Trash Fairy ✨ — inteligentny odbiór odpadów dla Krakowa

> „Kraków nie potrzebuje więcej koszy, potrzebuje wróżki.”
> HackYeah 2026 · Smart City (zadanie otwarte)

[English below](#english)

## Problem
Kosze uliczne w centrum Krakowa (Planty, Rynek, Kazimierz) przepełniają się, zwłaszcza w weekendy i podczas wydarzeń.
MPO opróżnia je według stałego harmonogramu, a nie według potrzeb. Część problemu bierze się z przepełnionych
altan osiedlowych: mieszkańcy wynoszą domowe worki do koszy ulicznych (KRKnews, 8.09.2026).

## Rozwiązanie
Trash Fairy to mózg dla MPO, który nie zależy od sprzętu. Zbiera tanie sygnały (przycisk „PEŁNY?” na koszu, dane od ekip MPO,
zdjęcia), przewiduje zapełnienie, rozpoznaje przyczynę, planuje trasy i podpowiada, gdzie opłaca się czujnik,
kompaktor albo większy kosz. Decyzje podejmują jawne reguły w kodzie, a AI tylko opisuje i rozpoznaje.

**Stan prac:** etapy 1–4 gotowe. Etap 1–2: mapa 60 koszy i 12 altan z OSM, 8 tygodni symulowanej historii z naciśnięciami, wirtualny przycisk `/przycisk/<id>`, scalanie zgłoszeń i wiarygodność przycisków, stan na żywo w panelu (polling co 2 s), zegar demo z przewijaniem. Etap 3: prognoza z profilu tygodniowego i wydarzeń (godzina przekroczenia 85% z przedziałem, MAE), szczegóły punktu z wykresem. Etap 4: trasy OR-Tools dla dwóch flot (kosze, altany) z bazy MPO i porównanie 4 tygodni ze stałym harmonogramem.

## Uruchomienie
```bash
python -m venv .venv && .venv/Scripts/activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
flask --app app seed        # import punktów z data/*.geojson + symulacja historii
flask --app app run         # http://localhost:5000
python -m pytest -q
```
Docker: `docker build -t trash-fairy . && docker run -p 8000:8000 trash-fairy` (z `-e DATABASE_URL=...` dla PostgreSQL).

## Dane i licencje
- **OpenStreetMap:** pozycje koszy, altan, lokali i przystanków; podkład mapy. © OpenStreetMap contributors, licencja ODbL 1.0.
  Cache w `data/*.geojson`, pobrany przez `scripts/fetch_osm.py` (Overpass API).
- **Wszystkie dane operacyjne** (poziomy zapełnienia, opróżnienia) są **syntetyczne**. Panel pokazuje to na stałym pasku.
- Biblioteki: Flask, SQLAlchemy, Leaflet (BSD-2), Tailwind CSS i DaisyUI (MIT).

## Narzędzia AI
- **Claude Code** (Anthropic): pomoc przy programowaniu, testach i dokumentacji podczas HackYeah.
- **Claude API** (od etapu 5): analiza zdjęć, zamiana opisów wydarzeń na JSON, raport dla dyspozytora. Tylko przez `app/llm.py`.

## Przejrzystość
Koncepcja została przemyślana przed wydarzeniem i jest w `docs/KONCEPCJA.md` (bez kodu).
**Cały kod powstał podczas HackYeah, 3–4.10.2026.** Historię zmian pokazują commity od tagu `start-hackyeah`,
a uzasadnienia decyzji są w `DECYZJE.md`.

---

## English

**Trash Fairy** is a hardware-agnostic brain for Kraków's waste collection company (MPO). Street bins in the city centre
overflow because they are emptied on a fixed schedule, not on demand, and partly because residents dump household
bags from overflowing housing-estate shelters. Trash Fairy collects cheap signals (a "FULL? PRESS" button on the bin,
crew reports, photos), forecasts fill levels, detects the cause, plans routes and recommends where a sensor,
a compactor or a bigger bin pays off. All decisions are made by explicit rules in code. AI only describes and recognises.

**Status:** stages 1–4 done. Stages 1–2: OSM map of 60 bins and 12 shelters, 8 weeks of simulated history incl. button presses, virtual button `/przycisk/<id>`, report merging and button reliability, live dispatcher panel (2 s polling), demo clock with fast-forward. Stage 3: forecast from a weekly profile and events (time of crossing 85% with an interval, MAE), point details with a chart. Stage 4: OR-Tools routes for two fleets (bins, shelters) from the MPO depot and a 4-week comparison with the fixed schedule.

**Run:** see the commands above. **Data:** © OpenStreetMap contributors (ODbL 1.0). All operational data is synthetic.
**AI tools:** Claude Code during development, Claude API for photo analysis and reports (later stages).

**Transparency:** the concept was prepared before the event (`docs/KONCEPCJA.md`, no code).
**All code was written during HackYeah, 3–4 Oct 2026**, starting at the `start-hackyeah` tag.
