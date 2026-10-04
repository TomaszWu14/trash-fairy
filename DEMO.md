# Jak poprowadzić demo w 3 minuty

Adres: https://trashfairy.twapp.pl (lokalnie `flask --app app run -p 5050`). Bez logowania. Przed pokazem: na ekranie startowym
**„Resetuj dane demo”** (dane wracają do soboty 3.10, 13:30; samo też po 30 min bezczynności). Okno 1366×768 albo 1920×1080, zoom 100%.
**„Zacznij scenariusz demo”** losuje jeden z trzech wariantów: **A** skan kodu QR z Panelu kosza, **B** przycisk „Przepełniony” na Panelu kosza,
**C** dzikie wysypisko poza koszem. Na pokaz z gotowym przebiegiem: `/?scenariusz=A&kosz=18` (kosz Rynek 18) albo `/?scenariusz=C&miejsce=0`.
Na drugim urządzeniu (telefon) możesz pokazać to samo zgłoszenie na żywo: zeskanuj kod QR z Panelu kosza nr 18 (kod zmienia się codziennie).
Nagrane przejście obu scenariuszy i prezentacja PDF: `python demo/build_all.py` (patrz `demo/README.md`).

| Czas | Klik | Co powiedzieć | Liczby do podkreślenia |
|---|---|---|---|
| 0:00–0:20 | Ekran **Przegląd** | „Kraków opróżnia kosze według kalendarza, nie według potrzeb. Trash Fairy to mózg odbioru: przewiduje zapełnienie, zbiera zgłoszenia i układa trasę tylko do koszy, które tego potrzebują. Pięć perspektyw, jedne dane.” | 57% → 27% pustych przyjazdów, 338 h → 0 h przepełnień altan, skala Krakowa po 12 zł za odbiór: [z produkcji] mln zł/rok (symulacja, `/metodologia`) |
| 0:20–0:45 | **Zacznij scenariusz demo** (wariant A) → **Panel kosza** 18 → klik w kod QR → „Przepełniony” → **Wyślij** | „Mieszkanka stoi przy koszu. Panel kosza pokazuje zapełnienie, termin odbioru i kod QR, który zmienia się codziennie, więc zdjęcie kodu nie pozwoli zgłaszać jutro z kanapy. Jedno dotknięcie, numer zgłoszenia i podziękowanie.” | numer TF-…, „Dziękujemy!” |
| 0:45–0:55 | Powrót na **Panel kosza** | „Panel kosza od razu potwierdza, że zgłoszenie dotarło do kierowcy.” | „Zgłoszony przez mieszkańca” |
| 0:55–1:15 | **Dyspozytor** | „Dyspozytor widzi mapę koszy na żywo: stan to kształt, znak i kolor. Pilne kosze podpowiada reguła, ale „Dodaj do kursu” klika człowiek. Obok ekipy, trasy i zgłoszenia na żywo.” | kafle: zagrożone, przepełnione, km trasy, −% odbiorów wobec harmonogramu |
| 1:15–1:45 | **Kierowca** → kosz 18 → **Jadę** → **Opróżniono** (opcjonalnie zdjęcie kosza) | „Kierowca widzi kosze po priorytecie, przy każdym powód. Nawigacja jest w aplikacji. „Opróżniono” zapisuje położenie śmieciarki i zdjęcie kosza: to dowód wykonania usługi, dotyczy kosza, nie osoby.” | postęp „Kurs 14:00”, dowód odbioru |
| 1:45–2:00 | Status zgłoszenia u mieszkańca | „Mieszkanka widzi: przyjęte, w realizacji, zrealizowane. Za trafne zgłoszenie dostaje punkty, o nagrodach decyduje regulamin MPO.” | oś czasu z godzinami, punkty |
| 2:00–2:45 | **Dashboard** | „Miasto widzi koszty, odbiory i zgłoszenia z 12 miesięcy. Oszczędność wobec planu liczymy po 12 zł za odbiór i 5 zł za km. Kliknięcie frakcji albo dzielnicy filtruje cały widok; rekomendacje podpowiadają kompaktor, większy kosz albo rzadsze odbiory.” Kliknij **Stare Miasto** na wykresie dzielnic, potem kartę projektu. | ostatnie 30 dni: oszczędności [z produkcji] zł i [z produkcji] odbiorów mniej niż w planie; projekt „Odbiory na żądanie – Stare Miasto”: [z produkcji] |
| 2:45–3:00 | **Zakończ** | „Decyzje liczą jawne reguły w kodzie, AI tylko opisuje zdjęcia, a dane operacyjne są demonstracyjne i każdy ekran to mówi. Kraków nie potrzebuje więcej koszy, potrzebuje wróżki.” | — |

