# Przegląd przed oddaniem: 50 decyzji (sob 3.10.2026, wieczór)

Brainstorm połączony z przeglądem aplikacji: uprawnienia, ekrany, wygląd, widoki, zależności, produkt.
Każda decyzja ma falę wdrożenia: **A** bezpieczny pokaz, **B** jedna aplikacja dla jury, **C** głębia, **M** materiały,
**R** ROADMAPA. Fale idą po kolei, a pozycje oznaczone „do cięcia” wypadają pierwsze, gdy zabraknie czasu.

## 1. Uprawnienia

| # | Decyzja | Fala |
|---|---|---|
| 1 | Trzy role: publiczna (mieszkaniec, jury), dyspozytor, kierowca z własną ścieżką PWA. | A |
| 2 | Loginy `dyspozytor`, `driver_bin`, `driver_altana`; wspólne hasło demo w `.env` / Coolify (`DEMO_PASSWORD`), nie w kodzie. Kierowca widzi i zapisuje tylko kurs swojej floty. | A |
| 3 | Panel `/dyspozytor` bez logowania w trybie podglądu; `/kierowca` tylko po zalogowaniu; dane logowania dla jury tylko w HackTribe i na slajdzie. | A, M |
| 4 | Zegar „Przewiń +1 h”: dyspozytor i jury (publiczne). | A |
| 5 | „Reset” tylko dla dyspozytora, z potwierdzeniem na stronie (nie `confirm()`). | A |
| 6 | AI (raport wróżki) i upload zdjęć tylko dla dyspozytora; kierowca: zdjęcie przy swoim przystanku; globalnie maks. 30 wywołań Claude na godzinę. | A |
| 7 | Ukryte pola podglądu (`reliability`, `check_reason`, `misuse`, `crew_issue`) filtrowane na serwerze; ranking i urządzenia publiczne. | A |
| 8 | `/logowanie`, sesja 12 h, 5 prób z IP na 15 min; kolejka offline nie kasuje zapisów po 401/403. | A |

## 2. Ekrany i nawigacja

| # | Decyzja | Fala |
|---|---|---|
| 9 | `/ekipa` → 301 `/kierowca`, `/przycisk/<id>` → 301 `/epapier/<id>`; przekierowania z QR zostają; `/zdjecia` w panelu. | A |
| 10 | Menu zależne od roli; „Jury” → „Zgłoś kosz”; PWA kierowcy bez menu. | B |
| 11 | `/telefony` „Na telefonie”: ramki z prawdziwymi aplikacjami; kierowca w podglądzie bez zapisów, mieszkaniec w pełni działający. | B |
| 12 | Trzy ramki dla kosza 18: e-papier, mieszkaniec, kierowca; scenariusz w 3 krokach nad ramkami. | B |
| 13 | QR jury zawsze na kosz 18 (pokazuje scalanie zgłoszeń); limit w trybie jury po ciasteczku, nie po IP. | B |
| 14 | Bez 5. kroku; linki „Zobacz w telefonie kierowcy” (krok 3) i „kliknij w telefonie na ekranie” (karta QR); „Na telefonie” wyróżnione w menu. | B |
| 15 | Panel: zakładka Sytuacja zaczyna od „Pilne teraz”, lista punktów posortowana po pilności; bez mobilnego układu panelu. | C |
| 16 | UI tylko po polsku + jedna linia EN (`lang="en"`) na `/` i `/telefony`. | B |

## 3. Wygląd

| # | Decyzja | Fala |
|---|---|---|
| 17 | Paleta C i IBM Plex na wszystkich ekranach przez podmianę wartości zmiennych (panel bez przepisywania); Fraunces tylko w nagłówkach PWA kierowcy. | B |
| 18 | Słownik stanów: W porządku ✓ koło, Zapełnia się ↑ romb, **Do opróżnienia** ! kwadrat, Zgłoszenie mieszkańca … dymek, Sprawdź przycisk ! trójkąt, altana = podwójna obwódka; „Przepełniony” tylko dla prognozy ≥ 100%. | B |
| 19 | Karta 1 na `/`: „10 przepełnionych teraz” + „+5 do opróżnienia przed kursem”. | B |
| 20 | Tryb ciemny tylko w obu PWA; desktop jasny; ramki na `/telefony` jasne z przełącznikiem „Pokaż tryb nocny”. | B |
| 21 | Ikony SVG (sprite) zamiast emoji w całym UI (do cięcia: wtedy tylko usuwamy emoji). | B |
| 22 | Usuwamy Tailwind i DaisyUI z panelu. | B |
| 23 | Trasy w kolorach C wszędzie; korek tylko etykietą i czasem jazdy, bez zmiany wzoru linii. | B |
| 24 | Jeden plik `tokens.css`, jeden kolor = jedno znaczenie; odcienie z walidacją kontrastu AA i daltonizmu (tabela w DECYZJE.md). | B |

