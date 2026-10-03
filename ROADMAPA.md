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
