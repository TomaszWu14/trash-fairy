# Wzorce z HugMe do przeniesienia (etap 0, 4.10.2026, ok. 06:40)

Porównanie z HugMe (drugi projekt autora z tego samego HackYeah). **Bierzemy wyłącznie pomysły, nie kod**: zwycięskie
projekty przenoszą prawa, więc wszystko poniżej piszemy w Trash Fairy od nowa, własnymi selektorami i tekstami.
Źródło: klon HugMe tylko do odczytu, materiał r0 z `audit/jury/r0/` i kod Trash Fairy.

Poza zakresem (robią to inni agenci): mapa, lista koszy, kreator zgłoszenia w 3 krokach, przyciski na panelu kosza
(decyzja 1) i wyjaśnienie KPI „Oszczędności wobec planu” z tabelką dzień/miesiąc/rok (decyzja 2). Poniżej są tylko
powiązane z nimi kwestie spójności.

## Co HugMe robi lepiej

| Co HugMe robi lepiej | Czy Trash Fairy to ma | Przenosimy? |
|---|---|---|
| Prezentacja ma dokładnie 10 slajdów, leży w repo (`docs/slajdy/prezentacja.html` → PDF), a `docs/KRYTERIA.md` przypisuje każde kryterium do dowodu | Nie: deck ma 14 slajdów (regulamin: maks. 10), jest artefaktem poza repo | **Tak, teraz (blokuje)** |
| Na telefonie menu pokazuje nazwę bieżącej strony (`.nav-m__cur`), nic nie znika bez słowa | Nie: na ≤ 720 px przełącznik to 5 ikon bez podpisów, a plakietka „Dane demonstracyjne” traci tekst (zostaje sama iskra) | **Tak, teraz** |
| Tekst się zawija (`overflow-wrap`), baza 18 px, nic nie jest ucinane wielokropkiem | Częściowo: baza 16 px, ale 12 px w setkach elementów (kierowca 121, urządzenia 114, dashboard 78), adresy na liście kierowcy ucięte | **Tak, teraz** (punktowo: ekran kierowcy) |
| Jeden łańcuch kosztów w `docs/KOSZTY.md`: koszt jednostkowy → miesiąc → skala regionu, każde założenie nazwane | Częściowo: `/metodologia` liczy wszystko z kodu (lepiej niż dokument), ale cztery kwoty na różnych ekranach nie mają pomostu | **Tak, teraz** (pomost, razem z pracą nad KPI) |
| Raport WCAG z liczbami (`docs/WCAG_RAPORT.md`: 136 widoków, 0 naruszeń) i te liczby w README | Częściowo: README ma axe na 8 ekranach i Lighthouse; `/dostepnosc` mówi „samoocena” bez liczb; r0: axe czysto poza `/api/docs` (1 naruszenie) | **Tak, teraz** |
| Link „Przejdź do treści” pojawia się po pierwszym Tab (`.skip-link:focus`) | Nie: link jest, ale ma `.sr-only` bez stanu fokusu, więc fokus ląduje na niewidocznym punkcie 1×1 | **Tak, teraz** |
| README zaczyna się od „Zobacz: demo · film · prezentacja PDF · opisy zgłoszenia” i plakietki testów CI | Częściowo: demo i kod są; PDF i teksty HackTribe żyją w artefaktach poza repo; plakietki CI brak | **Tak, teraz** |
| Mikrokopia przy wezwaniu: „bez logowania, ok. minuty”; notka prywatności przy formularzu; pusty stan z wezwaniem i czasem | Częściowo: CTA „Zacznij scenariusz demo” bez czasu; przy formularzu zgłoszenia brak zdania o prywatności | **Tak, teraz** (pliki drugiego agenta: przekazać) |
| Dopasowanie bez AI z wyjaśnieniem „dlaczego pasuje” | **Tak**: decyzje regułami, powód kolejności i pominięcia kosza, `/metodologia` | Nie trzeba |
| Automatyczny reset demo po 20 min bez wpisów | **Tak**: 30 min bez akcji (`app/clock.py`), przycisk „Resetuj dane demo” | Nie trzeba (zdanie przy przycisku: patrz wyżej) |
| Pasek wyboru roli bez haseł | **Tak**: przełącznik perspektyw w nagłówku, bez logowania | Nie trzeba |
| Sufit kosztu AI wpisany w kod | **Tak**: `AI_PER_HOUR = 30` w `app/llm.py` | Nie trzeba |
| CI z testami | **Tak** (pytest na PR i main) | Tylko plakietka w README |
| Krój Atkinson Hyperlegible | Nie (Plus Jakarta Sans) | **Nie**: zmiana kroju 12 h przed oddaniem zmienia wygląd i metryki każdego ekranu, a Plus Jakarta jest częścią marki. Czytelność poprawiamy rozmiarem i zawijaniem |
| Tryb wysokiego kontrastu i A+ w tokenach, bez JS | Nie (panel na koszu ma ciemne, wysokokontrastowe tło) | **Nie teraz**: nowy przycisk w nagłówku to dodawanie, nie upraszczanie. Do `ROADMAPA.md` |
| Audyt axe w CI blokujący scalenie | Nie (axe skryptem lokalnie) | Nie teraz: jury tego nie zobaczy |
| Film MP4 generowany skryptem (Playwright, syntezator, napisy) | Częściowo: scenariusz i napisy PL/EN w `docs/video/`, filmu brak | Nie teraz: film jest opcjonalny, maszyna ma mało RAM |

