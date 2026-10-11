# 03. User flow: mapa ekranów i przejść

**Ról i logowania nie ma** (`app/ui.py:1`, `app/api_pl.py:69`). „Rola” to perspektywa w przełączniku nagłówka (`templates/ui/base.html:29-40`). Tożsamości demo są zaszyte na stałe: „Anna K.”, „Ekipa MPO” (`?ekipa=1`), „trasa K-07”. Logowanie istniało i zostało świadomie usunięte (`DECYZJE.md:340,355`; `/logowanie` przekierowuje 301 na `/`, `views.py:69-79`). Dostępu bronią tylko tokeny: dzienny QR (403 `brak_skanu_qr`) i token panelu (403).

## Diagram 1 — mieszkaniec

```mermaid
flowchart LR
  subgraph S2["2 Panel kosza /panel/id"]
    s2btn["Przepełniony / Inny problem"]
    s2qr["Kod QR z tokenem dnia"]
    s2ack["Potwierdzenie albo błąd"]
  end
  subgraph S3["3 Mieszkaniec /zglos"]
    s3scan["Zeskanuj kod QR"]
    s3wd["Dzikie wysypisko"]
    s3mine["Twoje zgłoszenia"]
  end
  subgraph S3a["3a Modal skanowania"]
    s3sim["Symuluj skan kodu"]
  end
  subgraph S4["4 Formularz /zglos/id"]
    s4qr["Stan kodu: ok / nieaktualny / brak"]
    s4typ["Typ problemu (4)"]
    s4err["Komunikat błędu"]
    s4send["Wyślij"]
  end
  subgraph S4a["4a Sukces TF-nr"]
    s4track["Śledź status"]
  end
  subgraph S5["5 Status /zgloszenie/nr"]
    s5tl["Oś czasu, dowód odbioru"]
  end
  subgraph S6["6 Wysypisko /wysypisko"]
    s6map["Mapa i pinezka"]
    s6err["Komunikat błędu"]
    s6send["Wyślij"]
  end
  subgraph S7["7 Status /wysypisko/nr"]
    s7st["Status i opis AI"]
  end
  s2btn -->|"POST przycisk"| s2ack
  s2qr -->|"skan"| S4
  s3scan --> S3a
  s3sim -->|"link z tokenem"| S4
  s3wd --> S6
  s3mine -->|"TF-"| S5
  s3mine -->|"WD-"| S7
  s4send -->|"201"| S4a
  s4send -->|"400 / 403 / 429"| s4err
  s4qr -->|"Skanuj"| S3
  s4track --> S5
  s6send -->|"201, Śledź status"| S7
  s6send -->|"400 / 429"| s6err
```

## Diagram 2 — kierowca i dyspozytor

```mermaid
flowchart LR
  subgraph S8["8 Kierowca /kierowca"]
    s8list["Lista po priorytecie"]
    s8map["Mapa z pinezkami"]
  end
  subgraph S9["9 Karta kosza /kierowca/kosz/id"]
    s9go["Jadę"]
    s9lvl["Ile było w koszu 0-100"]
    s9ok["Opróżniono"]
    s9pr["Problem"]
    s9toast["Toast błędu"]
  end
  subgraph S9a["9a Modal Jaki problem"]
    s9kinds["5 rodzajów"]
    s9wd["Dzikie wysypisko w pobliżu"]
  end
  subgraph S9b["9b Opróżniono"]
    s9next["Następny kosz / Wróć do trasy"]
  end
  subgraph S7e["7 Wysypisko w trybie ekipy"]
    s7clear["Oznacz jako uprzątnięte"]
  end
  subgraph S10["10 Dyspozytor /dyspozytor"]
    s10urg["Pilne: Dodaj do kursu / Cofnij"]
    s10feed["Zgłoszenia na żywo"]
    s10map["Mapa"]
  end
  s8list -->|"klik"| S9
  s8map -->|"pinezka"| S9
  s9ok -->|"201"| S9b
  s9ok -->|"błąd / brak zdjęcia"| s9toast
  s9pr --> S9a
  s9kinds -->|"POST problem, toast"| S9
  s9wd -->|"formularz ekipy, potem status"| S7e
  s9next --> S9
  s9next --> S8
  s10urg -->|"kosz na górę listy"| S8
  s10feed -->|"Pokaż na mapie"| s10map
```

