# Brainstorm: przycisk dla mieszkańców, awarie, spam, wyświetlacz, program „Przyjaciele Wróżki”

**Jak wypełniać:** pod każdym pytaniem wpisz swoją odpowiedź po `Odpowiedź:`.
**Puste pole = akceptuję propozycję.** Możesz pisać skrótami („tak”, „nie”, „10 zł”, „jak propozycja, ale…”).
Po zapisaniu pliku napisz „gotowe”. Przeczytam odpowiedzi, zaproponuję 2–3 warianty wdrożenia i napiszę spec.

> Kontekst czasu: do oddania (niedziela 11:00) zostało około 17 godzin, a przed nami jeszcze slajdy, nagranie i deploy.
> To trzy podsystemy (sprzęt, ochrona przed spamem, program nagród). Domyślnie robimy pitch i roadmapę oraz lekką wersję w aplikacji.

---

## A. Cel i zakres

**1. Budujemy to teraz w aplikacji czy pokazujemy w pitchu i roadmapie?**
Propozycja: pitch i roadmapa, a w aplikacji tylko lekki program mieszkańca bez pieniędzy (punkty i ranking).
Odpowiedź:budujemy

**2. Główny cel: więcej zgłoszeń czy lepsze zgłoszenia?**
Propozycja: lepsze. Liczy się trafność, a nie liczba naciśnięć.
Odpowiedź:lepsze. Liczy się trafność,

**3. Kto jest użytkownikiem: każdy przechodzień czy zarejestrowany mieszkaniec?**
Propozycja: oba. Przycisk działa anonimowo, a rejestracja jest dobrowolna i daje punkty.
Odpowiedź:ok, zarejestrowani bedą inaczej liczeni i bedą potwierdzać userów niezarejestrowanych,na wyswietlaczy dla niezarejestrowanych moze wyswietlic sie prosba i reklam rejestracji qr

**4. Czy program obejmuje też altany osiedlowe, czyli zgłoszenia mieszkańców bloków?**
Propozycja: tak. Tam mieszkańcy są stali i najbardziej zmotywowani.
Odpowiedź:ok

**5. Miara sukcesu programu?**
Propozycja: wzrost trafności zgłoszeń i spadek godzin przepełnienia. Liczba rejestracji jest drugorzędna.
Odpowiedź:ok

## B. Fizyczny przycisk: sprzęt i awarie

**6. Łączność?**
Propozycja: LoRaWAN (tani, bateria na lata, w Krakowie są bramki). Plan B: NB-IoT.
Odpowiedź:LoRaWAN 

**7. Zasilanie?**
Propozycja: bateria litowa na 3–5 lat plus raport stanu baterii co dobę.
Odpowiedź:ok

**8. Jak wykryć martwy przycisk?**
Propozycja: heartbeat raz na dobę. Brak sygnału przez 48 h daje flagę „sprawdź przycisk”, którą już mamy dla innego przypadku.
Odpowiedź:ok

**9. Wandalizm?**
Propozycja: przycisk zabudowany w obudowie kosza, IP67, bez wystających części, a pod nim naklejka z numerem kosza.
Odpowiedź:ok

**10. Zablokowany, wciśnięty na stałe przycisk?**
Propozycja: „naciśnięcie dłuższe niż 10 s” traktujemy jako usterkę, a nie zgłoszenie.
Odpowiedź: przycisk jest fizyczny czy na monitorze?ma byc chyba na monitorze. co kilka godzin moze byc autocheck przycisku bez wplywu na dane

**11. Zimno i wilgoć?**
Propozycja: klasa temperaturowa od −25°C, przycisk membranowy zamiast mechanicznego.
Odpowiedź: wyswietlacz

**12. Mocowanie i kradzież?**
Propozycja: nity zrywalne i ID urządzenia przypisane do kosza. Przycisk przeniesiony gdzie indziej sam się nie przepisze.
Odpowiedź:ok

**13. Koszt jednego przycisku?**
Propozycja: cel poniżej 150 zł (czujnik zapełnienia to około 800–1500 zł). To liczba na slajd.
Odpowiedź:ok

**14. Kto montuje i serwisuje?**
Propozycja: wykonawca odbioru koszy przy okazji kursu. Według informacji MPO kosze obsługują wykonawcy zewnętrzni.
Odpowiedź:ok

