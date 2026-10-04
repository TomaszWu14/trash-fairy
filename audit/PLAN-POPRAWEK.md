# Plan poprawek po jury r0 (4.10.2026, ok. 06:40)

Źródło: `audit/JURY.md` (ID J-xx). Budżet do 08:00: ok. 75 minut pracy kilku agentów równolegle. Kolejność w grupie: (waga kryterium × zysk) / nakład. `do 08:00` = mieści się w budżecie. Każdy pakiet kończy się `python -m pytest -q -n auto`; po wszystkich pakietach sonda r1 (`scripts/jury_check.py`) i porównanie z r0.

## Zaplanowane wcześniej (decyzje autora)

| Pozycja | Stan | Pakiet | Uwagi |
|---|---|---|---|
| **D1.** Mieszkaniec zgłasza tylko przy koszu (przyciski na panelu, QR rotujący co 10 min, formularz na jednym ekranie, „Twoje zgłoszenia”) | **w pracy** (osobny agent) | – | Po scaleniu rusza pakiet „po-przebudowie-mieszkanca”. Do sprawdzenia przez agenta D1: tekst „Kod zmienia się codziennie” przeczy rotacji co 10 min; `api_pl.py:281` „Położenia nie sprawdzamy” przeczy 150 m (i /prywatnosc); karta „Twoje zgłoszenia” na pierwszym ekranie 390×844; „Przepełniony” bez okna potwierdzenia. |
| **D2.** KPI „Oszczędności wobec planu”: wyjaśnienie planu, przedział dat, oszczędność dziennie, tabelka dzień / miesiąc / rok | **zaplanowane, do 08:00** | dashboard (pierwsze zadanie) | Kryteria akceptacji od jury: bez słowa „kurs” (u kierowcy „Kurs 14:00” to przejazd pojazdu), „N odbiorów (opróżnień koszy) i M km mniej niż w planie”, rozbicie: odbiory × 4 zł + km × 5 zł, opłata za tony bez zmian; wiersz „na 1 kosz” (dziś ok. 4 074 zł / 30 dni ≈ 136 zł dziennie ≈ 49,6 tys. zł rocznie ≈ 18 zł na kosz w 30 dni, 222 kosze); etykieta „CO₂ mniej niż w planie” (J-02). Przeliczenie miesiąc/rok oznaczone jako liniowe, na danych demonstracyjnych. |

## 1. BLOKUJE

| ID | Co | Nakład | Kto | do 08:00 |
|---|---|---|---|---|
| J-01 | Deck 14 → 10 slajdów, PDF do `docs/`, link w README | M | materiały (autor / agent decku) | nie musi; **przed 23:00 obowiązkowo** |

## 2. ODBIERA PUNKTY (od najlepszego stosunku zysku do nakładu)

