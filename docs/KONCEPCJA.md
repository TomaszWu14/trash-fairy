# Trash Fairy — koncepcja projektu (HackYeah 2026, Smart City)

> **Status:** koncepcja przygotowana 2026-10-02, **przed** HackYeah. Ten dokument nie zawiera kodu.
> Cały kod powstaje podczas HackYeah (start: sobota 2026-10-03, 11:00).

**Podtytuł:** inteligentny odbiór odpadów dla Krakowa
**Kategoria:** Smart City (zadanie otwarte), pula 8 000 PLN
**Tryb pracy:** solo, 24 h. Checkpoint w sobotę o 20:00, oddanie w niedzielę o 11:00 (Challenge Rocket).

---

## 1. Problem

- Kosze uliczne w centrum Krakowa (Planty, Rynek, Kazimierz) przepełniają się, zwłaszcza w weekendy i podczas wydarzeń. MPO opróżnia je według stałego harmonogramu, a nie według potrzeb.
- **Dowód:** KRKnews, 2026-09-08. MPO apeluje, bo mieszkańcy wrzucają do ulicznych koszy worki z domowymi śmieciami, ubrania i buty. Cytat MPO: *„nie tylko zaśmieca miasto, ale też utrudnia naszą pracę”*.
- **Kontekst kosztowy:** „Analiza stanu gospodarki odpadami komunalnymi w GMK za 2025 r.” (kwiecień 2026):
  - koszt całego systemu to 414,4 mln zł (w 2020 było 237,6 mln, czyli +74%);
  - odbiór i transport to 111,0 mln zł (26,8%);
  - wniosek #10: *„Bieżącego monitorowania wymaga częstotliwość odbioru odpadów komunalnych w kontekście zgłaszanych wniosków mieszkańców.”*;
  - wniosek #14: rosnące koszty transportu i energii to ryzyko dla stabilności systemu.
  - ⚠️ Analiza dotyczy odpadów z nieruchomości. Kosze uliczne idą z osobnej umowy o utrzymanie czystości. Kwotę 111 mln zł podajemy jako skalę, nie jako koszt koszy ulicznych.
- **Ciąg przyczynowy:** przepełniona altana osiedlowa → mieszkańcy wynoszą worki do koszy ulicznych → kosze uliczne są przepełnione.

## 2. Konkurencja i nasza różnica

| Istniejące | Co robi | Luka |
|---|---|---|
| Mr Fill (Sopot), solarny kompaktor | zgniata odpady do 7×, mierzy zapełnienie, ma platformę Smart City Manager | działa tylko z własnymi, drogimi pojemnikami; nie rozpoznaje przyczyny (worki domowe) |
| Wrocław (131 czujników), Sierpc (ponad 100, PW), Rzeszów | czujniki zapełnienia, czasem trasy | wymagają czujnika w każdym koszu; reagują, zamiast przewidywać |

**Trash Fairy to mózg niezależny od sprzętu.** Zaczyna od taniego przycisku i danych od ekip MPO, przewiduje zapełnienie, rozpoznaje przyczynę (zdjęcie i AI), planuje trasy i podpowiada miastu, gdzie opłaca się czujnik, kompaktor albo większy kosz.

**Hasło:** „Kraków nie potrzebuje więcej koszy, potrzebuje wróżki.”

## 3. Użytkownicy i główna ścieżka

- **Bohater demo: dyspozytor MPO.** Rano otwiera panel, widzi prognozę i przyczyny przepełnień, dostaje dwie trasy i raport AI.
- Wejścia danych: przechodzień (wirtualny przycisk), ekipa MPO (opróżnienie, poziom, opcjonalne zdjęcie).
- **Ścieżka główna:** naciśnięcie przycisku → zmiana stanu punktu → punkt na liście do opróżnienia → przeliczona trasa → raport AI.

## 4. Zakres demo

- **Obszar:** Stare Miasto, Kazimierz i Grzegórzki.
- **Punkty:** 60 koszy ulicznych (prawdziwe pozycje z OSM `amenity=waste_basket`, w centrum jest ich 351) i 12 altan osiedlowych w Grzegórzkach (OSM `amenity=waste_disposal`/`recycling` albo ręcznie przy blokach).
- **Jednostka: punkt.** Kosz uliczny albo altana. Przycisk jest na koszu albo obok (na słupku). Altana to jeden punkt z ogólnym stanem, bez podziału na frakcje.
- **Wszystkie dane operacyjne są syntetyczne**, a w UI jest stały pasek „Dane demonstracyjne / symulacja”.

