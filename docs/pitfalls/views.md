# Pułapki: widoki, API, szablony, frontend

Czytaj przed zmianą `app/ui.py`, `app/views.py`, `app/api_*.py`, `app/templates/`, `app/static/`.

1. **API po polsku i bez 500.** Błędy `/api/*` zwracają JSON `{blad, kod}` (handlery w `app/__init__.py`). Zły JSON, id,
   data → 400/404 z komunikatem, nigdy wyjątek (przegląd kodu: 500-tki na złym wejściu, PR po #13).
2. **Waliduj liczby z wejścia na `NaN`/`inf`**: `NaN` omijał regułę 150 m geolokalizacji. `float(x)` przyjmuje `"nan"`.
3. **Upload zdjęć**: limit ciała 10 MB (`MAX_CONTENT_LENGTH`, 413 po polsku), `MAX_PIXELS` z nagłówka przed dekodowaniem
   (bomba dekompresyjna), EXIF/GPS czytany i usuwany w `app/photos.py`. Nie zapisuj oryginału, tylko oczyszczoną kopię.
4. **Decyzje tylko regułami w kodzie.** AI (`app/llm.py`: `ask`, `ask_json`) opisuje i rozpoznaje, nie ustala stanu,
   priorytetu ani trasy. Błąd API = komunikat + ostatni wynik z cache, nigdy 500. Tekst od użytkownika do promptu tylko przez `llm.fence()`.
5. **Bez CDN i bez builda**: biblioteki w `app/static/vendor`, fonty w `app/static/fonts`. Link do CDN psuje tryb offline PWA
   i pracę w sieci bez CDN (sala HackYeah blokowała CARTO). CSP (`_security_headers`) ma dziś tylko `frame-ancestors`.
6. **Kolor nigdy jedynym nośnikiem informacji** (WCAG 2.1 AA): stan kosza = kolor + tekst/ikona. UI po polsku.
7. **Flask bez `--debug` cache’uje szablony i nie przeładowuje tras**: po zmianie HTML/nowym endpoincie restart serwera
   (404 na `/zglos/sw.js` nie był błędem kodu).
8. **Service worker**: `navigator.serviceWorker.ready` nie rozwiązuje się bez zarejestrowanego SW, każdy `await ready`
   potrzebuje timeoutu. Zakres SW to `/zglos` i `/kierowca`: nowe pliki PWA muszą leżeć w tym zakresie.
9. **Polling co kilka sekund z wielu kart**: odpowiedź musi być tania (wersja danych + cache), a wersja identyczna na obu
   workerach (patrz `db.md` pkt 5), inaczej klienci przeładowują się w kółko.
10. **Zamknij pliki przy `get_data()` na odpowiedzi statycznej** (`_gzip` w `app/__init__.py`): inaczej wyciek uchwytów
    (ResourceWarning, commit a1e1a9e).
