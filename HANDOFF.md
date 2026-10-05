# Handoff: stan 5.10.2026 ok. 10:40 (NAJNOWSZY)

- Etap 2c domknięty i wypchnięty: commit `59aab48` na `claude/jury-sym` (BEZ PR — po terminie oddania merge do main tylko na prośbę autora).
- Filmy (NIEZACOMMITOWANE): `demo/film_3min.py` → `demo/demo_trash-fairy_3min.mp4` (3:06, wysłany autorowi, zaakceptowany „jest okej”);
  `demo/film_pelny.py` → `demo_trash-fairy_pelne.mp4` (8:21). Lektor: `demo/lektor_pelny/` (34 mp3) + `demo/lektor/`.
- Sceny AI: `demo/animacja/mieszkanka-qr.png`, `mieszkanka-panel.png` (wpis w `SCENY` w film_3min.py). Autor chce ok. 10 scen
  (kabina śmieciarki z tabletem, pracownik opróżnia kosz, przystanek z przepełnionym koszem, wysypisko przy ROD, ekipa sprząta, kosze w różnych
  miejscach) — ElevenLabs: kredyty 759/10000 i dzienny limit obrazów wyczerpany 5.10; wideo AI wymaga płatnego planu.
- Do decyzji autora: commit filmów/skryptów (demo/ ma duże mp4 — raczej tylko .py, testy, lektor, animacja), PR do main.

# Handoff: sesja „symulacja jury + wariant A” (niedz. 4.10.2026, ok. 09:00)

Termin Trash Fairy: zamrożenie kodu 19:00, ostatni Redeploy 20:00, zgłoszenie w HackTribe przed 23:00 (regulamin Smart City).
Gałąź `claude/jury-sym` (wypchnięta, BEZ PR), commit `1e0c02a` = checkpoint po Etapie 2a. Commity: 24 (budżet przekroczony za zgodą).

## Zrobione
- Etap 0+1: `audit/JURY.md` (wynik wstępny 6,96/10 wg oficjalnych wag 30/20/20/20/10), `audit/PLAN-POPRAWEK.md`, `audit/WZORCE.md`;
  sonda `scripts/jury_check.py <runda> [axe.min.js] [adres] [--budzety]` (r0 w `audit/jury/r0/`, PNG poza repo).
- Decyzje autora (pełna lista: pamięć `decyzje-autora-4-10-rano.md` i DECYZJE.md, ostatnie wpisy): mieszkaniec bez mapy, dzienny token QR
  per kosz, przycisk na panelu, bez geolokalizacji; 12 zł/odbiór; dowód usługi; rekomendacje, podrzucanie, dzikie wysypiska, punkty;
  wariant A (ciemny domyślny + jasny), „Panel kosza” jako symulacja 10,1″; prezentacja scalona do 10 slajdów (artefakt GGR9i57v8ELBsQYtLqshVZ).
- Akceptacja wyglądu: 12/12 ekranów zaakceptowanych (artefakt https://claude.ai/artifact/GNKka6fPDnCykCmFo1Tuem, odpowiedzi w jego bazie
  `akceptacja`); jedyne odstępstwo od zaleceń: ikony stanów „większe i wszędzie, także na mapach”.
- Logo: „kosz ze skrzydełkami” (autor wybrał), pliki `docs/logo/` — `trash-fairy-logo-bajka.jpg` (bajkowy nocny Kraków, najnowsze),
  `*-mapa-*.jpg` (mapa OSM), starsze bez skrzydełek do usunięcia po decyzji autora. Skrypty: scratchpad `logo_bajka.py`, `logo_skrzydla.py`.

## Stan 4.10 ok. 11:00 — KONIEC (autor: „kończ co się da”)
- Produkcja = PR #16 (przetestowany), bez dalszych Redeployów. Film oddany: demo/demo_trash-fairy.mp4 = kopia
  demo/trash-fairy_film_z_lektorem.mp4 (2:14, lektor „Piotr Dokumentalny” z łącznika MCP ElevenLabs, 29 klipów).
- Lektor z plików: demo/lektor/NN.mp3 + teksty.json; `python demo/build_all.py --tylko lektor` listuje brakujące nagrania;
  test demo/test_build_all.py pilnuje stałych tekstów. S2: krok „Dodaj do kursu” poprawiony (klik zakładki Pilne), nie nagrany.
- Etap 2c NIEDOKOŃCZONY, zmiany niezacommitowane (21 plików). Wyniki agentów: scratchpad sesji e68d3b25 `etap2c/r01..r13.txt`
  (r12 = recenzja powitania, r13 = recenzja dyspozytora, 21 uwag); skrypt dokończenia: workflow `etap2c-dokonczenie-wf_2ff2cc7c-102.js`
  (zatrzymany zanim cokolwiek zmienił).