## 5. Źródła sygnałów (MVP)

1. **Wirtualny przycisk** (`/przycisk/<id>`) wyglądający jak fizyczny: żeliwna zieleń, czerwony przycisk „PEŁNY? NACIŚNIJ / FULL? PRESS”, dioda, brokat, napis „Wróżka już leci!”.
2. **Ekipa MPO** (widok na telefon): kolejny punkt z trasy, kliknięcie poziomu 25/50/75/100% i „opróżniony”, opcjonalne zdjęcie.
3. **Zdjęcie analizowane przez Claude Vision** (w tle, wynik zapisany w bazie).
4. Czujniki i kompaktory są **tylko na slajdzie**, jako przyszłe źródła tego samego sygnału.

### Schemat wyniku analizy zdjęcia

```json
{
  "fill_level": 75,
  "overflow_outside": true,
  "misuse": ["household_bag", "clothes"],
  "damage": false,
  "confidence": 0.8,
  "note": "Dwa worki domowe obok kosza, kosz pełny."
}
```

- `fill_level` przyjmuje wartości 0/25/50/75/100.
- `misuse` przyjmuje wartości `household_bag | clothes | bulky | construction | none`.
- Prompt zabrania opisywania osób.
- Rozbieżność poziomu ze zdjęcia i poziomu klikniętego większa niż 25 punktów daje flagę w panelu.

## 6. Logika (reguły w kodzie, nie w AI)

### 6.1 Zgłoszenia i ochrona przed spamem

- **Scalanie:** wiele naciśnięć jednego punktu w ciągu 15 minut to jedno zgłoszenie (na serwerze; w przyszłości także w urządzeniu).
- **Trafność zgłoszenia:** po opróżnieniu z poziomem co najmniej 75% zgłoszenie było trafne, w przeciwnym razie fałszywe.
- **Wiarygodność przycisku:** odsetek trafnych zgłoszeń z ostatnich 10. Nowy przycisk zaczyna od 70%.
- **Waga zgłoszenia** równa się wiarygodności przycisku.
- **Flaga „sprawdź przycisk”:** wiarygodność poniżej 40% przez 7 dni albo brak zgłoszeń, gdy prognoza od dłuższego czasu mówi, że punkt jest pełny.
- **Zdrowy rozsądek:** zgłoszenie niedługo po opróżnieniu, przy niskiej prognozie, liczymy jako słaby sygnał.

### 6.2 Stan punktu

- `stan = max(prognoza, zgłoszenie × wiarygodność)`, reset po zapisie „opróżniony”.
- Progi: zielony poniżej 60%, żółty 60–85%, czerwony powyżej 85% albo świeże zgłoszenie o wysokiej wadze.

### 6.3 Prognoza

- **Profil tygodniowy:** średnie tempo zapełniania punktu w podziale na dzień tygodnia i godzinę, liczone z historii.
- **Mnożnik wydarzeń:** punkty w promieniu zależnym od skali tłumu (mały 200 m, średni 400 m, duży 800 m) w godzinach wydarzenia plus 1 godzina po nim.
- Wynik: godzina przekroczenia 85% z przedziałem. Błąd MAE na ostatnim tygodniu to jedna liczba na slajd.

### 6.4 Wydarzenia

- Pobieramy listę z Karnet Kraków (karnet.krakowculture.pl; publicznego API brak). Claude zamienia tekst na JSON: nazwa, miejsce, data, godziny, skala tłumu.
- Nominatim zamienia nazwę miejsca na współrzędne, z cache.
- Wynik zapisujemy w bazie. Zapas: ręczna lista 3–4 wydarzeń w danych demo.

### 6.5 Nadużycia i powiązania

- Wykryte `misuse` daje znacznik „nadużycie” na mapie i wpis w raporcie. **Bez** automatycznych zgłoszeń do Straży Miejskiej.
- **Reguła altana → kosz:** worki domowe w koszu ulicznym w promieniu 200 m od altany, która była przepełniona w ciągu ostatnich 48 h, dają powiązanie (przerywana fioletowa linia) i rekomendację „zwiększ częstotliwość odbioru altany”.

### 6.6 Trasy