**Uczciwie, jeśli jury zapyta:** dane operacyjne, koszty i projekty są syntetyczne (deterministyczny generator `app/history.py`);
prawdziwe są położenia koszy i frakcje z OpenStreetMap, harmonogram MPO 08/2026 i wydarzenia z Karnetu. Liczby dashboardu liczy baza (GROUP BY),
a akcje ze scenariusza (zgłoszenie, odbiór) wchodzą do nich od razu. „Kurs” to jeden przejazd śmieciarki (np. „Kurs 14:00”);
kosz pominięty dzięki regułom to „odbiór mniej”.

**Gdy coś pójdzie nie tak:** „Resetuj dane demo” na ekranie startowym; zgłoszenie z tego samego telefonu do tego samego kosza jest możliwe raz na minutę.

## Ściągawka: trudne pytania

- **Stack?** Python 3.12, Flask, SQLAlchemy, PostgreSQL 16, OR-Tools, Gunicorn, Docker (`docker compose up --build`). Front bez builda i bez CDN: Jinja, własny CSS, Leaflet, ECharts. Testy: `python -m pytest -q`.
- **Dlaczego reguły, a nie AI?** Decyzja o kursie śmieciarki musi być powtarzalna, sprawdzalna i do wytłumaczenia urzędnikowi. Reguły są jawne na `/metodologia`; AI tylko opisuje zdjęcia i wydarzenia, a jego odpowiedź po walidacji schematu jest wejściem dla reguły.
- **Jak zgłoszenie jest przypięte do kosza?** Tylko przy koszu: przycisk na Panelu kosza albo kod QR z panelu, który zmienia się codziennie. Nie sprawdzamy położenia telefonu mieszkańca.
- **RODO i zdjęcia?** EXIF (GPS, aparat) usuwamy przed zapisem i przed wysłaniem do modelu. Model ma zakaz opisywania osób i tablic; zdjęcie z osobą nie jest publiczne. IP zgłoszeń kasujemy po 24 h. Szczegóły: `/prywatnosc`.
- **Ile kosztuje wdrożenie?** Założenia oszczędności (12 zł za odbiór: 3 min postoju × (3 osoby × 45 zł/h + pojazd 105 zł/h); 5 zł za km), koszt pilotażu i zwrot są na `/metodologia`; liczbę ekip MPO i ceny paneli ustalimy w pilotażu.
- **Czy to się skaluje?** Kraków ma 9 383 kosze w harmonogramie MPO 08/2026; `methodology.city_scale` liczy z niego [z produkcji] mln zł/rok po 12 zł za odbiór. Trasy liczymy osobno per rejon i flota, więc rośnie liczba rejonów, nie rozmiar jednego problemu.
- **Konkurencja?** Systemy czujnikowe (np. Sensoneo, Enevo) wymagają kupna i utrzymania sprzętu na każdym koszu. My działamy na tanich sygnałach i przyjmujemy czujniki tam, gdzie się opłacają (moduł urządzeń już je rozróżnia).
- **Co jest symulowane?** Poziomy zapełnienia, historia 12 miesięcy dashboardu (`app/history.py`), koszty, projekty, urządzenia i Panel kosza (symulacja ekranu 10,1″). Prawdziwe: kosze i frakcje z OSM, przebiegi OSRM, harmonogram MPO, Karnet, pogoda, reguły i trasy. Każdy ekran ma plakietkę „Dane demonstracyjne”.
- **Co po hackathonie?** Pilotaż: 50 koszy w Dzielnicy I, grupa testowa kontra kontrolna. Plan krok po kroku w `ROADMAPA.md`.
