# 02. Proces biznesowy: przed i po

## Aktorzy

| Aktor | Rola w procesie |
|---|---|
| Mieszkaniec | widzi problem przy koszu i go zgłasza |
| Panel na koszu | przycisk „Przepełniony”, ekran e-papierowy z dziennym kodem QR, telemetria |
| System (reguły w kodzie) | łączy zgłoszenia, liczy stan i prognozę, wybiera kosze na kurs, układa trasę |
| Dyspozytor | reaguje na pilne kosze, ręcznie dokłada kosz do kursu |
| Kierowca / ekipa | jedzie trasą, oznacza „Jadę” i „Opróżniono”, zgłasza problemy i wysypiska |
| Miasto / operator | ocenia koszty wobec planu i decyduje o inwestycjach |

## PRZED: stały harmonogram

Źródła: [`kontekst-mpo.md`](kontekst-mpo.md) (organizacja i harmonogram) oraz model bazowy w symulacji
([`app/simulation.py`](../app/simulation.py), [`app/comparison.py`](../app/comparison.py): wszystkie kosze o 6:00 i 14:00, altany co 3 dni).

```mermaid
flowchart TD
  subgraph MI["Mieszkaniec"]
    A1["Widzi przepełniony kosz"] --> A2{"Zgłasza?"}
    A2 -->|"telefon / e-mail"| A3["Zgłoszenie do dyspozytorni"]
    A2 -->|"nie"| A4["Kosz czeka na kurs z harmonogramu"]
    A5["Przepełniona altana: worek do kosza ulicznego"] --> A4
  end
  subgraph DY["Dyspozytornia 24/7"]
    B1["Przyjmuje zgłoszenie"] --> B2["Praca interwencyjna, termin 2 h"]
  end
  subgraph WY["Ekipa / wykonawca"]
    C1["Kurs według stałego harmonogramu"] --> C2["Opróżnia każdy kosz z listy, także pusty"]
    B2 --> C3["Interwencja przy koszu"]
  end
  A3 --> B1
  A4 --> C1
```

Słabe punkty procesu PRZED:
1. **Decyzja o przyjeździe nie zależy od zapełnienia.** W modelu 57% przyjazdów trafia na kosz zapełniony poniżej połowy.
2. **Zgłoszenie jest kosztowne dla mieszkańca** (telefon, e-mail), więc większość przepełnień nie jest zgłaszana.
3. **Brak sprzężenia zwrotnego:** nikt nie zapisuje, ile było w koszu przy opróżnieniu, więc harmonogramu nie da się poprawić danymi.

**Założenie, niezweryfikowane z MPO:** dyspozytornia przekazuje zgłoszenie ekipie lub wykonawcy telefonicznie, a ekipa nie zapisuje
poziomu zastanego w koszu. Opis harmonogramu i dyspozytorni pochodzi z publicznych materiałów MPO. Weryfikacja: rozmowa z dyspozytorem
w tygodniu 0–2 pilotażu ([`ROADMAPA.md`](../ROADMAPA.md)).

## PO: Trash Fairy

