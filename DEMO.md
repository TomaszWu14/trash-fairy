# Jak poprowadzić demo w 3 minuty

Adres: https://trashfairy.twapp.pl (lokalnie `flask --app app run -p 5050`). Bez logowania. Przed pokazem: na ekranie startowym
**„Resetuj dane demo”** (dane wracają do soboty 3.10, 13:30; samo też po 30 min bezczynności). Okno 1366×768 albo 1920×1080, zoom 100%.
Na drugim urządzeniu (telefon) możesz pokazać to samo zgłoszenie na żywo: zeskanuj kod QR z panelu kosza nr 18.

| Czas | Klik | Co powiedzieć | Liczby do podkreślenia |
|---|---|---|---|
| 0:00–0:20 | Ekran **Przegląd** | „Kraków opróżnia kosze według kalendarza, nie według potrzeb. Trash Fairy to mózg odbioru: przewiduje zapełnienie, zbiera zgłoszenia i układa trasę tylko do koszy, które tego potrzebują. Cztery perspektywy, jedne dane.” | 57% → 27% pustych przyjazdów, 338 h → 0 h przepełnień altan, 1,5–2,8 mln zł/rok w skali Krakowa (symulacja, `/metodologia`) |
| 0:20–0:55 | **Zacznij scenariusz demo** → krok 1: „Przepełniony”, komentarz, **Wyślij** | „Mieszkanka skanuje kod QR na koszu. Zgłoszenie przyjmujemy tylko z kodu tego kosza i do 150 m od niego, więc nikt nie zgłosi kosza z kanapy. Trzy kroki, numer zgłoszenia i status.” | numer TF-…, położenie symulowane (jawnie opisane) |
| 0:55–1:10 | **Dalej** → panel kosza | „Ekran na koszu widać z daleka: zapełnienie, termin odbioru i potwierdzenie, że zgłoszenie dotarło.” | „Zgłoszony przez mieszkańca” |
| 1:10–1:45 | **Dalej** → kierowca → kosz 18 → **Jadę** → **Opróżniono** | „Kierowca widzi kosze po priorytecie: zgłoszone na górze. Nawigacja jest w aplikacji, bez przełączania do map. Jedno dotknięcie zamyka zgłoszenie.” | postęp trasy „1 z 54”, czas do końca kursu |
| 1:45–2:00 | **Dalej** → status u mieszkańca | „Mieszkanka widzi, że zrobione: przyjęte, w realizacji, zrealizowane.” | oś czasu z godzinami |
| 2:00–2:45 | **Dalej** → **Dashboard** | „Miasto widzi koszty, wywozy i zgłoszenia z 12 miesięcy. Od wdrożenia w maju koszt jest poniżej planu. Kliknięcie frakcji albo dzielnicy filtruje cały widok.” Kliknij **Stare Miasto** na wykresie dzielnic, potem kartę projektu. | ostatnie 30 dni: koszt 70,4 tys. zł (−2,7%), oszczędności 4,1 tys. zł i 668 kursów mniej niż w planie; od maja 3–4 tys. zł/mies. poniżej planu; projekt „Odbiory na żądanie – Stare Miasto”: −13% wywozów, czas reakcji 6,3 h → 2,7 h |
| 2:45–3:00 | **Zakończ** | „Decyzje liczą jawne reguły w kodzie, dane operacyjne są demonstracyjne i każdy ekran to mówi. Kraków nie potrzebuje więcej koszy, potrzebuje wróżki.” | — |

**Uczciwie, jeśli jury zapyta:** dane operacyjne, koszty i projekty są syntetyczne (deterministyczny generator `app/history.py`);
prawdziwe są położenia koszy i frakcje z OpenStreetMap, harmonogram MPO 08/2026 i wydarzenia z Karnetu. Liczby dashboardu liczy baza (GROUP BY),
a akcje ze scenariusza (zgłoszenie, odbiór) wchodzą do nich od razu. Czas reakcji z ostatnich 30 dni jest wyższy niż miesiąc wcześniej:
pokazujemy to bez poprawiania, a trend roczny spada (8,6 h → 5,7 h w mieście).

**Gdy coś pójdzie nie tak:** „Resetuj dane demo” na ekranie startowym; zgłoszenie z tego samego telefonu do tego samego kosza jest możliwe raz na minutę.

## Ściągawka: trudne pytania

- **Stack?** Python 3.12, Flask, SQLAlchemy, PostgreSQL 16, OR-Tools, Gunicorn, Docker (`docker compose up --build`). Front bez builda i bez CDN: Jinja, własny CSS, Leaflet, ECharts. Ponad 270 testów.
- **Dlaczego reguły, a nie AI?** Decyzja o kursie śmieciarki musi być powtarzalna, sprawdzalna i do wytłumaczenia urzędnikowi. Reguły są jawne na `/metodologia`; AI tylko opisuje zdjęcia i wydarzenia, a jego odpowiedź po walidacji schematu jest wejściem dla reguły.
- **RODO i zdjęcia?** EXIF (GPS, aparat) usuwamy przed zapisem i przed wysłaniem do modelu. Model ma zakaz opisywania osób i tablic; zdjęcie z osobą nie jest publiczne. IP zgłoszeń kasujemy po 24 h. Szczegóły: `/prywatnosc`.
- **Ile kosztuje wdrożenie?** Start nie wymaga sprzętu: naklejka z kodem QR, aplikacje w przeglądarce, jeden kontener z bazą. Założenia oszczędności (4 zł za wizytę, 5 zł za km) i skalowanie na Kraków są na `/metodologia`; koszt paneli i czujników policzymy w pilotażu na realnych ofertach.
- **Czy to się skaluje?** Kraków ma 9 383 kosze w harmonogramie MPO 08/2026; `methodology.city_scale` liczy z niego 1,5–2,8 mln zł/rok. Trasy liczymy osobno per rejon i flota, więc rośnie liczba rejonów, nie rozmiar jednego problemu.
- **Konkurencja?** Systemy czujnikowe (np. Sensoneo, Enevo) wymagają kupna i utrzymania sprzętu na każdym koszu. My działamy od pierwszego dnia bez sprzętu, na tanich sygnałach, i przyjmujemy czujniki tam, gdzie się opłacają (moduł urządzeń już je rozróżnia).
- **Co jest symulowane?** Poziomy zapełnienia, historia 12 miesięcy dashboardu (`app/history.py`), koszty, projekty, urządzenia i położenie mieszkańca w demo. Prawdziwe: kosze i frakcje z OSM, przebiegi OSRM, harmonogram MPO, Karnet, pogoda, reguły i trasy. Każdy ekran ma plakietkę „Dane demonstracyjne”.
- **Co po hackathonie?** Pilotaż: Dzielnica I, 50 koszy, 3 miesiące, grupa testowa kontra kontrolna. Plan krok po kroku w `ROADMAPA.md`.
