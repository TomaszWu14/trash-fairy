# Decyzje

Każdy wpis: CO zrobiliśmy, DLACZEGO, JAKĄ alternatywę odrzuciliśmy.

## Etap 1 — mapa z punktami (sob 3.10, 11:15–)

**Prawdziwe pozycje koszy z OSM, cache w repo.** Punkty pochodzą z Overpass API (`amenity=waste_basket`,
`waste_disposal`, `recycling`) i są zapisane w `data/*.geojson`, więc demo nie zależy od Overpass.
Odrzuciliśmy losowe punkty na mapie, bo jury zobaczyłoby nieprawdziwe miasto.

**60 koszy wybieranych od Rynku i Placu Nowego, co najmniej 80 m od siebie.** W centrum OSM ma ponad 1000 koszy,
a najbliższe 60 zbiłoby się w jedną plamę wokół Sukiennic. Odrzuciliśmy losowanie, bo daje inny wynik po każdym imporcie.

**Tempo zapełniania z otoczenia.** Wzór: 1,5%/h + 0,06 za każdy lokal lub sklep + 0,6 za każdy przystanek w promieniu 100 m,
z limitem 8%/h. Pierwsza wersja (0,25 za lokal) dawała limit połowie koszy, więc współczynniki zmniejszyliśmy, żeby punkty się różniły.

**Historia jako szereg w tabeli `forecast` (`source='sim'`).** Symulacja i przyszła prognoza (`source='pred'`) mają ten sam kształt,
więc wykres i porównanie „przed i po” czytają jedno źródło. Odrzuciliśmy osobną tabelę `fill_history`, której nie ma w koncepcji.

**Symulacja ze stałym harmonogramem MPO.** Kosze są opróżniane o 6:00 i 14:00, altany co 3 dni, a poziom może dojść do 120%
(powyżej 100% to przepełnienie). Wynik: 68% opróżnień koszy przypada na kosz zapełniony poniżej 75%.
To jest punkt wyjścia do porównania w etapie 4. Seed jest stały, więc dane są powtarzalne.

**Stan punktu to na razie tylko poziom z symulacji, z progami 60 i 85%.** Zgłoszenia z przycisku i wiarygodność dojdą w etapie 2.
Każdy stan ma kolor, symbol (✓ ~ !) i opis słowny, a lista w panelu jest tekstową alternatywą mapy (WCAG).

**Kafelki OSM zamiast CARTO.** Serwer CARTO nie odpowiadał z sieci, w której pracujemy, a OSM jest zgodny z koncepcją.

**Python 3.13 lokalnie, 3.12 w Dockerze.** Lokalny venv już był na 3.13, a kod nie korzysta z różnic między wersjami.
Sterownik Postgresa to psycopg 3. `DATABASE_URL` w formacie `postgres://` jest przepisywany na `postgresql+psycopg://`.

## Etap 2 — przycisk, stan, polling (sob 3.10, ~11:30–)

**Osobna tabela `report` (zgłoszenie).** Naciśnięcia w ciągu 15 minut od pierwszego łączą się w jedno zgłoszenie.
Okno liczymy od pierwszego naciśnięcia, więc spamer nie przedłuży go w nieskończoność. Odrzuciliśmy liczenie zgłoszeń
w locie z naciśnięć, bo wiarygodność z ostatnich 10 zgłoszeń wymagałaby wtedy grupowania całej historii przy każdym zapytaniu.

**Trafność rozstrzyga opróżnienie.** Opróżnienie z poziomem co najmniej 75% oznacza zgłoszenie trafne, niższy poziom oznacza fałszywe.
Wiarygodność przycisku to odsetek trafnych wśród ostatnich 10 zgłoszeń, a nowy przycisk zaczyna od 70%.
Te same czyste funkcje (`app/reports.py`) liczą historię w symulatorze i żywe naciśnięcia, więc nie ma dwóch wersji reguł.

**Stan = max(poziom, 100 × wiarygodność zgłoszenia).** Świeże zgłoszenie (do 15 minut) z wagą co najmniej 0,7 od razu daje czerwony.
Zgłoszenie mniej niż 2 h po opróżnieniu przy poziomie poniżej 30% liczy się w połowie. Każdy stan ma powód słowny,
np. „zgłoszenie: 3× naciśnięty, wiarygodność 80%”. Decyzje podejmują wyłącznie reguły, AI nie bierze w tym udziału.

**Flaga „⚠ sprawdź przycisk”.** Zapala się w dwóch przypadkach: poniżej 40% trafnych zgłoszeń z 7 dni (co najmniej 3 zgłoszenia)
albo 6 h przepełnienia bez żadnego naciśnięcia. Zamiast warunku „przez 7 dni” liczymy zgłoszenia z 7 dni,
dzięki czemu nie trzeba przechowywać historii samej wiarygodności. Symulator ma 2 trollowane przyciski (dni robocze 14–16)
i właśnie te 2 dostają flagę.

**Zegar demo w bazie i 24 h „przyszłości” w symulacji.** Przycisk „przewiń +1 h” odsłania kolejną godzinę symulacji
i rozstrzyga zgłoszenia na opróżnieniach z harmonogramu. Zegar jest w bazie, bo gunicorn ma kilka procesów.
Reset odtwarza symulację od zera (około 3 s), co jest prostsze i pewniejsze niż cofanie zmian pojedynczo.

