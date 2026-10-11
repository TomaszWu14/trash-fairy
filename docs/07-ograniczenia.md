# 07. Ograniczenia, znane problemy i co dalej

## Czego aplikacja świadomie nie robi

| Brak | Skutek | Co byłoby potrzebne |
|---|---|---|
| **Logowanie i role** ([06-decyzje.md](06-decyzje.md), D4) | Każdy może oznaczyć „Opróżniono” z dowolnym poziomem, „Uprzątnięte” i „Dodaj do kursu” (`app/api_kierowca.py:119-170`, `app/wysypiska_api.py:114-127`, `app/dyspozytor_api.py:133-142`). Opróżnienie rozstrzyga zgłoszenia i przyznaje punkty. | role dyspozytora i kierowcy (np. SSO miasta) przed pilotażem |
| **Czujnik zapełnienia jako wejście do decyzji** | Odczyt z `POST /api/odczyty` zapisuje się w `point.snapshot_fill` (`app/devices_api.py:102`), ale silnik stanu go nie czyta. | decyzja, czy czujnik ma nadpisywać prognozę |
| **Rejestracja mieszkańca przez SMS** | Kod Twilio Verify i rejestracji jest gotowy (`app/sms.py`, `app/residents.py:46-86`), ale żaden ekran go nie wywołuje. W demo działa jedno konto „Anna K.”. | ekran rejestracji, zgoda na koszt SMS |
| **Raport AI „Wróżka podpowiada”** | `app/fairy.py` nie ma ekranu ani endpointu. | decyzja: przywrócić albo usunąć |
| **Przyjmowanie zgłoszeń przez Open311** | Otwarte API jest tylko do odczytu. | uzgodnienie z systemem zgłoszeń miasta |
| **Upływ czasu w demo** | Zegar demo stoi na sobocie 3.10.2026 13:30 (`app/simulation.py:23`). Funkcja `clock.advance()` istnieje, ale nie ma przycisku. Skutki: zgłoszenia jednego kosza scalają się aż do opróżnienia, a „Dodaj do kursu” nie wygasa po 24 h. | w produkcji zegar ścienny zamiast demo |
| **Prawdziwe dane zapełnienia i kosztów** | Poziomy, historia 12 miesięcy, koszty, masy i projekty są syntetyczne, z plakietką „Dane demonstracyjne”. Kwoty to założenia ([06-decyzje.md](06-decyzje.md), D8). | pilotaż (poniżej) |
| **Realistyczny model bazowy** | Stały plan w porównaniu to „wszystkie kosze 2× dziennie”, a prawdziwy harmonogram to mieszanka 3×/2×/1× dziennie i 3–5× w tygodniu. | dane harmonogramu per kosz od przewoźnika |

## Znane problemy (otwarte)

1. **„Jadę” nie sprawdza, czy kosz jest na trasie** (`app/api_kierowca.py`). Kierowca może jechać do kosza spoza planu, np. ze zgłoszenia — to świadome.
2. **Wspólne konto demo „Anna K.” może zaliczyć wysypisko uprzątnięte z tej samej przeglądarki** (scenariusz C dla jury). To jawny wyjątek jak stały adres kosza 18; prawdziwy mieszkaniec tego nie zrobi (`app/wysypiska.py`, `resident_dump_items`).
3. **Wyczyszczenie ciasteczek daje nowy identyfikator telefonu.** Zostaje wtedy limit na IP i dzienny kod QR. „Uprzątnięte” i „Opróżniono” nadal nie wymagają konta ekipy (pilotaż).

## Decyzje autora (11.10.2026)

| Problem | Decyzja | Gdzie |
|---|---|---|
| progi „pełny” różne na ekranach (50/80) i w silniku (60/85) | jedna definicja: progi silnika tras (≥ 60% „zapełnia się”, > 85% „pełny”) na ekranach, u dyspozytora i kierowcy, w legendach i podpowiedziach | `app/api_wspolne.py` (`poziom_stan`), `app/static/ui/app.js` (`TF.lvl`), `app/dyspozytor_api.py` |
| trzy progi baterii (15/20/35%) | dwa progi o różnych rolach w jednym miejscu: 15% krytyczny (status, e-papier), 35% ostrzeżenie; martwy próg 20% usunięty | `app/devices.py` (`CRITICAL_BATTERY`, `WARN_BATTERY`) |
| poziom od ekipy niezgodny ze zdjęciem | decyzja zostaje przy kierowcy (reguła, nie AI); rozbieżność > 25 p.p. trafia na listę „Do sprawdzenia” w szczegółach anomalii na dashboardzie (z filtrami dzielnicy i frakcji) | `app/dashboard_api.py` (`_photo_mismatches`) |
| równoczesne naciśnięcia i potwierdzenia | blokada wiersza kosza przy scalaniu naciśnięć (`SELECT … FOR UPDATE` na PostgreSQL; SQLite bez blokady), atomowy licznik potwierdzeń wysypiska | `app/reports.py`, `app/wysypiska.py` |
| limit „na telefon” z pola wysyłanego przez przeglądarkę | identyfikator telefonu w podpisanym ciasteczku sesji (`phone_id`), pole „klient” ignorowane; ten sam telefon (także w trybie ekipy) nie potwierdzi ani nie uprzątnie własnego wysypiska; ciasteczko `SameSite=Lax`, `Secure` przy `PUBLIC_URL` z https | `app/api_wspolne.py`, `app/__init__.py`, `/prywatnosc` |
| dyspozytor bez przejścia do szczegółów | linki: zgłoszenie TF- → status, wysypisko WD- → status (tryb ekipy), kosz → karta kosza | `app/static/ui/dyspozytor.js` |

Testy: `tests/test_decyzje_otwarte.py`, `tests/test_zglos.py::test_phone_limit_ignores_forged_client_field`,
`tests/test_wysypiska.py::test_registered_resident_does_not_score_dump_cleared_from_own_phone`. Przegląd bezpieczeństwa i warstwy
danych (agenci z `.claude/agents/`) wykonany raz na tej gałęzi; zasadne uwagi poprawione.

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
5. role i logowanie ekipy („Uprzątnięte” i „Opróżniono” tylko z kont ekipy).
