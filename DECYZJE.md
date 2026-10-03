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
