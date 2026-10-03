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

## Etap 5 — ekipa MPO, Claude Vision, nadużycia (sob 3.10, ~15:00–)

**Jedna brama do AI: `app/llm.py` (`ask`, `ask_json`), oficjalne SDK `anthropic`, model z `ANTHROPIC_MODEL` (domyślnie `claude-opus-5`).**
Każdy błąd (brak klucza, limit, sieć, odmowa modelu, zły JSON) zamieniamy na `LLMError` z komunikatem dla człowieka.
Panel pokazuje komunikat i ostatni udany wynik z bazy, nigdy błąd 500 (test 9). Odpowiedź modelu jest ograniczona schematem JSON
(structured outputs), więc nie parsujemy wolnego tekstu. Dla Opus 5 włączony jest serwerowy fallback po odmowie filtra bezpieczeństwa.

**Zdjęcie: walidacja po sygnaturze pliku (JPEG, PNG, WebP, maksymalnie 8 MB), analiza w tle, plik usuwany po 7 dniach.**
Ekipa na telefonie nie czeka na model. Wynik (poziom, nadużycia, uszkodzenia, notatka) zostaje w `photo_analysis`,
a samo zdjęcie po 7 dniach kasuje `flask cleanup-photos` (RODO). Prompt zabrania opisywania osób i tablic rejestracyjnych.
Odrzuciliśmy synchroniczne wywołanie w żądaniu, bo kilka sekund oczekiwania na telefonie przy koszu to zły UX.

**Opróżnienie od ekipy to prawdziwy odczyt.** Zeruje szacunek i rozstrzyga zgłoszenia po tym samym progu 75% co w etapie 2.
Gdy poziom ze zdjęcia różni się od klikniętego o więcej niż 25 p.p., panel pokazuje flagę.

**Reguła altana → kosz w kodzie, a nie w AI.** AI tylko rozpoznaje „worek z domowymi śmieciami”. Powiązanie powstaje, gdy taki kosz
stoi w promieniu 200 m od altany, którą szacunek pokazywał jako przepełnioną (>100%) w ostatnich 48 h. Wtedy altana dostaje
rekomendację „zwiększ częstotliwość odbioru”. Bez zgłoszeń do Straży Miejskiej.

**6 z 60 koszy przenieśliśmy do Grzegórzek, po 3 przy każdej przeciążonej altanie.** Najbliższy kosz z Rynku i Kazimierza stał 877 m
od altany, więc reguła 200 m nigdy by się nie uruchomiła. Liczby po zmianie: MAE 2,4 p.p. vs 7,1 p.p.; kosze −24% wizyt, −5% km,
puste przyjazdy z 57% do 27%; altany z 338 h do 0 h przepełnień (+163 km); 71% opróżnień koszy przy poziomie poniżej 75%.

**Harmonogram MPO 08/2026 (9 383 koszy) potwierdza założenia porównania.** W Dzielnicy I 43% koszy opróżnia się 3× dziennie,
a 36% 2× dziennie, więc nasz stały plan „2× dziennie” raczej zaniża realny koszt (szczegóły w `docs/kontekst-mpo.md`).

## Etap 6 — raport, rekomendacje, jury, Metodologia, Karnet (sob 3.10, ~17:00–)

**Rekomendacje (sekcja 6.8) liczymy z poziomów zastanych przy opróżnieniach, a nie z ukrytej „prawdy”.** Te dane MPO naprawdę ma od ekip.
Reguły: kompaktor, gdy kosz jest przepełniony w ponad 50% dni mimo opróżniania 2× dziennie; większy kosz przy 20–50% dni;
rzadsze opróżnianie, gdy mniej niż 20% opróżnień wypada przy poziomie ≥50%; interwencja przy altanie z reguły altana → kosz.
Efekt podajemy w jednostkach fizycznych („−46 wizyt w miesiącu”). Wynik demo: 13 kompaktorów, 9 większych koszy, 13 do rzadszego opróżniania, 2 altany.