## Stan 4.10 ok. 10:30 — RESTART SESJI (po to, by załadować łącznik „claude.ai ElevenLabs”)
- **PR #16 scalony do main** (commit gałęzi `6216c08`, merge `6a3a58d`, CI zielone, pytest lokalnie 448 passed). Autor ma zrobić
  Redeploy w Coolify → potem `python scripts/e2e_demo.py https://trashfairy.twapp.pl` i PDF z liczbami z produkcji
  (`python demo/build_all.py --base https://trashfairy.twapp.pl --tylko pdf`). Szkic PDF (10 stron) autor już dostał.
- **Workflow Etap 2c `wf_8524202c-ecc` mógł zginąć przy restarcie** (resume działa tylko w tej samej sesji). Stan o 10:25: skończone
  wdrożenia+recenzje+poprawki: bateria/logo, mieszkaniec, materiały; w toku „Poprawki: Powitanie i przewodniki”, „Poprawki: Panel
  dyspozytora”; NIE ruszyła faza „Podpowiedzi — pełne pokrycie” (3 agenty: dyspozytor+dashboard, mieszkaniec+panel+wysypisko+start,
  kierowca+metodologia; wynik do scratchpad `help-<grupa>.json`, scalić do podpowiedzi.json). Wyniki agentów: journal
  `~/.claude/projects/C--Users-tomas-PycharmProjects-trash-fairy/336aa886-f89c-47ba-9ecd-20da3477e3bd/subagents/workflows/wf_8524202c-ecc/journal.jsonl`,
  skrypt: `.../336aa886.../workflows/scripts/etap2c-dyspozytor-podpowiedzi-logo-wf_8524202c-ecc.js` (można uruchomić ponownie tylko fazę Podpowiedzi).
  Po restarcie: `git status` (zmiany po 6216c08 są niezacommitowane), pytest, check_help --scisle, potem drugi PR przed 19:00.
- **FILM (autor: „to podstawa”)**: max 3 min na dwa scenariusze (FILM_MAX_S=180, SCENARIO_S=80 już w demo/build_all.py), LEKTOR męski
  polski z ElevenLabs PRZEZ ŁĄCZNIK MCP „claude.ai ElevenLabs” (autor nie chce klucza API; w .env go nie ma). build_all.py ma klasę
  `Voice` (HTTP API z kluczem) — trzeba dodać tryb plików: wygenerować mp3 narzędziem MCP dla każdego tekstu lektora (CARDS[*][3]
  w build_all.py ~l.757 i wszystkie `take.say(..., spoken=...)` w scenario_1/scenario_2 ~l.559–670: gdy jest `spoken`, czytamy
  `spoken`, inaczej `text`; teksty z liczbami {pct}/{nr}/{wd}/{pts} mają `spoken` bez liczb albo trzeba je ujednolicić), zapisać do
  `demo/lektor/NN.mp3` + `demo/lektor/teksty.json` (tekst → plik), a `Voice.clip(text)` czyta plik i mierzy długość (`duration`).
  Potem `python demo/build_all.py --tylko film` (lokalnie albo `--base https://trashfairy.twapp.pl` po Redeployu), obejrzeć klatki
  `demo/podglad/film-*.png`, wysłać MP4 autorowi (SendUserFile). Stary film bez lektora: demo/demo_trash-fairy.mp4 (09:52).
- Opis do HackTribe „Instructions on how to open project” (bez localhost) autor już dostał.

## Stan 4.10 ok. 09:40 (sesja 336aa886)
- Etap 2b: 5 pakietów ZROBIONYCH z recenzją i poprawkami (wyniki: journal wf_0b1b6482-9dc). Faza podpowiedzi przeniosła się do tej sesji;
  ich częściowe wpisy (92 klucze + przewodniki 13 stron) są już scalone w `app/static/ui/podpowiedzi.json`.
- Szkielet dyspozytora zrobiony ręcznie: trasa `/dyspozytor` (app/ui.py `dispatcher`), szablon-szkielet, pozycja w menu (base.html),
  przekierowanie usunięte z views.REDIRECTS; linki apple-touch-icon + manifest w base.html.
- W toku: workflow Etap 2c `wf_8524202c-ecc` (skrypt w ~/.claude/projects/.../336aa886.../workflows/scripts/): pakiety dyspozytor,
  podpowiedzi (powitanie + propozycje przewodnika, navigator.webdriver je wyłącza, `?powitanie=1` wymusza), mieszkaniec (losowy skan,
  Dziękujemy, J-08/J-30), bateria A + logo, materiały (demo/build_all.py); potem 3 agenty pokrycia podpowiedzi → pliki
  scratchpad `help-<grupa>.json` do scalenia w podpowiedzi.json. Wrapper zrzutów: scratchpad `zrzut.sh` (blokada `zrzut.lock`).

