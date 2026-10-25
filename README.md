<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/logo/trash-fairy-logo-ciemne.jpg">
    <img src="docs/logo/trash-fairy-logo-jasne.jpg" alt="Trash Fairy" width="440">
  </picture>
</h1>

<p align="center">
  <a href="https://github.com/TomaszWu14/trash-fairy/actions/workflows/ci.yml"><img src="https://github.com/TomaszWu14/trash-fairy/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <a href="https://github.com/TomaszWu14/trash-fairy/actions/workflows/security.yml"><img src="https://github.com/TomaszWu14/trash-fairy/actions/workflows/security.yml/badge.svg?branch=main" alt="Security"></a>
  <img src="https://img.shields.io/badge/python-3.12-3776AB?logo=python&amp;logoColor=white" alt="Python 3.12">
  <a href="LICENSE"><img src="https://img.shields.io/badge/licencja-AGPL--3.0-blue" alt="Licencja AGPL-3.0"></a>
  <img src="https://img.shields.io/badge/HackYeah-2026-orange" alt="HackYeah 2026">
</p>

<p align="center"><b>▶ Zobacz demo: <a href="https://trashfairy.twapp.pl">https://trashfairy.twapp.pl</a></b><br>(przy wejściu demo poprosi o imię, nazwisko i firmę)</p>

**Planowanie odbioru koszy ulicznych według zapełnienia, a nie stałego harmonogramu: dla operatora odbioru odpadów, jego dyspozytorów i kierowców oraz mieszkańców, którzy zgłaszają przepełnione kosze.**

<p align="center"><img src="docs/screenshots/demo.gif" width="360" alt="Zgłoszenie z telefonu: panel kosza z kodem QR, wybór „Przepełniony”, wysłanie i status zgłoszenia"></p>