**Raport „Wróżka podpowiada”: fakty liczy kod, Claude pisze 5 sekcji przez structured outputs.** Prompt zabrania dodawania liczb,
a kod dodatkowo sprawdza, czy każda liczba z tekstu występuje w faktach. Jeśli nie, panel pokazuje ostrzeżenie.
Raporty zapisujemy w `fairy_report`. Przy błędzie API panel pokazuje komunikat i ostatni raport. Raport powstaje raz na godzinę zegara albo na żądanie,
a nie przy każdym pollingu, bo to by kosztowało. Odrzuciliśmy wolny markdown od modelu, bo sekcje w JSON łatwo bezpiecznie wyrenderować.

**Metodologia czyta wartości wprost ze stałych w kodzie.** Złotówki i CO₂ to jawne, konfigurowalne założenia (env), nie dane MPO.
Bilans miesięczny: −866 wizyt i ≈2 976 zł mniej (5 zł/km, 4 zł za wizytę), ale +97 km i +97 kg CO₂, bo częściej jeździmy do przeciążonych altan.

**Karnet Kraków bez Nominatim.** Lista wydarzeń Karnetu ma już współrzędne, więc geokodowanie okazało się zbędne.
Pobieramy 5 stron z 3 list (1 zapytanie na sekundę, z identyfikującym User-Agentem), a wynik trafia do `data/karnet.json`.
Daje to 28 wydarzeń w obszarze demo w weekend demo. Godziny i skalę tłumu uzupełnia Claude, a bez klucza robią to jawne reguły:
koncerty i festiwale to 18–22 i średni tłum, długie wystawy mały tłum. Wydarzenia z Karnetu wchodzą do symulacji i prognozy tak samo jak lista zapasowa.

**Godziny przepełnienia koszy po dodaniu Karnetu: 1822 h przy stałym planie i 1823 h u wróżki (+1 h).** Piszemy „praktycznie bez zmian”,
a nie „bez zmian”. Przepełnień między stałymi godzinami kursów nie usuwa trasa. Na to są rekomendacje (kompaktor, większy kosz).

## Program „Przyjaciele Wróżki”, ochrona przed spamem, stan urządzeń (sob 3.10, ~19:00–)

Źródło: brainstorm 50 pytań (`docs/brainstorm-przycisk-program.md`) i spec (`docs/superpowers/specs/2026-10-03-program-mieszkancow-design.md`).

**Fizyczny przycisk z wyświetlaczem e-papierowym, a nie ekran dotykowy.** Ekran na ulicy potrzebuje stałego zasilania, gorzej znosi wandalizm
i nie da się go odczytać w słońcu. E-papier zużywa prąd tylko przy zmianie obrazu i działa na baterii LoRaWAN. W demo jest makietą nad wirtualnym przyciskiem
(stan, godzina kursu, a dla niezarejestrowanych kod QR do programu).

**Zarejestrowani mają własną wiarygodność i potwierdzają zgłoszenia anonimowe.** Waga zgłoszenia to max z wiarygodności przycisku i mieszkańca
(start 80%). Potwierdzone zgłoszenie nie jest osłabiane przez reguły antyspamowe. Punkty są tylko za trafne zgłoszenia (10, a za altanę 15),
najwyżej raz na osobę, punkt i dzień, więc spam i nabijanie nic nie dają.

**Dane osobowe dopiero przy nagrodzie.** Rejestracja wymaga pseudonimu, dzielnicy i HMAC numeru telefonu (samego numeru nie zapisujemy).
Imię i nazwisko podaje tylko zwycięzca. Odrzuciliśmy pełne dane przy rejestracji (sugestia „prawdziwe dane do rozliczeń”),
bo RODO wymaga minimalizacji, a rozliczenie i tak jest możliwe przy odbiorze nagrody. SMS jest symulowany (kod na ekranie z etykietą DEMO).

