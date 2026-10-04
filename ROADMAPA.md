# Roadmapa

Etapy HackYeah (przycisk i stan, prognoza, trasy OR-Tools z porównaniem, Claude Vision, `app/llm.py`, przebudowa UI) są zrealizowane;
uzasadnienia w `DECYZJE.md`. Poniżej: co po hackathonie.

## Pilotaż: Dzielnica I, 50 koszy, 3 miesiące

Cel: sprawdzić na prawdziwych koszach, czy wyniki z symulacji się potwierdzają. Bez kupowania sprzętu na start: sygnały z kodów QR,
od mieszkańców i od kierowców.

**Tydzień 0–2: przygotowanie**
- Wybór 50 koszy w Dzielnicy I razem z MPO (różne miejsca: Planty, Rynek, Kazimierz, okolice przystanków i lokali).
- Naklejki z kodem QR na każdym koszu; panele na kilku najbardziej obciążonych, jeśli miasto chce je testować.
- Dostęp do harmonogramu opróżnień tych koszy i do GPS śmieciarek (położenie, czas postoju przy koszu).
- Konto dyspozytora MPO, konta kierowców obsługujących rejon, krótkie szkolenie z aplikacji kierowcy.

**Miesiąc 1: zbieranie sygnałów obok stałego harmonogramu**
- MPO jeździ jak dotąd. Trash Fairy zbiera zgłoszenia, odczyty kierowców przy opróżnieniu i liczy prognozę, ale nie zmienia tras.
- Wynik: prawdziwy profil 7 × 24 dla każdego kosza i punkt odniesienia (puste przyjazdy, przepełnienia, czas reakcji).

**Miesiąc 2: trasy Trash Fairy na połowie koszy**
- 25 koszy (grupa testowa) obsługiwanych według prognozy i zgłoszeń, 25 (grupa kontrolna) według stałego harmonogramu.
- Grupy dobrane parami o podobnym obciążeniu, żeby porównanie było uczciwe; bezpieczniki z symulacji (maksymalny odstęp między opróżnieniami) zostają.

**Miesiąc 3: ocena**
- Porównanie grup: odsetek pustych przyjazdów, godziny przepełnienia, czas od zgłoszenia do opróżnienia, koszt (km i wizyty).
- Raport dla miasta i MPO z danymi źródłowymi i decyzją: rozszerzać, poprawiać czy zakończyć.

**Czego potrzebujemy od miasta i MPO**
- Zgody na naklejki QR na koszach i osoby kontaktowej w MPO (dyspozytor).
- Harmonogramu i danych GPS pojazdów dla rejonu pilotażu (eksport lub API, tylko do odczytu).
- Kierowców, którzy przez 3 miesiące oznaczają opróżnienia w aplikacji.
- Hostingu w UE (jeden kontener + PostgreSQL) albo zgody na nasz.

**Kryteria sukcesu (hipotezy do sprawdzenia, nie obietnice)**
- Grupa testowa ma wyraźnie mniej pustych przyjazdów niż kontrolna (w symulacji: 57% → 27%).
- Godziny przepełnienia w grupie testowej nie rosną, a w weekendy i przy wydarzeniach spadają.
- Czas reakcji na zgłoszenie mieszkańca mieści się w standardzie MPO dla prac interwencyjnych (2 h).
- Koszt obsługi grupy testowej (km i wizyty) nie jest wyższy niż kontrolnej.
- Jeśli hipoteza się nie potwierdzi, raport mówi to wprost.

## 3 miesiące / 6 miesięcy / 12 miesięcy

**3 miesiące (równolegle z pilotażem)**
- Prawdziwe czujniki na endpoincie `POST /api/odczyty` (endpoint, token urządzenia i symulator `scripts/symulator_czujnikow.py` już są): montaż i kalibracja w pilotażu.
- Web Push dla zgłaszającego („Opróżniono”), dziś status odświeża się na otwartym ekranie.
- Eksport tras do CSV (eksport odbiorów i zgłoszeń z filtrami dashboardu już jest: `/api/eksport/*.csv`).
- Logowanie i role (dyspozytor, kierowca, miasto); dziś demo bez logowania.

**6 miesięcy**
- Czujniki LoRaWAN na koszach, gdzie sygnały z QR nie wystarczają (silnik przyjmuje czujnik jako kolejne źródło stanu).
- Rozmycie twarzy i tablic rejestracyjnych na zdjęciach przed zapisem.
- Interfejs mieszkańca po angielsku i ukraińsku (turyści, mieszkańcy z Ukrainy).
- Integracja z systemami MPO (harmonogram, GPS pojazdów) zamiast eksportów.
- Eksport zgłoszeń do miejskiego systemu zgłoszeń (np. format Open311).