## (archiwum) W toku (workflow Etap 2b, run wf_0b1b6482-9dc)
5 pakietów (kierowca+dowód+`mapa.js`, dashboard, mieszkaniec, wspólne+losowy scenariusz+panel, dokumenty) z recenzją,
potem 3 agenty podpowiedzi zwracają `wpisy` i `przewodniki` do scalenia w `app/static/ui/podpowiedzi.json` (scalić ręcznie!).

## Do zrobienia po Etapie 2b
1. Scalić podpowiedzi do `podpowiedzi.json`; `python scripts/check_help.py --scisle` (przez blokadę przeglądarki).
2. Prośba autora: po zgłoszeniu (zglos.html, sekcja sukcesu) i po wysypisku: „Dziękujemy!” + przycisk powrotu (start / panel kosza).
2b. Prośba autora: karty urządzeń — pasek baterii (mylony z zapełnieniem) → propozycja A (OSTATECZNIE wybrana, nie C): pozioma ikona
   baterii z 5 segmentami (z nóżką), podpis „Bateria”, procent obok (kolor stanu przy < 30%); wiersz „Wymiana za…” zostaje
   (wzór: scratchpad `bateria.py` funkcja `seg`, obraz `bateria-propozycje.png`; pliki urzadzenia.js/.css, tylko tokeny).
2c. Prośba autora: PANEL DYSPOZYTORA zarządzający ekipami (wzór: makieta A02 wariantu A, scratchpad `kierunki/A02.jpg`): nowa perspektywa
   „Dyspozytor” `/dyspozytor` (usunąć przekierowanie w views.REDIRECTS), w menu między Kierowcą a Dashboardem; mapa na cały ekran z
   pinezkami stanów (mapa.js), „gorące obszary” (zgłoszenia 90 dni), podrzucanie i dzikie wysypiska; pływające panele: Pilne (85% ok. HH:MM,
   „Dodaj do kursu” = decyzja człowieka, kosz na górę listy kierowcy, np. record_press source="dispatcher"), Ekipy i trasy (K-07, pojazdy
   z /api/trasa, postęp, punkty ekip), Zgłoszenia na żywo; kafle: zagrożone, przepełnione, km trasy, −% wizyt vs harmonogram.
   Mapę operacyjną przenieść z dashboardu do dyspozytora (w dashboardzie link „Mapa na żywo w panelu dyspozytora”).
2d. Prośba autora: WIĘCEJ PODPOWIEDZI, „żeby nowy użytkownik widział prawie wszystko”: (a) powitanie przy pierwszej wizycie
   (localStorage) = przewodnik po całej aplikacji 5–7 kroków (problem, 5 perspektyw z dyspozytorem, losowy scenariusz, Podpowiedzi,
   „Dane demonstracyjne”, „Jak liczymy”), wywoływalny ponownie z nagłówka; (b) przy pierwszej wizycie na każdej stronie propozycja
   „Pierwszy raz tutaj? Pokaż N kroków” (pamięć odwiedzonych stron); (c) pełne pokrycie data-help także dyspozytor, wysypisko, bateria;
   `scripts/check_help.py --scisle` = 0 braków.