## 4. Widoki i stany

| # | Decyzja | Fala |
|---|---|---|
| 25 | Porównanie 4 tygodni liczone przy `seed`; szare paski zamiast „–”; trasa z ponowieniem i ostatnią z pamięci. | C |
| 26 | Dymek pinu na `/` → „Szczegóły w panelu”; mapa ↔ lista w panelu; tabela punktów pod mapą na `/` (do cięcia). | C |
| 27 | „Wyślij do kierowcy” (tabela `Dispatch`, etykieta „Od dyspozytora”, odpowiedź kierowcy). | C, do cięcia |
| 28 | GPS przy „Opróżniony” i „Problem”: bez blokady, flaga > 150 m, punkty dla mieszkańców wstrzymane do potwierdzenia. | C |
| 29 | „Moje zgłoszenia” w telefonie, status odświeżany co 30 s; bez Web Push. | C, do cięcia |
| 30 | Postęp kierowcy w panelu; „Pomiń” zapisywane na serwerze (`stop-issue` `skip`). | C |
| 31 | `/dostepnosc`: deklaracja dostępności, status „częściowo zgodna”. | C |
| 32 | `/prywatnosc`, IP zgłoszeń przechowywane 24 h, zgoda przy rejestracji w programie. | C |

## 5. Zależności i infrastruktura

| # | Decyzja | Fala |
|---|---|---|
| 33 | Leaflet, markercluster, qrcode, Chart.js i IBM Plex lokalnie (`static/vendor`, `static/fonts`); fallback SVG mapy wszędzie. | A |
| 34 | Tabela `Counter` w bazie dla wszystkich limitów (SMS, AI, logowanie, kosz 18). | A |
| 35 | Cache `point_states`/`plan_routes` po wersji danych; `ETag` dla PNG e-papieru; e-papier co 2 s. | A |
| 36 | Najpierw scalenie PR #3 i #4; fale jako osobne PR-y; zamrożenie kodu w niedzielę o 19:00, deploy o 20:00. | — |
| 37 | `scripts/smoke.py` (10 przepływów, Playwright, poza pytest). | C |
| 38 | Model `claude-opus-5-5` dla Vision, raportu i Karnetu, z jawnym `effort`. | A |
| 39 | Automatyczny reset demo po 30 min bezczynności; ostatni deploy z `seed --force`. | A |
| 40 | Licencja AGPL-3.0, plik `NOTICE` z atrybucjami. | A |

## 6. Produkt i pokaz

| # | Decyzja | Fala |
|---|---|---|
| 41 | Dwie liczby główne: puste przyjazdy 57% → 27% i przepełnione altany 338 h → 0 h (zamiast „−16%”). | B, M |
| 42 | Porównanie kategorii („czujnik w każdym koszu”) bez nazw firm i liczb o konkurencji. | M |
| 43 | Skalowanie na Kraków liczone w kodzie: 1,5–2,8 mln zł/rok (wariant ostrożny / pełny). | C, M |
| 44 | Nagranie 2:00: problem → `/` → `/telefony` → liczby → hasło. | M |
| 45 | Lektor PL (autor), napisy EN wtopione, `.srt` PL w repo. | M |
| 46 | PDF 10 slajdów EN (artefakt Slides). | M |
| 47 | Teksty dla HackTribe w prywatnym artefakcie; hasło wpisuje autor. | M |
| 48 | Kolejność A → B → C → materiały; cięcia: 27, 29, tabela z 26, ikony z 21. | — |
| 49 | Plan fali = ten dokument; zgoda z góry na commit, push i PR po fali (pytest + smoke + DECYZJE); merge i Redeploy robi autor. | — |
| 50 | Zapis: ten plik, DECYZJE.md, notatka Obsidian, pamięć Claude, ROADMAPA.md. | — |
