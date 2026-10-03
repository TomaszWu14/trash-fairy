# Trash Fairy – wdrożenie widoku C „Pokaz dla jury”

Instrukcja dla sesji Claude Code. Cel: przebudować panel dyspozytora (obecnie `/` na porcie 5050) według projektu z `design/widok-c.dc.html`, zachowując istniejącą logikę predykcji, symulacji czasu i endpoint `/jury`.

## Zawartość paczki

| Plik | Do czego |
|---|---|
| `design/widok-c.dc.html` | Projekt referencyjny. Markup + CSS to wzór wyglądu. Format `.dc.html` (szablon `{{…}}`, `<sc-for>`, `<sc-if>`, klasa `DCLogic`) to tylko format edytora – **nie kopiuj runtime'u**, przepisz na Jinja/JS aplikacji. |
| `map/krakow-basemap.svg` | Statyczny podkład (ulice OSM, Wisła, Planty) – tylko jako fallback offline. Domyślnie używamy Leafleta z kafelkami. |
| `map/mapdata.json` | Pozycje punktów demo, strefy wydarzeń, trasy po ulicach w układzie 1600×900 px. |
| `map/build.py` | Skrypt, który wygenerował podkład i trasy (shapely + Dijkstra po sieci ulic OSM). Referencja, nie uruchamiaj w aplikacji. |
| `map/podglad-podkladu-i-tras.png` | Podgląd podkładu z trasami. |

## Układ (1440 px laptop, 1920×1080 projektor)

1. **Nagłówek** (granat `#0E1222`, wys. 64 px, flex-wrap): „Trash Fairy” + gwiazdka (SVG, nie emoji) · podtytuł · **grupa symulacji w jednej ramce** [zegar, „sob. 03.10.2026 · 13:30”, „Przewiń +1 h”, „Reset”] · link „Metodologia” · badge „Dane demonstracyjne · symulacja” (`flex:none; white-space:nowrap` – nie może być ucięty).
2. **4 karty kroków** (grid `repeat(auto-fit, minmax(240px,1fr))`, gap 16): 1 Problem (przepełnione teraz) → 2 Predykcja (zagrożone przed kolejnym kursem) → 3 Trasa (km + liczba punktów) → 4 Efekt (przed/po). Aktywna karta: tło granatowe, żółty numer, pasek postępu 6 px u góry (żółty dla kroków ≤ aktywnego). Kliknięcie zmienia widok mapy.
3. **Główna część**: mapa (flex 999, `aspect-ratio:16/9`, radius 16, cień) + prawa kolumna 340–400 px.
4. **Prawa kolumna**: fioletowa karta „Zgłoś pełny kosz” (`#2A1A63`): kropka „Na żywo”, nagłówek, prawdziwy QR do `/jury`, 3 kroki, URL, „Ostatnie: <nazwa ostatniego zgłoszenia>”. Pod nią „Najbliższe przepełnienia” – top 3 z listy zagrożonych.

## Zachowanie kroków

| Krok | Mapa |
|---|---|
| 1 Problem | trasy ukryte, punkty bez stanu „przepełniony” przyciemnione (`opacity:.2`) |
| 2 Predykcja | trasy ukryte, przyciemnione wszystko poza „zbliża się do pełna” |
| 3 Trasa (domyślny) | trasy widoczne + numery przystanków (1–6, 7–28…) |
| 4 Efekt | zamiast mapy 3 duże karty „Przed i po: 4 tygodnie” (przepełnienia, km, kursy) |

Opis kroku: półprzezroczysty panel w lewym górnym rogu mapy (żółty numer + tekst 18 px).

## Mapa – Leaflet

- Kafelki jasne, spokojne: CARTO Positron `https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png` z atrybucją „© OpenStreetMap contributors © CARTO”. Fallback offline: `L.imageOverlay('krakow-basemap.svg', bounds)` z granicami z `build.py` (lon 19.912–19.992, lat wg `mapdata.json` → `lat`).
- Widok startowy: centrum ok. `[50.0555, 19.952]`, zoom 14, tak by mieściły się Stare Miasto, Kazimierz, Grzegórzki i baza.
- **Znaczniki = `L.divIcon`** z klasami z projektu (`.mk .st-ok|st-near|st-full|st-report|st-warn`, `.alt` dla altan). Stan = kolor + kształt + znak:
  - OK: zielone koło ✓ `#127A3E`
  - Zbliża się do pełna: bursztynowy romb ↑ `#F0A500` (znak czarny)
  - Przepełniony: czerwony kwadrat ! `#C40000`
  - Zgłoszenie mieszkańca/jury: fioletowy dymek … `#5B2A9A`
  - Ostrzeżenie czujnika: grafitowy trójkąt ! `#2F3A41`
  - Altana: podwójna obwódka
  - Przepełnione i zgłoszenia: pulsujący pierścień (`.pulse`, wyłączany przez `prefers-reduced-motion`)