**Antyspam w regułach wagi:** zgłoszenie przy koszach w promieniu 100 m z szacunkiem poniżej 30% liczy się ×0,7; ≥3 fałszywe zgłoszenia o tej porze
(±1 h) w 14 dni dają ×0,5; zgłoszenie z telefonu z położeniem dalej niż 150 m od kosza jest odrzucane. `REQUIRE_GEO=1` wymusza położenie.
W demo jest wyłączone, bo jury głosuje z hali, a nie spod kosza. Autotest urządzenia nie tworzy zgłoszeń, a brak sygnału przez 48 h daje flagę.

## Widok C „Pokaz dla jury” (sob 3.10, ~15:30–)

**Strona główna to teraz historia w 4 krokach (Problem → Predykcja → Trasa → Efekt) na jednej mapie, a pełny panel przeniósł się pod `/dyspozytor`.**
Jury w 2 minuty ma zobaczyć problem, prognozę, trasę i efekt, a nie zakładki. Odrzuciliśmy usunięcie starego panelu, bo szczegóły punktu,
zdjęcia AI, raport wróżki i rekomendacje są potrzebne przy pytaniach jury. „Zagrożone” liczy tę samą regułę co planer tras
(60–85% i 85% przed kolejnym kursem), a krok 4 pokazuje uczciwie także wzrost km (+7%), a nie tylko spadki.

**Trasy po ulicach z OSRM liczy serwer, z cache w `data/osrm_cache.json` i fallbackiem do linii prostej.** Przebieg służy tylko do rysowania,
a kilometry dalej liczymy jako linia prosta × 1,3, więc porównanie i Metodologia się nie zmieniają. Odrzuciliśmy wołanie OSRM z przeglądarki:
publiczny serwer bywa wolny, a cache w repo pozwala pokazać demo bez sieci. CARTO Positron wymaga już klucza API (kafelki „API KEY REQUIRED”),
więc używamy OSM z filtrem CSS (szarość), a przy braku sieci statycznego podkładu SVG.

## Ekran „Zgłoś kosz” (PWA mieszkańca) (sob 3.10, ~16:30–)

**Nowy publiczny ekran `/zglos/<id>` zamiast makiety słupka; `/jury` prowadzi na niego.** Jedno dotknięcie wysyła zgłoszenie
(1,5 s na „Cofnij”), potwierdzenie pojawia się w miejscu, bez nowej strony. Stara makieta `/przycisk/<id>` zostaje tylko jako
podgląd fizycznego przycisku. Zamiast nowego `/api/reports` rozszerzyliśmy `/api/press` (status accepted/merged, eta, retry_at,
distance_m), bo to on już scala zgłoszenia, liczy limity i wagi programu. Publiczne `/api/zglos/<id>` nie zwraca wiarygodności przycisku.

**Rodzaj zgłoszenia zmienia regułę tylko dla „uszkodzony”.** „Pełny” i „przepełniony, odpady obok” działają jak naciśnięcie przycisku
(odpady obok to notatka w panelu), a „uszkodzony” nie podnosi poziomu: to zadanie dla ekipy, więc tylko flaga 🛠 w panelu do najbliższego
opróżnienia (max 48 h). Odrzuciliśmy traktowanie uszkodzenia jak pełnego kosza, bo wysyłałoby śmieciarkę do pustego kosza.

**Offline: IndexedDB + Background Sync, a nie localStorage.** Zgłoszenie zapisane w telefonie wysyła service worker także po zamknięciu
aplikacji; bez Background Sync strona wysyła po zdarzeniu `online`. SW ma zakres `/zglos` (nagłówek `Service-Worker-Allowed`), więc nie
dotyka panelu. Kolumnę `press.kind` dokładamy bez Alembica małym `ALTER TABLE` przy starcie, bo to jedyna zmiana schematu w hackathonie.

## Wyświetlacz e-papierowy na koszu, etap 1 (sob 3.10, ~17:00–)

