# 06. Dziennik decyzji

Najważniejsze decyzje w formacie: kontekst → rozważane opcje → wybór i powód → skutki.
Pełny chronologiczny dziennik z hackathonu (ok. 500 wpisów) jest w [`DECYZJE.md`](../DECYZJE.md). Uwaga: późniejsze wpisy
zmieniają wcześniejsze, np. role i logowanie oraz limit 150 m. Rozbieżności opisuje [07-ograniczenia.md](07-ograniczenia.md).

---

### D1. Decyzje podejmują reguły w kodzie, AI tylko opisuje

- **Kontekst:** stan kosza, priorytet i trasa decydują o kosztach i o tym, kto przyjeżdża. Musi się dać wyjaśnić każdą decyzję i ją przetestować.
- **Opcje:**
  - model AI oceniający pilność;
  - jawne reguły z progami.
- **Wybór:** reguły (`app/state.py`, `app/routes.py`). AI (`app/llm.py`) tylko opisuje zdjęcia i teksty, a jego odpowiedź przechodzi walidację schematu.
- **Dlaczego:** reguła ma test i powód słowny („zgłoszenie: 3× naciśnięty, wiarygodność 80%”). Ocena AI jest niepowtarzalna i trudna do obrony przed miastem.
- **Skutki:**
  - bez klucza API aplikacja działa w pełni;
  - AI nigdy nie odrzuca zgłoszenia: [D6](#d6-ai-nigdy-nie-odrzuca-zgłoszenia), wymagania AI-01, AI-02.
- **Źródło:** `DECYZJE.md:44`.

### D2. Naciśnięcie to nie zgłoszenie: scalanie w 15 minut i waga z wiarygodności

- **Kontekst:** przycisk na koszu jest anonimowy i tani. Grupa osób albo jeden żartowniś może nacisnąć go wiele razy.
- **Opcje:**
  - każde naciśnięcie to osobne zgłoszenie;
  - naciśnięcia scalone w zgłoszenie z wagą.
- **Wybór:** encje `press` (surowe zdarzenie) i `report` (zgłoszenie). Naciśnięcia w ciągu 15 min tworzą jedno zgłoszenie. Waga to odsetek trafnych zgłoszeń z ostatnich 10 (start 70%). Trafność ustala kierowca przy opróżnieniu: poziom ≥ 75% oznacza trafne.
- **Dlaczego:** 30 naciśnięć to nadal jeden problem przy jednym koszu. Waga z historii pozwala ignorować przyciski, które często się mylą, bez ręcznej moderacji.
- **Skutki:**
  - model danych `press` → `report` → `emptying` ([04-model-danych.md](04-model-danych.md));
  - przyciski z niską trafnością dostają flagę „sprawdź przycisk”;
  - poziom zapisany przez kierowcę zasila wiarygodność i prognozę.
- **Źródło:** `DECYZJE.md:40-48`, `docs/KONCEPCJA.md` §6.

### D3. Wybór na kurs: „czy zdążymy do następnego kursu”, a nie „czy jest pełny”

- **Kontekst:** trzeba zdecydować, które kosze jadą w tym kursie.
- **Opcje:**
  - jeden próg poziomu, np. „bierz powyżej 60%”;
  - prognoza przekroczenia 85% przed kolejnym kursem plus bezpiecznik.
- **Wybór:** kosz jedzie, gdy jest „do opróżnienia”, albo przekroczy 85% przed kolejnym kursem, albo minął bezpiecznik (3 dni dla kosza, 7 dla altany). Trasę liczy OR-Tools (VRP z pojemnością), deterministycznie, bez metaheurystyki.
- **Dlaczego:** jeden próg ignoruje tempo zapełniania i odstęp do następnego kursu. Odrzucona metaheurystyka z limitem 1 s dawałaby wynik zależny od szybkości maszyny i trwałaby ponad minutę w porównaniu.
- **Skutki:**
  - każdy pominięty kosz ma powód;
  - kilometry liczone są jako linia prosta × 1,3, a OSRM służy tylko do rysowania trasy;
  - wynik jest powtarzalny w testach.
- **Źródło:** `DECYZJE.md:92-99`.

### D4. Pokaz bez logowania (role usunięte)

- **Kontekst:** jury testuje zdalnie i w kilka minut. Wcześniej aplikacja miała role publiczną, dyspozytora i kierowców ze wspólnym hasłem.
- **Opcje:**
  - role i loginy;
  - konta osobowe;
  - jedna rola bez logowania z tożsamościami demo.
- **Wybór:** jedna rola bez logowania. „Rola” to perspektywa w nagłówku. Ochronę pokazu przejmują reset i auto-reset danych.
- **Dlaczego:** sześć ekranów pod jednym logo z logowaniem było zbyt skomplikowane dla jury. Konta osobowe to pół dnia bez efektu dla oceny.
- **Skutki:**
  - akcje zmieniające dane („Opróżniono”, „Uprzątnięte”, „Dodaj do kursu”) są dostępne dla każdego;
  - to świadoma granica demo, pilotaż wymaga ról ([07-ograniczenia.md](07-ograniczenia.md)).
- **Źródło:** `DECYZJE.md:273, 340, 355`.

### D5. Dzienny kod QR zamiast weryfikacji położenia

- **Kontekst:** trzeba odróżnić zgłoszenie spod kosza od zgłoszenia „z kanapy”.
- **Opcje:**
  - GPS telefonu w promieniu 150 m z kodem zmienianym co 10 min;
  - token kosza w kodzie QR, inny każdego dnia.
- **Wybór:** token HMAC(sekret, kosz + data) w kodzie QR na panelu; wczorajszy działa jeszcze godzinę po północy. Przycisk fizyczny chroni osobny token urządzenia.
- **Dlaczego:** GPS w kamienicach jest zawodny, a jury nie stoi przy koszu. Dzienny kod nadal nie pozwala zgłosić jutro ze zdjęcia kodu.
- **Skutki:**
  - położenie nie jest sprawdzane (`app/api_pl.py:131-133`);
  - wcześniejsze wpisy `DECYZJE.md` o limicie 150 m są nieaktualne.
- **Źródło:** `DECYZJE.md:408-417`.

### D6. AI nigdy nie odrzuca zgłoszenia

- **Kontekst:** zdjęcie od mieszkańca można ocenić AI, które czasem się myli.
- **Opcje:**
  - odrzucać zgłoszenia z niską pewnością;
  - oznaczać „Do weryfikacji” i przepuszczać.
- **Wybór:** „Zweryfikowane AI” tylko przy pewności ≥ 0,7 i zgodnym stanie; poza tym „Do weryfikacji”. Zgłoszenie idzie dalej zawsze.
- **Dlaczego:** fałszywy alarm kosztuje jeden kurs. Odrzucony mieszkaniec przestaje zgłaszać na zawsze.
- **Skutki:** przy błędzie API albo braku klucza zgłoszenie trafia do dyspozytora bez opisu AI.
- **Źródło:** `DECYZJE.md:359-363`.

### D7. Efekt mierzony porównaniem na tym samym przebiegu zapełniania

- **Kontekst:** nie ma prawdziwych danych o zapełnieniu koszy, a trzeba pokazać efekt bez naciągania.
- **Opcje:**
  - deklarowane procenty;
  - symulacja, w której obie polityki (stały plan i Trash Fairy) działają na identycznych przyrostach zapełnienia.
- **Wybór:** porównanie 4 tygodni na tym samym przebiegu (stały seed). Profil prognozy uczony jest na danych sprzed okresu porównania. Trash Fairy decyduje bez przycisków (wariant ostrożny).
- **Dlaczego:** różnica wynika wtedy tylko z polityki odbioru, a nie z danych. Pokazujemy też to, co wychodzi gorzej.
- **Skutki:**
  - wynik: puste przyjazdy 57% → 27%, odbiory koszy −24%, przepełnienia altan 338 h → 0 h;
  - kilometry przy altanach rosną o ok. 156 km;
  - liczby pilnuje test regresji, a dashboard oznacza dane syntetyczne.
- **Źródło:** `DECYZJE.md:101-106, 277`.

### D8. Koszt odbioru z rozpisanych składników, jako założenie

- **Kontekst:** oszczędności w złotówkach wymagają kosztu jednego odbioru, którego nie znamy.
- **Opcje:**
  - stała kwota bez uzasadnienia (pierwotnie 4 zł);
  - kwota z rozpisanych składników.
- **Wybór:** 12 zł = postój 3 min × (ekipa 3 × 45 zł/h + pojazd 105 zł/h) oraz 5 zł/km. Wartości można nadpisać zmiennymi środowiskowymi, a `/metodologia` je pokazuje.
- **Dlaczego:** rozpisana kwota jest sprawdzalna i łatwa do skorygowania przez przewoźnika.
- **Skutki:** wszystkie kwoty w aplikacji to szacunki „do potwierdzenia z przewoźnikiem”.
- **Źródło:** `DECYZJE.md:453`, `app/methodology.py:21-40`.

### D9. Prawdziwe położenia z OpenStreetMap, cache w repozytorium

- **Kontekst:** mapa musi pokazywać prawdziwe miasto, a demo nie może zależeć od zewnętrznego serwera.
- **Opcje:**
  - losowe punkty;
  - zapytanie do Overpass przy każdym starcie;
  - plik GeoJSON w repo.
- **Wybór:** pliki `data/*.geojson` w repo, odświeżane ręcznie skryptem `scripts/fetch_osm.py`.
- **Dlaczego:** losowe punkty dają nieprawdziwe miasto. Overpass bywa niedostępny.
- **Skutki:** aplikacja startuje bez sieci, a dane mogą się zestarzeć.
- **Źródło:** `DECYZJE.md:7-9`.

### D10. Bez builda i bez CDN

- **Kontekst:** pokaz w sieci hackathonu, mały zespół, mało czasu.
- **Opcje:**
  - SPA z bundlerem;
  - Jinja z bibliotekami trzymanymi lokalnie.
- **Wybór:** szablony Jinja, własny CSS z tokenami, Leaflet i biblioteki wykresów w `app/static/vendor`, fonty lokalnie.
- **Dlaczego:** brak kroku budowania i zależności od zewnętrznych serwerów. Jedna komenda uruchamia całość.
- **Skutki:** prostsze wdrożenie (Dockerfile + Gunicorn) kosztem ręcznego zarządzania wersjami bibliotek front-endu.
- **Źródło:** `DECYZJE.md:289`.
