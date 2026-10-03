# Trash Fairy – wdrożenie ekranu „Zgłoś kosz” (PWA dla mieszkańców)

Instrukcja dla sesji Claude Code. Cel: zbudować publiczny ekran zgłoszenia zapełnienia kosza, na który mieszkaniec trafia z kodu QR na koszu (bez logowania). Zgłoszenie ma się pojawić na mapie dyspozytora w ≤ 2 s. Obecny endpoint `/jury` musi dalej działać (może przekierowywać na nowy ekran z losowym koszem przy Rynku).

## Zawartość paczki

| Plik | Do czego |
|---|---|
| `design/ekran-zgloszenia.dc.html` | **Wzór ekranu we wszystkich stanach.** Jeden komponent; stan wybiera prop `screen` (`start`, `sending`, `sent`, `dup`, `offline`, `far`, `limit`, `error`, `nosignal`), dodatkowo `member` (true/false), `theme` (light/dark), `layout` (phone/tablet/desktop), `chosen` (full/over/broken). Tokeny kolorów: obiekt `TH` w skrypcie. Teksty: dokładnie te z markupu. Format `.dc.html` (`{{…}}`, `<sc-if>`, `<sc-for>`, `DCLogic`) to tylko format edytora – **przepisz na zwykły HTML/CSS/JS, nie kopiuj runtime'u**. |
| `design/komponenty-i-tokeny.dc.html` | Karta komponentów: przycisk zgłoszenia (3 warianty + wysyłanie + wyłączony), badge stanów, karta kosza, mini-mapa, oś statusu, toast offline, pusty stan, błąd, kolory, typografia, odstępy. |
| `design/pwa.dc.html` | Ikona (SVG do wycięcia), splash, `theme_color`, wygląd po instalacji. |
| `map/krakow-basemap.svg` | Statyczny podkład OSM centrum Krakowa – fallback mini-mapy offline. Punkt (lon, lat) → piksel: patrz sekcja „Mini-mapa”. |
| `zrzut-*.png` | (dodaj sam) zrzuty z kanwy: A, B, C, brzegowe, tablet, desktop. |

## Technologia

- Zwykły HTML + CSS + vanilla JS, bez frameworków. Jedna strona, np. `GET /zglos/<bin_id>` (Flask + Jinja), cała zmiana stanów po stronie klienta, bez przeładowań.
- PWA: `manifest.webmanifest` + service worker (cache powłoki strony, Background Sync dla kolejki offline).
- Font IBM Plex Sans 400/500/600/700 (self-host lub Google Fonts), `font-variant-numeric: tabular-nums`.
- Tryb jasny/ciemny przez `prefers-color-scheme` + zmienne CSS (wartości z `TH.light` i `TH.dark`).
- Bez ciężkich animacji. Jedyne „ruchy”: zmiana treści przycisku, pasek postępu (statyczny lub prosta transycja szerokości).

## Układ telefonu (390×844, mobile-first)

1. **Nagłówek 56 px** (granat `#0E1222`): „Trash Fairy” + gwiazdka (SVG), podpis „MPO Kraków · zgłoś stan kosza”, żółty chip „Demo · sob. 03.10, 13:24” (tylko w trybie demo).
2. **Mini-mapa** 16 px od krawędzi, wysokość 148 px (112 px gdy jest baner, 120 px po wysłaniu), promień 16. Kosz na środku, sąsiednie kosze małymi znacznikami, niebieska kropka „Ty”, chip „Jesteś ok. X m od kosza”, atrybucja OSM.
3. **Karta kosza**: nazwa 24/30 bold, adres + typ 16 px, ramka ze statusem „Szacujemy 62 %. Odbiór planowo ok. 14:00.” + pasek 8 px.
4. **Arkusz przypięty do dołu** (białe tło, górne rogi 20 px, cień do góry): „Co widzisz?” + „Jedno dotknięcie wysyła zgłoszenie.”, 3 przyciski (min. 72 px, etykieta 20 px bold, podpis 16 px), pod nimi „Dodaj zdjęcie” i „Komentarz” (48 px, opcjonalne, nie blokują wysyłki), linia prywatności z kłódką.
5. Wszystko klikalne w dolnych 60 % ekranu. Środkowa część przewija się, gdy brak miejsca – arkusz zostaje przy dole.

**Tablet 768 / desktop 1024**: dwie kolumny – mapa po lewej na całą wysokość (336 / 528 px szerokości), po prawej karta kosza i arkusz. Podpis w nagłówku: „Kraków nie potrzebuje więcej koszy, potrzebuje wróżki.”