**12 miesięcy**
- Prognoza uczona na prawdziwych danych z pilotażu (Holt-Winters lub ML) zamiast profilu z symulacji.
- Cały Kraków (9 383 kosze z harmonogramu MPO 08/2026), potem inne miasta.
- Kilka pojazdów na flotę, okna czasowe i ruch drogowy w macierzy czasów OR-Tools.

## Backlog techniczny

**Silnik i trasy**
- Frakcje w altanach i trasy według frakcji; ulice jednokierunkowe.
- Prognoza świadoma planu tras (przyszłe opróżnienia w trajektorii); dodatkowe kursy poza 6:00/14:00 dla punktów krytycznych (np. wieczorem przy wydarzeniach).
- Prawdziwe opróżnienia od kierowców zamiast harmonogramu z symulacji jako źródło trafności zgłoszeń.
- Stały harmonogram w porównaniu z prawdziwego pliku MPO (`harmonogram_oczyszczania_08_2026.xlsx`): dopasowanie koszy OSM do symboli KUL
  po ulicy (reverse geocoding z cache) i częstotliwość 1–3×/dzień zamiast stałych 2×/dzień.
- Świeże zgłoszenie jako zlecenie interwencji z terminem 2 h; „Wyślij do kierowcy” z dashboardu.
- Paliwo i CO₂ z jawnych, konfigurowalnych współczynników na stronie Metodologia.
- Wzorce spamu w czasie, korelacja sąsiednich przycisków.

**Urządzenia**
- Firmware przycisku i e-papieru LoRaWAN wg `docs/epapier/ETAP2-LORAWAN.md`: limit 1 zgłoszenie na 15 min w urządzeniu, sygnał życia
  i bateria raz na dobę, autotest co 6 h, downlink 12 B, test w słońcu i mrozie; `ETag` dla PNG e-papieru.

**Aplikacje**
- Kierowca: czas opróżnienia z telefonu przy wysyłce z kolejki offline, numer pojazdu, kafelki mapy pobierane z góry na cały kurs, odczyt QR kosza.
- Mieszkaniec: „Moje zgłoszenia”; ikony PNG 192/512 obok SVG dla starszych Androidów.
- Tryb ciemny dashboardu; oznaczanie wydarzeń z Karnetu na mapie.
- Program „Przyjaciele Wróżki” (`app/residents.py`, SMS Twilio Verify) jest poza obecnym UI: wrócić do niego albo usunąć.
- Czat z AI (tylko opis danych, decyzje dalej regułami).

**Infrastruktura i bezpieczeństwo**
- Alembic zamiast dodawania brakujących kolumn przy starcie; Sentry lub logi strukturalne; runbook i kopie zapasowe bazy.
- Limity, cache pogody i ruchu we wspólnym magazynie (Redis/Postgres) przy kilku workerach Gunicorna; dziś pamięć procesu + plik.
- Autoryzacja endpointu resetu demo (`/api/demo/reset`); w pilotażu tylko dla dyspozytora.
- Otwarte API: klucze i limity na klienta, wersjonowanie kontraktu, webhook „kosz przepełniony”, zagregowane miesięczne CSV jako open data.
- Kafelki mapy z własnego serwera lub komercyjnego dostawcy przy większym ruchu (polityka użycia tile.openstreetmap.org).
- Model per zadanie (mniejszy model dla prostych wywołań), gdy wolumen wywołań AI wzrośnie.
- CI: `scripts/e2e_demo.py` i Lighthouse w GitHub Actions, skan sekretów (gitleaks).

**Nieaktualne po przebudowie UI (4.10):** panel `/dyspozytor` (mobilny i ciemny), `/telefony`, loginy floty ze wspólnym hasłem, sekcja „Pilne teraz”,
tabela punktów pod mapą, emoji zamiast ikon i wspólny `tokens.css` (zrobione w design systemie `app/static/ui/`). Stare adresy przekierowują do nowych ekranów.
- Wydajność `/dashboard` na słabych telefonach (Lighthouse mobile ok. 65): lżejsza paczka ECharts (tylko użyte wykresy) albo wykresy SVG renderowane na serwerze.
- Indeksy na `point.district` i `pickup.fraction` (filtry dashboardu) przez migracje Alembic.
- `.env.example` bez `DEMO_PASSWORD` (logowanie usunięte) i zmienna usunięta w Coolify.
