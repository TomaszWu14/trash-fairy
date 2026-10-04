# Jury: przegląd przed oddaniem (runda r0)

**Data:** 4.10.2026, ok. 06:40 (zamrożenie kodu 19:00, oddanie 23:00).
**Metoda:** sonda `scripts/jury_check.py`, runda r0: zrzuty 1366×768 (laptop), 390×844 (telefon), 1280×800 (kiosk), pierwszy ekran i cała strona dla 16 ekranów; metryki (`audit/jury/r0/metryki.json`: poziomy scroll także przy 200%, cele < 44 px, kolory spoza `tokens.css`, ucięty tekst, kolejność Tab, axe WCAG 2.1 A/AA, żargon, błędy JS); budżety kliknięć (`audit/jury/r0/budzety.json`). Trzej jurorzy: **Juror 1** (trzy przeglądy: przegląd/panel/mieszkaniec, kierowca/dashboard, dokumenty/spójność), **Juror 2** (użytkownik 68+ i WCAG), **Juror 3** (ekspert merytoryczny i wdrożeniowy). Wspólne zaplecze: analityk architektury informacji (budżety) i analityk wzorców z HugMe. Każde znalezisko przeszło przez sceptyka, który sprawdzał zrzuty, kod i odpowiedzi API.

**Wagi kryteriów** (oficjalne, `docs/zadanie/Open Task - SMART CITY/Details - SMART CITY.pdf`): Idea i innowacja **30%**, Związek z kategorią **20%**, Użyteczność **20%**, Design **20%**, Kompletność i wdrożenie **10%**. Wymóg formalny: prezentacja PDF **maks. 10 slajdów**.

**Decyzje autora (ustalone, nie podważamy):**
1. Mieszkaniec nie widzi mapy ani listy koszy. Zgłasza tylko przy koszu: przyciskiem na panelu („Przepełniony” / „Inny problem”) albo skanem kodu QR z panelu (kod rotuje co 10 min, HMAC z oknem czasu, położenie do 150 m). Formularz na jednym ekranie, na `/zglos` lista „Twoje zgłoszenia”. **W pracy** (osobny agent). Znalezisk o mapie, liście koszy, kreatorze 3 kroków i braku przycisków na panelu tu nie ma.
2. KPI „Oszczędności wobec planu”: nie wiadomo, jaki to plan, a „668 kursów mniej” myli (to opróżnienia koszy, nie wyjazdy śmieciarki; 4 zł to koszt wizyty przy koszu, km osobno po 5 zł). Do zrobienia: wyjaśnienie planu (`app/dashboard.py` `plan()`), przedział dat, oszczędność dziennie, tabelka dzień/miesiąc/rok. Znaleziska poniżej tylko uzupełniają tę pracę o spójność liczb.

**Stan wyjściowy z sondy:** 0 błędów JS, brak poziomego scrolla (także przy 200%), axe czysto poza `/api/docs` (1 reguła: `scrollable-region-focusable`).

---

## Znaleziska

Format: `[ID] [Jurorzy] [Ekran] [Waga] [Kryterium]`, potem: co widzi juror → dlaczego to problem → poprawka → nakład.

### BLOKUJE

**[J-01] [Juror 3, wzorce] [Prezentacja PDF] [BLOKUJE] [Kompletność i wdrożenie]**
Deck ma 14 slajdów (cover, problem, solution, idea, ai-flow, demo-field, dashboard, devices, results, scale, honesty, tech, business, ask) i leży poza repo jako artefakt. → Regulamin dopuszcza PDF z najwyżej 10 slajdami, więc zgłoszenie łamie wymóg formalny. → Scalić do 10: 1 cover; 2 problem; 3 rozwiązanie + idea; 4 AI w przepływie (reguły decydują, AI opisuje); 5 demo w terenie (panel → mieszkaniec → kierowca); 6 dashboard + urządzenia; 7 wyniki + „co syntetyczne” (jeden łańcuch kwot: kosz → dashboard → Kraków); 8 skala + biznes; 9 technologia (testy z wyniku pytest, WCAG); 10 prośba (pilotaż Dzielnica I, bez nowych liczb). PDF do `docs/`, link w README, sprawdzić 10 stron. → **M**

### ODBIERA PUNKTY

**[J-02] [Juror 1, Juror 2, Juror 3, wzorce, IA] [Przegląd / Dashboard / Metodologia / README] [ODBIERA PUNKTY] [Idea i innowacja]**
Cztery kwoty oszczędności bez wspólnej jednostki i źródła: hero „1,5–2,8 mln zł rocznie w skali Krakowa”, dashboard „4 097 zł / 668 kursów mniej” (r0; teraz 4 074 zł / 664), metodologia „≈ 2 976 zł miesięcznie, 866 wizyt mniej, +97 km, +97 kg CO₂”, README „ok. 2 976 zł”, /metodologia „2 576 zł/mies.” w pilotażu. 866 obok 668 wygląda jak literówka, a CO₂ na jednej stronie rośnie (+97 kg), na drugiej spada („Redukcja CO₂ 285 kg”). → To dwa różne pomiary (symulacja 4 tygodni bez zgłoszeń w `methodology.money()` oraz historia wobec planu w `dashboard_api._kpi_values()`), ale nigdzie tego nie napisano. Juror uzna liczby za zmyślone. Bez mianownika 4 074 zł wygląda na grosze, a to ok. 18 zł na kosz w 30 dni (222 kosze), ten sam rząd co 51,5 zł/kosz w metodologii. → (a) Metodologia: jedno zdanie pod kafelkami, że to symulacja ostrożna 4 tygodni, a dashboard pokazuje historię wybranego okresu wobec planu, z linkiem do `/dashboard`. (b) Etykieta KPI „Redukcja CO₂” → „CO₂ mniej niż w planie” i `KPI_OPIS["co2"]`. (c) Kryteria dla decyzji 2: kolumna „na 1 kosz”, bez słowa „kurs”, rozbicie wizyty i km. (d) Tabela „Skąd te kwoty” na metodologii: ROADMAPA (M). → **S** (a–c)

**[J-03] [Juror 1] [Metodologia, wejście z „Jak to policzyliśmy”] [ODBIERA PUNKTY] [Idea i innowacja]**
Juror klika link pod trzema liczbami hero (57% → 27%, 338 h → 0 h, 1,5–2,8 mln zł), a kafelki „Najważniejsze wyniki” pokazują coś innego: 2,4 p.p., 866, „+97 km”, ≈ 2 976 zł. → Ślad urywa się na kliknięciu, które buduje wiarygodność, a gorszy wynik (+97 km) stoi na górze. Liczby z hero są niżej w tabelach, ale nie w kafelkach. → `metodologia.html:10-15`: kafelki z danych, które szablon już ma (`result.fixed/fairy.bin.empty_share`, `shelter.overflow_hours`, `city.careful/full.pln_year`) + 2,4 p.p.; usunąć kafelki „+97 km”, „866 wizyt”, „≈ 2 976 zł” (zostają w tabeli i bilansie); `id="porownanie"` i `id="krakow"` na H2. Bez zmian w `app/ui.py`. → **S**