## Przyciski zgłoszenia (kolor + kształt + znak + słowo)

| id (API) | Etykieta | Podpis | Ikona | Tło / obwódka (jasny) |
|---|---|---|---|---|
| `full` | Pełny | Nie mieści się więcej | bursztynowy romb ↑ `#F0A500`, znak czarny | `#FFF3D1` / `#B57D00` |
| `overflow` | Przepełniony, odpady obok | Worki lub śmieci wokół kosza | czerwony kwadrat ! `#C40000` | `#FBE4E4` / `#C40000` |
| `damaged` | Uszkodzony | Zepsuty, przewrócony, bez klapy | grafitowy trójkąt ! `#2F3A41` | `#E8EBED` / `#2F3A41` |

Wyłączony: tło `#EFECE5`, obwódka `#CFC9BE`, ikona opacity .4, atrybut `disabled`. W trybie ciemnym wartości z `TH.dark`.

## Przepływ i stany

**Jedno dotknięcie = wysyłka.** Żadnego okna „Czy na pewno?”.

1. **A `start`** – jak wyżej.
2. **B `sending`** – dotknięty przycisk zamienia się w miejscu w granatową kartę „Wysyłamy: Pełny” z paskiem postępu (żółty) i przyciskiem „Cofnij” (44 px). Pozostałe przyciski wyłączone. Wysyłkę opóźnij o ok. 1,5 s (okno na „Cofnij”), potem `POST`.
3. **C `sent`** – arkusz zamienia się w potwierdzenie (bez nowej strony):
   - fioletowy dymek z ✓ + „Dziękujemy. Dyspozytor widzi zgłoszenie.”
   - „Przewidywany odbiór” + **„ok. 14:00”** 48 px + „Twoje zgłoszenie: Pełny”
   - oś statusu `<ol>`: Przyjęte 13:24 → Zaplanowane (kurs 14:00) → Opróżnione
   - „2 inne osoby też to zgłosiły.”
   - uczestnik programu: fioletowa karta „+10 pkt po potwierdzeniu przez ekipę” + pseudonim, odznaka, miejsce w dzielnicy; anonim: dyskretne zaproszenie do „Przyjaciół Wróżki” z linkiem „Więcej”
   - akcje: „Śledź status” (główny, 56 px), „Kosze w okolicy”, „Zgłoś inny kosz”
   - znacznik kosza na mini-mapie zmienia się na fioletowy dymek „zgłoszenie”.

### Stany brzegowe

| Stan | Kiedy | Co pokazać |
|---|---|---|
| `dup` | serwer scalił z otwartym zgłoszeniem < 15 min | jak C, nagłówek „Wróżka już wie!”, treść „Twoje naciśnięcie dołączyliśmy do zgłoszenia z 13:11.”, „Przyjęte 13:11”, „Ty i 2 inne osoby zgłosiły ten kosz.” |
| `offline` | brak sieci przy wysyłce | granatowy toast „Brak zasięgu. Zgłoszenie jest zapisane w telefonie.”; wybrany przycisk → karta z przerywaną obwódką „Pełny · w kolejce od 13:24 / Wyślemy, gdy wróci zasięg. Możesz zamknąć aplikację.” Zapis w IndexedDB + Background Sync; po wysłaniu → C. |
| `far` | GPS > 150 m od kosza | baner „Jesteś ok. 280 m od tego kosza” + wyjaśnienie bez oskarżeń; przyciski wyłączone; akcje „Odśwież lokalizację”, „Kosze w pobliżu”; na mapie przerywany okrąg 150 m i kropka „Ty” poza nim. Brak zgody na GPS → nie blokuj, wyślij z flagą `location: null`. |
| `limit` | serwer zwrócił 429 | baner „Dziękujemy za Twoją pomoc… Kolejne możesz wysłać o 13:54.” (godzina z `retry_at`); przyciski wyłączone. |
| `error` | 5xx / timeout | wybrany przycisk → karta „Pełny · nie udało się wysłać / To problem po naszej stronie. Zgłoszenie czeka w telefonie.” + „Spróbuj ponownie” (52 px). Nigdy surowy kod błędu. |
| `nosignal` | kosz ma flagę „przycisk bez sygnału 48 h” | baner z grafitowym trójkątem „Przycisk na koszu chwilowo nie działa / Zgłoszenie przez telefon działa normalnie…”; przyciski aktywne. |