**Stan ekranu liczy `app/epaper.py` z tych samych danych co panel, a renderer z paczki (`app/epaper_render.py`) rysuje go 1-bitowo.**
Priorytet: fault > overflow > confirm > enroute > emptied > night > calm. „Przepełniony” liczymy z prognozy (`level`), a nie z wartości
podbitej samym zgłoszeniem, bo inaczej każde naciśnięcie dawałoby od razu stan 5 zamiast 2. „Ekipa w drodze” = punkt ma przystanek na
najbliższym kursie i do kursu zostało < 45 min, a zgłoszenie nie jest już świeże (15 min). Odrzuciliśmy osobny model „ekranu” w bazie:
stan jest funkcją zgłoszeń, opróżnień, tras i urządzenia, więc nie ma czego synchronizować.

**Pełne mignięcie tylko przy zmianie stanu.** API zwraca dwa klucze: `state_key` (pas stanu, QR) i `values_key` (okno 24,344–776,432).
Symulator `/epapier/<nr>` przy zmianie `values_key` podmienia tylko wycinek okna, co odpowiada odświeżaniu częściowemu sterownika 7,5".
Test XOR pilnuje, że zmiana wartości nie rusza pikseli poza oknem. Fizyczny przycisk na stronie to zwykłe `POST /api/press` (źródło `button`),
które przy okazji odświeża heartbeat urządzenia, bo nadający przycisk na pewno żyje. Etap 2 (LoRaWAN) tylko jako kontrakt w `docs/epapier/ETAP2-LORAWAN.md`.

## Bezpieczeństwo AI: prompt injection i walidacja odpowiedzi (sob 3.10, wieczór)

**Zewnętrzne treści traktujemy jako dane, nie polecenia:** opis wydarzenia, zdjęcie i fakty trafiają do modelu w ograniczniku
`<dane_zewnetrzne>`, a system prompt każe ignorować instrukcje w danych, także te widoczne na zdjęciu. **AI zwraca tylko zwalidowany JSON:**
poza structured outputs sprawdzamy sami pola, enumy, zakresy i długości, a odrzucona odpowiedź oznacza komunikat i ostatni dobry wynik.
**Decyzje podejmują reguły w kodzie,** więc zmanipulowana odpowiedź AI nie zmieni trasy ani priorytetu: najwyżej ustawi skalę tłumu
na „large”, czyli to, co reguła i tak dopuszcza. Odrzuciliśmy pydantic (nowa zależność dla trzech schematów) na rzecz 40-linijkowego walidatora.

## Audyt UX, Fala 1: poprawki P0 przed demo (sob 3.10, wieczór)

**Naprawiliśmy to, co jury zobaczy na telefonie i rzutniku: brak poziomego scrolla w widoku C i panelu (360–1440 px), zwijaną legendę,
„Najbliższe przepełnienia” nad kodem QR, trasy w panelu po ulicach (OSRM, jak w widoku C), polską stronę 404 i wskaźnik świeżości danych.**
Panel rozpychał nagłówek, bo `body` było gridem z kolumną `auto`; `minmax(0, 1fr)` naprawia to u źródła zamiast ukrywać `overflow-x`.
Po 3 nieudanych pollach pokazujemy „Brak połączenia · dane z hh:mm” tekstem i trójkątem, nie samym kolorem. Odrzuciliśmy przepisanie panelu na tokeny widoku C (Fala 2, ROADMAPA).

**Blokada odległości 150 m odejmuje dokładność GPS, obciętą do 150 m, tą samą regułą na serwerze i w telefonie.**
Słaby GPS w kamienicy (233 m ± 120 m) nie blokuje już mieszkańca stojącego przy koszu, a podanie „dokładności 5 km” nie wyłącza kontroli.
Odrzuciliśmy zostawienie przycisków aktywnych w stanie `far`, bo serwer i tak odrzuciłby zgłoszenie, a dwie różne reguły to gorszy błąd niż jedna łagodniejsza.