**[J-04] [Juror 1, Juror 2] [Przegląd (hero)] [ODBIERA PUNKTY] [Idea i innowacja]**
„338 h → 0 h przepełnień altan w 4 tygodnie”: słowo „altana” nie pada wcześniej, strona mówi o koszach, a „0 h” bez „symulacja” brzmi jak obietnica. „1,5–2,8 mln zł rocznie w skali Krakowa” bez „szacunek”. → Sceptyczny juror zestawi 2,8 mln zł z 4 tys. zł na dashboardzie. → `start.html:17-20`, tylko teksty: „przepełnień altan śmietnikowych w 4 tygodnie”, „rocznie w skali Krakowa · szacunek”, link „Symulacja 4 tygodni: jak to policzyliśmy”. Liczb nie zmieniamy. Po scaleniu decyzji 1 (ten sam plik). → **S**

**[J-05] [Juror 1, Juror 2] [Dashboard: kafle KPI] [ODBIERA PUNKTY] [Idea i innowacja / Użyteczność]**
Trzy czerwone chipy na KPI, które mają dowodzić sensu produktu: zapełnienie przy odbiorze −3,1%, obsłużone w ≤ 2 h 29% −8,6%, czas reakcji 6,2 h +19,2%. Ta sama strzałka ↘ raz zielona, raz czerwona: „lepiej/gorzej” niesie tylko kolor. → Chip porównuje 30 dni z poprzednimi 30 (szum), a efekt wdrożenia widać w trendzie: zapełnienie ok. 52 → 63%, SLA ok. 9 → 30%, czas reakcji ok. 8,5 → 5,8 h. WCAG 1.4.1 i zasada repo „kolor nigdy jedynym nośnikiem”. → Dla `zapelnienie`, `sla_2h`, `czas_reakcji` dopisać `<p class="kpi-sub">przed wdrożeniem: śr. X</p>` (średnia trendu z miesięcy < `meta.wdrozenie`, `WDROZENIE = 2026-05-01`); w chipie `<span class="sr-only">, lepiej/gorzej niż w poprzednim okresie</span>` + `title`. Chipów nie przeliczać na przed/po (koszt i zgłoszenia wyszłyby czerwone, a zima kontra lato to błąd sezonowości). → **S**

**[J-06] [Juror 1, IA] [Dashboard: rząd KPI] [ODBIERA PUNKTY] [Design]**
„Oszczędności wobec planu” to siódmy z 9 kafli (środek drugiego rzędu); pierwszy rząd kończy się czerwonym +19,2%. → Lewy górny róg czyta się pierwszy; liczba, którą produkt sprzedaje, nie jest pierwsza. → `dashboard_api.py:138-142` kolejność: `oszczednosci, co2, wywozy, anomalie` (rząd 1, wszystkie zielone; oszczędności zajmują 2 kolumny), potem `koszt, zapelnienie, zgloszenia, czas_reakcji, sla_2h`. **Zaktualizować `tests/test_dashboard.py:90`** (test sprawdza dokładną kolejność id). Kafla SLA nie usuwać (dziura w siatce). → **S**