## Kontrakt API (propozycja – dopasuj do istniejącego backendu)

- `GET /api/bins/<bin_id>/public` → `{id, name, address, type, capacity_l, lat, lon, fill_pct, next_pickup: "14:00", next_route_name, button_offline: bool, neighbors:[{lat,lon,state}]}`. **Nie zwracaj** `button_reliability` ani innych danych wewnętrznych.
- `POST /api/reports` body `{bin_id, kind: full|overflow|damaged, lat?, lon?, accuracy_m?, client_id, created_at, photo_id?, comment?}`:
  - `201` → `{status:"accepted", accepted_at, eta:"14:00", route:"kurs 14:00", others_count}` → stan C
  - `200` → `{status:"merged", merged_with_at:"13:11", others_count}` → `dup`
  - `422 {reason:"too_far", distance_m}` → `far`
  - `429 {retry_at:"13:54"}` → `limit`
  - `5xx` → `error`
- `client_id`: losowy UUID w `localStorage` (bez konta, tylko do limitu i scalania).
- Po `201/200` backend podnosi priorytet punktu i emituje zdarzenie do panelu dyspozytora (ten sam mechanizm co dziś przy `/jury`, ≤ 2 s).
- `GET /api/reports/<id>/status` dla „Śledź status”.

## Mini-mapa

- Domyślnie Leaflet (lekki, bez frameworka) z kafelkami CARTO Positron, `zoomControl:false`, `dragging` włączone, zoom 17, kosz na środku. Ciemny motyw: CARTO Dark Matter.
- Fallback offline: `map/krakow-basemap.svg` jako `<img>` 3200×1800 przesunięty tak, by kosz był na środku. Przeliczenie (dla SVG 1600×900, skala ×2 = 3200×1800):
  `x = (lon − 19.912) · 71 472.5 · 0.27983 · 2`, `y = (50.070048 − lat) · 110 540 · 0.27983 · 2`. Kosz Rynek 03 (50.0618, 19.9360) → ok. (960, 510); przesunięcie obrazka: `left = szerokośćMapy/2 − x`, `top = wysokośćMapy/2 − y`. 1 px w skali ×2 ≈ 1,79 m (okrąg 150 m ≈ 84 px promienia).
- Znaczniki stanów identyczne jak w panelu (patrz `komponenty-i-tokeny.dc.html` → „Badge stanu”).

## PWA

- `manifest.webmanifest`: `name` „Trash Fairy”, `short_name` „Trash Fairy”, `start_url` „/zglos”, `display` „standalone”, `theme_color` `#0E1222`, `background_color` `#0E1222`, `lang` „pl”, ikony 192/512 + maskable (SVG z `pwa.dc.html`, motyw w środkowych 80 %).
- `<meta name="theme-color" content="#0E1222">` oraz wariant `media="(prefers-color-scheme: dark)"` → `#05070F`.
- Splash: granat, gwiazdka, „Trash Fairy”, hasło, „dla MPO Kraków”.

## Dostępność i ton

- Tekst podstawowy ≥ 16 px, przyciski ≥ 19 px (u nas 20), kontrast ≥ 4,5:1, cele dotyku ≥ 44 px (przyciski zgłoszenia ≥ 64 px).
- Prawdziwe `<button>`, `aria-live="polite"` na obszarze zmiany stanu (B/C/błędy), `role="alert"` dla błędu, oś statusu jako `<ol>`.
- Ton: przyjazny, konkretny, po polsku, bez wykrzykników w komunikatach systemowych (wyjątek: „Wróżka już wie!”).
- Widoczna prywatność: „Zapisujemy tylko czas i miejsce zgłoszenia. Bez konta i numeru telefonu.”

## Kryteria odbioru

- [ ] Otwarcie z QR → jedno dotknięcie → potwierdzenie, bez przeładowania strony.
- [ ] Zgłoszenie widać na mapie dyspozytora w ≤ 2 s; `/jury` nadal działa.
- [ ] Wszystkie stany (A, B, C anonim/uczestnik, 6 brzegowych) odtworzone wg `ekran-zgloszenia.dc.html`.
- [ ] 390, 768, 1024 px bez poziomego scrolla; tryb jasny i ciemny.
- [ ] Offline: zgłoszenie nie ginie po zamknięciu aplikacji, wysyła się po powrocie sieci.
- [ ] Brak danych wewnętrznych (wiarygodność przycisku) w odpowiedzi publicznego API i na ekranie.
- [ ] Lighthouse: PWA installable, dostępność ≥ 95.
