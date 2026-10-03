# Trash Fairy – wyświetlacz e-papierowy na koszu (800×480)

Instrukcja dla sesji Claude Code. Cel: dodać do aplikacji Trash Fairy obsługę ekranu e-papierowego na koszu: logikę stanów, renderowanie 1-bitowe i symulator w przeglądarce do pokazu jury. Opcjonalnie: przygotować kontrakt pod prawdziwe urządzenie (LoRaWAN).

## Zawartość paczki

| Plik | Do czego |
|---|---|
| `renderer/epaper_render.py` | **Gotowy renderer** (Pillow + qrcode). `render(state, data, tri=False)` → obraz 800×480 tryb „1” (lub paleta czerń/biel/czerwień). `render_partial()` → wycinek okna odświeżania częściowego. Prawdziwe, skanowalne kody QR (adres bazowy: zmienna `TF_BASE_URL`). |
| `renderer/IBMPlexSans-*.ttf`, `OFL-IBM-Plex.txt` | Fonty 500/700 (licencja SIL OFL). |
| `renderer/out/*.png` | Wzorcowe obrazy wszystkich 8 stanów + przykład okna częściowego – punkt odniesienia dla testów wizualnych. |
| `design/ekran-epapier.dc.html` | Projekt z kanwy (format edytora, nie runtime). Źródło tekstów i siatki. |
| `design/mapa-odswiezania.dc.html`, `karta-zasad.dc.html`, `obudowa.dc.html` | Mapa obszarów odświeżania z wyzwalaczami, zasady typografii/QR/linii, widok obudowy. |

Uruchomienie: `pip install pillow qrcode && python renderer/epaper_render.py` → `renderer/out/`.

## Siatka (px, stałe – nie zmieniać między stanami)

| Obszar | Prostokąt (x0, y0, x1, y1) | Odświeżanie |
|---|---|---|
| Nagłówek | 0, 0, 800, 64 | statyczny (serwis) |
| Pas stanu | 0, 64, 584, 344 | pełne, przy zmianie stanu |
| QR + podpis | 584, 64, 800, 344 | pełne, razem ze stanem |
| **Okno częściowe** | **24, 344, 776, 432** | częściowe: zapełnienie, liczba osób, czasy |
| Stopka | 0, 432, 800, 480 | raz na godzinę (bateria, ostatni sygnał) |