- **Dwie floty:** mały pojazd do koszy ulicznych, śmieciarka do altan.
- **Kursy:** kosze uliczne o 6:00 i 14:00, altany o 6:00.
- **Wybór punktów:** pełne teraz albo z prognozą przekroczenia 85% przed następnym kursem, plus bezpiecznik (kosz nieopróżniany od 3 dni, altana od 7 dni).
- **OR-Tools VRP**, odległości w linii prostej × 1,3. Start z bazy MPO (jeden punkt).

### 6.7 Porównanie „przed i po”

- Symulacja 4 tygodni na tych samych danych zapełnienia: **stały harmonogram** (wszystkie punkty na każdym kursie) kontra **Trash Fairy**.
- Miary: kilometry, liczba wizyt, godziny przepełnienia (stan powyżej 100% przed przyjazdem). Opcjonalnie paliwo i CO₂ z jawnego współczynnika.

### 6.8 Rekomendacje inwestycyjne (dane z 4 tygodni)

| Warunek | Rekomendacja |
|---|---|
| przepełniony w ponad 50% dni i opróżniany 2× dziennie | kompaktor |
| przepełniony w 20–50% dni | większy kosz |
| przyczyną są głównie worki domowe | interwencja przy altanie |
| rzadko zapełniony powyżej 50% | można zmniejszyć częstotliwość |

- W panelu jednostki fizyczne („-42 wizyty w miesiącu”). Złotówki tylko jako **jawne, konfigurowalne założenia** na stronie Metodologia.

## 7. Dane syntetyczne

- **Historia:** 8 tygodni wstecz.
- **Tempo zapełniania koszy** zależy od gęstości lokali gastronomicznych, sklepów i przystanków z OSM w promieniu 100 m, z profilem godzinowym (obiad, wieczór, na Kazimierzu noc) i weekendowym.
- **Tempo zapełniania altan** zależy od liczby mieszkań (`building:flats` albo kondygnacji z OSM). 1–2 altany są celowo przeciążone.
- **Naciśnięcia:** gdy poziom przekracza 80%, szansa naciśnięcia rośnie z ruchem pieszym. 5% naciśnięć to fałszywe alarmy. 2 przyciski są celowo trollowane (przy szkole, w godzinach 14–16).
- **Zegar demo:** zamrożony scenariusz „sobota 13:30, jarmark na Rynku” z przyciskiem „przewiń +1 h”.

## 8. Rola AI (Claude, moduł `app/llm.py`: `ask()`, `ask_json()`)

1. **Vision:** zdjęcie zamieniane na JSON według schematu z sekcji 5.
2. **Wydarzenia:** tekst z Karnetu zamieniany na JSON.
3. **Raport „Wróżka podpowiada”** dla dyspozytora, około 150 słów, 5 sekcji: najważniejsze dziś, trasy, nadużycia i powiązania, przyciski do sprawdzenia, rekomendacja inwestycyjna. Claude dostaje gotowe liczby w JSON i **niczego nie liczy**.

- Model i klucz z env (`ANTHROPIC_MODEL`, `ANTHROPIC_API_KEY`).
- Każdy wynik jest zapisywany w bazie. Przy błędzie API pokazujemy komunikat i ostatni wynik z cache, nigdy błąd 500.
- **Decyzje** (stan, priorytet, trasa, rekomendacja) podejmują wyłącznie reguły w kodzie.

## 9. Ekrany

1. **Panel dyspozytora:** mapa po lewej (Leaflet + OSM, z atrybucją), boczny panel po prawej (raport AI, lista punktów do opróżnienia z powodem, liczby oszczędności). Pasek: zegar demo, przycisk „przewiń +1 h”, napis „DANE DEMONSTRACYJNE”.
2. **Szczegóły punktu:** w bocznym panelu, z przyciskiem „← wróć”. Wykres Chart.js (historia 48 h, prognoza z przedziałem, próg 85%, znaczniki opróżnień), wiarygodność przycisku, zdjęcia z analizą, powiązania, rekomendacja.
3. **Wirtualny przycisk** (`/przycisk/<id>`, na telefon).
4. **Tryb dla jury** (`/jury`, z kodu QR): losowy kosz z puli 5–6 koszy przy Rynku, limit naciśnięć na adres IP. Na panelu licznik „N naciśnięć → M zgłoszeń”.
5. **Widok ekipy MPO** (na telefon).
6. **Metodologia:** źródła danych, założenia, licencje, akapit o RODO.

### Kodowanie wizualne mapy

