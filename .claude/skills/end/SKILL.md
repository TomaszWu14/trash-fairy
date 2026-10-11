---
name: end
description: Retrospektywa harnessu na koniec sesji – przegląda przebieg sesji i proponuje MAKSYMALNIE 3 usprawnienia (strażnik w guard.py, wpis w docs/pitfalls, poprawka CLAUDE.md lub agenta), każde z gotową zmianą. Niczego nie wdraża bez zgody.
disable-model-invocation: true
---

# /end – usprawnienia harnessu po sesji

Cel: żeby następna sesja nie powtórzyła błędów tej. Proponujesz, **nie wdrażasz**.

## Krok 1. Zbierz fakty z sesji (nie z pamięci ogólnej)
Przejrzyj przebieg tej rozmowy i stan repo:
- blokady strażnika (`[guard] ...`) i blokady Stop hooka (`[check] ...`) – zasadne czy fałszywe?
- komendy/zmiany cofnięte, poprawiane kilka razy, błędy testów, pomyłki co do API/kodu, poprawki człowieka („nie tak”, „cofnij”);
- `git log origin/main..HEAD --oneline`, `git diff --stat origin/main...HEAD`.

## Krok 2. Wybierz maksymalnie 3 problemy
Tylko problemy, które **realnie wystąpiły w tej sesji** i mogą się powtórzyć. Kolejność wartości:
1. groźna akcja, której strażnik nie zatrzymał (lub fałszywa blokada, która utrudniła pracę) → `.claude/hooks/guard.py` + przypadek w `test_guard.sh`;
2. pułapka w kodzie/środowisku, w którą agent wpadł → punkt w `docs/pitfalls/<obszar>.md` (max 10 punktów na plik – wskaż, który zastępujesz);
3. niejasna/nieaktualna instrukcja → `CLAUDE.md` albo `.claude/agents/*.md`.
Brak takich problemów to poprawny wynik: napisz „Bez propozycji – sesja nie ujawniła luk w harnessie.” i zakończ.

## Krok 3. Format (dla każdej propozycji)
```
### N. <krótki tytuł>
Problem z sesji: co się stało (konkretna komenda/plik/komunikat).
Propozycja: co zmienić i dlaczego to zapobiegnie powtórce.
Zmiana (gotowa do wklejenia):
<plik>
<diff albo pełny nowy fragment>
Test: jak sprawdzić (np. przypadek JSON dla test_guard.sh i oczekiwany exit).
```

## Krok 4. Zatrzymaj się
Zapytaj, które propozycje wdrożyć (numery). Wdrażasz dopiero po wyraźnej zgodzie, potem uruchamiasz
`bash .claude/hooks/test_guard.sh` (gdy zmieniasz strażnika) i pokazujesz wynik.