```mermaid
flowchart TD
  subgraph M["Mieszkaniec"]
    M1["Skanuje dzienny kod QR na panelu kosza"] --> M2["Formularz: typ, komentarz, zdjęcie"]
    M9["Śledzi status: przyjęte, w realizacji, zrealizowane"]
  end
  subgraph P["Panel na koszu"]
    P1["Przycisk Przepełniony"]
    P3["E-papier pokazuje stan i kod QR"]
  end
  subgraph S["System: reguły w kodzie"]
    S0{"Token QR ważny dziś i limit nieprzekroczony?"}
    S0 -->|"nie"| SX["Odmowa 403 / 429 z komunikatem"]
    S0 -->|"tak"| S1["Scal naciśnięcia w 15 min, waga = wiarygodność"]
    S1 --> S3{"Stan = max(prognoza, sygnał), po antyspamie"}
    S2["Prognoza 7x24 x wydarzenia x pogoda: godzina 85%"] --> S3
    S3 -->|"do opróżnienia / 85% przed kursem / bezpiecznik"| S4["Na kurs"]
    S3 -->|"inaczej"| S5["Pominięty z podanym powodem"]
    S4 --> S6["OR-Tools VRP z pojemnością, kursy 6:00 i 14:00"]
    SA["AI opisuje zdjęcie"] -.-> SB{"Kosz widoczny, stan zgodny, pewność min. 0,7?"}
    SB -->|"tak"| SC["Zweryfikowane AI"]
    SB -->|"nie / błąd"| SD["Do weryfikacji"]
    S7["Rekomendacje z 4 tygodni: kompaktor, większy, rzadziej"]
  end
  subgraph D["Dyspozytor"]
    D1["Pilne, ekipy i trasy, zgłoszenia na żywo"] --> D2{"Dodać do kursu?"}
    D2 -->|"tak"| D3["Kosz pierwszy na trasie, wygasa po 24 h"]
  end
  subgraph K["Kierowca / ekipa"]
    K1["Trasa po priorytecie"] --> K2["Jadę"]
    K2 --> K3["Opróżniono: poziom 0-100, zdjęcie opcjonalne"]
    K3 --> K4{"Poziom min. 75%?"}
    K4 -->|"tak"| K5["Zgłoszenie trafne, punkty dla mieszkańca"]
    K4 -->|"nie"| K6["Zgłoszenie nietrafne, wiarygodność spada"]
  end
  subgraph C["Miasto"]
    C1["Dashboard: koszt vs plan, KPI, CSV"]
    C2["Otwarte API i Open311 tylko do odczytu"]
  end
  M2 --> S0
  P1 --> S1
  M2 -.-> SA
  K3 -.-> SA
  S3 --> P3
  S6 --> D1
  D3 --> S4
  S6 --> K1
  K5 --> M9
  K3 --> S2
  S7 --> C1
  S3 --> C2
```

## Punkty decyzyjne

| # | Decyzja | Kto decyduje | Reguła | Kod |
|---|---|---|---|---|
| 1 | Czy przyjąć zgłoszenie z telefonu? | system | ważny dzienny token QR kosza i limit (1/min na telefon i kosz, 200/h z IP) | `app/api_pl.py:24-50, 140-151` |
| 2 | Nowe zgłoszenie czy dołączenie do istniejącego? | system | naciśnięcia w 15 min od pierwszego tworzą jedno zgłoszenie | `app/reports.py:49-76` |
| 3 | Ile waży zgłoszenie? | system | wiarygodność przycisku (trafne z ostatnich 10, start 70%), osłabienia antyspamowe | `app/reports.py:14-24`, `app/state.py:67-86` |
| 4 | Jaki jest stan kosza? | system | max(prognoza, 100 × waga); „do opróżnienia” > 85% albo świeże silne zgłoszenie | `app/state.py:20-51, 223` |
| 5 | Czy kosz jedzie w tym kursie? | system | stan „do opróżnienia”, albo 85% przed kolejnym kursem, albo bezpiecznik 3/7 dni | `app/routes.py:26-31, 66-75` |
| 6 | Czy dołożyć kosz poza regułą? | dyspozytor | „Dodaj do kursu”: kosz jedzie pierwszy, decyzja wygasa po opróżnieniu lub 24 h | `app/routes.py:34-49, 172-175` |
| 7 | Czy zgłoszenie było trafne? | system na podstawie danych kierowcy | poziom przy opróżnieniu ≥ 75% | `app/reports.py:13, 79-90` |
| 8 | Czy zdjęcie potwierdza zgłoszenie? | system (AI opisuje, reguła ocenia) | kosz widoczny, stan zgodny z typem, pewność ≥ 0,7; AI nigdy nie odrzuca | `app/photos.py:92-121` |
| 9 | Co zmienić w infrastrukturze? | miasto, na podstawie rekomendacji | kompaktor / większy kosz / rzadziej z danych z 4 tygodni | `app/recommendations.py:11-60` |

## Wejścia i wyjścia

| Wejścia | Wyjścia |
|---|---|
| naciśnięcia przycisku, zgłoszenia z QR, zdjęcia | stan i prognoza każdego kosza (z powodem słownym) |
| poziom przy opróżnieniu i zdjęcia od ekipy | trasa na kurs, z listą pominiętych i powodami |
| położenia koszy z OpenStreetMap | status zgłoszenia dla mieszkańca, punkty |
| wydarzenia (Karnet Kraków), pogoda (Open-Meteo), ruch (TomTom) | rekomendacje inwestycyjne, KPI, eksport CSV, otwarte API |
