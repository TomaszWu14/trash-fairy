# Film 2:00: scenariusz (wersja z napisami, bez lektora i muzyki)

Film nagrywa i skleja skrypt: `python demo/build_all.py --base https://trashfairy.twapp.pl --tylko film` → `demo/demo_trash-fairy.mp4`
(H.264 1920×1080, 30 fps, ≤ 120 s). Playwright nagrywa prawdziwą aplikację w motywie ciemnym, kółko pokazuje każde kliknięcie,
a ładowanie stron i czekanie (dojazd nawigacji, analiza zdjęcia) jest wycięte. Napisy to nakładka w stronie, w fontach aplikacji.
Skrypt sprawdza każdy krok (numer zgłoszenia, „Opróżniono”, status „Zrealizowane”, punkty); brak ekranu dyspozytora albo „Dziękujemy!”
tylko ostrzega w logu. Przed nagraniem i po nim resetuje dane demo (to samo API co przycisk „Resetuj dane demo”).
Pliki `pl.srt` i `en.srt` obok to napisy starej wersji z lektorem (opisują nieaktualne reguły i kwoty): nie używać.

## Przebieg

| Część | Czas | Obraz | Napis |
|---|---|---|---|
| Plansza | 3 s | logo, „Trash Fairy” | Mózg odbioru odpadów dla Krakowa |
| Plansza | 2 s | „Scenariusz 1” | Przepełniony kosz: od zgłoszenia do odbioru |
| S1 | ok. 55 s | `/` | Kraków opróżnia kosze według kalendarza. Trash Fairy: według potrzeb. |
| | | `/?scenariusz=A&kosz=18` (okienko scenariusza) | Scenariusz demo: mieszkanka przy koszu nr 18 |
| | | Panel kosza `/panel/18` | Panel kosza: zapełnienie, termin odbioru i kod QR zmieniany codziennie |
| | | klik w kod QR → `/zglos/18?qr=…` | Skan kodu QR otwiera zgłoszenie tego kosza → „Przepełniony” i Wyślij |
| | | potwierdzenie z numerem | Zgłoszenie TF-… przyjęte: numer i status od razu |
| | | Panel kosza | Panel kosza potwierdza zgłoszenie |
| | | `/dyspozytor` | Dyspozytor widzi pilne kosze, trasy i ekipy na żywo |
| | | `/kierowca` → kosz 18 | Kierowca: zgłoszony kosz na liście, z powodem |
| | | **Jadę** | „Jadę”: nawigacja w aplikacji, bez przełączania do map |
| | | **Opróżniono** ze zdjęciem kosza (rysunek podpisany „demo”) | „Opróżniono” ze zdjęciem kosza: dowód odbioru |
| | | potwierdzenie | Odbiór potwierdzony: położenie śmieciarki i zdjęcie |
| | | `/zgloszenie/TF-…` | Mieszkanka widzi: zrealizowane |
| | | `/dashboard` | Miasto: oszczędności wobec planu, odbiory i zgłoszenia |
| Plansza | 2 s | „Scenariusz 2” | Dzikie wysypisko i decyzje dla miasta |
| S2 | ok. 55 s | `/?scenariusz=C&miejsce=0` | Dzikie wysypisko poza koszem: zgłasza mieszkaniec |
| | | `/wysypisko` (okolice ROD „Grzegórzki”, bio i tworzywa, 20 worków) | Miejsce na mapie, rodzaje odpadów, liczba worków → Zdjęcie: AI opisuje, reguła decyduje |
| | | potwierdzenie, status `/wysypisko/WD-…` | Przyjęte: WD-… → Status zgłoszenia dzikiego wysypiska |
| | | `/dyspozytor`, dodanie kosza do kursu | Dyspozytor: gorące obszary i pilne zgłoszenia → Dyspozytor dodaje kosz do kursu: decyzja człowieka |
| | | `/wysypisko/WD-…?ekipa=1` | Ekipa sprząta i oznacza „Uprzątnięte” |
| | | `/zglos` | Mieszkaniec dostaje punkty: N pkt (liczba z aplikacji) |
| | | `/dashboard`, rekomendacje | Miasto: oszczędności dziennie, w miesiącu i w roku → Rekomendacje z reguł: od tablicy po fotopułapkę |
| Plansza | 3 s | logo | Kraków nie potrzebuje więcej koszy. Potrzebuje wróżki. · trashfairy.twapp.pl · github.com/TomaszWu14/trash-fairy |

## Liczby w filmie

Napisy nie zawierają kwot. Numery zgłoszeń (TF-…, WD-…) i punkty mieszkańca pochodzą z odpowiedzi aplikacji w trakcie nagrania;
oszczędności (po 12 zł za odbiór i 5 zł za km) widać na nagranym dashboardzie produkcji. Zgłoszenie przyjmujemy tylko przy koszu
(przycisk na Panelu kosza albo dzienny kod QR z panelu), bez sprawdzania położenia telefonu.