| # | ID | Co | Kryterium | Nakład | Pakiet | do 08:00 |
|---|---|---|---|---|---|---|
| 1 | J-07 | Sparkline'y i projekt bez niepełnego miesiąca (`TF.fullMonths`) | Design | S | dashboard | tak |
| 2 | J-06 | Oszczędności i CO₂ na początek KPI (+ test kolejności) | Design | S | dashboard | tak |
| 3 | J-05 | „przed wdrożeniem: śr. X” przy 3 KPI, `sr-only` lepiej/gorzej | Idea | S | dashboard | tak |
| 4 | J-03 | Kafelki metodologii = liczby z hero, bez „+97 km” | Idea | S | dokumenty | tak |
| 5 | J-02 | Zdanie o dwóch pomiarach w metodologii + „CO₂ mniej niż w planie” | Idea | S | dokumenty + dashboard (D2) | tak |
| 6 | J-16 | Podpis kosztu w projekcie (opłata za tonę) | Idea | S | dashboard | tak |
| 7 | J-11 | Usunąć „· przystanek N” u kierowcy | Użyteczność | S | kierowca | tak |
| 8 | J-12 | Adresy kierowcy: `--fs-sm`, bez ucinania | Użyteczność | S | kierowca | tak |
| 9 | J-09 | Telefon: podpisy pod ikonami, „Dane demonstracyjne” widoczne (`app.css` + `help.css`) | Użyteczność | S | global | tak |
| 10 | J-13 | Scenariusz krok 3: prawdziwy tekst + podświetlenie kosza 18 | Użyteczność | S | global + kierowca | tak |
| 11 | J-15 | Osie słupków w projekcie od zera | Design | S | dashboard | tak |
| 12 | J-17 | Dashboard na telefonie: KPI nad filtrami, bez CSV | Design | S | dashboard | tak |
| 13 | J-18 | Wykres dzielnic na telefonie (obrót etykiet, marginesy) | Design | S | dashboard | tak |
| 14 | J-14 | Urządzenia: spójne liczby | Użyteczność | S | dashboard | tak |
| 15 | J-27 | Skip-link widoczny po fokusie, pierścień 3:1 | Użyteczność | S | global | tak |
| 16 | J-28 | Reset demo: potwierdzenie, postęp, dłuższe toasty | Użyteczność | S | global (+ start.html po D1) | tak |
| 17 | J-25 | /api/docs: H1 „Otwarte API”, notka Open311, plakietka POST | Kategoria | S | dokumenty | tak |
| 18 | J-23 | Metodologia: przecinki, „Trash Fairy”, zdanie o 1822 → 1823 | Użyteczność | S | dokumenty | tak |
| 19 | J-24 | Metodologia: `<details>`, kotwice, bez nazw zmiennych | Design | S | dokumenty | tak |
| 20 | J-21 | Prywatność: 7 dni, AI, EXIF, administrator | Kompletność | S | dokumenty | tak |
| 21 | J-22 | Prywatność: tabela jako karty na telefonie | Design | S | dokumenty | tak |
| 22 | J-26 | 404 i /dostepnosc zgodne z D1 | Kompletność | S | global + dokumenty | tak |
| 23 | J-19 | Słownik: odbiór / kurs (tylko etykiety) | Użyteczność | M | dashboard (po D2) + dokumenty | tak |
| 24 | J-20 | Reset na produkcji po ostatnim Redeployu, `DEMO.md` | Kompletność | S | materiały (operacyjne) | po deployu |
| 25 | J-08 | Panel: „Najbliższy odbiór” tylko gdy kosz na trasie | Idea | S | po-przebudowie | tak, po D1 |
| 26 | J-10 | Panel na telefonie: `minmax(0,1fr)`, mniejsza liczba | Design | S | po-przebudowie | tak, po D1 |
| 27 | J-04 | Hero: „altan śmietnikowych”, „szacunek”, „Symulacja 4 tygodni” | Idea | S | po-przebudowie | tak, po D1 |
| 28 | J-29 | Status: bez trzech identycznych godzin | Użyteczność | S | po-przebudowie | tak, po D1 |
| 29 | J-30 | Panel: „Do opróżnienia ok. …” zamiast „Przewidywane 85%” | Użyteczność | S | po-przebudowie | tak, po D1 |

## 3. KOSMETYKA (tylko S)

Do 08:00, jeśli pakiet skończy powyższe: J-31 (`<pre tabindex>`, jedyne axe), J-34, J-35, J-32, J-33, J-37 (`time_label` u kierowcy), J-38, J-39, J-41, J-42, J-43, J-44, J-45, J-46, J-48, J-51, J-55, J-36 (tylko zamiany w plikach pakietu po dodaniu tokenów przez „global”).
Po 08:00 lub po sondzie r1: J-40, J-47, J-49, J-50, J-52, J-53, J-54.

## 4. Pakiety (rozłączne pliki)