## Diagram 3 — miasto, strony publiczne, scenariusz demo

```mermaid
flowchart LR
  subgraph S1["1 Przegląd /"]
    s1cta["Zacznij scenariusz"]
    s1reset["Resetuj dane demo"]
  end
  subgraph S1a["1a Modal scenariusza"]
    s1go["Wariant A / B / C, Zacznij"]
  end
  subgraph S1c["1c Pasek scenariusza"]
    s1next["Dalej / Wstecz / Zakończ"]
  end
  subgraph S11["11 Dashboard /dashboard"]
    s11f["Filtry: okres, dzielnica, frakcja, projekt"]
    s11csv["CSV"]
    s11det["Szczegóły"]
    s11proj["Karty projektów"]
  end
  subgraph S11a["11a Modal Szczegóły"]
    s11tbl["Tabela"]
  end
  subgraph S12["12 Urządzenia"]
    s12card["Karta urządzenia, modal"]
  end
  subgraph S13["13 Projekt"]
    s13back["Wróć do dashboardu"]
  end
  subgraph PUB["14-17 Metodologia, API, Dostępność, Prywatność"]
    p14["Strony informacyjne"]
  end
  s1cta --> S1a
  s1go -->|"krok 0: panel albo wysypisko"| S1c
  s1reset -->|"modal, toast, przeładowanie"| S1
  s11f -->|"stan w URL"| S11
  s11det --> S11a
  s11proj --> S13
  s13back --> S11
  S11 -->|"zakładka"| S12
  S1 -->|"stopka"| PUB
```

## Tabela ekranów

| Nr | Ekran | Elementy | Akcja użytkownika | Prowadzi do |
|---|---|---|---|---|
| 1 | Przegląd `/` | 3 liczby, „Zacznij scenariusz”, 4 kafle perspektyw, „Resetuj dane demo” | Zacznij / kafel / Reset | 1a, 2, 3, 8, 11, 1b |
| 1a | Modal scenariusza | wariant A/B/C, Losuj ponownie, Zacznij | Zacznij / X / Esc | A, B → 2; C → 6; zamknięcie → 1 |
| 1b | Modal resetu | Anuluj, Przywróć dane | Przywróć | toast i przeładowanie; 429 → toast błędu |
| 1c | Pasek scenariusza (każda strona) | krok i z N, Wstecz, Dalej, X | Dalej / Zakończ / X | kolejny krok / 1 / ukrycie |
| 2 | Panel kosza `/panel/<id>` | poziom, prognoza, najbliższy odbiór, QR, Przepełniony / Inny problem | przycisk; skan QR | komunikat 10 s; 4 |
| 3 | Mieszkaniec `/zglos` | Zeskanuj QR, Dzikie wysypisko, Twoje zgłoszenia (localStorage), punkty | Skanuj / wysypisko / wiersz | 3a, 6, 5, 7 |
| 3a | Modal skanu | wizjer, Symuluj skan, Losuj inny | Symuluj | 4 z tokenem |
| 4 | Formularz `/zglos/<id>?qr=` | stan kodu QR, 4 typy, komentarz, zdjęcie, błąd, Wyślij z powodem blokady | Wyślij | 4a; błąd 400/403/429 w alercie; brak kodu → 3 |
| 4a | Sukces | numer TF-, punkty, Śledź status, Wróć | linki | 5, 2/3, 1 |
| 5 | Status `/zgloszenie/<nr>` | oś czasu 3 kroki, dowód odbioru, AI | wstecz | 3; nieznany numer → karta z linkiem do 3 |
| 6 | Wysypisko `/wysypisko` | mapa, GPS, rodzaje, ilość, zdjęcie, Wyślij | Wyślij | 6a; błąd 400/429 w alercie; błąd GPS opisany |
| 6a | Sukces WD- | numer, status, Śledź | link | 7 |
| 7 | Status `/wysypisko/<nr>` | status, fakty, zdjęcie; w trybie ekipy „Uprzątnięte” | Uprzątnięte | toast; 409, gdy już uprzątnięte |
| 8 | Kierowca `/kierowca` | postęp kursu, mapa, lista po priorytecie, pominięte z powodem | wiersz / pinezka | 9 |
| 9 | Karta kosza | mapa, stan, zgłoszenia + AI, poziom 0–100, zdjęcie, Jadę / Opróżniono / Problem | Jadę / Opróżniono / Problem | toast; 9b; 9a |
| 9a | Modal problemu | 5 rodzajów, link do wysypiska | rodzaj / link | toast; 6 w trybie ekipy |
| 9b | Opróżniono | podsumowanie, dowód, następny kosz | klik | 9 / 8 / krok scenariusza |
| 10 | Dyspozytor `/dyspozytor` | mapa, KPI, Pilne / Ekipy i trasy / Zgłoszenia | Dodaj do kursu / Cofnij / Pokaż na mapie | toast; kosz na górze w 8 |
| 11 | Dashboard `/dashboard` | filtry, 9 KPI, wykresy, rekomendacje, kolejka napraw, projekty, 3 CSV, Drukuj PDF | filtr / Szczegóły / projekt / CSV / druk | 11 (URL), 11a, 13, plik |
| 11a | Modal Szczegóły | tabela danych | X / Esc | 11 |
| 12 | Urządzenia | filtry, karty, modal z danymi urządzenia | karta | 12a → 2 |
| 13 | Projekt `/dashboard/projekty/<slug>` | fakty, 5 wykresów przed i po | wstecz (filtry zachowane) | 11 |
| 14–17 | Metodologia, Otwarte API, Dostępność, Prywatność | tekst, tabele, linki | linki | 11, JSON/CSV |
| 18 | 404 / 413 / 500 | komunikat, Przegląd, Twoje zgłoszenia | klik | 1, 3 |

