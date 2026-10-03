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

**Stan prac:** etap 1. Mapa 60 koszy ulicznych i 12 altan z OSM, 8 tygodni symulowanej historii, panel dyspozytora.

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

**Status:** stage 1. Map of 60 street bins and 12 housing-estate shelters from OSM, 8 weeks of simulated history, dispatcher panel.

**Run:** see the commands above. **Data:** © OpenStreetMap contributors (ODbL 1.0). All operational data is synthetic.
**AI tools:** Claude Code during development, Claude API for photo analysis and reports (later stages).

**Transparency:** the concept was prepared before the event (`docs/KONCEPCJA.md`, no code).
**All code was written during HackYeah, 3–4 Oct 2026**, starting at the `start-hackyeah` tag.
