# 07. Ograniczenia, znane problemy i co dalej

## Czego aplikacja świadomie nie robi

| Brak | Skutek | Co byłoby potrzebne |
|---|---|---|
| **Logowanie i role** ([06-decyzje.md](06-decyzje.md), D4) | Każdy może oznaczyć „Opróżniono” z dowolnym poziomem, „Uprzątnięte” i „Dodaj do kursu” (`app/api_kierowca.py:119-170`, `app/wysypiska_api.py:114-127`, `app/dyspozytor_api.py:133-142`). Opróżnienie rozstrzyga zgłoszenia i przyznaje punkty. | role dyspozytora i kierowcy (np. SSO miasta) przed pilotażem |
| **Czujnik zapełnienia jako wejście do decyzji** | Odczyt z `POST /api/odczyty` zapisuje się w `point.snapshot_fill` (`app/devices_api.py:102`), ale silnik stanu go nie czyta. | decyzja, czy czujnik ma nadpisywać prognozę |
| **Rejestracja mieszkańca przez SMS** | Kod Twilio Verify i rejestracji jest gotowy (`app/sms.py`, `app/residents.py:48-88`), ale żaden ekran go nie wywołuje. W demo działa jedno konto „Anna K.”. | ekran rejestracji, zgoda na koszt SMS |
| **Raport AI „Wróżka podpowiada”** | `app/fairy.py` nie ma ekranu ani endpointu. | decyzja: przywrócić albo usunąć |
| **Przyjmowanie zgłoszeń przez Open311** | Otwarte API jest tylko do odczytu. | uzgodnienie z systemem zgłoszeń miasta |
| **Upływ czasu w demo** | Zegar demo stoi na sobocie 3.10.2026 13:30 (`app/simulation.py:23`). Funkcja `clock.advance()` istnieje, ale nie ma przycisku. Skutki: zgłoszenia jednego kosza scalają się aż do opróżnienia, a „Dodaj do kursu” nie wygasa po 24 h. | w produkcji zegar ścienny zamiast demo |
| **Prawdziwe dane zapełnienia i kosztów** | Poziomy, historia 12 miesięcy, koszty, masy i projekty są syntetyczne, z plakietką „Dane demonstracyjne”. Kwoty to założenia ([06-decyzje.md](06-decyzje.md), D8). | pilotaż (poniżej) |
| **Realistyczny model bazowy** | Stały plan w porównaniu to „wszystkie kosze 2× dziennie”, a prawdziwy harmonogram to mieszanka 3×/2×/1× dziennie i 3–5× w tygodniu. | dane harmonogramu per kosz od przewoźnika |

## Znane problemy (otwarte)

Obserwacje z przeglądu kodu (11.10.2026), których świadomie nie poprawiono, bo wymagają decyzji, a nie samej poprawki.

**Logika i dane**
1. **Kierowca może podać poziom niezgodny ze zdjęciem.** Opróżnienie rozstrzyga zgłoszenia poziomem podanym przez kierowcę, zanim AI obejrzy zdjęcie. Rozbieżność > 25 p.p. kończy się tylko flagą (`app/api_kierowca.py`, `app/photos.py:38`). Decyzja: czy rozbieżność ma cofać rozstrzygnięcie.
2. **Progi „pełny” różnią się między ekranami:**
   - silnik: 60/85 (`app/state.py:20-21`);
   - ekrany: 50/80 (`app/api_wspolne.py:47-48`);
   - dyspozytor i kierowca: 80.

   Kosz z 82% jest na ekranie „pełny”, a dla trasy dopiero „zapełnia się”. Decyzja: jedna definicja dla wszystkich ekranów.
3. **Trzy progi niskiej baterii:** 15% (`app/devices.py:29`), 20% (`app/residents.py:24`), 35% (`app/devices.py:72`).
4. **Limit „na telefon” opiera się na polu `klient` z przeglądarki** (`app/api_pl.py:146`, `app/wysypiska_api.py:67`), więc da się go obejść. Działa limit na IP; pewna tożsamość telefonu wymaga logowania.
5. **„Sprawdź, potem zapisz” bez blokady** (`app/reports.py:53-75`, `app/wysypiska.py:161`): równoczesne naciśnięcia mogą dać dwa otwarte zgłoszenia. Przy ruchu z pilotażu: blokada wiersza albo unikalny indeks.
6. **„Jadę” nie sprawdza, czy kosz jest na trasie** (`app/api_kierowca.py`). Kierowca może jechać do kosza spoza planu, np. ze zgłoszenia.
7. **Dyspozytor nie może otworzyć szczegółów zgłoszenia ani wysypiska** (`app/static/ui/dyspozytor.js`). To brakująca funkcja, nie błąd.

