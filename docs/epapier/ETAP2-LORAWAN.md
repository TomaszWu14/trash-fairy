# E-papier na koszu – etap 2: prawdziwe urządzenie (kontrakt, bez firmware)

Stan: opis. W hackathonie działa symulator (`/epapier/<nr>`, etap 1). Ten dokument jest kontraktem między serwerem
Trash Fairy a przyszłym urządzeniem LoRaWAN z panelem e-papierowym 7,5″ (800×480, 1-bit, opcjonalnie 3 kolory).

## Dlaczego urządzenie renderuje samo
LoRaWAN nie przeniesie obrazu (downlink 51–222 B, limit czasu nadawania ~1 %/dobę w EU868). Serwer wysyła tylko
**stan i wartości**, a urządzenie składa ekran z wbudowanych szablonów (ta sama siatka co `app/epaper_render.py`)
i fontów rastrowych Plex 500/700 w rozmiarach 16, 20, 24, 28/30, 32, 48, 56, 60 px.

## Downlink (port 10, ≤ 12 B)
| Bajt | Pole |
|---|---|
| 0 | `state` 1–7 (calm, confirm, enroute, emptied, overflow, fault, night); bit 7 = panel 3-kolorowy |
| 1 | zapełnienie 0–100, 255 = brak danych |
| 2–3 | godzina A, minuty od północy (odbiór / zgłoszenie / opróżnienie) |
| 4–5 | godzina B (ekipa ok. / następny odbiór) |
| 6 | liczba zgłaszających |
| 7 | numer przystanku |
| 8 | liczba przystanków |
| 9 | minuty do przyjazdu |
| 10 | flagi: bit0 „jutro”, bit1 wydarzenie w strefie, bit2 serwis zaplanowany |
| 11 | dni do serwisu |

Źródło wartości po stronie serwera: `app/epaper.py::display_state` (te same reguły co symulator). Zmiana samego
bajtu 1, 6, 7 lub 9 → urządzenie odświeża **tylko okno 24,344–776,432**; zmiana bajtu 0 lub godzin → pełne odświeżenie.

## Uplink
- Naciśnięcie przycisku: natychmiast (port 1, 1 B: licznik). Urządzenie **od razu lokalnie** pokazuje stan 2 z bieżącą
  godziną RTC, nie czeka na downlink; downlink uzupełnia „Ekipa ok. …” i liczbę osób przez okno częściowe.
- Heartbeat co godzinę (port 2: bateria %, temperatura, licznik naciśnięć od ostatniego raportu). Brak heartbeatu
  48 h albo bateria < 15 % → serwer ustawia `fault` (dziś: `Device.last_heartbeat`, `Device.battery`).
- Autotest co 6 h (port 3) nie tworzy zgłoszeń (spec programu mieszkańców, pkt 5).

## QR na urządzeniu
Generowany lokalnie z numeru urządzenia i stanu: wersja 2–3, korekcja M, moduł 6 px, biała ramka 8 px.
Adresy jak w rendererze: `/kosz/<nr>/zglos` (calm, fault, night), `/kosz/<nr>/status` (confirm, enroute, overflow),
`/przyjaciele` (emptied). Serwer przekierowuje je na właściwe ekrany PWA.

## Co jeszcze przed pilotażem
Limit 1 zgłoszenie / 15 min w firmware, RTC z synchronizacją z sieci, test czytelności w słońcu i w −10 °C,
obudowa IK08, mocowanie 120 cm na słupku kosza.
