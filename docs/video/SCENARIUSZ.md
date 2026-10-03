# Nagranie 2:00: scenariusz (decyzje 44–45)

Lektor po polsku (głos autora), napisy EN wtopione w obraz (`en.srt`), `pl.srt` dla wersji z napisami PL.
Tekst czyta się w tempie ok. 2 słów na sekundę; każdy blok mieści się w swoim oknie czasu z zapasem na pauzę.

## Przygotowanie (przed nagraniem)

1. Produkcja po Redeployu: `python scripts/smoke.py https://trashfairy.twapp.pl` przechodzi.
2. Demo w stanie startowym (sobota 13:30): zaloguj się jako `dyspozytor` i kliknij „Zacznij od nowa” na `/telefony`
   albo odczekaj 30 min bez akcji (auto-reset).
3. Wyloguj się i zaloguj jako `driver_bin`: ramka kierowcy na `/telefony` zapisuje wtedy naprawdę (bez `?podglad=1` w sesji).
4. Okno przeglądarki 1920×1080, zoom 100%, bez zakładek i rozszerzeń w kadrze. Karta widoczna (schowana usypia timery).

## Tekst słowo w słowo

| Czas | Obraz | PL (lektor) | EN (napisy) |
|---|---|---|---|
| 0:00–0:15 | Slajd 2 „Problem” albo zdjęcie Floriańskiej, potem mapa na `/` | Na Floriańskiej każdy kosz opróżnia się trzy razy dziennie, pełny czy pusty. W Krakowie 9 383 kosze opróżnia się według kalendarza, a przepełnione altany osiedlowe wypychają worki na ulicę. | On Floriańska Street every bin is emptied three times a day, full or empty. Kraków's 9,383 street bins run on a calendar, and overflowing estate shelters push household bags onto the street. |
| 0:15–0:50 | `/`: krok 1 → krok 2 → krok 3 (trasa na mapie), kursor na „Najbliższe przepełnienia” | Trash Fairy to mózg dla MPO, który nie potrzebuje czujników. Zbiera tanie sygnały: przycisk na koszu, zgłoszenia z telefonu i dane od kierowców. Krok pierwszy: co jest przepełnione teraz. Krok drugi: kiedy kosz przekroczy 85%, z wydarzeniami z Karnetu i pogodą. Krok trzeci: trasa na jutro rano, kilkadziesiąt przystanków po prawdziwych ulicach. Decyzje podejmują jawne reguły w kodzie. AI tylko opisuje. | Trash Fairy is a brain for MPO that needs no sensors. It collects cheap signals: a button on the bin, reports from phones and data from drivers. Step one: what is overflowing right now. Step two: when each bin will cross 85%, with city events and the weather. Step three: tomorrow morning's route, dozens of stops on real streets. Decisions are explicit rules in code. AI only describes. |
| 0:50–1:25 | `/telefony`: klik „Pełny” w ramce mieszkańca → e-papier „Zgłoszono” → „Przewiń +1 h” → e-papier „Ekipa w drodze” → w ramce kierowcy przystanek kosza 18 → „Opróżniony” | Teraz jeden kosz, numer 18, na trzech urządzeniach. Mieszkaniec skanuje QR i klika „Pełny”. Po dwóch sekundach kosz pokazuje „Zgłoszono”. Przewijam czas o godzinę: kosz trafia na trasę, a e-papier pokazuje „Ekipa w drodze”. Kierowca klika „Opróżniony” i zgłoszenie się zamyka. Punkty w programie mieszkańców są tylko za trafne zgłoszenia. | Now one bin, number 18, on three devices. A resident scans the QR code and taps "Full". Two seconds later the bin shows "Reported". I move the clock one hour: the bin joins the route and the e-paper says "Crew on the way". The driver taps "Emptied" and the report is closed. Residents earn points only for reports that prove right. |
| 1:25–1:45 | `/`: krok 4 „Efekt”, potem `/metodologia#krakow` | W czterech tygodniach symulacji puste przyjazdy spadają z 57 do 27 procent, a przepełnione altany z 338 godzin do zera. Dla całego Krakowa to od 1,5 do 2,8 mln zł rocznie. | Over four simulated weeks, empty trips drop from 57 to 27 percent, and shelter overflow from 338 hours to zero. Across Kraków: PLN 1.5 to 2.8 million a year. |
| 1:45–2:00 | Slajd 1 z logo i QR | Kod otwarty, dane syntetyczne pokazane wprost, sprzęt tylko tam, gdzie się zwraca. Kraków nie potrzebuje więcej koszy. Potrzebuje wróżki. | Open code, synthetic data stated plainly, hardware only where it pays off. Kraków doesn't need more bins. It needs a fairy. |

## Liczby w tekście i ich źródło

57% → 27% i 338 h → 0 h: karta 4 „Efekt” (`comparison.compare`); 1,5–2,8 mln zł: `methodology.city_scale` (strona `/metodologia#krakow`);
9 383 kosze i Floriańska 3× dziennie: harmonogram MPO 08/2026 (`docs/kontekst-mpo.md`). Liczba przystanków zależy od stanu demo,
dlatego lektor mówi „kilkadziesiąt”.