📹 **[Prezentacja działania z lektorem — YouTube](https://youtu.be/mQma-SUte-s)** · pliki w repo: [3 min](demo/demo_trash-fairy_3min.mp4), [8 min](demo/demo_trash-fairy_pelne.mp4)

🇬🇧 [English version below](#english) · **Demo:** https://trashfairy.twapp.pl. Bez logowania (tylko krótkie przedstawienie się), na danych demonstracyjnych. Przycisk „Resetuj dane demo” przywraca stan wyjściowy.

## Problem → rozwiązanie

Kosze w centrum miasta są opróżniane według stałego planu. W symulacji 57% przyjazdów trafia na kosz zapełniony poniżej połowy, a mimo to kosze przepełniają się w weekendy i przy wydarzeniach.
Trash Fairy zbiera tanie sygnały (przycisk i dzienny kod QR na koszu, poziom zastany przez kierowcę), prognozuje godzinę zapełnienia i wybiera na kurs tylko te kosze, które nie doczekają następnego kursu.
Decyzje podejmują jawne reguły w kodzie, a AI tylko opisuje zdjęcia.
Wynik w symulacji 4 tygodni na tym samym przebiegu zapełniania:
- puste przyjazdy spadają z 57% do 27%;
- odbiorów koszy jest o 24% mniej;
- altany nie przepełniają się wcale (338 h → 0 h).

## Dokumentacja analityczna

| Dokument | Co zawiera |
|---|---|
| [01. Problem i zakres](docs/01-problem-i-zakres.md) | problem z liczbami, interesariusze, miary sukcesu, co w zakresie i co świadomie poza nim |
| [02. Proces](docs/02-proces.md) | proces przed i po (diagramy), aktorzy, 9 punktów decyzyjnych z regułami |
| [03. User flow](docs/03-user-flow.md) | mapa 18 ekranów i 6 modali z przejściami (3 diagramy według ról), tabela ekranów, ślepe ścieżki |
| [04. Model danych](docs/04-model-danych.md) | diagram ER, encje, reguły integralności: co pilnuje baza, a co kod |
| [05. Wymagania](docs/05-wymagania.md) | 38 wymagań z kryteriami akceptacji, każde z miejscem w kodzie i testem |
| [06. Decyzje](docs/06-decyzje.md) | 10 kluczowych decyzji: kontekst, opcje, wybór, skutki |
| [07. Ograniczenia](docs/07-ograniczenia.md) | czego nie ma i dlaczego, znane problemy z plikiem i linią, rozbieżności dokumentacji, warunki pilotażu |

Materiały źródłowe:
- [`docs/KONCEPCJA.md`](docs/KONCEPCJA.md): koncepcja sprzed pisania kodu;
- [`docs/kontekst-mpo.md`](docs/kontekst-mpo.md): jak działa odbiór dziś;
- [`DECYZJE.md`](DECYZJE.md): pełny chronologiczny dziennik decyzji;
- [`ROADMAPA.md`](ROADMAPA.md): plan pilotażu;
- `/metodologia` w aplikacji: wszystkie założenia i progi, czytane wprost z kodu.

## Jak uruchomić

Komendy sprawdzone od zera na świeżym klonie (Windows 11, Python 3.13, Docker 28).

**Docker (aplikacja + PostgreSQL 16):**
```bash
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") docker compose up --build   # http://localhost:8080
```
`SECRET_KEY` podpisuje dzienne kody QR i tokeny urządzeń. Poza SQLite aplikacja nie wystartuje bez własnego klucza, bo domyślny jest jawny w kodzie.
Bramka odwiedzających (przedstawienie się przed wejściem do demo) jest domyślnie włączona; `DEMO_VISITOR_GATE=0` ją wyłącza.
Przepustka z portfolio: gość, który przedstawił się w https://portfolio.twapp.pl (ciasteczko `gosc` na `.twapp.pl`), nie widzi formularza; backend pyta `GET {PORTFOLIO_URL}/api/gosc` (timeout 2 s, tylko kod 200 się liczy, błąd = formularz). `PORTFOLIO_URL` (domyślnie `https://portfolio.twapp.pl`, wymagany `https://`), `PORTFOLIO_PASS=0` wyłącza sprawdzanie.
Lista osób: ustaw `VISITORS_TOKEN`, potem `/odwiedzajacy?token=…` (`&format=csv` = CSV); bez zmiennej adres zwraca 404.
Powiadomienie push o każdym nowym gościu: `NTFY_URL` (pełny URL tematu ntfy, np. `https://ntfy.sh/<tajny-temat>`) i opcjonalnie `NTFY_TOKEN` (Bearer dla serwera z kontrolą dostępu); bez `NTFY_URL` nic nie jest wysyłane.
`NTFY_WATCH_COMPANIES` (frazy po przecinku, bez wielkości liter i polskich znaków): gość z firmą zawierającą frazę daje pilny push „UWAGA firma z listy”. `NTFY_ENGAGED_VIEWS` (domyślnie 10, `0` = wyłączone): jeden push, gdy gość obejrzy tyle ekranów. Lista `/odwiedzajacy` pokazuje liczbę ekranów, czas wizyty i 3 najczęstsze sekcje.
Pierwszy start trwa ok. 2 minuty, bo aplikacja sama importuje punkty i symuluje 8 tygodni. Dopiero potem `/health` zwraca `ok`.

**Lokalnie (SQLite):**
```bash
python -m venv .venv
.venv\Scripts\activate             # Windows; Git Bash: source .venv/Scripts/activate; Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
flask --app app seed               # punkty z data/*.geojson + 8 tygodni symulacji, ok. 45 s
flask --app app run                # http://localhost:5000; pierwsze wejście na / liczy porównanie (do 20 s)
python -m pytest -q -n auto        # ok. 490 testów, 3–6 min
```
- Na Windows trzymaj klon w krótkiej ścieżce, np. `C:\dev\trash-fairy`. Pakiet `anthropic` ma bardzo długie nazwy plików i bez włączonych długich ścieżek `pip install` kończy się błędem `OSError: No such file or directory`.
- Zmienne środowiskowe są opcjonalne: wzór w [`.env.example`](.env.example), skopiuj go do `.env`. Bez klucza API aplikacja działa w pełni, a zdjęcia dostają status „Do weryfikacji”.

## Stack i dlaczego taki

| Element | Dlaczego |
|---|---|
| **Python 3.12 + Flask** (app factory, blueprinty) | Mała aplikacja z kilkoma ekranami i API. Flask nie narzuca struktury, a OR-Tools i biblioteki danych są w Pythonie. |
| **Jinja + własny CSS, bez builda i CDN** | Jedna komenda uruchamia całość, a demo nie zależy od zewnętrznych serwerów. Biblioteki i fonty leżą w `app/static/vendor` ([06-decyzje.md](docs/06-decyzje.md), D10). |
| **SQLAlchemy: SQLite lokalnie, PostgreSQL na produkcji** | Zero konfiguracji do uruchomienia i testów (każdy test ma własną bazę w pamięci), a produkcja na tym samym modelu. |
| **Google OR-Tools** (VRP z pojemnością) | Trasy dla kilku pojazdów z limitem ładunku, deterministycznie i powtarzalnie w testach (D3). |
| **Leaflet + OpenStreetMap** | Otwarte dane prawdziwych koszy i otwarta mapa, bez klucza i kosztów (D9). |
| **Claude API** (tylko przez `app/llm.py`) | Opis zdjęć i wydarzeń z walidacją schematu. Nie podejmuje decyzji, a błąd API nie zatrzymuje aplikacji (D1, D6). |
| **Gunicorn + Docker** | Jeden kontener plus baza. `/health` sprawdza połączenie z bazą. |
| **pytest + ruff + GitHub Actions** | Ok. 490 testów i lint przy każdym PR. Kluczowe liczby (57% → 27%, −24%) pilnuje test regresji. |

## Zakres i ograniczenia

| Prawdziwe | Symulowane |
|---|---|
| Położenia koszy i altan z OpenStreetMap | Poziomy zapełnienia koszy |
| Publiczny harmonogram oczyszczania 08/2026 | Historia 12 miesięcy, koszty, masy i projekty na dashboardzie |
| Wydarzenia (Karnet Kraków), pogoda (Open-Meteo) | Urządzenia i telemetria |
| Reguły, prognoza i trasy OR-Tools | Położenie mieszkańca w demo |

Świadomie poza zakresem: logowanie i role, czujnik zapełnienia jako wejście do decyzji, rejestracja mieszkańca przez SMS, przyjmowanie zgłoszeń przez Open311.
Kwoty (12 zł za odbiór, 5 zł/km) to założenia do potwierdzenia z przewoźnikiem.
Pełna lista ze znanymi problemami (plik i linia): [07. Ograniczenia](docs/07-ograniczenia.md).

## Bezpieczeństwo

Podatności zgłaszaj prywatnie, zgodnie z [SECURITY.md](SECURITY.md). Każdy PR i push do `main` przechodzi
w CI (`.github/workflows/security.yml`) skan sekretów (gitleaks), SAST (Bandit, Semgrep OWASP Top 10),
audyt zależności (pip-audit) i Trivy (zależności, sekrety, konfiguracja). Aplikacja wysyła nagłówki
bezpieczeństwa na każdej odpowiedzi (`_security_headers` w `app/__init__.py`).

## Dane i licencja

- © OpenStreetMap contributors (ODbL 1.0).
- Harmonogram oczyszczania: [mpo.krakow.pl/czystosc](https://mpo.krakow.pl/czystosc/).
- Wydarzenia: Karnet Kraków (Krakowskie Biuro Festiwalowe).
- Atrybucje bibliotek: [NOTICE](NOTICE).
- Kod na licencji [GNU AGPL-3.0](LICENSE).

Kod powstał z pomocą Claude Code. Każdy etap zaczynał się od planu zaakceptowanego przez autora, a uzasadnienia są w [`DECYZJE.md`](DECYZJE.md).

## Kontekst projektu

Projekt powstał solo na hackathonie **HackYeah 2026** (3–4.10.2026) w zadaniu otwartym **Smart City**: „rozwiąż konkretny problem miasta lub jego mieszkańców, wskaż użytkowników i pokaż, jak rozwiązanie działa w konkretnej sytuacji”. Z obszarów podanych w zadaniu wybrałem zarządzanie odpadami i wykorzystanie danych miejskich do podejmowania decyzji. Treść zadania i regulamin: [`docs/zadanie/`](docs/zadanie/).
Koncepcja powstała przed wydarzeniem ([`docs/KONCEPCJA.md`](docs/KONCEPCJA.md), bez kodu). Rdzeń aplikacji napisałem podczas hackathonu, a po nim (5–6.10) domknąłem podpowiedzi, scenariusze demo i filmy.

**Ocena w pierwszej fazie (komisja zadania, platforma HackTribe):**

| Pomysł i innowacyjność (30%) | Zgodność z kategorią (20%) | Użyteczność (20%) | Design (20%) | Kompletność i gotowość wdrożenia (10%) | Średnia ważona | Średnia wszystkich zespołów |
|---|---|---|---|---|---|---|
| 6,25 | 7,00 | 4,50 | 6,25 | 4,25 | **5,85** | 4,66 |

Najniżej oceniono użyteczność i kompletność wdrożenia.

**Czego się nauczyłem:** zaczynać od jednego głównego przepływu użytkownika, a nie od ekranów, bo najniżej oceniono użyteczność. Ciąć zakres wcześnie i spisywać go jako „poza zakresem”, zanim powstanie kod, którego nikt nie zobaczy. Jawnie oddzielać fakty od założeń, bo liczba z symulacji i kwota z założenia to dwie różne rzeczy.

Materiały z hackathonu:
- [film na YouTube](https://youtu.be/mQma-SUte-s);
- [film 3 min](demo/demo_trash-fairy_3min.mp4);
- [film 8 min](demo/demo_trash-fairy_pelne.mp4);
- [slajdy PDF](demo/prezentacja_trash-fairy.pdf);
- [scenariusz pokazu](DEMO.md);
- [logo, miniatura filmu i logo kanału](docs/logo/).

---

## English

**Trash Fairy plans street-bin pickups by forecast fill level instead of a fixed schedule** — for a waste-collection operator, its dispatchers and drivers, and residents who report overflowing bins.
Built solo at **HackYeah 2026** (3–4 Oct 2026, open *Smart City* track). The UI and the analysis docs are in Polish.

- 📹 Video walkthrough: [YouTube](https://youtu.be/mQma-SUte-s) (Polish voice-over; English subtitle file: [`docs/video/en.srt`](docs/video/en.srt)).
- 🌐 Live demo: https://trashfairy.twapp.pl — no login (the demo asks for your first name, last name and company), demo data, “Resetuj dane demo” restores the initial state.

### Problem → solution

City-centre bins are emptied on a fixed plan. In the simulation 57% of visits hit a bin that is less than half full, yet bins still overflow at weekends and during events.
Trash Fairy collects cheap signals (a button and a daily QR code on the bin, the level found by the driver), forecasts when each bin will be full and puts on a run only the bins that will not last until the next one.
Decisions are explicit rules in code; AI (Claude API) only describes photos. Result of a 4-week simulation on the same fill pattern:

- empty visits drop from 57% to 27%;
- 24% fewer bin pickups;
- shelters (waste enclosures) never overflow (338 h → 0 h).

These numbers are guarded by a regression test.

### How to run

Docker (app + PostgreSQL 16):
```bash
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") docker compose up --build   # http://localhost:8080
```
The first start takes about 2 minutes (it imports the bins and simulates 8 weeks); `/health` returns `ok` afterwards.

Locally (SQLite):
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
flask --app app seed               # bins from data/*.geojson + 8 weeks of simulation, ~45 s
flask --app app run                # http://localhost:5000
python -m pytest -q -n auto        # ~490 tests, 3–6 min
```
Environment variables are optional (template: [`.env.example`](.env.example)). Without an API key the app works fully and photos get the “to be verified” status.

### Stack

Python 3.12 + Flask (app factory, blueprints) · Jinja + plain CSS, no build step and no CDN · SQLAlchemy (SQLite locally and in tests, PostgreSQL in production) · Google OR-Tools (capacitated VRP for several vehicles) · Leaflet + OpenStreetMap · Claude API only through `app/llm.py` (an API error never stops the app) · Gunicorn + Docker · pytest, ruff and security scans (gitleaks, Bandit, Semgrep, pip-audit, Trivy) in GitHub Actions.

### Real vs simulated

Real: bin and shelter locations (OpenStreetMap), the public cleaning schedule, events (Karnet Kraków), weather (Open-Meteo), the rules, forecast and OR-Tools routes.
Simulated: fill levels, 12-month history, costs, devices and telemetry, the resident's position in the demo.
Out of scope on purpose: login and roles, fill sensors as a decision input, SMS sign-up, Open311.

### Documentation (Polish)

[Problem and scope](docs/01-problem-i-zakres.md) · [Process](docs/02-proces.md) · [User flow](docs/03-user-flow.md) · [Data model](docs/04-model-danych.md) · [Requirements](docs/05-wymagania.md) · [Decisions](docs/06-decyzje.md) · [Limitations](docs/07-ograniczenia.md) · [Decision log](DECYZJE.md) · [Pilot roadmap](ROADMAPA.md)

### Hackathon result and lessons

First-round jury score: **5.85 / 10** weighted (all-teams average: 4.66); lowest marks for usability and deployment readiness.
Lessons: start from one main user flow rather than from screens; cut scope early and write down what is out of scope before writing code; keep facts and assumptions clearly apart.

Code licensed under [GNU AGPL-3.0](LICENSE); map data © OpenStreetMap contributors (ODbL 1.0); library attributions in [NOTICE](NOTICE). Written with the help of Claude Code — every stage started from a plan approved by the author.