## PWA kierowcy `/kierowca` (sob 3.10, wieczór)

**Kierowca dostaje aplikację w czterech krokach (start zmiany → trasa z następnym przystankiem → przystanek → podsumowanie),
w kierunku C z kanwy, z celami dotykowymi od 56 px i trybem ciemnym.** Kurs zapisujemy w telefonie jako migawkę w chwili „Rozpocznij trasę”,
bo po każdym „Opróżniony” serwer planuje trasę od nowa i opróżniony punkt z niej wypada. Bez migawki numeracja „32/53” skakałaby, a bez zasięgu nie byłoby trasy.
Nowe punkty z aktualnego planu pokazujemy jako „Nowy pilny punkt · +n”, a kierowca sam dopisuje je na koniec. Odrzuciliśmy ciche przestawianie kolejności w trakcie jazdy.

**„Nie da się podjechać” i „Problem” to nowy `POST /api/stop-issue` (tabela `StopIssue`), który nie zmienia trasy, tylko pokazuje flagę dyspozytorowi do opróżnienia, najwyżej 12 h.**
Decyzję, czy wysłać kogoś ponownie, zostawiamy człowiekowi. Odrzuciliśmy automatyczne przeplanowanie, bo jedno zgłoszenie z drogi nie powinno samo przestawiać floty.
Zapisy idą przez tę samą kolejkę IndexedDB co zgłoszenia mieszkańców, ale w osobnej bazie i z własnym SW (zakres `/kierowca`), z 5 s na „Cofnij”.
Ikony PNG 192/512 i maskable dostał przy okazji także manifest `/zglos`.

**Pomiar przed i po (`docs/audit/RESULTS.md`) złapał regresję, której nie widać gołym okiem:** CLS panelu 0,18 → 0,5.
Menu z `overflow-x: auto` dostawało pasek przewijania w trakcie ładowania fontów i nagłówek rósł. Ukryliśmy pasek (przewijalność
pokazuje cień krawędzi) i skróciliśmy plakietkę do „DEMO · SYMULACJA”; CLS 0,13. Przyczynę potwierdziliśmy pomiarem tej samej strony na `main`,
zamiast zgadywać po kolejnych poprawkach CSS.

## Etap 8: integracje API (pogoda, ruch, SMS, otwarte API) (sob 3.10, wieczór)

**Pogoda z Open-Meteo zmienia tylko prognozę na godziny przyszłe, regułą w kodzie: opad ≥ 1 mm/h ×0,8, ciepły (≥ 20 °C), suchy weekend 10–22 ×1,25.**
Profil, MAE i porównanie 4 tygodni liczymy bez pogody, żeby wyniki na slajdach nie zależały od dnia pokazu. Sprawdzone na żywo:
sobota 3.10, 13:00, 20,7 °C i bezchmurnie dały ×1,25, a kurs 14:00 urósł z 53 do 54 punktów. Odrzuciliśmy pogodę w profilu historycznym
(symulacja nie ma pogody, więc model nauczyłby się szumu). Bez sieci zostaje `data/weather_cache.json`, a bez niego mnożnik 1,0.

**Ruch z TomTom zmienia tylko czas (przejazdu i ETA), nigdy wyboru punktów ani km.** Trasa odpowiada na pytanie „kogo trzeba odwiedzić”,
a korek nie zmienia potrzeby; korek w macierzy OR-Tools to osobny krok (ROADMAPA.md). Bez klucza lub przy starym pomiarze (> 2 h) nie ma korekty,
a nie „brak korków”. **SMS przez Twilio Verify, bez SDK** (`urllib` w `app/http.py`): w sesji tylko SID weryfikacji, numer tylko jako HMAC,
limity 3 kody/numer/h i 30/h. Bez bramki kod demo na ekranie, jak wcześniej. **Otwarte API `/api/v1` tylko do odczytu** z kontraktem OpenAPI 3.1
i własną stroną `/api/docs` (bez Swagger UI z CDN); bez wiarygodności przycisków i danych mieszkańców, `meta.synthetic` wprost.
Kod etapu 8 z sesji w chmurze nie trafił do repo, więc odtworzyliśmy go na podstawie opisu, od razu sprawdzając pola na prawdziwej odpowiedzi Open-Meteo
i w dokumentacji TomTom i Twilio.