**15. Pilotaż?**
Propozycja: 20 przycisków na Plantach i Kazimierzu przez 3 miesiące, zgodnie z modelem biznesowym z koncepcji.
Odpowiedź:ok

## C. Wyświetlacz

**16. Wyświetlacz na koszu: tak czy nie?**
Propozycja: nie ekran, tylko dioda RGB i naklejka. E-papier w drugiej fazie.
Odpowiedź:nie wiem

**17. Co pokazuje dioda po naciśnięciu?**
Propozycja: fioletowe mignięcie oznacza „zgłoszenie przyjęte”, a ciągły kolor „ekipa już wie”. To ten sam język co wirtualny przycisk.
Odpowiedź: ok

**18. Czy pokazywać godzinę przyjazdu ekipy?**
Propozycja: tak, ale tylko w aplikacji lub po zeskanowaniu QR, a nie na koszu.
Odpowiedź:ok

**19. Kod QR na koszu?**
Propozycja: tak. Prowadzi do `/przycisk/<id>` i daje zapasowe zgłoszenie z telefonu oraz rejestrację w programie.
Odpowiedź:ok

**20. Komunikat na naklejce?**
Propozycja: „PEŁNY? NACIŚNIJ / FULL? PRESS” i drobny dopisek „worki domowe → altana”.
Odpowiedź:ok

**21. Czy dioda pokazuje „już zgłoszono”, żeby ludzie nie naciskali w kółko?**
Propozycja: tak. Po pierwszym zgłoszeniu przez 15 min świeci na stałe, co zmniejsza spam.
Odpowiedź:

## D. Spam i nadużycia

**22. Pierwsza linia obrony?**
Propozycja: to, co już działa: scalanie w 15 minut, wiarygodność przycisku z ostatnich 10 zgłoszeń i flaga przy wiarygodności poniżej 40%.
Odpowiedź:ok

**23. Limit w urządzeniu?**
Propozycja: najwyżej 1 zgłoszenie na 15 minut na przycisk, filtrowane już w firmware, więc oszczędza też baterię.
Odpowiedź:ok

**24. Trolle w stałych godzinach (szkoła 14–16)?**
Propozycja: wykrywanie wzorca czasowego, czyli fałszywe zgłoszenia o podobnej porze tygodnia. Da się to zrobić prostą regułą.
Odpowiedź:ok

**25. Korelacja z sąsiednimi koszami?**
Propozycja: tak. Pojedynczy kosz zgłaszający „pełny” przy pustych sąsiadach w 100 m dostaje niższą wagę.
Odpowiedź:ok

**26. Zgłoszenia z QR, czyli przez internet?**
Propozycja: limit na IP i urządzenie (już jest) plus geolokalizacja w promieniu 150 m od kosza przy zgłoszeniu z telefonu.
Odpowiedź:ok

**27. Czy zarejestrowany użytkownik może spamować dla punktów?**
Propozycja: punkty tylko za zgłoszenie trafne, czyli potwierdzone opróżnieniem przy poziomie co najmniej 75%. Spam nic nie daje.
Odpowiedź:ok

**28. Kara za fałszywe zgłoszenia?**
Propozycja: brak kar finansowych. Spada tylko wiarygodność konta, a przy jej niskim poziomie zgłoszenia ważą mniej.
Odpowiedź:ok

**29. Zmowa, np. sąsiedzi celowo przepełniający kosz dla punktów?**
Propozycja: limit punktów na dzień i na kosz oraz flaga, gdy jeden kosz „karmi” jedną osobę.
Odpowiedź:ok

**30. Fikcyjne konta?**
Propozycja: rejestracja przez numer telefonu (SMS), jedno konto na numer.
Odpowiedź:ok

**31. Zdjęcia jako dowód?**
Propozycja: opcjonalne zdjęcie daje premię. Claude Vision weryfikuje poziom, a reguła rozbieżności o 25 p.p. już istnieje.
Odpowiedź:ok

## E. Program dla mieszkańców: rejestracja

**32. Nazwa programu?**
Propozycja: „Przyjaciele Wróżki” (spójne z marką).
Odpowiedź:ok

**33. Gdzie się rejestrujemy?**
Propozycja: strona `/program` jako PWA w stylu widoku ekipy, bez aplikacji ze sklepu.
Odpowiedź:ok

