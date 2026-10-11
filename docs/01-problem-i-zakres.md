# 01. Problem i zakres

## Problem

Kosze uliczne w centrum miasta są opróżniane według stałego harmonogramu, a nie według tego, ile w nich jest.

- W Dzielnicy I Krakowa 43% koszy jest opróżnianych 3× dziennie, a 36% 2× dziennie (publiczny harmonogram oczyszczania 08/2026,
  [mpo.krakow.pl/czystosc](https://mpo.krakow.pl/czystosc/); opracowanie w [`kontekst-mpo.md`](kontekst-mpo.md)).
- W symulacji (te same kosze, ten sam przebieg zapełniania) **57% przyjazdów według stałego planu trafia na kosz zapełniony poniżej 50%**,
  a jednocześnie kosze przepełniają się w weekendy i przy wydarzeniach ([`app/comparison.py`](../app/comparison.py), test `tests/test_dashboard.py`).
- Mieszkaniec, który widzi przepełniony kosz, może go zgłosić tylko telefonicznie albo mailowo do dyspozytorni ([`kontekst-mpo.md:11`](kontekst-mpo.md)).
- Część problemu tworzą przepełnione altany śmietnikowe: mieszkańcy wynoszą worki do koszy ulicznych ([`KONCEPCJA.md`](KONCEPCJA.md), KRKnews 8.09.2026).

Skutek: jeżdżą puste kursy, a przepełnienia i tak zostają. Nikt nie wie wcześniej, który kosz się zapełni.

## Interesariusze

| Interesariusz | Potrzeba | Co dostaje w aplikacji |
|---|---|---|
| Mieszkaniec | zgłosić problem przy koszu w kilka sekund i wiedzieć, co się z tym dzieje | zgłoszenie z kodu QR lub przycisku, status, punkty za trafne zgłoszenia |
| Kierowca / ekipa odbioru | wiedzieć, gdzie jechać i dlaczego | trasę według priorytetu z powodem każdego przystanku; „Jadę” i „Opróżniono” |
| Dyspozytor | szybko zareagować na pilne kosze | listę pilnych koszy, mapę na żywo, „Dodaj do kursu” |
| Miasto / operator odbioru odpadów | wydać mniej na puste kursy i podejmować decyzje inwestycyjne na danych | dashboard kosztów wobec planu, rekomendacje (kompaktor, większy kosz, rzadszy odbiór), otwarte API |

<DO UZUPEŁNIENIA: czy wskazać konkretnego operatora (MPO Kraków), czy opisywać rolę ogólnie>

## Cel i miary sukcesu

Miary liczy kod na danych symulacji, z porównaniem 4 tygodni (stały harmonogram kontra Trash Fairy, ten sam przebieg zapełniania):

| Miara | Stały plan | Trash Fairy | Gdzie liczone |
|---|---|---|---|
| Puste przyjazdy (kosz < 50%) | 57% | 27% | `app/comparison.py` |
| Odbiory koszy w 4 tygodniach | 3 360 | 2 543 (−24%) | `app/comparison.py` |
| Godziny przepełnienia altan | 338 h | 0 h | `app/comparison.py` |
| Błąd prognozy (MAE) | 7,1 p.p. (średnia naiwna) | 2,4 p.p. | `app/forecast.py` |

Kwoty (12 zł za odbiór, 5 zł/km) to **założenia** do potwierdzenia z przewoźnikiem ([`app/methodology.py`](../app/methodology.py)).
Zobacz też: [07-ograniczenia.md](07-ograniczenia.md).

## W zakresie

1. Zgłoszenie przy koszu: fizyczny przycisk na panelu oraz formularz po zeskanowaniu dziennego kodu QR.
2. Stan kosza i prognoza godziny zapełnienia (85%) z profilu tygodniowego, wydarzeń i pogody.
3. Wybór koszy na kurs regułami i trasa z optymalizacją (OR-Tools).
4. Aplikacja kierowcy: trasa, „Jadę”, „Opróżniono” z poziomem i zdjęciem, zgłoszenie problemu.
5. Panel dyspozytora: pilne kosze, mapa, ręczne „Dodaj do kursu”.
6. Status zgłoszenia dla mieszkańca i punkty za trafne zgłoszenia.
7. Zgłoszenie dzikiego wysypiska z mapą, wykrywanie duplikatów i drabinka działań.
8. Dashboard miasta: koszty wobec planu, KPI, rekomendacje, eksport CSV.
9. Analiza zdjęć przez AI, która tylko opisuje; decyzje podejmują reguły.
10. Otwarte API (GeoJSON, CSV, Open311 tylko do odczytu).

## Poza zakresem (świadomie)

| Czego nie ma | Dlaczego |
|---|---|
| Logowanie i role | Pokaz dla jury bez kont. Role istniały i zostały usunięte decyzją autora ([06-decyzje.md](06-decyzje.md), D4). W pilotażu potrzebne są role. |
| Czujniki zapełnienia jako wejście do decyzji | Aplikacja ma działać bez drogiego sprzętu. Odczyt czujnika jest zapisywany, ale nie zmienia stanu ani trasy. |
| Rejestracja mieszkańca przez SMS | Kod jest gotowy (`app/sms.py`, `app/residents.py`), ale nie podpięty do ekranu. W demo działa jedno konto „Anna K.”. |
| Raport tekstowy AI „Wróżka podpowiada” | Kod jest (`app/fairy.py`), ale żaden ekran go nie wywołuje. |
| Przyjmowanie zgłoszeń przez Open311 (POST) | Otwarte API jest tylko do odczytu. |
| Rozliczenia z wykonawcą, integracja z systemem przewoźnika | Brak danych i dostępu. |
| Prawdziwe dane zapełnienia i kosztów | Poziomy, koszty, masy i projekty są syntetyczne (oznaczone „Dane demonstracyjne”). Prawdziwe są położenia koszy (OpenStreetMap), harmonogram, wydarzenia i pogoda. |

## Kontekst projektu

Projekt powstał solo na hackathonie **HackYeah 2026** (3–4.10.2026) w zadaniu otwartym **Smart City**: „rozwiąż konkretny problem miasta lub jego mieszkańców, wskaż użytkowników i pokaż, jak rozwiązanie działa w konkretnej sytuacji”. Z obszarów podanych w zadaniu wybrałem zarządzanie odpadami i wykorzystanie danych miejskich do podejmowania decyzji. Treść zadania i regulamin: [`docs/zadanie/`](zadanie/).
Koncepcja powstała przed wydarzeniem ([`docs/KONCEPCJA.md`](KONCEPCJA.md), bez kodu). Rdzeń aplikacji napisałem podczas hackathonu, a po nim (5–6.10) domknąłem podpowiedzi, scenariusze demo i filmy.

**Ocena w pierwszej fazie (komisja zadania, platforma HackTribe):**

| Pomysł i innowacyjność (30%) | Zgodność z kategorią (20%) | Użyteczność (20%) | Design (20%) | Kompletność i gotowość wdrożenia (10%) | Średnia ważona | Średnia wszystkich zespołów |
|---|---|---|---|---|---|---|
| 6,25 | 7,00 | 4,50 | 6,25 | 4,25 | **5,85** | 4,66 |

Najniżej oceniono użyteczność i kompletność wdrożenia.

**Czego się nauczyłem:** <DO UZUPEŁNIENIA>