## Przegląd przed oddaniem: 50 decyzji (sob 3.10, noc)

**Pełna lista w `docs/PRZEGLAD.md`; tu tylko rozstrzygnięcia, które zmieniają charakter aplikacji.**
Trzy role (publiczna, dyspozytor, kierowca floty) zamiast otwartej aplikacji, bo publiczny Reset, płatne wywołania AI i „Opróżniony”
z dowolnego miejsca pozwalały komuś z sali zepsuć pokaz albo dane. Odrzuciliśmy konta osobowe (pół dnia bez efektu dla jury).
Ekran `/telefony` pokazuje cały cykl jednego kosza (e-papier → mieszkaniec → kierowca), bo na rzutniku jury nie zobaczy PWA inaczej.
Stan `bad` nazywa się „Do opróżnienia”, a „Przepełniony” zostaje dla prognozy ≥ 100%: 86% to nie jest przepełnienie.
Zamiast uśrednionego „−16% godzin przepełnień” pokazujemy dwie uczciwe liczby, bo kosze mają tyle samo godzin przepełnienia,
tylko mniej wizyt. Skalowanie na Kraków (1,4–2,7 mln zł/rok) liczy kod z harmonogramu MPO, jako przedział, a nie jedna liczba.

## Fala A: bezpieczny pokaz (sob 3.10, noc)

**Role i loginy (`app/auth.py`): publiczna, `dyspozytor`, `driver_bin`, `driver_altana`; wspólne hasło demo tylko w env (`DEMO_PASSWORD`).**
Kierowca zapisuje tylko punkty **swojej floty**, a nie „bieżącego planu”: planer po opróżnieniu liczy trasę od nowa i punkt z niej wypada,
więc reguła „tylko z planu” odrzuciłaby zapisy z kolejki offline i „Cofnij”. Pola dyspozytora filtrujemy na serwerze w jednym miejscu (`public_view`).
**Limity (SMS, AI 30/h, logowanie 5/15 min) w tabeli `Counter`**, bo przy 2 workerach Gunicorna limity w pamięci były w praktyce podwójne.
**Stan i trasy z cache po wersji danych** (300 + 580 ms raz na zmianę, nie raz na zapytanie); wersja obejmuje teraz problemy kierowcy i urządzenia,
których wcześniej nie widziała (panel nie zauważał nowego problemu). Przy okazji: klucze e-papieru liczył `hash()`, losowany per proces, więc
2 workery dawały fałszywe pełne mignięcia; teraz `hashlib`. Auto-reset demo po 30 min bezczynności, warunkowy UPDATE wybiera jeden worker.
Biblioteki i fonty lokalnie (bez unpkg, jsDelivr i Google Fonts), licencja AGPL-3.0 z `NOTICE`, model `claude-opus-5-5` z fallbackiem po odmowie.
**CI (GitHub Actions: pytest) i auto-merge do `main`** na prośbę autora: PR scala się sam po zielonym teście, Redeploy w Coolify zostaje ręczny.

## Fala B: jedna aplikacja dla jury (sob 3.10, noc)

