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