| Pakiet | Pliki | Zadania (ID) | Uwagi |
|---|---|---|---|
| **global** | `tokens.css`, `app.css`, `base.html`, `_ui.html`, `app.js`, `start.css`, `404.html`, `help.css` | J-09, J-27, J-26 (404), J-28 (app.js), J-13 (tekst kroku 3), J-34, J-36 (tokeny), J-48, J-53 (helper) | `app.js`: agent D1 zmienia tylko `TF.SCENARIO`; edytować pojedynczymi `Edit`, po sprawdzeniu `git diff`. Tokeny J-36 dodać najpierw: używają ich kierowca, dokumenty i kiosk. |
| **kierowca** | `kierowca.html`, `kierowca_kosz.html`, `kierowca.css`, `kierowca.js`, `app/routes.py`, `tests/test_routes.py` | J-11, J-12, J-13 (podświetlenie), J-42, J-39, J-38, J-41, J-37, J-36 | `TF.scenarioNudge?.()` wołać z optional chaining (helper w „global”). |
| **dashboard** | `dashboard.html`, `dashboard.css`, `dashboard.js`, `charts.js`, `projekt.html`, `projekt.js`, `urzadzenia.html`, `urzadzenia.css`, `urzadzenia.js`, `app/dashboard_api.py`, `app/dashboard.py`, `app/devices_api.py`, `tests/test_dashboard.py` | **D2**, J-07, J-06, J-05, J-16, J-15, J-17, J-18, J-14, J-19, J-43, J-44, J-45, J-46, J-36, J-47, J-49 | Najcięższy pakiet. Jeśli są dwa agenty: urządzenia (`urzadzenia.*`, `devices_api.py`) można oddzielić, pliki są rozłączne. |
| **dokumenty** | `metodologia.html`, `api_docs.html`, `dostepnosc.html`, `prywatnosc.html`, `doc.css`, `app/methodology.py`, `app/open_api.py`, `app/static/openapi.json` | J-03, J-02, J-23, J-24, J-21, J-22, J-25, J-31, J-26 (dostępność), J-19 (wizyty), J-36, J-38, J-51, J-50, J-54, J-49 | `openapi.json` jest już zmieniony w drzewie roboczym: J-50 tylko po sprawdzeniu diffu. |
| **po-przebudowie-mieszkanca** | `zglos_wybor.html`, `zglos.html`, `zgloszenie.html`, `mieszkaniec_base.html`, `mieszkaniec.css`, `mieszkaniec.js`, `kiosk.html`, `kiosk.css`, `kiosk.js`, `start.html`, `app/api_pl.py`, `app/ui.py`, `app/views.py`, `tests/test_perspektywy.py`, `tests/test_poprawki_jury.py` | J-08, J-10, J-04, J-28 (start.html), J-29, J-30, J-32, J-33, J-35, J-36, J-55, J-40, J-53 | Start dopiero po scaleniu D1. |
| **materiały** | `README.md`, `DEMO.md`, `docs/video/*`, `docs/img/zglos.png`, deck, teksty HackTribe | J-01, J-26 (materiały), J-20, J-54, liczby po D2 | Po D1 i D2; jeden łańcuch kwot w decku i tekście zgłoszenia. |

## 5. ROADMAPA (po hackathonie, nie robimy teraz)

- Wspólny `TF.date` i jeden format dat w całej aplikacji (J-37).
- Tabela „Skąd te kwoty” w metodologii: kwota, ekran, baza, zł na kosz (J-02d).
- Jeden zestaw progów koloru i stanu (50/80 kontra 60/85) w kodzie (J-38).
- /api/docs: endpointy publiczne i wewnętrzne osobno (`<details>`).
- Mini-przełącznik perspektyw na panelu kiosku.
- Automatyczne „Dalej” w scenariuszu (czeka na decyzję autora, pytanie IA).
- Pamięć filtrów dashboardu w `sessionStorage`.
- Pojazd dyżurny / kurs interwencyjny pod normę 2 h (pytanie Jurora 3).
- Pełne przeniesienie palety kiosku na tokeny, jeśli nie zdążymy dziś.