2e. Prośba autora: symulowany skan na `/zglos` zawsze proponuje kosz 18 → losować kosz uliczny z obszaru demo („Symuluj skan kodu
   kosza nr N” + „Losuj inny”); token dzienny wylosowanego kosza podaje serwer w szablonie (jak panel — w demo publiczny), BEZ nowego
   endpointu wydającego tokeny. Pliki: app/ui.py (report_pick), zglos_wybor.html. Produkcja jest na starej wersji (fiolet, PR #15) —
   nowy wygląd po PR + Redeploy; service workery nie cache'ują statyków.
3. Logo OSTATECZNE (autor: „to jest logo”): `docs/logo/trash-fairy-ikona.svg` = ciemny szklany kafel z turkusową obwódką, turkusowy kosz
   ze skrzydełkami, biała gwiazdka; lockup poziomy, napis w 2 wierszach (`trash-fairy-logo.jpg`, skrypt scratchpad `logo_final.py`).
   W aplikacji: `_ui.html` makro `logo()`, `app/static/ui/logo.svg`, favicon, ikony PWA (glif w scratchpad `logo_skrzydla.py`).
4. Weryfikacja: `pytest -q -n 3`, `scripts/e2e_demo.py`, `scripts/jury_check.py r1 <axe>`, axe w obu motywach; JURY.md: oceny końcowe, przed/po,
   10 trudnych pytań, 5 zdań do prezentacji.
5. Commit + PR (auto-merge) → Redeploy w Coolify (autor) → `scripts/e2e_demo.py https://trashfairy.twapp.pl`.
6. Materiały: slajdy — kwoty po 12 zł (lista miejsc: slajd 6 podpis i notatki, 7 notatki, 8 nagłówek „PLN 1.5–2.8 m” → liczby z prod po Redeployu);
   README/DEMO/SCENARIUSZ: 150 m (DEMO.md:10, :32, README.md:113), „kursów”, nowe zrzuty; teksty HackTribe.

## Materiały prezentacyjne (zatwierdzone przez autora, robić PO zmianach w aplikacji)
- Folder `demo/` + `python demo/build_all.py` (jedna komenda), `demo/requirements.txt` (playwright, pypdf, imageio-ffmpeg — ffmpeg
  NIE ma w systemie; długość przez `ffmpeg -i`). Wyjście: `prezentacja_trash-fairy.pdf` (DOKŁADNIE 10 stron, 16:9 1920×1080,
  HTML → page.pdf printBackground, PL, wariant A: paleta tokenów, Space Grotesk + IBM Plex Sans, ≤ 40 słów/slajd) i `demo_trash-fairy.mp4`
  (≤ 120 s, H.264 1920×1080 30 fps, napisy drawtext, bez muzyki). ZMIANA 4.10 ~09:50 (autor): LEKTOR — męski polski głos z ElevenLabs
  (eleven_multilingual_v2, klucz ELEVENLABS_API_KEY w .env — dopisuje autor, nie czytać/wypisywać; voice_id w ELEVENLABS_VOICE_ID z domyślnym
  męskim głosem z biblioteki), tekst per scena, nagranie dopasowane do długości scen (ffmpeg adelay + amix), bez imitacji prawdziwych osób.
- PDF to oficjalna prezentacja do HackTribe (zamiast decku EN w artefakcie). Struktura: 1 tytuł, 2 problem (71% opróżnień < 75%,
  puste przyjazdy 57%), 3 rozwiązanie w 3 punktach, 4 funkcje 4–6 kafli, 5 przepływ, 6 zrzut dyspozytora z adnotacjami, 7 zrzut
  zgłoszenia/panelu z adnotacjami, 8 architektura, 9 korzyści (57→27%, 338 h→0, −24% odbiorów, skala Krakowa po 12 zł z prod),
  10 roadmapa + kontakt. Po wygenerowaniu: 10 stron (pypdf), każda strona do PNG i obejrzeć.
- Film, plansze: tytuł 3 s → S1 ~55 s → „Scenariusz 2” 2 s → S2 ~55 s → koniec 3 s. Nagrywać Playwright record_video 1920×1080,
  slow_mo 300–500 ms, kółko przy kliknięciu (wstrzyknięty CSS/JS), asercje sukcesu, wyciąć ładowanie; 4–5 klatek obejrzeć.
  S1 „Przepełniony kosz: od zgłoszenia do odbioru”: start → scenariusz (wariant A, kosz 18) → panel 10″ klik QR → Przepełniony →
  Wyślij → Dziękujemy → panel pokazuje → kierowca (kosz na górze) → Jadę → Opróżniono ze zdjęciem → status: zrealizowane,
  potwierdzone zdjęciem, +10 pkt → dashboard.
  S2 „Dzikie wysypisko i decyzje dla miasta”: /zglos → Dzikie wysypisko (ROD Grzegórzki, bio+tworzywa, 20 worków, zdjęcie) → status WD
  → dyspozytor (mapa, gorące obszary, Pilne, „Dodaj do kursu”) → ekipa „Uprzątnięte” → punkty → dashboard: oszczędności dziennie/
  miesiąc/rok i rekomendacje (drabinka do fotopułapki).

## Grabie z tej sesji
- Git Bash zamienia „/404” na ścieżkę Windows → `MSYS_NO_PATHCONV=1` (wrapper scratchpad `zrzut.sh` z blokadą mkdir).
- Fonty w `page.set_content` z `file://` się nie ładują → osadzać base64.
- Ułamkowy zoom Leaflet (14,25) daje szwy kafelków na zrzutach → zoom całkowity.
- Serwer `flask --debug` pada przy równoległych edycjach Pythona → strażnik w tle (pętla curl /health → restart).
- Kilku agentów + jedna baza demo: e2e_demo resetuje dane — uruchamiać tylko na końcu.