Okno częściowe ma x wyrównane do 8 px (wymóg większości sterowników 7,5" – np. UC8179/GDEY075T7). Ramka okna i etykiety pól są stałe; zmieniają się tylko wartości.

## Stany i wyzwalacze

| # | `state` | Wyzwalacz | Kształt | QR prowadzi do |
|---|---|---|---|---|
| 1 | `calm` | domyślny, brak otwartego zgłoszenia | koło ✓ | `/kosz/<nr>/zglos` |
| 2 | `confirm` | naciśnięcie przycisku lub zgłoszenie z QR (cel: ekran w < 5 s) – pas stanu odwrócony (biały tekst na czarnym) | dymek … | `/kosz/<nr>/status` |
| 3 | `enroute` | punkt trafił do aktywnej trasy, ekipa wyjechała | dymek … | `/kosz/<nr>/status` |
| 4 | `emptied` | czujnik potwierdził opróżnienie (lub ekipa zamknęła punkt) | koło ✓ | `/przyjaciele` |
| 5 | `overflow` | 100 % przy otwartym zgłoszeniu (np. wydarzenie w strefie) | kwadrat ! | `/kosz/<nr>/status` |
| 6 | `fault` | brak sygnału ≥ 48 h lub bateria < 15 % – przycisk może nie działać | trójkąt ! | `/kosz/<nr>/zglos` |
| 7 | `night` | 22:00–06:00 i stan = 1 (inaczej pokazuj właściwy stan) | koło ✓ | `/kosz/<nr>/zglos` |
| 8 | `confirm` + `tri=True` | jak 2 na panelu 3-kolorowym – czerwień tylko w pasie stanu | dymek … | jak 2 |

Priorytet przy konflikcie: `fault` > `overflow` > `confirm` > `enroute` > `emptied` > `night` > `calm`. Stan `emptied` trzymaj 60 min, potem `calm`.

Zmiana **tylko** wartości w obrębie stanu (np. „Zgłosiły: 2 osoby” → „3 osoby”, „ok. 12 min” → „ok. 8 min”, zapełnienie) → wyłącznie okno częściowe, bez pełnego odświeżenia.

## Dane wejściowe renderera

```python
render("enroute", {
    "fill": 62,                       # 0–100 albo None (brak danych)
    "b": ("Przyjazd", "ok. 12 min"),  # pola zmienne → tylko okno częściowe
    "c": ("Przystanek", "34 z 53"),
    "foot": "Bateria 78 % · ostatni sygnał 13:20",
    "device": {"name": "Kosz Rynek 03", "device_no": "1183", "address": "Rynek Główny 3, róg Szewskiej"},
})
```
Domyślne teksty każdego stanu są w `STATES` (dokładnie te z projektu). Pas stanu (`head`, `big`, `sub`) zawiera tylko treści stałe dla danego stanu – godzina zdarzenia („przyjęte o 13:24”, „14:02”) ustalana raz przy wejściu w stan. Wszystko, co zmienia się w trakcie stanu (czas przyjazdu, przystanek, liczba osób, zapełnienie), idzie wyłącznie do pól `fill`, `b`, `c` okna częściowego. Bateria i ostatni sygnał (`foot`) – co godzinę.

Zasady treści: bez danych osobowych i pseudonimów, bez wykrzykników, wersaliki tylko w nagłówku stanu. Pasek zapełnienia: 10 bloków, zaokrąglenie w dół (62 % → 6 bloków).

## Etap 1 – symulator do pokazu (zalecany na hackathon)

1. `GET /epapier/<nr>.png` – Flask zwraca `render(...)` dla aktualnego stanu kosza (PNG, `Cache-Control: no-store`).
2. `GET /epapier/<nr>` – strona z obrazem w ramce obudowy (wzór: `design/obudowa.dc.html`: ciemnoszara obudowa, żółta naklejka „PEŁNY? NACIŚNIJ” z okrągłym przyciskiem pod ekranem).
   - Przycisk na stronie = fizyczny przycisk: `POST /api/bins/<nr>/press` → to samo co zgłoszenie z `/jury`.
   - Odświeżanie: SSE/polling co 1 s. Przy zmianie **stanu** pokaż krótkie mignięcie całego ekranu (czarny → biały → nowy obraz, ok. 1,5 s), przy zmianie samych wartości podmień tylko okno częściowe bez mignięcia. Jury zobaczy różnicę pełne/częściowe.
3. Na panelu dyspozytora (widok C) dodaj link „Ekran na koszu” przy wybranym punkcie.

## Etap 2 – prawdziwe urządzenie (kontrakt, bez implementacji firmware)

LoRaWAN nie przeniesie obrazu (ładunek downlink ~51–222 B, ograniczony czas nadawania), więc **urządzenie renderuje samo** z wbudowanych szablonów i fontów rastrowych, a serwer wysyła tylko stan i wartości.

Proponowany downlink (port 10, ≤ 24 B):

| Bajt | Pole |
|---|---|
| 0 | `state` (1–7), bit 7 = tryb tri |
| 1 | zapełnienie 0–100, 255 = brak danych |
| 2–3 | godzina A w minutach od północy (odbiór / zgłoszenie / opróżnienie) |
| 4–5 | godzina B (np. ekipa ok. / następny odbiór) |
| 6 | liczba zgłaszających |
| 7 | przystanek (34) |
| 8 | liczba przystanków (53) |
| 9 | minuty do przyjazdu |
| 10 | flagi: bit0 jutro, bit1 wydarzenie, bit2 serwis zaplanowany |
| 11 | dni do serwisu |

Uplink: naciśnięcie przycisku (natychmiast), heartbeat co godzinę (bateria %, temperatura). Po naciśnięciu urządzenie **od razu lokalnie** pokazuje stan 2 z bieżącą godziną (nie czeka na downlink), a downlink tylko uzupełnia „ekipa ok. …” i liczbę osób przez okno częściowe.

QR generowany na urządzeniu z numeru urządzenia i stanu (wersja 2–3, korekcja M, moduł 6 px, ramka 8 px). Fonty: Plex 500/700 przerastrowane do rozmiarów 16, 20, 24, 28/30, 32, 48, 56, 60 px.

## Kryteria odbioru

- [ ] `python renderer/epaper_render.py` generuje 8 stanów zgodnych z `renderer/out/` (porównanie pikselowe, tolerancja na antyaliasing = brak, obraz 1-bitowy).
- [ ] Logika wybiera stan wg tabeli wyzwalaczy i priorytetu; testy jednostkowe dla każdego przejścia.
- [ ] Zmiana samych wartości nie zmienia pikseli poza oknem `24,344–776,432` (test: XOR dwóch obrazów).
- [ ] Symulator `/epapier/<nr>`: naciśnięcie → stan 2 w < 2 s, mignięcie tylko przy zmianie stanu.
- [ ] QR każdego stanu prowadzi do właściwego adresu i jest skanowalny telefonem z 50 cm.
- [ ] Brak danych osobowych na ekranie.