**Polling co 2 s z numerem wersji (zegar + ostatnie naciśnięcie).** Gdy nic się nie zmieniło, odpowiedź ma kilka bajtów.
Odrzuciliśmy WebSocket i SSE, bo przy 72 punktach i demo polling wystarczy, a nie wymaga dodatkowej infrastruktury.

**Łagodny limit naciśnięć: 1 na 2 s dla punktu i 120 na godzinę z jednego IP.** Plan zakładał 1 na 5 s i 30 na godzinę,
ale na sali cała publiczność zwykle wychodzi przez jeden adres (NAT), więc ostry limit zablokowałby demo z jury.
ProxyFix przekazuje prawdziwy adres klienta zza proxy Coolify (Traefik).

## Etap 3 — prognoza (sob 3.10, ~12:30–)

**Panel pokazuje szacunek systemu, a nie „prawdę” z symulacji.** System bez czujników nie zna prawdziwego poziomu.
Zna opróżnienia, naciśnięcia i historię. Poziom z symulatora jest ukrytą „prawdą”: generuje zdarzenia i służy do liczenia błędu.
Szacunek to suma przyrostów z profilu od ostatniego opróżnienia. Test `test_state_does_not_read_hidden_truth` pilnuje,
żeby stan nie czytał „prawdy”. Odrzuciliśmy pokazywanie poziomu z symulacji, bo na pytanie jury „skąd to wiecie bez czujnika?”
nie mielibyśmy uczciwej odpowiedzi.

**Profil tygodniowy 7 × 24 na punkt: średnia i kwantyle p20/p80.** Profil uczymy na historii sprzed zegara.
W godzinie opróżnienia przyrost liczymy od zera, a godziny z przepełnieniem (120%, przyrost ucięty) pomijamy.
Godziny wydarzeń dzielimy przez mnożnik, żeby profil był bazowy. Odrzuciliśmy Holt-Winters i ML:
przy 8 tygodniach danych zysk byłby niepewny, a profil da się wytłumaczyć jednym zdaniem.

**Wydarzenia: ręczna lista zapasowa (`data/events.json`) i mnożnik zależny od skali tłumu.** Mały tłum: 200 m, ×1,3.
Średni: 400 m, ×1,6. Duży: 800 m, ×2,0. Mnożnik działa w godzinach wydarzenia i przez godzinę po nim.
Ten sam mnożnik stosują symulator i prognoza. Pobieranie z Karnetu zostaje na etap 6, zgodnie z kolejnością cięcia z koncepcji.

**Godzina przekroczenia 85% z interpolacją w godzinie, przedział z tempa p80 (najwcześniej) i p20 (najpóźniej).**
Prognoza nie zakłada przyszłych opróżnień, bo odpowiada na pytanie „kiedy się przepełni, jeśli nikt nie przyjedzie”.
Na tej podstawie etap 4 wybierze punkty do trasy.

**Trafność: MAE 2,5 p.p. na ostatnim tygodniu, a naiwna stała średnia ma 7,3 p.p.** Profil do tego pomiaru uczymy
na danych sprzed tego tygodnia, więc nie ma przecieku. Odrzuciliśmy liczenie błędu na danych treningowych, bo zawyżyłoby trafność.

**Prognozę liczymy na żądanie, z cache profilu na godzinę zegara, zamiast zapisywać ją do tabeli `forecast`.**
Zmienia się przy każdym przewinięciu zegara, a obliczenie dla 72 punktów trwa około 20 ms przy gotowym profilu.
Tabela `forecast` przechowuje historię (`source='sim'`).

## Etap 4 — trasy i porównanie (sob 3.10, ~13:30–)

**Wybór punktów regułami: pełny teraz, przekroczenie 85% przed *kolejnym* kursem albo bezpiecznik (kosz 3 dni, altana 7 dni).**
Pytanie brzmi „czy zdążymy, jeśli nie weźmiemy go teraz”, a nie „czy jest pełny”. Każdy przystanek ma powód słowny.
Odrzuciliśmy jeden próg poziomu, np. „bierz powyżej 60%”, bo ignoruje tempo i odległość do następnego kursu.

**OR-Tools (routing VRP), 1 pojazd na flotę, start i koniec w bazie MPO (ul. Nowohucka 1, adres z OSM).**
Odległość to linia prosta × 1,3. Solver działa bez metaheurystyki z limitem czasu, więc wynik jest deterministyczny
i powtarzalny w testach. Odrzuciliśmy guided local search z limitem 1 s: przy 84 kursach w porównaniu trwałoby to ponad minutę,
a wynik zależałby od szybkości maszyny. OSRM i kilka pojazdów są w roadmapie.

**Porównanie na tych samych przyrostach zapełnienia, profil uczony na danych sprzed okresu porównania.**
Trash Fairy decyduje tylko na podstawie własnego szacunku, bez przycisków (wariant ostrożny).
Wynik dla 4 tygodni: przy koszach 19% mniej wizyt, 6% mniej km, puste przyjazdy spadają z 53% do 28%, a liczba godzin przepełnienia się nie zmienia.
Przy altanach przepełnienia spadają z 338 h do 0 kosztem +158 km. W sumie kilometrów jest o 6% więcej. Pokazujemy to uczciwie,
z rozbiciem na floty, bo sama suma ukryłaby, że dodatkowe kilometry idą na przeciążone altany, czyli na rekomendację z sekcji 6.8.

**Godziny przepełnienia koszy są takie same w obu wariantach.** Przepełnienia między kursami nie da się usunąć,
jeśli godziny kursów są stałe. Tu pomagają kompaktor albo większy kosz (rekomendacje, etap 6), a nie trasa.
