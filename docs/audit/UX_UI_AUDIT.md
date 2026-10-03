# Audyt UX / UI / funkcjonalności – Trash Fairy (Etap 2)

Data: 3.10.2026 wieczór. Podstawa: `ETAP1_ROZPOZNANIE.md`, 152 zrzuty w `screens/`, pomiary `screens/_findings.json`, Lighthouse w `lighthouse/*.json`.
Priorytety: **P0** blokuje demo · **P1** poważny · **P2** średni · **P3** kosmetyczny. Nakład: S (< 1 h), M (1–3 h), L (> 3 h).
Dowód: nazwa zrzutu z `docs/audit/screens/` albo kroki.

## Lighthouse (lokalnie, Chrome headless)

| Strona | Perf | A11y | Best | SEO | LCP | Żądań | Waga |
|---|---|---|---|---|---|---|---|
| `/` widok C (desktop) | 80 | 100 | 100 | 91 | 1,5 s | 47 | 1,4 MB |
| `/dyspozytor` (desktop) | 80 | 97 | 100 | 91 | 2,0 s | 44 | 1,5 MB |
| `/zglos/18` (mobile) | **59** | 98 | 92 | 100 | **4,2 s** | 19 | 302 kB |
| `/ekipa` (mobile) | 69 | 100 | 100 | 90 | **4,4 s** | 7 | 280 kB |
| `/epapier/18` (desktop) | 98 | 98 | 96 | 91 | 0,9 s | 14 | 92 kB |

Instalowalność PWA (`/zglos`): manifest, SW w zakresie `/zglos`, ikona SVG; brak PNG 192/512 (starsze Androidy). Ekipa: brak manifestu i SW.

---

## A. Funkcjonalność i błędy

| ID | Ekran (plik) | Problem | Dowód | Wpływ | P | Poprawka | N |
|---|---|---|---|---|---|---|---|
| A1 | widok C, karta QR (`pokaz.js:renderQr`) | Link i QR budowane z `location.origin`, gdy brak `PUBLIC_URL` → lokalnie `127.0.0.1:5050/jury`; na prod OK tylko dlatego, że origin = domena. Przy pokazie z laptopa w sieci sali QR nie zadziała. | `pokaz-krok3-1920.png` (link 127.0.0.1) | jury nie zeskanuje | **P0** | `PUBLIC_URL` ustawiony także lokalnie w `.env`; w UI ostrzeżenie, gdy host to localhost (panel to ma, widok C nie) | S |
| A2 | widok C (`pokaz.js:apply`) | Każdy poll pobiera `/api/routes` (OR-Tools + OSRM) nawet gdy zmieniła się tylko wersja przez naciśnięcie; przy 2 otwartych kartach i e-papierze co 1 s serwer liczy `point_states` kilka razy na sekundę | `_findings.json`: `/epapier/18.png` 466 ms × 4 | opóźnienia przy kilku widzach w demo | P1 | cache `point_states`/`plan_routes` na wersję (`lru_cache` po `version()`), e-papier: `ETag` zamiast nowego PNG | M |
| A3 | panel (`/api/comparison`) | pierwsze wejście liczy porównanie **2,3 s** synchronicznie; po restarcie gunicorna każdy proces liczy osobno | `_findings.json` slow | pusta sekcja „Przed i po” przez 2–3 s | P2 | policzyć przy `seed` i zapisać do bazy/JSON | S |
| A4 | zgłoszenie (`zglos.js:locate`) | Przy GPS > 150 m ekran blokuje się w `far` **także gdy mieszkaniec wszedł z QR na koszu**, jeśli telefon ma słabą dokładność (np. 300 m w kamienicach); brak użycia `accuracy` | kroki: `/zglos/18` z lokalizacją 233 m (zrzut `zglos-start-360.png` pokazuje chip 233 m przy koszu) | fałszywa blokada | P1 | blokować tylko gdy `dist − accuracy > 150`; w `far` zostawić przyciski aktywne z ostrzeżeniem | S |
| A5 | zgłoszenie (`api.press`) | `comment` z formularza nie jest zapisywany; „Dodaj zdjęcie” tylko notka | kod | obietnica w UI bez skutku | P2 | zapisać komentarz w `Press` (kolumna) albo usunąć przyciski z ekranu | S |
| A6 | panel (`panel.js`) | Po `Reset` otwarte szczegóły punktu nie odświeżają wykresu, dopóki nie klikniesz ponownie | kroki: szczegóły → Reset | mylące w demo | P2 | w `apply()` wywołać `openDetails(detailId,false)` zawsze (jest, ale po `loadRoutes` nadpisuje listę) – sprawdzić kolejność | S |
| A7 | ekipa (`ekipa.html`) | Brak obsługi 0 przystanków poza tekstem; „zrobione” liczone tylko w pamięci karty, po odświeżeniu znika | kroki | niepewność ekipy | P2 | stan `done` z `/api/routes` (opróżnienia po `run_at`) | S |
| A8 | wszystkie | Nieprawidłowy `id` w URL → surowa strona Flask „404 Not Found” po angielsku | `/zglos/99999` | nieprofesjonalne przy skanie starej naklejki | P1 | własny szablon 404 po polsku z linkiem do `/zglos` | S |
| A9 | panel | Tailwind z CDN (ostrzeżenie w konsoli, 300 kB JIT w przeglądarce) | konsola, każdy zrzut panelu | wolniejszy start, ostrzeżenie w DevTools jury | P2 | usunąć Tailwind/DaisyUI z panelu (używane są 3 klasy siatki) | M |
| A10 | polling | Przy utracie sieci panel milczy (brak banera), QR „Ostatnie” nie wraca po reconnect | kroki: wyłącz sieć | dyspozytor nie wie, że dane są stare | P2 | wskaźnik „ostatnia aktualizacja hh:mm:ss” + baner offline po 3 nieudanych pollach | S |

