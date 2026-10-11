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

## Znane problemy

Obserwacje z przeglądu kodu (11.10.2026) nie zostały poprawione. Każda wskazuje plik i linię.

**Błędy logiki**
1. **Jedna nagroda dziennie:** okno doby liczone jest od `report.first_at` (`app/residents.py:129`), a nagroda zapisuje się z `resolved_at` (`:135`). Zgłoszenie z 23:50 rozstrzygnięte o 6:00 przechodzi sprawdzenie dwa razy.
2. **Brak karty „Nie ma takiego projektu”:** `app/static/ui/projekt.js:23` sprawdza kod `projekt_nie_istnieje`, a API zwraca `nieznany_projekt` (`app/dashboard_api.py:449`). Strona pokazuje tylko komunikat, a szkielety ładowania zostają.
3. **Kierowca może podać poziom niezgodny ze zdjęciem.** Opróżnienie rozstrzyga zgłoszenia poziomem podanym przez kierowcę, zanim AI obejrzy zdjęcie. Rozbieżność > 25 p.p. kończy się tylko flagą (`app/api_kierowca.py:152-157`).
4. **Progi „pełny” różnią się między ekranami:**
   - silnik: 60/85 (`app/state.py:20-21`);
   - ekrany: 50/80 (`app/api_wspolne.py:47-48`);
   - dyspozytor i kierowca: 80.

   Kosz z 82% jest na ekranie „pełny”, a dla trasy dopiero „zapełnia się”.
5. **Trzy progi niskiej baterii:** 15% (`app/devices.py:29`), 20% (`app/residents.py:24`), 35% (`app/devices.py:72`).
6. **Cache dashboardu nie widzi części zmian.** Klucz wersji danych (`app/state.py:111-122`) nie obejmuje wysypisk, urządzeń ani punktów mieszkańców, więc te liczby mogą być nieaktualne.

**Brak obsługi błędów i walidacji**

| Plik:linia | Problem |
|---|---|
| `app/views.py:30-31` | e-papier dla punktu z warstwy miasta (`live=False`): KeyError → 500 |
| `app/open_api.py:69`, `app/devices_api.py:56` | id bez górnego limitu: na PostgreSQL „integer out of range” → 500 (w `app/api_wspolne.py:63-69` limit jest) |
| `app/devices_api.py:90` | porównanie tokenu jako `str`: nagłówek spoza ASCII → TypeError → 500 (w `app/api_pl.py:116` naprawione) |
| `app/devices_api.py:106-107`, `app/devices.py:127, 133` | brak wiersza `device` albo `last_seen = NULL` → 500 |
| `app/methodology.py:119-121` | dzielenie przez zero przy pustej bazie (`/`, `/metodologia`) |
| `app/dashboard_api.py:424` | `STATUS_PL[...]` bez wartości domyślnej → KeyError przy nieznanym statusie projektu |
| `app/events.py:20-29` | import `events.json` bez walidacji skali i dat |
| `app/karnet.py:113-117` | błąd sieci przerywa komendę `flask karnet` |
| `app/photos.py:198-199`, `app/wysypiska.py:169-178` | analiza AI w wątku nie obsługuje wiersza skasowanego przez reset demo |
| `app/api_kierowca.py:128-130` | „Jadę” bez limitu i bez sprawdzenia, czy kosz jest na trasie |
| `app/api_kierowca.py:154-158` | opróżnienie zapisuje się przed zdjęciem: błąd zapisu pliku → 500 przy zapisanym opróżnieniu |
| `app/api_pl.py:153` | zdjęcie zapisane przed zgłoszeniem: przy błędzie zostaje osierocony plik |
| `app/api_pl.py:146`, `app/wysypiska_api.py:67` | limit „na telefon” opiera się na polu `klient` wysyłanym przez przeglądarkę, więc da się go obejść |
| `app/reports.py:53-75`, `app/wysypiska.py:161` | „sprawdź, potem zapisz” bez blokady: równoczesne naciśnięcia mogą dać dwa otwarte zgłoszenia |

**Ekrany bez informacji zwrotnej**
- **Brak ponowienia po błędzie pierwszego ładowania.** Kierowca, karta kosza, dyspozytor i dashboard nie mają „Spróbuj ponownie” (`app/static/ui/app.js:107`).
- **Statusy zgłoszenia i wysypiska milczą przy błędzie innym niż 404** (`mieszkaniec.js:187`, `wysypisko.js:197-199`).
- **Eksport CSV przy błędnym filtrze pobiera plik z komunikatem błędu** zamiast danych.
- **Dyspozytor nie może otworzyć szczegółów zgłoszenia ani wysypiska.**

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

Plan pilotażu (Dzielnica I, 50 koszy, 3 miesiące, grupa testowa i kontrolna) jest w [`ROADMAPA.md`](../ROADMAPA.md). Warunki wstępne wynikające z tej listy:
1. role i autoryzacja akcji kierowcy i dyspozytora;
2. zegar ścienny zamiast zegara demo;
3. prawdziwy harmonogram jako model bazowy i dane GPS pojazdów do porównania;
4. potwierdzone stawki kosztów;
5. jedna definicja progów „pełny” we wszystkich ekranach.