- Kształt oznacza typ: koło to kosz, kwadrat to altana.
- Kolor i symbol oznaczają stan: ✓ zielony, ~ żółty, ! czerwony.
- Plakietki: 🛍 nadużycie, ⚠ przycisk do sprawdzenia.
- Pulsujący fioletowy pierścień: zgłoszenie z ostatnich 15 minut.
- Linie: przerywana fioletowa to powiązanie altana → kosz; dwie trasy mają dwa odcienie.

### Styl

- **Panel:** jasny, kremowe tło `#f4f1ea`, zieleń Plant `#2f3b2a` / `#4d6b45`, złoto `#c9a227` dla codziennej pracy MPO.
- **Magia (AI i przycisk):** fiolet `#7c3aed` i róż `#db2777` z poświatą, tylko tam, gdzie działa wróżka.
- **Telefon:** ciemne, magiczne tło; przycisk w zieleni Plant ze złotą obwódką.
- Kolory stanu (zielony, żółty, czerwony) są osobne i nie mieszają się z magicznymi akcentami.
- Zgodność z WCAG 2.1 AA: kontrast, etykiety, obsługa klawiaturą, kolor nigdy nie jest jedynym nośnikiem informacji.

## 10. Architektura i technika

- **Backend:** Python 3.12, Flask (app factory, blueprinty), Flask-SQLAlchemy, Gunicorn, Dockerfile (port 8000), `/health` sprawdzający bazę.
- **Baza:** PostgreSQL na produkcji, SQLite lokalnie.
- **Tabele:** `point`, `press`, `emptying`, `photo_analysis`, `event`, `forecast`, `route`, `report`.
- **Frontend:** Jinja, Tailwind i DaisyUI z CDN, Leaflet, Chart.js. Bez osobnego budowania.
- **Aktualizacje na żywo:** polling `/api/changes?since=` co 2 s.
- **API przycisku:** `POST /api/press` z `point_id`, limit naciśnięć na IP, scalanie w oknie 15 minut.
- **Trasy:** OR-Tools. **Geokodowanie:** Nominatim (z cache i zgodnie z zasadami użycia).
- **Wdrożenie:** Coolify na VPS-ie, subdomena z HTTPS. Pierwsze wdrożenie w sobotę po południu, potem po każdym większym kroku.
- **Sekrety** tylko w `.env` (w `.gitignore`), do tego `.env.example`.
- **Zdjęcia demo** pochodzą z internetu, są w `demo_photos/` (w `.gitignore`), a ich źródła są wypisane w README.
- **Prywatność:** w bazie zostaje wynik analizy, zdjęcie jest usuwane po 7 dniach.

## 11. Testy (pytest, około 10, Claude zastąpiony atrapą)

1. `/health` sprawdza bazę.
2. 30 naciśnięć w ciągu 15 minut daje 1 zgłoszenie.
3. 7 fałszywych zgłoszeń z 10 daje wiarygodność 30% i flagę.
4. Progi stanu oraz bezpieczniki 3 i 7 dni.
5. Prognoza na znanym profilu daje oczekiwaną godzinę przekroczenia.
6. Wybór punktów do trasy.
7. Trasa odwiedza każdy wybrany punkt dokładnie raz.
8. Reguła altana → kosz (200 m, 48 h).
9. Błąd API daje komunikat i dane z cache, a nie błąd 500.
10. Ścieżka główna: naciśnięcie → stan → lista do opróżnienia.

## 12. Plan 24 h

| Kiedy | Co | Stan „da się pokazać” |
|---|---|---|
| sob 11–13 | szkielet, model danych, import danych z OSM, generator symulacji, `/health`, pierwsze wdrożenie | mapa z punktami |
| 13–17 | stan, prognoza, panel, przycisk, polling | naciskasz → punkt czerwony |
| 17–20 | trasy OR-Tools, porównanie ze stałym harmonogramem | **checkpoint: cała ścieżka działa** |
| 20–01 | widok ekipy, Claude Vision, nadużycia, altana → kosz | |
| 01–05 | raport AI, Karnet, rekomendacje, tryb dla jury | |
| 05–08 | sen | |
| 08–10 | szlif UI, testy, README, slajdy, próba pitchu, **2-minutowe nagranie zapasowe** | |
| 10–11 | bufor, oddanie | |

**Kolejność cięcia przy opóźnieniu:**
1. Karnet → zostaje lista zapasowa.
2. Rekomendacje → zostaje zdanie w raporcie.
3. Tryb dla jury.
4. Powiązania altana → kosz.
5. Widok ekipy → upload zdjęcia z panelu.