Sprawdzone i OK: zgłoszenie → `fresh` w API 263 ms; podwójne kliknięcie nie dubluje wysyłki; `Przewiń +1 h` i `Reset` aktualizują KPI, mapę, trasy i listy (widok C i panel); brak `pageerror` na 6 szerokościach.

## B. Hierarchia informacji i architektura

| ID | Ekran | Problem | Dowód | P | Poprawka | N |
|---|---|---|---|---|---|---|
| B1 | widok C | Cztery karty mają tę samą wagę wizualną; „co jest pilne” (najbliższe przepełnienia) jest w prawej kolumnie **pod** QR, na 1440 px poniżej zgięcia | `pokaz-krok3-1440.png` | P1 | kolejność kolumny: pilne nad QR; karta 1 „Problem” zawsze z liczbą i listą 3 nazw | S |
| B2 | panel | 4 zakładki + 9 sekcji w panelu bocznym; „Punkty” to lista 72 pozycji bez grupowania po pilności | `dyspozytor-sytuacja-1024.png` | P1 | sekcje: Pilne (≤ 5) → Zgłoszenia na żywo → Trasy; reszta za „Więcej” | M |
| B3 | wszystkie | Dwa języki stanów: panel „zapełnia się / do opróżnienia”, widok C „zbliża się do pełna / przepełniony”, e-papier „W PORZĄDKU / ZGŁOSZONO”; dwa symbole dla tego samego stanu (koło ~ vs romb ↑) | tabela stanów w ETAP1 | **P1** | jedna biblioteka stanów (etap 3) | M |
| B4 | nav (`_nav.html`) | Menu „Pokaz · Panel · Program · Ekipa · Jury · Metodologia” miesza ekrany dla 3 różnych ról; „Jury” otwiera losowy kosz bez wyjaśnienia | zrzuty program/ekipa | P2 | menu per rola: w panelu tylko Pokaz/Panel/Metodologia; Ekipa i Program jako osobne wejścia (QR / link) | S |
| B5 | widok C krok 4 | „−16 % godzin przepełnień” w karcie, ale na ekranie 3 metryki, w tym „+7 % km” bursztynowo bez wyjaśnienia na karcie | `pokaz-krok4-1440.png` | P2 | podpis karty: „kosze −24 % wizyt, altany 338 → 0 h” | S |

