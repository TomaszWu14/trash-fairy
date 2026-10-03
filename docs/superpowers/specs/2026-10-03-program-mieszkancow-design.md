# Program „Przyjaciele Wróżki”, ochrona przed spamem i stan urządzeń (wariant A)

Data: 2026-10-03 · Źródło decyzji: `docs/brainstorm-przycisk-program.md` (50 pytań + odpowiedzi) · Status: zatwierdzony.

## Cel
Lepsze zgłoszenia zamiast ich większej liczby. Zarejestrowani mieszkańcy mają własną wiarygodność i potwierdzają
zgłoszenia anonimowe. Punkty dostają tylko za zgłoszenia trafne. Urządzenie (fizyczny przycisk i wyświetlacz e-papierowy)
samo zgłasza swój stan. Ekran dotykowy na ulicy odrzucony: potrzebuje stałego zasilania, gorzej znosi wandalizm
i nie da się go odczytać w słońcu.

## Zakres (wariant A)
1. **Rejestracja `/program`:** pseudonim, telefon (zapisujemy tylko hash z sekretem aplikacji), dzielnica. Kod SMS jest symulowany
   i pokazywany na ekranie z etykietą DEMO. Logowanie przez sesję Flask. Jeden numer to jedno konto.
   Dane osobowe (imię, nazwisko, adres) podaje dopiero zwycięzca przy odbiorze nagrody. W demo tego nie budujemy.
2. **Wiarygodność mieszkańca:** trafne z ostatnich 10 rozstrzygniętych zgłoszeń z jego naciśnięciem, start 80%.
   Waga zgłoszenia = max(wiarygodność przycisku, wiarygodność zarejestrowanych naciskających).
   Naciśnięcie zarejestrowanego dołączone do zgłoszenia zaczętego przez kogoś innego oznacza **potwierdzenie** (`report.confirmed`).
3. **Punkty** przyznawane przy rozstrzygnięciu trafnego zgłoszenia: 10, a za altanę 15. Najwyżej 1 nagroda na mieszkańca, punkt i dzień,
   bez duplikatów na zgłoszenie. Odznaki są liczone z nagród. Ranking osób i dzielnic.
4. **Spam:**
   - korelacja: niepotwierdzone zgłoszenie przy koszach w promieniu 100 m, które według szacunku są poniżej 30%, liczy się ×0,7;
   - wzorzec trolli: co najmniej 3 fałszywe zgłoszenia tego przycisku o tej samej godzinie (±1 h) w 14 dni dają ×0,5;
   - geolokalizacja: zgłoszenie z telefonu z podanym położeniem dalej niż 150 m od kosza jest odrzucane.
     Brak położenia jest akceptowany, przełącznik `REQUIRE_GEO` decyduje, czy położenie jest wymagane (w demo nie jest, bo jury jest daleko).
5. **Urządzenie:** tabela `device` (ostatni sygnał życia, bateria, ostatni autotest). Autotest **nie tworzy** naciśnięć ani zgłoszeń.
   Brak sygnału przez 48 h daje flagę „sprawdź przycisk”. Bateria poniżej 20% trafia do panelu.
6. **Wyświetlacz e-papierowy (makieta)** nad wirtualnym przyciskiem: stan („Zgłoszono 13:24 · ekipa ok. 14:00”).
   Niezarejestrowany widzi zachętę z kodem QR do `/program`.
7. **Panel:** karty „Przyjaciele Wróżki” (ranking) i „Stan urządzeń”. **Regulamin** `/program/regulamin`: punktacja, limity, RODO, nagrody.

## Poza zakresem (ROADMAPA)
Prawdziwy SMS (Twilio), odbiór nagród z danymi osobowymi, losowanie nagród, +5 za zdjęcie od mieszkańca, firmware LoRaWAN.

## Testy
Potwierdzenie podnosi wagę; punkty tylko za trafne i z limitem; wiarygodność mieszkańca; korelacja z sąsiadami; wzorzec trolli;
geolokalizacja; autotest bez zgłoszenia; 48 h bez sygnału daje flagę; jeden numer to jedno konto; telefon zapisany jako hash.