**Nie wycinamy nigdy:** mapy, przycisku, prognozy, trasy z porównaniem, analizy zdjęcia, raportu AI.

## 13. Pitch (3–5 min, slajdy po angielsku)

1. **(30 s) Problem:** zdjęcie przepełnionego kosza, cytat MPO z 8 września, skala kosztów (z zastrzeżeniem z sekcji 1).
2. **(15 s) Pomysł:** czujniki istnieją i kosztują; my zaczynamy od przycisku i robimy mózg dla MPO.
3. **(90 s) Demo na żywo:** jury skanuje kod QR i naciska, scalanie widać na liczniku; wgrywam zdjęcie, wykryty worek domowy prowadzi linią do altany; przewijam czas, trasa na 14:00 się zmienia; raport „Wróżka podpowiada”.
4. **(30 s) Liczby:** porównanie ze stałym harmonogramem.
5. **(20 s) Różnica:** Mr Fill i Wrocław, rekomendacje inwestycyjne.
6. **(15 s) Zakończenie:** „Kraków nie potrzebuje więcej koszy, potrzebuje wróżki.”

**Model biznesowy:**
- 3-miesięczny pilotaż dla MPO na Starym Mieście i w Grzegórzkach, potem opłata miesięczna za punkt.
- Sprzęt dowolnego dostawcy.
- Możliwe źródła finansowania: Budżet Obywatelski albo program innowacji miejskich.

## 14. Język

- **Interfejs:** po polsku (przycisk ma dodatkowo napis „FULL? PRESS”).
- **Slajdy i opis zgłoszenia:** po angielsku.
- **README:** PL i EN.

## 15. Przygotowanie przed startem (bez kodu)

- Zdjęcia koszy z internetu, z zapisanymi źródłami.
- Ręczny eksport GeoJSON z overpass-turbo.eu: kosze, altany, lokale, przystanki w obszarze demo.
- Zapisane źródła: KRKnews 2026-09-08, PDF z analizą GMK 2025, Mr Fill, Wrocław, Sierpc, Karnet.
- Subdomena w Coolify, działający klucz API Claude.
- W sobotę o 11:00: sprawdzić wymagania zgłoszenia w Challenge Rocket i limit czasu pitchu.

## 16. Poza zakresem → ROADMAPA.md

- Fizyczny przycisk (LoRaWAN, NB-IoT) i prawdziwe czujniki.
- Frakcje w altanach i trasy według frakcji.
- OSRM, ulice jednokierunkowe, okna czasowe.
- Pogoda w prognozie, Holt-Winters lub ML na prawdziwych danych.
- Rozmywanie twarzy i tablic rejestracyjnych.
- Aplikacja kierowcy, konta i role.
- Czat z AI.
- Integracje z systemami MPO i z kalendarzem miasta przez API.
- Cały Kraków, inne sektory, inne miasta.
- Wzorce spamu w czasie, korelacja sąsiednich przycisków.

## 17. Wymagane dokumenty w repozytorium

- **CLAUDE.md:** zasady z bloku HackYeah.
- **README.md:** problem, rozwiązanie, uruchomienie, dane i licencje (OSM ODbL, źródła zdjęć), użyte narzędzia AI, sekcja *„Przejrzystość: koncepcja przemyślana przed wydarzeniem; cały kod powstał na HackYeah”*.
- **DECYZJE.md:** po każdym większym kroku 2–3 zdania (CO, DLACZEGO, jaka alternatywa odrzucona).
- **ROADMAPA.md.**

## Źródła

- KRKnews, 2026-09-08: https://krknews.pl/worki-z-domowymi-smieciami-zapychaja-uliczne-kosze-mpo-apeluje-do-mieszkancow/
- Analiza stanu gospodarki odpadami komunalnymi w GMK za 2025 r. (UMK, kwiecień 2026), PDF.
- Mr Fill: https://swiatpojemnikow.pl/pojemniki-naziemne/solarny-pojemnik-kompaktujacy/
- Wrocław: https://wroclaw.naszemiasto.pl/wroclaw-inteligentne-kosze-na-smieci-pojawily-sie-na/ar/c1-7333063
- Sierpc / PW: https://www.pw.edu.pl/aktualnosci/inteligentne-kosze-na-smieci-sukces-pomyslu-z-pw
- Karnet Kraków: https://karnet.krakowculture.pl/wydarzenia
- Otwarte Dane Kraków: https://otwartedane.um.krakow.pl/
- OpenStreetMap (ODbL), Overpass API, Nominatim.