## C. Mapa

| ID | Ekran | Problem | Dowód | P | Poprawka | N |
|---|---|---|---|---|---|---|
| C1 | panel | **Brak klastrowania**: 53 numerowane piny + 72 znaczniki nachodzą na siebie na Rynku; cele kliknięcia 18 px | `dyspozytor-sytuacja-1024.png` | **P1** | użyć `markercluster` i ikon z widoku C (ta sama warstwa) | M |
| C2 | panel | Trasy w linii prostej (zielone odcinki przez kwartały) wyglądają jak błąd, choć widok C ma już OSRM | j.w. | P1 | rysować `geometry` z `/api/routes` (już w API) | S |
| C3 | widok C | Po kliknięciu klastra `spiderfy` rozrzuca 33 piny bez etykiet; brak przejścia pin → szczegóły (popup ma tylko 2 linki) | `pokaz-krok3-1920.png` | P2 | popup z poziomem, prognozą 85 % i przyciskiem „Szczegóły” → otwiera panel z `?point=` | M |
| C4 | panel | Lista ↔ mapa tylko w jedną stronę (lista → zoom); kliknięcie pinu otwiera szczegóły, ale lista nie podświetla pozycji | kroki | P2 | `aria-selected` + scroll do pozycji | S |
| C5 | widok C 360–390 px | Mapa 16:9 ma 190 px wysokości; legenda i podpis kroku zasłaniają 70 % mapy | `pokaz-krok3-390.png` | **P1** | na < 768 px: mapa 3:4, legenda zwijana „Legenda ▾”, podpis kroku jedna linia | S |
| C6 | panel 360–390 px | mapa 55 vh + przewijanie strony vs przesuwanie mapy: gest kradnie scroll | `dyspozytor-sytuacja-390.png` | P2 | mapa w zakładce (pełny ekran) lub `dragging` dopiero po dotknięciu dwoma palcami | S |
| C7 | widok C | Domyślny kadr obejmuje bazę MPO 4 km na wschód → centrum jest małe; punkty zajmują 40 % mapy | `pokaz-krok3-1920.png` | P2 | kadr na punkty, baza jako strzałka/etykieta przy krawędzi | S |
| C8 | legenda | widok C: 10 pozycji w jednym pasku, na 1920 px czytelne; panel: legenda opisuje progi % zamiast stanów | zrzuty | P2 | jedna legenda ze stanów (etap 3) | S |

## D. Wygląd (UI)