**[J-07] [Juror 1, Juror 2, Juror 3, wzorce] [Dashboard: sparkline'y; Projekt: wykresy] [ODBIERA PUNKTY] [Design]**
Każdy sparkline (koszt, wywozy, zgłoszenia, oszczędności, CO₂, anomalie) kończy się pionowym spadkiem prawie do zera; na stronie projektu ostatni słupek (paź 26) to ok. 2,9 tys. zł przy ok. 34 tys. Pod KPI stoi „Wykresy: pełne miesiące”. → Ostatni punkt to 3 dni października (koszt 6 954 zł wobec ok. 70 tys.). Wygląda jak krach, a podpis jest nieprawdziwy. Duże wykresy tną ten miesiąc przez `fullMonths()`, sparkline'y i projekt nie. → Przenieść `fullMonths` z `dashboard.js:67-72` do `charts.js` jako `TF.fullMonths`; w `renderKpis` `TF.spark(k.trend.slice(0, n))`, gdzie `n = TF.fullMonths(d.meta).miesiace.length`; w `projekt.js` `const pp = TF.fullMonths(p.przed_po || {})`. Backend bez zmian. → **S**

**[J-08] [Juror 1, Juror 3] [Panel na koszu po opróżnieniu (kiosk)] [ODBIERA PUNKTY] [Idea i innowacja / Związek z kategorią]**
Po opróżnieniu panel pokazuje 8% i „Najbliższy odbiór: dziś, 14:00”, choć kosz wypadł z kursu (`/api/kosze/18`: `trasa.na_trasie=false`, „85% dopiero ok. 04.10 10:48”). Przy zgłoszeniu panel pisze „Kosz jest na liście kierowcy MPO” bez względu na trasę. → To dokładnie „pusty przyjazd”, który hero obiecuje usunąć; panel pokazuje kurs floty (`next_runs`), a nie odbiór tego kosza. Dotyczy też zwykłego stanu (34%). → `api_pl.py` `kosz_json`: `nastepny_odbior = run_at.isoformat() if route['na_trasie'] else None`; `kiosk.js`: przy `null` „gdy będzie potrzebny”; „Kosz jest na liście kierowcy MPO” tylko przy `k.trasa.na_trasie`, inaczej „Zgłoszenie przyjęte, sprawdzimy przy kolejnym kursie”. Jeden test w `tests/test_perspektywy.py`. Po scaleniu decyzji 1. → **S**

**[J-09] [Juror 1, Juror 2, Juror 3, wzorce, IA] [Wszystkie ekrany z górnym paskiem, telefon] [ODBIERA PUNKTY] [Użyteczność]**
Przełącznik perspektyw na 390 px to 5 ikon bez podpisów (monitor = Panel, smartfon = Mieszkaniec łatwo pomylić); plakietka „Dane demonstracyjne” zwinięta do fioletowej iskierki 38×28, która kojarzy się z AI. Podpisy znikają już przy ≤ 1100 px. → Juror z telefonu zgaduje, gdzie jest; `title` nie działa na dotyk; znika wymagane oznaczenie danych syntetycznych. → `base.html`: krótka etykieta pod ikoną (te same słowa: Przegląd, Panel, Mieszkaniec, Kierowca, Dashboard) w `<small aria-hidden="true">`, przy ≤ 720 px układ kolumnowy (`--fs-xs`, wysokość 48 px). Plakietka: zdjąć ukrywanie napisu w **dwóch** miejscach (`app.css:45` i `help.css:53`), ikona `info` zamiast `sparkles`; jeśli z przyciskami Podpowiedzi/Przewodnik pasek przy 390 px zawija się do trzeciego wiersza, na ≤ 720 px pokazać krótsze „Dane demo”. Sprawdzić hscroll na 390 px. → **S**

**[J-10] [Juror 1, Juror 2, Juror 3] [Panel na koszu, telefon 390×844] [ODBIERA PUNKTY] [Design]**
Prawa krawędź ucięta: „Kosz nr 1…”, „%” przy 34, „zabrudzone opakowania,”, karty wychodzą poza ekran. Sonda nie widzi (`.kiosk { overflow: hidden }`). → Liczba ma `clamp(96px, 18vh, 168px)`, czyli 152 px na telefonie (więcej niż na kiosku), a kolumna `1fr` rozpycha się do treści. Kafel przeglądu prowadzi tu z telefonu. → `kiosk.css` w `@media (max-width: 900px)`: `grid-template-columns: minmax(0, 1fr)` i `.kiosk-num { font-size: clamp(64px, 22vw, 120px) }`. Iteracja r2 agenta mieszkańca zawija już resztę. Po scaleniu decyzji 1, potem rzut oka na 390 px z „120%”. → **S**

**[J-11] [Juror 1, Juror 2, Juror 3] [Kierowca /kierowca] [ODBIERA PUNKTY] [Użyteczność]**
Pierwszy kosz na liście „po priorytecie” ma dopisek „przystanek 32”, drugi „przystanek 43”; pinezki 1–5 idą według listy, linia trasy (OR-Tools) w innej kolejności. Trzy numeracje na jednym ekranie. → Kierowca ma podjąć jedną decyzję: dokąd teraz. Sprzeczne numery podważają wiarygodność trasy. → `kierowca.js:34`: usunąć `` · przystanek ${k.kolejnosc}``. → **S**

**[J-12] [Juror 1, Juror 2, wzorce] [Kierowca /kierowca, telefon] [ODBIERA PUNKTY] [Użyteczność]**
Adresy pod nazwą kosza mają 12 px i są ucięte wielokropkiem („okolice ul. Karmelicka · przy…”) w 11–12 pozycjach; 120 z 256 elementów tekstu ma 12 px. → Adres to informacja, której kierowca szuka. → `kierowca.css:29` `.k-stop-txt > span`: usunąć `white-space: nowrap; overflow: hidden; text-overflow: ellipsis`, `var(--fs-xs)` → `var(--fs-sm)`. → **S**

**[J-13] [Juror 3, IA] [Scenariusz demo, krok 3 (/kierowca)] [ODBIERA PUNKTY] [Użyteczność]**
Pasek mówi „Jest na górze listy, bo ma zgłoszenie mieszkańca. Kliknij go.”, a na górze stoją 4–6 świeżo zgłoszonych koszy z 91–120%; Kosz Rynek 18 jest pod linią przewijania. → Juror nie znajduje kosza i traci zaufanie do opisu; e2e celowo sprawdza tylko `ids[:15]`. → `app.js:121` tekst: „Kosze ze zgłoszeniem mieszkańca idą na górę listy, od najpełniejszego. Nasz jest podświetlony. Kliknij go.”; `kierowca.js`: w trybie scenariusza klasa `.top` dla `TF.demoBin` i jednorazowe `scrollIntoView({block:'nearest'})` po pierwszym renderze (nie przy każdym odświeżeniu). → **S**

**[J-14] [Juror 1] [Urządzenia] [ODBIERA PUNKTY] [Użyteczność]**
Chip „Sprawne 95”, nagłówek sekcji „Sprawne 12”; KPI „Baterie do wymiany w 30 dni: 2”, chip „Wymiana baterii w 30 dni: 1”; karta z baterią krytyczną 11% i „Wymiana za 40 dni”. → To samo słowo przy różnych liczbach; „krytyczna, wymiana za 40 dni” wygląda na błąd (`dni_do_wymiany` to czas do rozładowania). → `urzadzenia.js:82` `group(title, sub, arr, n = arr.length)`, dla „Sprawne” `n = ok.length`; `left()` dla `bateria_poziom === 'full'` „Wymień przy najbliższym kursie” i „rozładuje się ok. {data}” (też w modalu, l. 123); `devices_api.py:39` liczyć `dni_do_wymiany <= REPLACE_WITHIN_DAYS or bateria_pct < CRITICAL_BATTERY`, podpis „krytyczne i kończące się w 30 dni”. → **S**

**[J-15] [Juror 1, Juror 2] [Projekt] [ODBIERA PUNKTY] [Design]**
Słupki „Zapełnienie przy odbiorze” (oś 45–69) i „Czas reakcji” (oś 2–7) nie startują od zera: spadek 6,3 → 2,7 h (−57%) wygląda na −85%. Pionowy napis „start projektu” leży na słupku. → Ucięta oś słupkowa to klasyczny błąd, który podważa także prawdziwe liczby. → `projekt.js:35` usunąć `scale: k !== 'koszt'`; l. 37 etykieta markLine `position: 'end'`. → **S**

**[J-16] [Juror 1, Juror 2, Juror 3] [Projekt „Odbiory na żądanie – Stare Miasto”] [ODBIERA PUNKTY] [Idea i innowacja]**
Kafel „−13% wywozów”, a koszt miesięczny po starcie (ok. 34,8 tys. zł) taki sam jak przed (ok. 34,6 tys.). → „Mniej wywozów, pieniądze te same: co miasto zyskuje?” Koszt obejmuje opłatę za tonę (ok. 40–45% kosztu), która rośnie latem. → `projekt.html:12` podpis dla `koszt`: „zł miesięcznie; obejmuje opłatę za tonę odpadów, która rośnie latem; mniej odbiorów obniża koszt wizyt i przejazdów”. Wykresu „koszt na wywóz” nie dodawać (rośnie o 15%). → **S**

**[J-17] [Juror 1, Juror 2, IA] [Dashboard, telefon] [ODBIERA PUNKTY] [Design]**
Pierwsze 844 px to nagłówek, trzy przyciski eksportu, przełącznik okresu i trzy listy; pierwsza liczba ok. 620 px od góry, strona 6 943 px. „Pobierz raport PDF” otwiera okno drukowania. → Przez pierwsze sekundy formularz zamiast dashboardu. → `dashboard.css` w `@media (max-width: 720px)`: `.dash-actions [data-export] { display: none }`, `.dash-h { order: -2 } .kpis { order: -1 }`; `dashboard.html:20` napis „Drukuj lub zapisz PDF”. → **S**

**[J-18] [Juror 2] [Dashboard, telefon: wykresy] [ODBIERA PUNKTY] [Design]**
Oś „Dzielnice: koszty według frakcji” nieczytelna („Stare MiaGrzegórzkKrowodr…”), legenda w dwóch wierszach przykrywa „35 tys.”, ostatnia etykieta osi kosztów ucięta do „wrz 2”, pionowy napis „Wdrożenie Trash Fairy” przecina linię. → Widoczny błąd układu na najważniejszym ekranie dla miasta. → `dashboard.js:122` `axisLabel.rotate: el.clientWidth < 560 ? 40 : 0`, `grid: { top: 56 }`; w `rKoszty` `grid: { right: 24 }`. → **S**

**[J-19] [Juror 1, IA] [Dashboard, projekt, metodologia, kierowca] [ODBIERA PUNKTY] [Użyteczność]**
Jedno zdarzenie (opróżnienie kosza) ma pięć nazw: „Wywozy”, „Koszt wywozów”, „Koszty odbioru”, „Odbiory CSV”, „wizyty” (metodologia), „kursy” (oszczędności), a u kierowcy „Kurs 14:00” znaczy przejazd pojazdu. → Właśnie przez to „668 kursów” wprowadziło autora w błąd. → Słownik: **odbiór** = opróżnienie jednego kosza, **kurs** = przejazd pojazdu. Tylko etykiety, id zostają: `dashboard_api.py:138` „Koszt odbiorów”, „Odbiory”, `:171` „% odbiorów”; `dashboard.html:66`; `dashboard.js:121, :188`; `projekt.html:12` „Liczba odbiorów”; `dashboard.py:328-330` (PROJECT_METRICS); `metodologia.html` wizyt → odbiorów. `start.html:37` po decyzji 1. W jednym przebiegu z decyzją 2. → **M**

**[J-20] [Juror 3] [Produkcja trashfairy.twapp.pl/dashboard] [ODBIERA PUNKTY] [Kompletność i wdrożenie]**
Na produkcji „Anomalie ekipy” = 0 bez zmiany, kolumna anomalii w tabeli „Jakość obsługi” 0 we wszystkich dzielnicach (lokalnie 134). → Funkcja z PR #15 wygląda na zepsutą, a jury ogląda link produkcyjny. `flask seed` w Dockerfile pomija istniejącą bazę; historię z `far_m` odtwarza dopiero reset (`clock.py:142`). → Po ostatnim Redeployu kliknąć „Resetuj dane demo” na produkcji i sprawdzić `GET /api/dashboard/kpi` (anomalie > 0). Dopisać to w `DEMO.md` („Przed pokazem”). Bez zmian w kodzie. → **S**

**[J-21] [Juror 1, Juror 2] [Prywatność (treść)] [ODBIERA PUNKTY] [Kompletność i wdrożenie]**
Zdjęcie przechowywane „do czyszczenia komendą cleanup-photos”, a metodologia mówi „usuwane po 7 dniach”. Brak informacji, że zdjęcie opisuje zewnętrzny model AI, że usuwamy EXIF, kto jest administratorem. Wiersz „sprawdzenie, czy jesteś do 150 m od kosza” przeczy `api_pl.py:281` („Położenia nie sprawdzamy”). → Strona RODO to element gotowości do wdrożenia u podmiotu publicznego. → `prywatnosc.html:13`: „7 dni, potem usuwane automatycznie”; „podgląd dla kierowcy; opis zdjęcia przez model AI (Anthropic); zapisujemy bez metadanych EXIF”; wiersz „Lista Twoich zgłoszeń: tylko w tej przeglądarce”; „W pilotażu administratorem danych byłoby MPO Kraków (do ustalenia w umowie)”; H1 „Prywatność: jak używamy danych”; wiersz o położeniu zgodny z kodem po decyzji 1. → **S**

**[J-22] [Juror 1, Juror 2] [Prywatność, telefon] [ODBIERA PUNKTY] [Design]**
Kolumna „Jak długo” ucięta: „Jak dłu”, „nie zapisuj”, „24 godz”, bez sygnału przewijania. → Ucięta jest najważniejsza kolumna z obietnicami. → `doc.css` w `@media (max-width: 720px)` tabela `.stack` jako karty (thead ukryty wizualnie, `td[data-label]::before`), `prywatnosc.html:9` `class="stack"` i `data-label` w komórkach; tylko tokeny. → **S**

**[J-23] [Juror 1, Juror 2, Juror 3] [Metodologia: tabela porównania] [ODBIERA PUNKTY] [Użyteczność]**
Ułamki z kropką (1202.2, 110.3, „5.0 zł/km”, „4.0 zł”), tysiące raz ze spacją, raz bez (3360), kolumna „Wróżka” (wewnętrzne przezwisko), „godziny przepełnienia 1822 → 1823” i 110 → 267 km bez komentarza. Na telefonie widać tylko kolumnę „Stały”. → Jedyna tabela, która ma udowodnić tezę; niewyjaśnione wiersze to gotowe pytania jury. → `metodologia.html:19, :29` „Wróżka” → „Trash Fairy”; `:24` `{{ '{:,}'.format(v).replace(',', ' ').replace('.', ',') }}`; `:37-41` `'%g'|format(...)|replace('.', ',')`; zdanie: „Przy koszach ulicznych godzin przepełnienia jest praktycznie tyle samo, a zysk to mniej odbiorów i pustych przyjazdów. Przy altanach Trash Fairy usuwa przepełnienia kosztem dłuższych tras.” `doc.css` ≤ 720 px: węższy padding komórek. → **S**

**[J-24] [Juror 1, Juror 2] [Metodologia: gęstość] [ODBIERA PUNKTY] [Design]**
5 181 px na laptopie, 9 953 px na telefonie, 12 sekcji H2 bez spisu, tabela 25 reguł, 12 wstawek kodu (`COST_PER_KM_PLN`, `app/llm.py`, `flask cleanup-photos`), sekcja RODO dubluje /prywatnosc z innymi faktami, „wspólny seed”. → Juror ma znaleźć 3–4 dowody, a dostaje ścianę tabel i nazwy zmiennych. → Tabela reguł w `<details>`; zamiast nazw zmiennych „Założenia można zmienić w konfiguracji, bez zmiany kodu”; sekcję RODO zastąpić zdaniem z linkiem (razem z J-21); kotwice pod H1: Wyniki · Porównanie · Skala Krakowa · Pilotaż; „wspólny seed” → „ten sam losowy przebieg”. → **S**

**[J-25] [Juror 1] [/api/docs: struktura] [ODBIERA PUNKTY] [Związek z kategorią]**
Płaska lista 23 endpointów (7 147 px); Open311 GeoReport v2 i otwarte dane CSV/JSON na pozycjach 5–8 wyglądają jak wewnętrzne `POST /api/odbiory`; POST ma zieloną plakietkę GET; H1 „Trash Fairy — API”, stopka „Otwarte API”. → Najmocniejszy argument Smart City ginie. → `api_docs.html:6` `<h1>Otwarte API</h1>`; notka na górze: „Dla miasta: zgłoszenia w standardzie Open311 GeoReport v2 i miesięczne otwarte dane CSV/JSON, bez klucza.” z linkami; klasa `c-doc-post` (`--brand-soft`/`--brand-ink`) dla metod innych niż GET. → **S**

**[J-26] [Juror 1, Juror 2, Juror 3, wzorce] [404, /dostepnosc, README, DEMO.md, film] [ODBIERA PUNKTY] [Kompletność i wdrożenie]**
404: „Kod QR mógł pochodzić ze starej naklejki… Wybierz kosz w pobliżu”, główny przycisk „Kosze w pobliżu”, tylko H3, stopka wisi w połowie ekranu. /dostepnosc: „zgłoszenie bez aparatu jest możliwe z listy koszy w pobliżu”. README, DEMO.md, SCENARIUSZ.md, napisy: „mapa i najbliższe kosze”, „zgłoszenie w 3 krokach”, „668 kursów”. → Po decyzji 1 to nieprawda, a tych plików nie ma na liście agenta mieszkańca. → `404.html`: H1, tekst „Nie ma takiej strony albo kosza. Problem z koszem zgłosisz przy nim: przyciskiem na panelu albo skanem jego kodu QR.”, przyciski „Przegląd” (primary, `house`) i „Twoje zgłoszenia”, `.page-404` z `min-height` zamiast stylów inline (bez globalnego `body{display:flex}`). `dostepnosc.html:13, :15`: alternatywa bez aparatu = przyciski na panelu. Materiały po scaleniu decyzji 1 (i decyzji 2 dla „668 kursów”). → **S** (kod) + **M** (materiały)

**[J-27] [Juror 1, Juror 2, wzorce] [Wszystkie ekrany: klawiatura] [ODBIERA PUNKTY] [Użyteczność]**
Pierwszy Tab trafia w „Przejdź do treści” (`.sr-only`, 1×1 px, bez stylu `:focus`), fokus znika; pierścień fokusu to fiolet 28% (ok. 1,5:1 na bieli). → WCAG 2.4.7 i 1.4.11, a /dostepnosc deklaruje widoczny fokus. Sonda nie wykryła (klika (1,1) przed Tabem). → `app.css` po l. 13 `.sr-only:focus-visible { position: fixed; top: var(--s3); left: var(--s3); z-index: 100; width: auto; height: auto; clip: auto; overflow: visible; padding: var(--s2) var(--s4); background: var(--surface); color: var(--brand-ink); font-weight: 700; border-radius: var(--r-md); box-shadow: var(--ring); }`; `tokens.css:60` `--ring: 0 0 0 2px var(--surface), 0 0 0 4px var(--brand);`. → **S**

**[J-28] [Juror 1, Juror 2] [Przegląd: „Resetuj dane demo”] [ODBIERA PUNKTY] [Użyteczność]**
Drugi przycisk w hero, na telefonie tuż pod CTA; działa od jednego dotknięcia, ok. 13 s bez informacji, przeładowanie po 0,7 s, toast znika; na produkcji kasuje stan innym jurorom. Toasty trwają 3,6 s. → Operacja niszcząca bez potwierdzenia i postępu, w miejscu pierwszych 5 sekund. → `app.js:105` `confirm('Przywrócić dane demo? Zgłoszenia i odbiory z ostatnich minut znikną dla wszystkich oglądających.')`, napis „Przywracam dane… (do 15 s)” na czas żądania; `app.js:61` toast `kind === 'err' ? 10000 : 6000`; `start.html`: przycisk do `.story-head` jako `btn btn-ghost btn-sm` (po decyzji 1). → **S**

**[J-29] [Juror 1] [Status zgłoszenia] [ODBIERA PUNKTY] [Użyteczność]**
Oś czasu: „Przyjęte / W realizacji / Zrealizowane: sob., 13:30”, trzy razy ta sama godzina, w dniu oceny „sob.”. → Wygląda na atrapę (zamrożony zegar demo). Krok 5 scenariusza odsyła właśnie tu. → `mieszkaniec.js`: godzinę pokazywać tylko, gdy różni się od poprzedniego etapu, sama godzina bez dnia tygodnia; bez zmyślonych odstępów. Po scaleniu decyzji 1. → **S**

**[J-30] [Juror 2] [Panel na koszu: prognoza] [ODBIERA PUNKTY] [Użyteczność]**
„Przewidywane 85% ok. 20:20” obok dużego „34%”: 85% czego, czy to dobrze? → 85% to próg silnika, nie słowo przechodnia. → `api_pl.py:187-189` „Do opróżnienia ok. {godz}”; jednocześnie `api_pl.py:373-374` (`startswith('Przewidywane')` daje plakietkę „Prognoza” u kierowcy) i `tests/test_poprawki_jury.py:133-134`. Po scaleniu decyzji 1. → **S**

### KOSMETYKA

**[J-31] [Juror 1, Juror 2, Juror 3, wzorce] [/api/docs] [KOSMETYKA] [Kompletność i wdrożenie]** Jedyne naruszenie axe: `<pre>` przewijane bez fokusu (23 na telefonie). → Bez tego „0 naruszeń axe na 16 ekranach” można powiedzieć uczciwie. → `api_docs.html:18, :21` `<pre tabindex="0">`. → **S**

**[J-32] [Juror 1] [Status zgłoszenia] [KOSMETYKA] [Design]** H1 to numer TF-03740, status jako mała plakietka, „Zrealizowane” trzy razy; link „← Zgłoś inny kosz” przeczy decyzji 1; kafel „Mieszkaniec” mówi „w trzech krokach”. → Eyebrow „Zgłoszenie {{ nr }}”, H1 = status, bez plakietki i bez „Zgłoszenie zamknięte.”; link „Twoje zgłoszenia”; `start.html:35` nowy opis. → **S**

**[J-33] [Juror 1] [Ekrany mieszkańca] [KOSMETYKA] [Design]** Inicjały „AK” szare na fioletowym gradiencie (ok. 1,2–2,6:1): `.m-who span` nadpisuje `.m-avatar`. → `mieszkaniec.css:6` selektor `.m-who > div > span`. → **S**

**[J-34] [Juror 1] [Przegląd, telefon] [KOSMETYKA] [Design]** Miniatury w kafelkach perspektyw przycięte (`object-fit: cover` w kolumnie 96 px). → `start.css:61` `object-fit: contain`. → **S**

**[J-35] [Juror 1, IA] [Panel na koszu, kiosk] [KOSMETYKA] [Użyteczność]** Chip „Perspektywy” (opacity .7, 124×32, ikona `layout-dashboard` jak „Dashboard”, prowadzi na Przegląd) i pod nim „Kosz nr 18” na innej wysokości. → `kiosk.html:11` ikona `house`; `kiosk.css:6-9` `min-height: 44px; opacity: 1`; usunąć `.kiosk-id` (numer jest w H1) i regułę `kiosk.css:32`. Pełnego przełącznika na panelu nie dodawać (urządzenie uliczne). → **S**

**[J-36] [Juror 1] [Kiosk, api-docs, dashboard, start, kierowca] [KOSMETYKA] [Design]** Kolory spoza `tokens.css`: ciemna paleta kiosku (#0B0F22, #C9CCE0, #E6E8F2, #B7A6FF, #8C92AB, #86EFAC, #FCA5A5, #1B1300, #9AA0B4), #E6E8F2 w `doc.css:29`, #C9CCE0 w `kierowca.css:87`, #B7AEFF w `app.css`, #E0F2F7 (`.badge.progress`), #ECE7FF/#F3F0FF w `start.css`, #C9CFDC w `projekt.js`, słupki zgłoszeń błękitne obok niebieskiego „Papieru”; plakietka „Zmieszane” wygląda jak checkbox. → Łamie zasadę „tylko tokeny”. → Blok „noc” w `tokens.css` (`--night`, `--on-night`, `--on-night-2`, `--on-night-3`, `--brand-on-night`, `--ok-on-night`, `--full-on-night`, `--warn-on`) + `--st-progress-soft`; zamiany per plik; frakcja jako kropka (`border-radius: 50%`, bez box-shadow). → **M** (w pakietach po S)

**[J-37] [Juror 1, Juror 3] [Wszystkie ekrany: daty] [KOSMETYKA] [Design]** Sześć formatów dat; u kierowcy „04.10 06:00”, a panel tego samego kosza mówi „jutro 10:48”. → `routes.py:50, :61-62` użyć istniejącego `state.time_label()` (S). Wspólny `TF.date` w `app.js`: ROADMAPA (M). → **S/M**

**[J-38] [Juror 1, Juror 2] [Kierowca, dashboard, metodologia] [KOSMETYKA] [Kompletność i wdrożenie]** Legenda kierowcy „do 50% / 50–80% / ponad 80%”, dashboard „< 50% / 50–80% / ≥ 80%”, kod `TF.lvl` to ≥ 80; metodologia podaje „żółty od 60%, czerwony powyżej 85%” (stan dla trasy). → Legendę w `kierowca.html:21` skopiować z `dashboard.html:75`; `methodology.py:45` opisać oba zestawy wprost. Ujednolicenie progów: ROADMAPA. → **S**

**[J-39] [Juror 1] [Kierowca: karta kosza] [KOSMETYKA] [Design]** Prognoza dwa razy („Przewidywane 85% ok. 20:20” i „Na trasie najbliższego kursu: 85% ok. 20:20…”); zaznaczony poziom granatowy konkuruje z fioletowym „Opróżniono”; na telefonie „34%” łamie tytuł. → `kierowca.js:86` pierwszy `p.k-fc` tylko bez `k.trasa?.powod`; `kierowca.css:70` zaznaczony poziom `--brand`/`--brand-soft`/`--brand-ink`; ≤ 480 px `.k-big { font-size: var(--fs-2xl) }`. → **S**

**[J-40] [Juror 1] [Kierowca: lista] [KOSMETYKA] [Design]** Procent dwa razy w wierszu (chip „5 zgłoszeń · 120%” i duże „120%”). → `api_pl.py` `powod()` bez `` · {k['poziom']}%``, test `test_poprawki_jury.py:137`, `SCENARIUSZ.md:32`. Po decyzji 1. → **S**

**[J-41] [IA] [Kierowca: karta po „Opróżniono”] [KOSMETYKA] [Użyteczność]** „Następny kosz” prowadzi na listę; w scenariuszu wyprowadza z kroku 4. → Po sukcesie: w scenariuszu „Dalej w scenariuszu” (`TF.goStep(step + 1)`), poza nim link do karty pierwszego niezrobionego kosza z `/api/trasa`. → **S**

**[J-42] [Juror 1, Juror 2, IA] [Kierowca] [KOSMETYKA] [Użyteczność]** Brak H1 („Kierowca MPO · trasa K-07” to `<b>`); podpis „najpierw zgłoszone, potem najpełniejsze”, a 91% stoi nad 120% (wyżej idą tylko świeże zgłoszenia, 15 min). → `kierowca.html:13` H1 `.k-title` (`--fs-lg`, 700); `:23` „najpierw nowe zgłoszenia (15 min), potem najpełniejsze”. → **S**

**[J-43] [Juror 1, IA] [Dashboard, urządzenia] [KOSMETYKA] [Design]** Dwa „Przegląd” na ekranie (pasek i zakładka), ikona `layout-dashboard` w trzech rolach. → Zakładka „Wskaźniki” z ikoną `gauge` (`dashboard.html:16`, `urzadzenia.html:16`). → **S**

**[J-44] [Juror 1] [Dashboard] [KOSMETYKA] [Design]** Sierota w siatce projektów (4 + 1); treść dashboardu zaczyna się od x=24, reszta aplikacji od x=43 (`.dash` 1440 px). → `dashboard.css:75` `repeat(auto-fit, minmax(220px, 1fr))`; `dashboard.css:2` usunąć własną szerokość `.dash`. → **S**

**[J-45] [Juror 1] [Dashboard: „Jakość obsługi”] [KOSMETYKA] [Kompletność i wdrożenie]** „35,1% z 821 zgłoszeń” i „Trafność 84,4% z 1652 rozstrzygniętych” w jednym wierszu (dwie populacje). → `dashboard.js:184` „Trafność przycisków (symulacja)”, `:189` „z N sprawdzeń w symulacji”. → **S**

**[J-46] [Juror 1] [Urządzenia] [KOSMETYKA] [Design]** 12 pełnych zielonych kart „Sprawne” pod 7 kartami „Wymaga uwagi”; na telefonie 6 882 px. → `urzadzenia.js:72` `OK_VISIBLE = 4`; opcjonalnie wyszarzony pasek baterii przy „Brak sygnału”. → **S**

**[J-47] [IA] [Dashboard → projekt → powrót] [KOSMETYKA] [Użyteczność]** „Wróć do dashboardu” zeruje filtry. → `projekt.js`: gdy `document.referrer` zaczyna się od `/dashboard?`, link powrotu = referrer. → **S**

**[J-48] [Juror 2] [Telefon: linki powrotu i przełączniki] [KOSMETYKA] [Użyteczność]** „Wróć do trasy” 21 px wysokości, „Koszt | Wywozy” 28 px z tekstem 12 px. → `app.css:193` `.back { min-height: 44px }`; `@media (pointer: coarse)` 44 px dla `.btn-sm`, `.seg span`, `.dash-tabs a`. → **S**

**[J-49] [Juror 2] [Dashboard, projekt: wykresy] [KOSMETYKA] [Kompletność i wdrożenie]** ECharts aria czyta „This is a chart about…” (brak locale PL); dwa wykresy bez „Szczegóły”, choć deklaracja obiecuje. → `echarts.registerLocale('PL', …)` w `charts.js`, init z `locale: 'PL'`; zdanie w `dostepnosc.html:14`. → **S**

**[J-50] [Juror 1] [/api/v1] [KOSMETYKA] [Kompletność i wdrożenie]** Dokumentacja: `{"blad","kod"}`, `openapi.json`: `{ok:false, message}`, `/api/v1/bins/999999` zwraca `{message, ok}`. → `open_api.py:42` `jsonify(blad=…, kod="nie_znaleziono")`, schemat Error w `openapi.json`, pytest. → **S**

**[J-51] [Juror 1] [Metodologia: koszt pilotażu] [KOSMETYKA] [Idea i innowacja]** Najtańszy wariant „Naklejki z kodem QR (5 zł/kosz)”, a ochrona z decyzji 1 opiera się na kodzie rotującym co 10 min. → „Naklejka z kodem QR (kod stały)” + zdanie, że kod zmienny wymaga panelu z ekranem; docstring `methodology.py:120`. Bez obietnicy „położenie do 150 m”, dopóki kod jej nie sprawdza. → **S**

**[J-52] [Juror 2] [Kierowca, urządzenia, dashboard] [KOSMETYKA] [Użyteczność]** Prawie połowa tekstu ma 12 px (kierowca 120/256, urządzenia 113/248). → `--fs-xs: 13px`, `charts.js` fontSize 13, tylko z czasem na zrzut r1. → **S**

**[J-53] [IA, Juror 3] [Scenariusz demo] [KOSMETYKA] [Użyteczność]** 13 kliknięć na 6 kroków; po „Wyślij” i „Opróżniono” ekran stoi do „Dalej”. Po decyzji 1 zostaje ok. 11. → `TF.scenarioNudge()` w `app.js` (wyróżnia „Dalej” po udanej akcji), wywołanie w `kierowca.js` i `mieszkaniec.js`; bez timerów i automatycznego „Jadę” (decyzja autora, pytanie IA). → **S**

**[J-54] [wzorce] [README, /dostepnosc] [KOSMETYKA] [Kompletność i wdrożenie]** README ma tylko „Demo · Kod”, brak linku do PDF, filmu, tekstów zgłoszenia i plakietki CI; /dostepnosc mówi „samoocena” bez liczb sondy. → Linki i plakietka CI w README; po sondzie r1 zdanie z liczbą ekranów i widoków, 0 naruszeń axe, brak scrolla przy 200%, data. → **S**

**[J-55] [wzorce] [Przegląd, formularz zgłoszenia, „Twoje zgłoszenia”] [KOSMETYKA] [Użyteczność]** CTA nie mówi, ile trwa; przy formularzu brak zdania o prywatności. → Pod CTA „6 kroków · ok. 3 min · bez logowania; dane wracają same po 30 min bez akcji”; pod „Wyślij” „Nie pytamy o imię ani telefon. Ze zdjęcia usuwamy dane aparatu (EXIF), adres IP kasujemy po 24 h.”; pusty stan „Nie masz jeszcze zgłoszeń. Zgłoś problem przy koszu: zeskanuj kod QR na jego panelu.” → **S**

---

## Przegląd wizualny

Skala 1–5. Juror 2 oceniał w skali 1–10: jego oceny podzielono przez 2 i uśredniono z Jurorem 1 tam, gdzie obaj oceniali ten sam ekran. Kolejność: od najsłabszej średniej.

| Ekran | Pierwsze wrażenie | Kolory | Schludność | Spójność | Gęstość | Czytelność | Średnia |
|---|---|---|---|---|---|---|---|
| **Panel na koszu, telefon** | 2,5 | 4,0 | 1,8 | 3,3 | 3,0 | 2,8 | **2,9** |
| **Metodologia** | 3,0 | 3,8 | 3,8 | 2,5 | 2,0 | 3,0 | **3,0** |
| Dashboard | 3,0 | 3,3 | 3,5 | 3,8 | 2,0 | 2,8 | 3,0 |
| API docs | 3,0 | 4,0 | 4,0 | 3,0 | 2,0 | 3,0 | 3,2 |
| Urządzenia | 3,8 | 3,5 | 3,8 | 3,5 | 2,3 | 3,5 | 3,4 |
| Kierowca (lista) | 3,8 | 4,0 | 3,8 | 4,0 | 2,8 | 3,3 | 3,6 |
| Projekt | 3,8 | 3,8 | 3,8 | 3,8 | 3,8 | 3,0 | 3,6 |
| Zgłoszenie (kreator, w przebudowie) | 3,0 | 4,0 | 4,0 | 4,0 | 3,0 | 4,0 | 3,7 |
| Prywatność | 4,0 | 5,0 | 3,0 | 3,0 | 4,0 | 3,0 | 3,7 |
| Wybór kosza /zglos (w przebudowie) | 4,0 | 4,0 | 4,0 | 4,0 | 3,0 | 4,0 | 3,8 |
| Kierowca: karta kosza | 4,0 | 4,0 | 4,0 | 4,0 | 3,8 | 4,0 | 4,0 |
| Status zgłoszenia | 4,0 | 4,5 | 4,0 | 4,0 | 3,5 | 3,8 | 4,0 |
| 404 | 3,8 | 4,5 | 3,5 | 3,5 | 4,5 | 4,0 | 4,0 |
| Przegląd, telefon | 4,0 | 4,5 | 3,5 | 4,5 | 3,8 | 3,8 | 4,0 |
| Panel po akcjach, kiosk | 4,0 | 5,0 | 4,0 | 3,0 | 4,0 | 4,0 | 4,0 |
| Dostępność | 4,0 | 5,0 | 4,0 | 4,0 | 4,0 | 4,0 | 4,2 |
| Panel na koszu, kiosk | 5,0 | 4,0 | 4,0 | 4,0 | 4,0 | 5,0 | 4,3 |
| Przegląd, laptop | 5,0 | 5,0 | 5,0 | 5,0 | 4,0 | 4,0 | 4,7 |

Wnioski: najsłabszy jest **panel na telefonie** (J-10) i dwa ekrany „gęste” (metodologia J-24, dashboard J-05/J-06/J-17). Gęstość to najniżej oceniana kategoria w całej aplikacji. Kolory i spójność trzymają poziom wszędzie poza drobnymi heksami (J-36). Najmocniejsze: Przegląd na laptopie i panel na kiosku.

---

## Budżet kliknięć

| Ścieżka | Budżet | Zmierzone (laptop / telefon) | Status | Jak skrócić |
|---|---|---|---|---|
| Wejście w perspektywę z Przeglądu | 1 | 1 / 1 | OK | Nic. Na telefonie podpisy pod ikonami (J-09), żeby to nie było zgadywanie. |
| Mieszkaniec: zgłoszenie z QR | 3 | 5 / 5 (stary kreator) | PONAD, w pracy | Decyzja 1: od skanu „Przepełniony → Wyślij” = 2. W demo z „/” zostaje 5 przez okno skanu; przycisk „Symuluj skan” od razu na karcie `/zglos` daje 4. |
| Mieszkaniec: przycisk na panelu | 3 | r0: brak; plan 2 | OK w planie | „Przepełniony” wysyła od razu, bez okna „Czy na pewno?”. |
| Mieszkaniec: status zgłoszenia | 2 | nieosiągalne | w pracy | Lista „Twoje zgłoszenia” na `/zglos` = 2; karta listy musi być na pierwszym ekranie telefonu; link „Twoje zgłoszenia” na statusie (J-32). |
| Kierowca: „Opróżniono” | 2 | 3 / 3 (2 od /kierowca) | PONAD od „/” | Liczyć od ekranu trasy (start aplikacji kierowcy) = 2. Bez „Opróżniono” na liście (gubi potwierdzenie na miejscu i dałoby anomalię > 150 m). „Następny kosz” → karta kolejnego kosza (J-41). |
| Dashboard: filtr okres + dzielnica | 2 | 3 / 3 (2 od dashboardu) | PONAD strukturalnie | Minimum to wejście + 2 filtry. W demo dzielnicę wybierać kliknięciem w słupek wykresu. Pamięć filtrów po powrocie z projektu (J-47). |
| Dashboard: szczegóły projektu | 2 | 2 / 2 | OK | Bez zmian. |
| Scenariusz demo do końca | 7 | 13 / 13 | PONAD | Jeden ekran formularza −2, „Jadę” opisane jako opcjonalne −1, wyróżnione „Dalej” po akcji (J-53): ok. 10. Auto-przejście po 2 s: decyzja autora (pytanie IA). |
| Z panelu do innej perspektywy | 1 | 2 / 2 | PONAD, akceptowane | Panel to urządzenie, nie aplikacja. Chip z ikoną `house`, 44 px, pełna widoczność (J-35); w demo dalej prowadzi pasek scenariusza. |

**Wnioski o architekturze informacji:**
- Model „jedna historia przez cztery perspektywy” działa: każda perspektywa jest 1 kliknięcie od Przeglądu. Przekroczenia wynikają z kreatora mieszkańca (już w przebudowie) i z liczenia od strony startowej zamiast od ekranu startowego roli.
- Słabe miejsca IA to **nazwy, nie liczba kliknięć**: ikony bez podpisów na telefonie (J-09), dwa „Przegląd” (J-43), pięć nazw jednego zdarzenia (J-19), trzy numeracje u kierowcy (J-11), opis kroku 3 niezgodny z listą (J-13).
- Scenariusz demo to główne narzędzie jurora: każdy krok musi zgadzać się z ekranem co do słowa. Po decyzji 1 i J-13 zmierzyć ponownie (sonda r1).

---

## Oceny wstępne

| Kryterium (waga) | Juror 1 | Juror 2 | Juror 3 |
|---|---|---|---|
| Idea i innowacja (30%) | 6,7 | 7 | 7 |
| Związek z kategorią (20%) | 7,7 | 8 | 8 |
| Użyteczność (20%) | 6,3 | 5 | 6 |
| Design (20%) | 7,0 | 7 | 8 |
| Kompletność i wdrożenie (10%) | 7,7 | 7 | 6 |
| **Wynik ważony** | **6,99** | **6,80** | **7,10** |

**Średnia ważona jury: 6,96 / 10.** Juror 1 to średnia trzech przeglądów ważona liczbą ocenianych ekranów (8 / 5 / 5). Dla porównania: analityk wzorców 7,6, analityk IA 7,6 (nie liczeni jako jurorzy).

**Uzasadnienia**

*Juror 1.* Idea: spójna i czytelna już w hero (prognoza, zgłoszenie przy koszu, trasa tylko do potrzebnych koszy, reguły decydują, AI opisuje), ale panel po opróżnieniu obiecuje odbiór za pół godziny, metodologia nie pokazuje liczb z hero, a dwa zestawy liczb miesięcznych (866/668, CO₂ +97 / −285 kg) podkopują tezę o oszczędnościach. Kategoria: wzorcowe Smart City (panel w przestrzeni miejskiej, MPO, dzielnice, Open311, OSM), choć Open311 ginie na stronie API. Użyteczność: perspektywy w 1 kliknięcie, „Opróżniono” z celami 88 px; minus za ikony bez podpisów, trzy numeracje u kierowcy, dashboard bez liczby na pierwszym ekranie telefonu, niewidoczny fokus. Design: jedna czcionka, jedna rodzina ikon, spokojny fiolet, kosz-wskaźnik jako motyw; minus za ucięty panel na telefonie, urwiska sparkline'ów, ucięte osie, gęstość metodologii i dashboardu. Kompletność: 0 błędów JS, axe prawie czysto, deklaracja dostępności, RODO, OpenAPI 3.1; braki to spójność liczb i dokumentów.

*Juror 2 (68+, WCAG).* Pomysł rozumiem od razu, ale dwie różne miesięczne oszczędności i słowo „altana” mnie gubią. Kategoria: typowo miejski problem, otwarte API, deklaracja według ustawy. Użyteczność 5: na telefonie gubię się w menu z ikon, ledwo widzę fokus, połowę tekstu czytam w 12 px, linki powrotu mają 21 px. Design: spójny i spokojny, kolor zawsze z ikoną i słowem, ale na telefonie nachodzące etykiety dzielnic i ucięty panel. Kompletność: działa na produkcji, ale 404 i deklaracja obiecują listę koszy, a wykresy opisują się czytnikowi po angielsku.

*Juror 3 (ekspert, wdrożenie).* Idea mocna (start bez czujników, prognoza, sygnały mieszkańców), ale własna symulacja pokazuje te same godziny przepełnienia koszy ulicznych (1822 → 1823 h), a oszczędność to głównie 4 zł za wizytę. Kategoria: prawdziwe kosze z OSM, harmonogram MPO, norma 2 h, Open311; minus za panel z terminem niezgodnym z trasą. Użyteczność: panel czytelny z daleka, „Opróżniono” jednym dotknięciem; lista kierowcy przeczy trasie, krok scenariusza każe kliknąć kosz, którego nie ma na górze. Design: czysty system wizualny; minus za sparkline'y i panel na telefonie. Kompletność 6: deck 14 slajdów przy limicie 10, produkcja pokazuje 0 anomalii, sprzeczne liczby metodologii i dashboardu.

**Pytania na salę**
- **Juror 1:** „Na stronie głównej obiecujecie 1,5–2,8 mln zł rocznie, metodologia podaje 866 wizyt mniej i +97 kg CO₂ miesięcznie, a dashboard 668 kursów mniej i 285 kg CO₂ redukcji. Którą liczbę MPO ma wpisać do budżetu pilotażu i dlaczego w waszej symulacji przebieg śmieciarek rośnie?” (Pozostałe pytania Jurora 1: co, gdy prognoza panelu się myli i ktoś naciśnie „Przepełniony”; gdzie są pieniądze w projekcie z −13% odbiorów przy tym samym koszcie.)
- **Juror 2:** „Jeśli naciśnę dziś „Przepełniony” na koszu przy Rynku, po ilu godzinach realnie przyjedzie śmieciarka i dlaczego wasze liczby pokazują, że czas reakcji się wydłuża?”
- **Juror 3:** „Godziny przepełnienia koszy ulicznych się nie zmieniają, kursy są o 6:00 i 14:00, a w normie 2 h obsłużono 29% zgłoszeń. Co zyskuje mieszkaniec Rynku poza ok. 4 tys. zł miesięcznie oszczędności MPO na 222 koszach i ile kosztowałby pojazd dyżurny, który dotrzyma 2 godzin?”

Przygotować odpowiedzi na slajd wyników (J-01) i do tekstu zgłoszenia: jeden łańcuch kwot (zł na kosz → dashboard → Kraków), uczciwe „czas reakcji i SLA to dane demo; efekt wdrożenia widać w trendzie przed/po (J-05)”, rozbicie kosztu odbioru (wizyta, km, masa).

---

## Odrzucone przez sceptyka

Sceptyk nie odrzucił w całości żadnego znaleziska. Odrzucił lub skorygował te propozycje:
- Przeliczenie chipów KPI na średnią przed/po dla wszystkich KPI: koszt i zgłoszenia wyszłyby czerwone, a zima kontra lato to błąd sezonowości.
- Wykres „koszt na wywóz” w projekcie: rośnie o 15% (9,67 → 11,09 zł) i podważyłby projekt.
- Kolumna „Zmiana” w tabeli porównania: zastąpiona jednym zdaniem.
- `head=headline()` w `app/ui.py`: koliduje z agentem decyzji 1; wystarczy szablon.
- Zastąpienie metryki altan wizytami w hero: gubi jedyny dowód jakości i dubluje „puste przyjazdy”.
- „Kod QR ważny 10 minut” na stronie 404: przeterminowany kod nie prowadzi do 404.
- Globalne `body { display: flex }` dla 404: ryzyko dla kiosku i układów pełnoekranowych.
- „Ochrona położeniem do 150 m” w tekstach: kod dziś położenia nie sprawdza (`api_pl.py:281`).
- `.ks { width: auto }`, `.kiosk-id { display: none }`, `flex-wrap` karty QR na panelu: zbędne po iteracji r2.
- Plakietki „Prognoza … 14:2…” ucięte u kierowcy: niepotwierdzone na zrzutach.
- Dane projektu 34,6 / 34,8 tys. zł u Jurora 2: niepotwierdzone (serwer nie odpowiadał), potwierdzone przez Jurora 1.
- „Opróżniono” na liście kierowcy: gubi pomiar poziomu i daje anomalię > 150 m.
- Automatyczne „Dalej” po 1,8 s i automatyczne „Jadę”: ucinają czytanie i ukrywają akcję (zostawione autorowi jako pytanie).
- Usunięcie kafla SLA: dziura w siatce KPI.
- Widoczne słowo „lepiej/gorzej” w chipie: ściska sparkline na telefonie; zamiast tego `sr-only` + `title`.
- Przemianowanie „Odbiory CSV” i tekstu „pustych przyjazdów” w hero: niewarte ryzyka.
- Wagi obniżone: reset demo (styl ghost, świadoma decyzja), pierścień fokusu, 12 px (nie łamie WCAG), 404/deklaracja (mało oglądane), tabela „Trafność” (nisko na stronie), naklejka QR w metodologii, „lepiej/gorzej” kolorem (strzałka i znak niosą kierunek).