- **Klastrowanie**: `Leaflet.markercluster`, `iconCreateFunction` → koło z liczbą, obwódka 4 px w kolorze **najgorszego stanu** w klastrze + mały znacznik tego stanu w prawym górnym rogu. Kolejność ważności: full > report > near > warn > ok. Rozmiar: ≥20 → 60 px, ≥9 → 50 px, inaczej 44 px. `showCoverageOnHover:false`, `spiderfyOnMaxZoom:true`.
- **Strefy wydarzeń**: `L.circle`, obrys 2 px przerywany `#C2570C`, delikatne kreskowanie/wypełnienie 10%, etykieta „Wydarzenie · <nazwa>”.
- **Baza MPO**: granatowy kwadrat z ikoną śmieciarki + etykieta „Baza MPO / ul. Nowohucka 1”.
- **Trasy po ulicach**: dla kolejności przystanków z istniejącego planera pobierz geometrię z OSRM (`https://router.project-osrm.org/route/v1/driving/{lon,lat;…}?overview=full&geometries=geojson`). Cache wyniku w pamięci/pliku. Jeśli OSRM nie odpowie → linie proste + komunikat „przybliżenie w linii prostej”. Kosze: niebieska `#0050B5` 5 px z białym obrysem 10 px + animowane białe kreski (`stroke-dasharray:2 16`, animacja `stroke-dashoffset`) pokazujące kierunek. Altany: fioletowa `#8E2C8C` przerywana. Powrót do bazy: kropkowana, cieńsza.
- Km w KPI liczone tak jak dziś (linia prosta × 1,3), dopóki nie przejdziesz na km z OSRM – wtedy zmień tekst w „Metodologii”.
- Na mapie: legenda (półprzezroczysty panel, lewy dół), strzałka N + skala (prawy górny), atrybucja OSM.

## Tokeny

- Font: IBM Plex Sans 400/500/600/700 (Google Fonts), `font-variant-numeric: tabular-nums`.
- Skala typografii: 12 / 13 / 14 / 16 / 18 / 24 / 26 / 32 / 44 / 64 px. Odstępy w siatce 8 px (8/12/16/20/24/40).
- Tło strony `#F6F4EF`, karty `#FFFFFF`, tekst `#0E1222`, drugorzędny `#454B57`, akcent marki `#CDBBFF`, żółty `#FFD34D`.
- Kontrast min. WCAG AA; przyciski min. 44 px wysokości; prawdziwe `<button>`/`<a>`; `aria-pressed` na kartach kroków.

## Dane (bez zmian logiki)

- KPI i listy biorą wartości z istniejącego API/symulacji (przepełnione teraz, zagrożone przed kolejnym kursem, trasa najbliższego kursu, przed/po 4 tyg.). Wartości `[XX]` w projekcie = miejsca na prawdziwe liczby z sekcji „Przed i po”.
- Karta „Najbliższe przepełnienia”: tag pilności (Krytyczne <3 h, Wysokie <6 h, Średnie <24 h, Niskie), „85% ok. HH:MM”, „za X h Y min”, pasek czasu: teraz → odbiór w trasie (niebieska kreska) → próg 85% (bursztynowa kropka) → kolejny kurs; zakreskowany odcinek = czas powyżej 85% bez odbioru.
- „Przewiń +1 h” i „Reset” działają jak dziś; po zmianie czasu odśwież KPI, listę i mapę.
- Zgłoszenie z `/jury` → punkt zmienia stan na „zgłoszenie”/„przepełniony” w ≤ 2 s (zachowaj obecny mechanizm odświeżania) i pojawia się jako „Ostatnie: …” w karcie QR.

## Kryteria odbioru

- [ ] Wygląd zgodny z `design/widok-c.dc.html` na 1440×900 i 1920×1080, bez poziomego scrolla, badge demo nieucięty.
- [ ] 4 kroki przełączają mapę zgodnie z tabelą.
- [ ] Brak nachodzących znaczników – klastry z liczbą i kolorem najgorszego stanu.
- [ ] Legenda: każdy stan ma kolor + kształt + etykietę.
- [ ] Trasy po ulicach (OSRM) z fallbackiem i opisem przybliżenia.
- [ ] QR prowadzi do `/jury`, zgłoszenie widać na mapie w ≤ 2 s.
- [ ] Nic nie zepsute w istniejących endpointach i symulacji.