## Wzorce do przeniesienia teraz (do 08:00)

### 1. Prezentacja: 10 slajdów ułożonych według kryteriów (BLOKUJE, nakład M)
- **Co:** scalić 14 slajdów w 10: 1 cover, 2 problem, 3 rozwiązanie (+ idea), 4 demo w terenie (mieszkaniec → panel → kierowca),
  5 dashboard (+ urządzenia), 6 AI w przepływie (reguły decydują, AI opisuje), 7 wyniki (+ skala Krakowa, jeden łańcuch kwot z wzorca 4),
  8 biznes (koszt pilotażu, zwrot), 9 technologia (+ „co prawdziwe, co symulowane”, testy, WCAG), 10 prośba (pilotaż w Dzielnicy I + QR).
  PDF wyeksportować do `docs/` i podlinkować w README (wzorzec 6).
- **Gdzie:** artefakt decku (poza repo), `docs/`, `README.md`.
- **Dlaczego jury to zauważy:** regulamin dopuszcza maks. 10 slajdów; 14 to formalny błąd zgłoszenia.

### 2. Telefon: nic nie znika bez słowa (ODBIERA PUNKTY, nakład S)
- **Co:** w `app/static/ui/app.css` usunąć regułę `.topbar-end .demo-tag span { display: none; }` (linia 45): w pierwszym rzędzie
  jest miejsce (logo ok. 125 px + plakietka ok. 172 px < 358 px). W bloku `@media (max-width: 1100px)` (linia 40) dodać
  `.switcher a[aria-current="page"] span { display: inline; }` i `.switcher a[aria-current="page"] { flex: 2.5; }`:
  aktywna perspektywa ma podpis, pozostałe ikony mają po ok. 52 px.
- **Dlaczego jury to zauważy:** juror skanuje QR telefonem i widzi pięć samych ikon oraz fioletową iskrę zamiast
  „Dane demonstracyjne”. Na telefonie znika więc też wymagane oznaczenie danych syntetycznych.

### 3. Ekran kierowcy: adres się zawija, nie ucina (ODBIERA PUNKTY, nakład S)
- **Co:** `app/static/ui/kierowca.css:29`: w `.k-stop-txt > span` usunąć `white-space: nowrap; overflow: hidden; text-overflow: ellipsis;`
  i zmienić `var(--fs-xs)` na `var(--fs-sm)`. Opcjonalnie, jeśli zostanie czas: `--fs-xs` z 12 na 13 px w `tokens.css` i ponowna sonda (ryzyko ucięć w plakietkach).
- **Dlaczego jury to zauważy:** sonda r0 znalazła 12 uciętych adresów na liście kierowcy w 390 px („okolice ul. Karmelicka · przy…”).
  Adres to informacja, której kierowca szuka, a 12 px w kabinie śmieciarki jest za małe.

### 4. Jeden łańcuch kwot: „Skąd te kwoty” (ODBIERA PUNKTY, nakład S–M, razem z pracą nad KPI oszczędności)
- **Co:** na `/metodologia` jedna tabelka, która łączy cztery kwoty widoczne w aplikacji i README: baza (liczba koszy, okres),
  wartość, wartość na kosz miesięcznie. Kwoty: przegląd „1,5–2,8 mln zł rocznie w skali Krakowa”, dashboard „4 097 zł” (30 dni,
  wobec planu, 222 kosze w danych demo), README „ok. 2 976 zł mniej na miesiąc” (symulacja 60 koszy i 12 altan),
  `/metodologia` „oszczędność pilotażu 2 576 zł/mies.” (50 koszy). Wszystko liczyć w kodzie (`app/methodology.py`), bez wpisywania liczb ręcznie.
  Z KPI na dashboardzie dać link do tej tabelki. Agent od KPI dodaje dzień/miesiąc/rok; tu chodzi tylko o pomost między ekranami.
