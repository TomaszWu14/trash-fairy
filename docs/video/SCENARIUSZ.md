# Nagranie 2:00: scenariusz (decyzje 44–45, po przebudowie UI)

Lektor po polsku (głos autora), napisy EN wtopione w obraz (`en.srt`), `pl.srt` dla wersji z napisami PL.
Tekst czyta się w tempie ok. 2 słów na sekundę; każdy blok mieści się w swoim oknie czasu z zapasem na pauzę.
Nagranie idzie po 6 krokach „Zacznij scenariusz demo” z `DEMO.md`, skrócone do 2:00.

## Przygotowanie (przed nagraniem)

1. Produkcja po Redeployu: `python scripts/e2e_demo.py https://trashfairy.twapp.pl` przechodzi 26/26.
2. Na ekranie startowym `/` kliknij „Resetuj dane demo” (stan startowy: sobota 3.10, 13:30). Bez logowania: jedna rola.
3. Okno przeglądarki 1920×1080, zoom 100%, bez zakładek i rozszerzeń w kadrze. Karta widoczna (schowana usypia timery).
4. Opcjonalnie ramka telefonu dla ekranów mieszkańca i kierowcy (to samo zgłoszenie można zeskanować z panelu kosza 18).

## Tekst słowo w słowo

| Czas | Obraz | PL (lektor) | EN (napisy) |
|---|---|---|---|
| 0:00–0:15 | Slajd 2 „Problem” albo zdjęcie Floriańskiej, potem ekran **Przegląd** `/` | Na Floriańskiej każdy kosz opróżnia się trzy razy dziennie, pełny czy pusty. W Krakowie 9 383 kosze opróżnia się według kalendarza, nie według potrzeb. | On Floriańska Street every bin is emptied three times a day, full or empty. Kraków's 9,383 street bins run on a calendar, not on need. |
| 0:15–0:40 | „Zacznij scenariusz demo” → krok 1: `/zglos/18?qr=…` (plakietka „położenie symulowane”), „Przepełniony”, zdjęcie, **Wyślij** → status „Zweryfikowane AI” albo „Do weryfikacji” | Trash Fairy to mózg odbioru. Mieszkanka skanuje kod QR na koszu. Zgłoszenie przyjmujemy tylko z kodu tego kosza i do 150 metrów od niego. Trzy kroki, opcjonalne zdjęcie. Usuwamy EXIF, Claude Vision ocenia kosz, a reguła nadaje „Zweryfikowane AI” albo „Do weryfikacji”. AI nigdy nie odrzuca zgłoszenia. | Trash Fairy is a waste collection brain. A resident scans the QR code on the bin. We accept a report only from that bin's code and within 150 metres of it. Three steps, an optional photo. We strip EXIF, Claude Vision assesses the bin, and a rule assigns "AI verified" or "To be reviewed". AI never rejects a report. |
| 0:40–0:48 | **Dalej** → krok 2: `/panel/18` (zapełnienie, najbliższy odbiór, „Co tu wrzucać”, QR) | Panel kosza widać z daleka: zapełnienie, najbliższy odbiór i co tu wrzucać. | The panel on the bin reads from afar: fill level, next pickup and what goes in. |
| 0:48–1:08 | **Dalej** → krok 3: `/kierowca` (chip powodu przy koszu 18) → `/kierowca/kosz/18` (prognoza „Przewidywane 85% ok. …”) → **Jadę** → **Opróżniono** | Kierowca widzi kosze po priorytecie, a przy każdym powód: ile zgłoszeń i jakie zapełnienie. Prognoza mówi, o której kosz przekroczy 85 procent. „Jadę” prowadzi nawigacją w aplikacji, bez przełączania do map. „Opróżniono” zamyka zgłoszenie jednym dotknięciem. | The driver sees bins by priority, each with a reason: how many reports and how full. The forecast says when the bin will cross 85%. "On my way" navigates inside the app, no switching to maps. "Emptied" closes the report with one tap. |
| 1:08–1:14 | **Dalej** → krok 4: `/zgloszenie/<nr>` (oś czasu z godzinami) | Mieszkanka widzi oś czasu: przyjęte, w realizacji, zrealizowane. | The resident sees a timeline: received, in progress, done. |
| 1:14–1:54 | **Dalej** → krok 5: `/dashboard` (plakietka „Dane demonstracyjne”), klik **Stare Miasto** na wykresie dzielnic, karta projektu; na koniec `/metodologia#krakow` | Dashboard miasta, dane demonstracyjne. Ostatnie 30 dni: koszt 70,4 tys. zł, minus 2,7 procent, 4,1 tys. zł oszczędności i 668 kursów mniej niż w planie. Projekt na Starym Mieście: 13 procent mniej wywozów, czas reakcji z 6,3 do 2,7 godziny. W symulacji puste przyjazdy spadają z 57 do 27 procent, przepełnione altany z 338 godzin do zera, a dla Krakowa to 1,5 do 2,8 mln zł rocznie. | The city dashboard, on demo data. Last 30 days: cost PLN 70.4k, minus 2.7%, PLN 4.1k saved and 668 fewer trips than planned. Old Town project: 13% fewer pickups, response time from 6.3 to 2.7 hours. In simulation, empty trips drop from 57 to 27%, shelter overflow from 338 hours to zero, and across Kraków that's PLN 1.5 to 2.8 million a year. |
| 1:54–2:00 | **Zakończ**, slajd 1 z logo i QR | Kraków nie potrzebuje więcej koszy. Potrzebuje wróżki. | Kraków doesn't need more bins. It needs a fairy. |

## Liczby w tekście i ich źródło

9 383 kosze i Floriańska 3× dziennie: harmonogram MPO 08/2026 (`docs/kontekst-mpo.md`). 150 m i reguła „Zweryfikowane AI” / „Do weryfikacji”:
README, sekcja „AI w przepływie” (`photos.verification`); 85%: próg prognozy. Dashboard (dane demonstracyjne, `app/history.py`, po „Resetuj dane demo”):
koszt 70,4 tys. zł (−2,7%), oszczędności 4,1 tys. zł, 668 kursów mniej niż w planie, projekt „Odbiory na żądanie – Stare Miasto” −13% wywozów
i czas reakcji 6,3 h → 2,7 h: `DEMO.md`. 57% → 27% i 338 h → 0 h (`comparison.compare`) oraz 1,5–2,8 mln zł/rok (`methodology.city_scale`):
strona `/metodologia#krakow`. Chip powodu (np. liczba zgłoszeń i procent) i godzina prognozy zależą od stanu demo, dlatego lektor ich nie czyta.