## Naprawione (11.10.2026)

Każda poprawka ma test-strażnika w `tests/test_naprawy_bledow.py`, który nie przechodził przed zmianą.

| Było | Poprawka |
|---|---|
| jedna nagroda dziennie liczona od innej daty niż zapisywana | okno doby z `resolved_at` (`app/residents.py`) |
| strona projektu nie pokazywała „Nie ma takiego projektu” | `projekt.js` sprawdza kod `nieznany_projekt` z API |
| cache dashboardu nie widział wysypisk, punktów i odczytów czujników | dodatkowa wersja danych `state.side_version()` w kluczu cache |
| e-papier dla punktu z warstwy miasta i id spoza zakresu → 500 | 404 w jednym miejscu: `Point.live_or_404` |
| token urządzenia spoza ASCII → 500 | porównanie na bajtach (`app/devices_api.py`) |
| panel bez wiersza `device`, czujnik bez odczytu → 500 | panel zakładany przy pierwszym odczycie; bez odczytu urządzenie jest offline |
| dzielenie przez zero przy pustej bazie | zero zamiast wyjątku (`app/methodology.py`) |
| nieznany status projektu → KeyError | etykieta z wartością domyślną |
| zły wpis w `events.json` wywracał każde przeliczenie | wpis pomijany przy imporcie |
| błąd sieci przerywał `flask karnet` | czytelny komunikat, cache bez zmian |
| analiza AI w wątku po resecie demo → wyjątek | brak wiersza = koniec bez błędu |
| drugie „Jadę” dokładało wpis | „Jadę” jest idempotentne |
| opróżnienie zapisane przed zdjęciem, zdjęcie mieszkańca przed zgłoszeniem | jeden commit: dane ze zdjęciem albo nic |
| pierwsze ładowanie ekranu nie ponawiało się po błędzie | `TF.watch` odświeża też co 10. próbę (ok. 30 s) |
| statusy zgłoszenia i wysypiska milczały przy błędzie innym niż 404 | jednorazowy komunikat |
| eksport CSV przy błędnym filtrze pobierał komunikat błędu | eksport wyłączony, a nieaktualne liczby wyszarzone, dopóki filtr nie zadziała |

**Martwy kod:** `app/sms.py`, `app/fairy.py`, `residents.register/verify/profile/rankings`, `photos.gps_from_exif`, `forecast.source='pred'`.

## Rozbieżności dokumentacji z kodem

| Dokument | Twierdzi | Kod |
|---|---|---|
| `DECYZJE.md:176`, `:351` | zgłoszenie spoza 150 m jest odrzucane | położenia nie sprawdzamy (`app/api_pl.py:131-133`); zmianę opisuje `DECYZJE.md:417` |
| `DECYZJE.md:273-284` | role i `app/auth.py` | usunięte (`DECYZJE.md:340, 355`) |
| `DECYZJE.md:51` | przycisk „przewiń +1 h” | brak przycisku i endpointu |
| `DECYZJE.md:58` | limity 1/2 s i 120/h | 1/min na telefon i kosz, 200/h z IP |
| `DECYZJE.md:278, 307`, `docs/PRZEGLAD.md:78` | skala Krakowa 1,4–2,8 mln zł/rok (przy 4 zł/odbiór) | 4,2–7,9 mln zł/rok (przy 12 zł, `app/methodology.py:106-133`) |
| `DECYZJE.md`, README | +163 km przy altanach | +156 km (`app/comparison.py`, seed) |
| `docs/KONCEPCJA.md:98, 180` | geokodowanie miejsc wydarzeń przez Nominatim | Karnet podaje współrzędne, Nominatim nieużywany (`DECYZJE.md:151`) |

Liczby obowiązujące w tej dokumentacji wylicza kod przy `flask seed`. Wpisy w `DECYZJE.md` są historyczne.

## Co dalej

Plan pilotażu (Dzielnica I, 50 koszy, 3 miesiące, grupa testowa i kontrolna) jest w [`ROADMAPA.md`](../ROADMAPA.md). Warunki wstępne wynikające z listy otwartych problemów:
1. role i autoryzacja akcji kierowcy i dyspozytora;
2. zegar ścienny zamiast zegara demo;
3. prawdziwy harmonogram jako model bazowy i dane GPS pojazdów do porównania;
4. potwierdzone stawki kosztów;
5. jedna definicja progów „pełny” we wszystkich ekranach.