Scenariusze demo (`app.js:159-179`):
- **A:** 2 → 4 → 2 → 10 → 8 → 9 → 5 → 11
- **B:** 2 (przycisk) → 10 → 8 → 9 → 2 → 11
- **C:** 6 → 7 → 10 → 7 (ekipa) → 3

## Ścieżki ślepe i akcje bez informacji zwrotnej

1. ~~**Projekt, który nie istnieje.**~~ *Naprawione 11.10.2026.* `projekt.js:23` czeka na kod `projekt_nie_istnieje`, a API zwraca `nieznany_projekt` (`dashboard_api.py:468`). Karta „Nie ma takiego projektu” nigdy się nie pokazuje: jest toast, a szkielety ładowania wiszą bez końca. *(potwierdzone)*
2. ~~**Pierwsze ładowanie nie ponawia się po błędzie.**~~ *Naprawione: `TF.watch` odświeża co ok. 30 s.* `TF.watch` przy błędzie tylko woła `onState(false)` (`app.js:107`). Kierowca, karta kosza, dyspozytor i dashboard zostają w stanie błędu bez przycisku „Spróbuj ponownie”. Ponowienie mają tylko Urządzenia (`urzadzenia.js:172-176`).
3. ~~**Statusy zgłoszeń obsługują wyłącznie 404.**~~ *Naprawione: komunikat przy innym błędzie.* Na innym błędzie oba ekrany statusu milczą (`mieszkaniec.js:187`, `wysypisko.js:197-199`). Do tego `/zgloszenie` odpytuje dalej nawet po „nie znaleziono”.
4. ~~**Dashboard przy sprzecznych filtrach**~~ *Naprawione: nieaktualne liczby wyszarzone.* pokazuje toast, ale zostawia stare liczby pod nowymi filtrami w URL (`dashboard.js:27-35,354`).
5. ~~**Eksport CSV przy błędnym filtrze**~~ *Naprawione: eksport wyłączony do czasu poprawnego filtra.* pobiera plik z JSON-em błędu zamiast danych (`dashboard.html:20-22`).
6. **Dyspozytor nie może przejść do szczegółów.** Brak przejścia do zgłoszenia TF- ani do wysypiska WD- i brak akcji na wysypiskach, choć ekran sukcesu obiecuje „trafia do dyspozytora” (`wysypisko.js:146`).
7. **„Skanuj” na formularzu bez kodu gubi kosz.** Symulowany skan losuje inny kosz (`zglos.html:23`, `mieszkaniec.js:31-35`).
8. **OSRM niedostępny.** Trasa rysuje się linią prostą bez informacji dla użytkownika (`kierowca.js:181`).

Prawdziwego ekranu bez wyjścia nie ma. Pełnoekranowy panel ma link „Przegląd” w rogu (`kiosk.html:16`).

---