**`/telefony`: cykl kosza 18 w trzech działających ramkach** (e-papier, PWA mieszkańca, PWA kierowcy w podglądzie `?podglad=1` bez zapisów).
QR jury zawsze na kosz 18, a limit w trybie jury liczymy po identyfikatorze telefonu (`client_id`), nie po IP, bo cała sala ma jedno IP z Wi-Fi.
Ramki wymuszają jasny motyw (`?theme=light`, `data-theme`), a „Pokaż tryb nocny” przełącza kierowcę świadomie. Menu zależne od roli w jednym `_nav.html`.
**Słownik stanów**: W porządku ✓ koło / Zapełnia się ↑ romb / Do opróżnienia ! kwadrat, altana = podwójna obwódka; karta 1 liczy „przepełnione”
tylko przy szacunku ≥ 100%, a karta 4 pokazuje puste przyjazdy 57% → 27% i altany zamiast uśrednionego „−16%”.
**Paleta C wszędzie przez podmianę wartości zmiennych**, IBM Plex zamiast Fraunces i Inter, Tailwind i DaisyUI usunięte z panelu.
**Kolor trasy altan zostaje śliwkowy `#8E2C8C`**: proponowany turkus `#00727A` miał względem zieleni stanu OK kontrast jasności tylko 1,05:1
(dla daltonisty ten sam kolor), a śliwka różni się od dymka zgłoszenia typem znaku (linia przerywana vs kształt). Kontrasty tekstu: biały na niebieskim
trasy 7,5:1, ciemny znak na bursztynie 8,9:1, bursztynowy tekst `#7A4F00` na bieli 7,1:1, fiolet AI `#6A3FD6` na bieli 6,4:1.
Pocięte (decyzja 48): ikony SVG zamiast emoji i jeden plik `tokens.css` dla wszystkich ekranów — w ROADMAPA.md.

## Fala C, część 1 (niedz. 4.10, noc)

**Skalowanie na Kraków liczy kod (`methodology.city_scale`): 1,5–2,8 mln zł/rok.** Wizyty z harmonogramu MPO 08/2026 (≈217,7 tys./mies.)
× spadek wizyt (−24%) i km (−5%) koszy z porównania, przy jawnych założeniach 4 zł/wizyta i 5 zł/km. Przedział, bo efekt jest pewny w centrum
(kosze opróżniane codziennie lub częściej: wariant ostrożny), a mniej pewny na przedmieściach. Odrzuciliśmy mnożenie przez liczbę koszy
(2 976 zł / 72 × 9 383): ignorowało, że przedmieścia opróżnia się 2–5× w tygodniu, a nie 2× dziennie.
**`/dostepnosc` i `/prywatnosc`**, IP zgłoszeń kasowane po 24 h przy starcie aplikacji (bez crona), zgoda przy rejestracji w programie.
**Gunicorn z `--preload` (`app/wsgi.py`)**: porównanie liczy się raz przed forkiem workerów, zamiast 2–5 s w każdym workerze przy pierwszym wejściu.
Pozostałe punkty fali C (postęp kierowcy, Pilne w panelu, flaga GPS, dymek → szczegóły, smoke.py) zostają na część 2.

## Fala C, część 2 (niedz. 4.10, noc)

**Postęp kierowcy w panelu tekstem** (opróżnione, problemy, pominięte, ostatnia akcja), bez paska procentowego: plan zmienia się po każdym
opróżnieniu, więc „12 z 53” byłoby nieprawdą. „Pomiń” trafia na serwer jako `StopIssue(kind="skip")` i nie flaguje punktu.
**Położenie przy „Opróżniony”** zapisujemy jako `far_m` (odległość minus dokładność GPS, ta sama reguła co u mieszkańca); ponad 150 m daje
flagę w panelu, bez blokady. Wstrzymanie punktów programu do potwierdzenia przez dyspozytora — ROADMAPA (zabrakło czasu).
Lista punktów w panelu posortowana po pilności, dymek pinu na `/` prowadzi do szczegółów w panelu, `scripts/smoke.py` (11 kontroli).
**Testy równolegle (`pytest-xdist -n auto`)**: 207 testów w 43 s zamiast 149 s, bez zmiany treści testów (każdy ma własną bazę w pamięci).
Pocięte: „Wyślij do kierowcy”, „Moje zgłoszenia”, tabela punktów pod mapą, osobna sekcja „Pilne teraz” (jest sortowanie).