- **Dlaczego jury to zauważy:** juror widzi na starcie miliony, a na dashboardzie 4 tys. zł. Bez wspólnej jednostki
  (zł na kosz miesięcznie) wygląda to na sprzeczność, a nie na różną skalę.

### 5. Dostępność z liczbami (KOSMETYKA, nakład S)
- **Co:** `app/templates/api_docs.html:18` i `:21`: dodać `tabindex="0"` do `<pre>` (axe: `scrollable-region-focusable`, jedyne naruszenie w r0).
  Potem na `/dostepnosc` (`app/templates/dostepnosc.html`, przy linii 24) dodać jedno zdanie z wynikiem sondy: 16 ekranów, 31 widoków w 1366, 390
  i 1280 px, 0 naruszeń axe WCAG 2.1 A/AA (po poprawce `<pre>`; liczby wziąć z ponownej sondy po przebudowie), brak przewijania w bok także przy powiększeniu 200%, z datą. Do tego widoczny skip-link
  w `app/static/ui/app.css`: `a.sr-only:focus-visible { position: fixed; left: var(--s4); top: var(--s2); width: auto; height: auto;
  clip: auto; padding: var(--s2) var(--s3); background: var(--ink); color: var(--surface); border-radius: var(--r-sm); z-index: 100; }`.
- **Dlaczego jury to zauważy:** WCAG to część „Użyteczności”. Liczba przekonuje bardziej niż słowo „samoocena”, a Tab jako pierwszy
  klawisz to pierwszy test każdego audytora dostępności. Dziś fokus znika na nim w niewidocznym punkcie (`clipped` w każdym ekranie metryki r0).

### 6. README jako drzwi wejściowe (KOSMETYKA, nakład S)
- **Co:** pod linią „Demo / Kod” w `README.md` (linia 6) dopisać: prezentacja PDF (`docs/…pdf`), teksty zgłoszenia, scenariusz
  (`docs/video/SCENARIUSZ.md`), `DEMO.md`. Pod logo dodać plakietkę CI
  `[![Testy](https://github.com/TomaszWu14/trash-fairy/actions/workflows/ci.yml/badge.svg)](…/actions/workflows/ci.yml)`.
- **Dlaczego jury to zauważy:** juror, który otwiera repo, w 5 sekund ma wszystkie materiały i widzi zielone testy (kryterium „Kompletność”).

### 7. Teksty zgodne z decyzją 1 poza plikami drugiego agenta (ODBIERA PUNKTY, nakład S)
- **Co:** `app/templates/ui/404.html:13–16`: zamiast „Wybierz kosz w pobliżu” i przycisku „Kosze w pobliżu” napisać „Zeskanuj kod QR na koszu
  jeszcze raz” i zostawić jeden przycisk „Przegląd”. `app/templates/dostepnosc.html:15`: zgłoszenie bez aparatu działa teraz przyciskiem na panelu kosza,
  nie z listy. `README.md:11` i `:113`, `DEMO.md:10`, `docs/video/SCENARIUSZ.md:19`: „3 kroki”, „mapa i najbliższe kosze”, „Trzy kroki”
  zamienić na „jeden ekran: problem → Wyślij”.
- **Dlaczego jury to zauważy:** po przebudowie strona 404 (stara naklejka QR) i deklaracja dostępności obiecają listę koszy, której już nie ma.

### 8. Mikrokopia z HugMe dla plików drugiego agenta (KOSMETYKA, nakład S, przekazać)
- Pod „Zacznij scenariusz demo” (`start.html`): „6 kroków · ok. 3 min · bez logowania; dane wracają same po 30 min bez akcji”.
- Pod „Wyślij” (`zglos.html`): „Nie pytamy o imię ani telefon. Ze zdjęcia usuwamy dane aparatu (EXIF), adres IP kasujemy po 24 h.”
- Pusty stan „Twoje zgłoszenia” (`zglos_wybor.html`): „Nie masz jeszcze zgłoszeń. Zgłoś problem przy koszu: zeskanuj kod QR na jego panelu.”

### Powiązane z KPI (spójność liczb, nie wzorzec HugMe)
Sparkline'y KPI na dashboardzie kończą się gwałtownym spadkiem, bo ostatni punkt to bieżący, niepełny miesiąc (październik, 3 dni:
koszt 6 954 zł wobec ok. 70 tys. zł, 418 wywozów wobec ok. 5 000). Podpis pod KPI mówi przy tym „Wykresy: pełne miesiące”.
`app/static/ui/dashboard.js:59`: `TF.spark(k.trend)` → `TF.spark(fullMonths({miesiace: d.meta.miesiace, t: k.trend}).t)`
(funkcja `fullMonths` już jest, linia 67). Jeśli ten plik zmienia też agent od KPI oszczędności, trzeba to z nim uzgodnić.