**34. Jakie dane zbieramy?**
Propozycja: numer telefonu i pseudonim. Bez imienia, nazwiska i adresu (minimalizacja danych, RODO).
Odpowiedź:chyba prawdziwe do rozliczeń

**35. Przypisanie do okolicy?**
Propozycja: opcjonalne „moje kosze”, do 5 ulubionych, z powiadomieniem, gdy zostaną opróżnione.
Odpowiedź:ok

**36. Co widzi mieszkaniec?**
Propozycja: swoje trafne zgłoszenia, punkty, ranking dzielnicy i informację „dzięki Tobie kurs przyspieszono o X h”.
Odpowiedź:ok

**37. Ranking: indywidualny czy dzielnicowy?**
Propozycja: oba, przy czym dzielnicowy na głównym ekranie, bo buduje wspólnotę zamiast rywalizacji.
Odpowiedź:ok

**38. Dostępność?**
Propozycja: seniorzy mogą zgłaszać samym przyciskiem, bez rejestracji, więc program nikogo nie wyklucza.
Odpowiedź:ok

## F. Nagrody i pieniądze

**39. Pieniądze czy nagrody rzeczowe?**
Propozycja: najpierw nagrody bez gotówki: bilety MPK, Karta Krakowska, wejściówki z Karnetu. Gotówka komplikuje podatki i kusi oszustów.
Odpowiedź:ok

**40. Jeśli jednak pieniądze, to w jakiej formie?**
Propozycja: miesięczna pula dla dzielnicy (zieleń lub kosze) z głosowaniem mieszkańców, jak w Budżecie Obywatelskim, zamiast wypłat dla osób.
Odpowiedź:ok

**41. Ile punktów za trafne zgłoszenie?**
Propozycja: 10 punktów, +5 za zdjęcie potwierdzone przez AI, +5 za zgłoszenie altany.
Odpowiedź:ok

**42. Próg nagrody?**
Propozycja: top 10 dzielnicy co miesiąc plus nagroda losowana wśród wszystkich z co najmniej 3 trafnymi zgłoszeniami. Dzięki temu nie wygrywają tylko „zawodowcy”.
Odpowiedź:ok

**43. Budżet programu?**
Propozycja: pokrywa go część oszczędności. Przy −866 wizyt w miesiącu (≈3 tys. zł według naszych założeń) 20% oznacza około 600 zł na nagrody miesięcznie na obszar pilotażu.
Odpowiedź:ok

**44. Kto funduje nagrody?**
Propozycja: MPO z oszczędności oraz partnerzy: MPK (bilety) i KBF/Karnet (wejściówki).
Odpowiedź:ok

**45. Jak ogłaszać zwycięzców?**
Propozycja: tylko pseudonimy, na stronie programu i opt-in w social mediach MPO.
Odpowiedź: ok

**46. Odznaki zamiast punktów?**
Propozycja: tak, jako dodatek: „Strażnik Plant”, „Pogromca worków”. Kosztują zero złotych.
Odpowiedź:ok

## G. Prawo, RODO, ryzyka

**47. Podatek od nagród?**
Propozycja: nagrody rzeczowe do 2 000 zł są zwolnione z PIT jako nagrody w konkursach (art. 21 ust. 1 pkt 68 ustawy o PIT). Przy gotówce trzeba to sprawdzić z prawnikiem MPO. Oznaczone jako ryzyko.
Odpowiedź:ok

**48. RODO?**
Propozycja: administrator: MPO. Numer telefonu szyfrowany, konto usuwane po 12 miesiącach braku aktywności, a eksport i usunięcie danych jednym kliknięciem.
Odpowiedź:ok

**49. Regulamin programu?**
Propozycja: tak, wymagany: zasady punktacji, wykluczenia za nadużycia i brak prawa do nagrody przy zmowie.
Odpowiedź:ok

**50. Największe ryzyko całego pomysłu?**
Propozycja: „gamifikacja śmieci”, czyli ludzie wyrzucający więcej, żeby zgłaszać. Zabezpieczenie: punkty tylko za trafność, limit na kosz i dzień oraz nagrody wspólnotowe zamiast gotówki.
Odpowiedź:ok

---

**Pytania otwarte (opcjonalnie):**
Czego tu brakuje? Co jeszcze chcesz, żeby program robił?
Odpowiedź:nic   
