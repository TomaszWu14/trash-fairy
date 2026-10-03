# Roadmapa

## Kolejne etapy HackYeah
2. **Przycisk + stan + polling:** `/przycisk/<id>`, `POST /api/press` (limit na IP, scalanie w 15 min),
   wiarygodność przycisku, `stan = max(prognoza, zgłoszenie × wiarygodność)`, `/api/changes?since=` co 2 s,
   zegar demo z „przewiń +1 h”.
3. **Prognoza:** profil tygodniowy (dzień × godzina) z historii, mnożnik wydarzeń, godzina przekroczenia 85% z przedziałem, MAE.
   Szczegóły punktu z wykresem Chart.js.
4. **Trasy OR-Tools + porównanie:** dwie floty, kursy 6:00/14:00, wybór punktów i bezpieczniki 3/7 dni,
   symulacja 4 tygodni: stały harmonogram kontra Trash Fairy (km, wizyty, godziny przepełnienia).
5. **Claude Vision:** widok ekipy MPO, analiza zdjęcia według schematu JSON, nadużycia, reguła altana → kosz.
6. **Raport „Wróżka podpowiada”:** `app/llm.py` (`ask`, `ask_json`), cache wyników, Karnet Kraków, rekomendacje, tryb jury.

## Później (poza HackYeah, koncepcja sekcja 16)
- Fizyczny przycisk (LoRaWAN, NB-IoT) i prawdziwe czujniki.
- Frakcje w altanach i trasy według frakcji.
- OSRM, ulice jednokierunkowe, okna czasowe.
- Pogoda w prognozie, Holt-Winters lub ML na prawdziwych danych.
- Rozmywanie twarzy i tablic rejestracyjnych.
- Aplikacja kierowcy, konta i role.
- Czat z AI.
- Integracje z systemami MPO i z kalendarzem miasta przez API.
- Cały Kraków, inne sektory, inne miasta.
- Wzorce spamu w czasie, korelacja sąsiednich przycisków.
- Kafelki mapy z własnego serwera lub komercyjnego dostawcy przy większym ruchu (polityka użycia tile.openstreetmap.org).
- Autoryzacja endpointów zegara demo (`/api/clock/*`). Na demo są otwarte, w pilotażu tylko dla dyspozytora.
- Prawdziwe opróżnienia od ekipy (etap 5) zamiast harmonogramu z symulacji jako źródło trafności zgłoszeń.
- Profil uczony na prawdziwych odczytach ekip przy opróżnieniu (etap 5) zamiast na historii z symulacji (pilotaż).
- Prognoza świadoma planu tras: przyszłe opróżnienia z harmonogramu w trajektorii.
- Kilka pojazdów na flotę (OR-Tools: wymiar czasu/ładowności) i okna czasowe.
- Paliwo, CO₂ i złotówki z jawnych, konfigurowalnych współczynników na stronie Metodologia (etap 6).
- Dodatkowe kursy poza 6:00/14:00 dla punktów krytycznych (np. wieczorem przy wydarzeniach).
- Stały harmonogram w porównaniu z prawdziwego harmonogramu MPO (`harmonogram_oczyszczania_08_2026.xlsx`, 9 383 koszy):
  dopasowanie koszy OSM do symboli KUL po ulicy (reverse geocoding z cache) i częstotliwość 1–3×/dzień zamiast stałych 2×/dzień.
- Świeże zgłoszenie jako zlecenie interwencji z terminem 2 h (standard MPO dla prac interwencyjnych).
- Program „Przyjaciele Wróżki”: prawdziwy SMS (np. Twilio Verify), odbiór nagród z danymi zwycięzcy, losowanie miesięczne, +5 pkt za zdjęcie od mieszkańca.
- Firmware przycisku LoRaWAN: limit 1 zgłoszenie na 15 min w urządzeniu, sygnał życia i bateria raz na dobę, autotest co 6 h, e-papier.
- Ekran „Zgłoś kosz”: zdjęcie od mieszkańca (upload do `/api/photo` po wysłaniu), zapis komentarza przy zgłoszeniu, status po opróżnieniu z powiadomieniem (Web Push),
  ikony PNG 192/512 obok SVG dla starszych Androidów, Lighthouse w CI.
- E-papier etap 2: firmware LoRaWAN wg `docs/epapier/ETAP2-LORAWAN.md` (downlink 12 B, uplink przycisk/heartbeat, QR i fonty rastrowe na urządzeniu), test w słońcu i mrozie.
- Audyt UX, Fala 2 (poza hackathonem): jeden zestaw tokenów i jedna biblioteka stanów dla panelu i widoku C (B3, D1–D3),
  klastry w panelu (C1), menu per rola (B4), cache `point_states`/tras per wersja danych (A2, I1), `ETag` dla PNG e-papieru (I3).
- PWA kierowcy: czas opróżnienia z telefonu (pole `at` przy wysyłce z kolejki offline; dziś serwer zapisuje chwilę dotarcia),
  logowanie kierowcy i numer pojazdu, kafelki mapy pobierane z góry na cały obszar kursu, odczyt QR kosza zamiast „Jestem”.