| ID | Problem | Dowód | P | Poprawka | N |
|---|---|---|---|---|---|
| D1 | **Trzy systemy wizualne**: widok C (granat/żółć, IBM Plex), panel + ekipa + program + metodologia (zieleń „plant”, Fraunces/Inter, gradient lila-róż), PWA (granat/lila, IBM Plex). Jury klikając „Panel” trafia do innej aplikacji. | `pokaz-*` vs `dyspozytor-*` vs `program-*` | **P1** | jeden zestaw tokenów (etap 3); panel i ekipa przepisane na `pokaz.css` | L |
| D2 | Kolory: inwentaryzacja dała 41 unikalnych heksów w 4 arkuszach (ok: #127A3E/#F0A500/#C40000/#5B2A9A/#2F3A41 w C i PWA; panel: #2e7d32/#a16207/#c53030/#7c3aed; ekipa: #2e7d32/#c53030). | grep po `#[0-9A-Fa-f]{6}` | P1 | tokeny semantyczne + stany; usunąć kolory inline w `<style>` szablonów | M |
| D3 | Typografia: 3 rodziny (IBM Plex, Fraunces, Inter) i 14 rozmiarów; emoji jako ikony w panelu (🔴 🚚 ✨ 🛍 🛠 🎪) renderują się różnie na projektorze/Windows | zrzuty panelu | P1 | IBM Plex Sans + jedna skala 12/13/14/16/18/24/32/44; ikony SVG (jak w C) | M |
| D4 | Nagłówek widoku C na 360–390 px: „Reset” wychodzi poza ekran, grupa zegara 100 % szerokości, badge demo w 3. wierszu | `pokaz-krok3-390.png` | **P1** | na < 768 px: zegar + „+1 h” w jednej linii, Reset jako ikona, badge pod spodem | S |
| D5 | Nagłówek panelu na 390 px: menu ucięte z obu stron („okaz … Metodolog”), brak sygnału, że się przewija | `program-start-390.png` | P1 | menu jako przewijane chipsy z cieniem krawędzi albo `<details>` | S |
| D6 | Karty kroków: wartość „21,2 km 53 pkt” i „−16 % godzin przepełnień” łamią się różnie; brak `tabular-nums` w panelu | zrzuty | P3 | `font-variant-numeric: tabular-nums` globalnie | S |
| D7 | Przycisk „Reset” bez obramowania na granacie wygląda jak tekst; na zielonym panelu „Przewiń +1 h” jasny, „Reset” kontur | zrzuty | P3 | warianty Button z tokenów | S |
| D8 | Ekipa: natywny `<input type=file>` „Choose File / No file chosen” po angielsku i w stylu systemowym | `ekipa-start-1440.png` | P2 | własny przycisk „Dodaj zdjęcie” z `label` | S |

## E. Responsywność

| ID | Ekran | Problem | Dowód | P | Poprawka | N |
|---|---|---|---|---|---|---|
| E1 | widok C 360/390 | poziomy scroll (460 px): legenda `max-width:70%` + `white-space:nowrap`, grupa zegara `flex:none` | `_findings.json` hscroll | **P0** | `flex-wrap` w nagłówku, legenda `max-width: calc(100% − 32px)`, elementy `min-width:0` | S |
| E2 | panel 360/390/**1024** | poziomy scroll 469 / **1339 px**: `grid-template-columns: 1fr 420px` do 860 px, menu `overflow-x:auto` w nagłówku bez `min-width:0` | `dyspozytor-sytuacja-1024.png` | **P0** | breakpoint 1100 px, `minmax(0,1fr)`, menu `flex:1 1 0; min-width:0` | S |
| E3 | metodologia 360 | tabela 377 px bez `overflow-x:auto` | hscroll | P2 | owinąć tabele w `div.scroll` | S |
| E4 | panel telefon | brak widoku „KPI + pilne” jako głównego; mapa pierwsza | `dyspozytor-sytuacja-390.png` | P1 | kolejność: KPI → pilne → zakładka Mapa | M |
| E5 | ekipa telefon | 53 karty × 330 px = 17 000 px; brak „następny przystanek” | `ekipa-start-390.png` | **P1** | patrz F1 | L |
| E6 | 1920×1080 | widok C czytelny; podpisy osi czasu 12 px i legenda 13 px za małe z 3 m | `pokaz-krok3-1920.png` | P2 | `@media (min-width:1800px)` skala ×1,15 | S |

## F. PWA (kierowca i zgłaszający)

| ID | Problem | P | Poprawka | N |
|---|---|---|---|---|
| F1 | **PWA kierowcy nie istnieje.** `/ekipa` to lista bez mapy, nawigacji, offline, manifestu. Brief wymaga: start zmiany, trasa z następnym przystankiem, przystanek (Opróżniony / Nie da się podjechać / Problem + zdjęcie), zmiana trasy na żywo, podsumowanie, offline z kolejką, tryb ciemny, cele 56 px. | **P1** | nowy ekran `/kierowca` wg kierunku z kanwy (A/B/C do wyboru), reużycie `queue.js` i SW z `/zglos` (zakres `/kierowca`), API: `/api/routes` + `/api/emptying` + nowy `POST /api/stop-issue` | L |
| F2 | zgłaszający: Lighthouse perf 59, LCP 4,2 s (Leaflet 150 kB + kafelki + Google Fonts render-blocking) | P2 | `font-display: swap` (jest w URL), preload CSS, mapa po `requestIdleCallback`, kafelki zoom 16 | S |
| F3 | zgłaszający: brak `<main>` landmark (a11y 98) | P3 | `<main>` wokół `.z-body` | S |
| F4 | ikony PWA tylko SVG | P2 | PNG 192/512 + maskable | S |
| F5 | zgłaszający offline: kolejka działa, ale brak widocznego statusu połączenia poza momentem wysyłki | P2 | pasek „offline” u góry gdy `!navigator.onLine` | S |

Zgłaszający: 1 tapnięcie do wysyłki (cel spełniony), potwierdzenie i status są.

## G. Stany i informacja zwrotna

| ID | Ekran | Brakujący stan | P | N |
|---|---|---|---|---|
| G1 | widok C | loading (karty „–” bez skeletonu), błąd API (cicho), offline | P2 | S |
| G2 | panel | „Liczę porównanie…” jest; brak błędu dla `/api/fairy` bez klucza poza tekstem; brak toast po „Analizuj” zdjęcie | P2 | S |
| G3 | ekipa | po „Opróżniony” tylko zmiana opacity karty; brak cofnięcia pomyłki | P2 | S |
| G4 | e-papier | gdy `/api/epapier` zwróci błąd, status zostaje „stan: …” | P3 | S |

## H. Dostępność

| ID | Problem | P | N |
|---|---|---|---|
| H1 | Mapa Leaflet: piny `keyboard:true`, ale klastry (divIcon `role=img`) nie są fokusowalne; brak alternatywy tekstowej dla widoku C (panel ma listę) | P1 | M |
| H2 | Zakładki panelu: strzałki działają; karty kroków w widoku C bez obsługi strzałek (OK, to przyciski) | P3 | — |
| H3 | Emoji w panelu bez `aria-hidden` w kilku miejscach (`🚚 kurs`, `🛍`) czytane przez czytnik jako „ciężarówka” | P2 | S |
| H4 | Kontrast: pokaz/PWA AA OK (Lighthouse 1.0); panel: tekst `--muted #5f5e55` na `#f4f1ea` = 5,6:1 OK; gradient lila-róż na „Fairy” < 3:1 na zieleni | P2 | S |
| H5 | `prefers-reduced-motion` obsłużone w C i PWA; w panelu animacja `fresh` wyłączona – OK | — | — |
| H6 | Fokus: widoczny w C i PWA (żółty), w panelu domyślny przeglądarki na zielonym tle słabo widoczny | P3 | S |

## I. Wydajność

| ID | Problem | P | N |
|---|---|---|---|
| I1 | `/api/changes` pełny snapshot (72 punkty + wydarzenia) przy każdej zmianie, dwa widoki + e-papier = do 3 obliczeń `point_states`/s | P2 | M (cache per `version`) |
| I2 | Widok C: 47 żądań, 1,4 MB (kafelki 25, Leaflet, markercluster, Google Fonts); panel 1,5 MB w tym Tailwind JIT | P2 | M |
| I3 | `/epapier/<nr>.png` 466 ms: PNG renderowany przy każdym pobraniu; `ETag` z `state_key+values_key` i `304` | P2 | S |
| I4 | Pamięć mapy po 1 h pollingu: `renderMarkers` podmienia ikony w miejscu (OK), `renderZones` tworzy warstwy od nowa co zmianę (OK, `clearLayers`). Nie zaobserwowano wycieku w 10 min. | — | — |

## J. Heurystyki Nielsena (1–5)

| Heurystyka | Ocena | Przykład |
|---|---|---|
| Widoczność stanu systemu | 3 | polling bez wskaźnika świeżości (A10); e-papier ma dziennik odświeżeń (dobrze) |
| Zgodność z rzeczywistością | 4 | język MPO (kurs, altana, dyspozytor); „Wróżka” jako metafora może mylić laika |
| Kontrola użytkownika | 4 | Cofnij 1,5 s w zgłoszeniu (dobrze); brak cofnięcia „Opróżniony” (G3) |
| Spójność i standardy | **2** | trzy systemy wizualne, dwa języki stanów (B3, D1) |
| Zapobieganie błędom | 4 | blokada > 150 m, limit na IP, scalanie 15 min; fałszywa blokada przy słabym GPS (A4) |
| Rozpoznawanie zamiast pamiętania | 3 | legenda jest; numery przystanków bez nazw na mapie |
| Elastyczność | 3 | skróty klawiaturowe tylko w zakładkach panelu |
| Estetyka i minimalizm | 3 | widok C 4; panel 2 (9 sekcji, emoji) |
| Pomoc w błędach | 3 | PWA ma czytelne błędy; 404 surowe (A8) |
| Pomoc i dokumentacja | 4 | Metodologia, regulamin; brak „jak czytać mapę” dla jury |

---

## Podsumowanie

Widok C i PWA zgłaszającego są blisko gotowości na demo, mają spójne tokeny i przechodzą dostępność (Lighthouse 98–100). Główny problem to **trzy niezależne systemy wizualne** i **dwa języki stanów**, które jury zobaczy po jednym kliknięciu „Panel”. Dwa błędy blokują demo na telefonie: poziomy scroll w widoku C (360–390 px) i w panelu (także na 1024 px), oraz QR z adresem localhost przy braku `PUBLIC_URL`. **PWA kierowcy nie istnieje** i wymaga decyzji, czy budować ją dziś (L) czy pokazać na slajdach jako etap 2. Wydajność jest wystarczająca na demo, ale polling trzech widoków przelicza stan kilka razy na sekundę, co warto zbuforować przed pokazem z kilkoma otwartymi kartami.

## TOP 10 (największy efekt / najmniejszy nakład)

1. **E1 + E2** poziomy scroll w widoku C i panelu (S) – P0.
2. **A1** `PUBLIC_URL` w `.env` + ostrzeżenie w widoku C (S) – P0.
3. **C2** trasy OSRM w panelu zamiast linii prostych (S).
4. **D4 + D5** nagłówki na telefonie (S).
5. **C5** mapa widoku C na telefonie 3:4 + zwijana legenda (S).
6. **B1** „Najbliższe przepełnienia” nad kartą QR (S).
7. **C1** klastry w panelu z tej samej biblioteki co widok C (M).
8. **A8** polska strona 404 (S).
9. **B3 / D2** jedna biblioteka stanów + tokeny w panelu (M) – otwiera etap 3.
10. **A4** blokada odległości z uwzględnieniem dokładności GPS (S).

## Plan prac w 3 falach

**Fala 1 – P0 i demo (ok. 3 h):** E1, E2, A1, D4, D5, C5, B1, C2, A8, A4, A10 (wskaźnik świeżości). Po fali: zrzuty `after/`, pytest, Lighthouse.
**Fala 2 – design system i spójność (ok. 5 h):** tokeny + biblioteka stanów (B3, D1, D2, D3), panel na `pokaz.css` bez Tailwinda (A9), klastry w panelu (C1), nav per rola (B4), ikony SVG zamiast emoji (H3), Button/Badge/Card/Legend/Toast.
**Fala 3 – responsywność, PWA, a11y, wydajność (ok. 6 h+):** E4, **F1 PWA kierowcy** (decyzja!), F2–F5, G1–G3, H1, I1–I3, E6, testy e2e Playwright (czas, reset, zgłoszenie → mapa, trasa, przystanek, offline).

**Decyzje potrzebne od Ciebie przed Etapem 3/4:**
1. Czy budujemy PWA kierowcy dziś (F1, L) – jeśli tak, który kierunek z kanwy (A/B/C)?
2. Czy panel `/dyspozytor` przepisujemy na tokeny widoku C (D1, L), czy zostawiamy go jako „widok ekspercki” i tylko naprawiamy P0/P1?
3. Kolejność fal: proponuję Fala 1 dziś wieczorem, Fala 2 jutro rano, Fala 3 tylko F1 + e2e, jeśli starczy czasu przed 23:00.
