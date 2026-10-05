# Materiały prezentacyjne (HackTribe)

Jedna komenda buduje prezentację i film z działającej aplikacji:

```bash
pip install -r demo/requirements.txt
python -m playwright install chromium
python demo/build_all.py --base https://trashfairy.twapp.pl          # oba pliki
python demo/build_all.py --base http://127.0.0.1:5050 --tylko pdf    # tylko prezentacja (nie zmienia danych)
```

| Wyjście | Co to |
|---|---|
| `prezentacja_trash-fairy.pdf` | oficjalna prezentacja: dokładnie 10 stron 1920×1080, po polsku, wariant A (tokeny i fonty aplikacji) |
| `demo_trash-fairy.mp4` | film ≤ 2:00, H.264 1920×1080 30 fps, napisy w obrazie i lektor ElevenLabs, bez muzyki (scenariusz: `docs/video/SCENARIUSZ.md`) |
| `podglad/slajd-01.png` … `slajd-10.png` | podgląd każdej strony PDF |
| `podglad/app-*.png` | zrzuty aplikacji użyte na slajdach 1, 6 i 7 |
| `podglad/film-1.png` … `film-6.png` | klatki kontrolne filmu |

Zasady, które skrypt pilnuje sam:
- **Liczby tylko z aplikacji pod `--base`:** `/metodologia` (porównanie 4 tygodni, skala Krakowa po stawce za odbiór, pilotaż)
  i `/api/dashboard/kpi` (oszczędności wobec planu). Gdy liczby nie ma albo stawki się nie zgadzają, skrypt kończy się błędem.
- PDF ma dokładnie 10 stron (`pypdf`), każdy slajd ≤ 40 słów i nic nie wychodzi poza slajd ani na stopkę.
- Film: każdy krok scenariusza ma asercję (numer zgłoszenia, „Opróżniono”, „Zrealizowane”, punkty), ładowanie stron jest wycięte,
  całość ≤ 120 s (`ffmpeg -i`). **Film zmienia dane demo:** przed nagraniem i po nim skrypt woła `POST /api/demo/reset`.
- **Lektor:** `ELEVENLABS_API_KEY` (i opcjonalnie `ELEVENLABS_VOICE_ID`) w zmiennych środowiska albo w `.env`; zapytania idą
  przez `urllib` (bez nowych zależności). Bez klucza film jest bez dźwięku, a log mówi to wprost. Przed nagraniem
  na produkcji odczekaj ok. 20 s po `scripts/e2e_demo.py` (reset ma blokadę 20 s; skrypt sam ponawia po HTTP 429).
- ffmpeg pochodzi z pakietu `imageio-ffmpeg` (w systemie go nie ma). Napisy są nakładką HTML w nagrywanej stronie, bo fonty
  aplikacji to woff2 dzielone na zakresy, a `drawtext` nie składa z nich polskich znaków.

## Pełny film (6–8 min, spokojne tempo)

```bash
python demo/build_all.py --tylko pdf            # raz: slajdy do podglad/slajd-NN.png
python demo/film_pelny.py --lektor              # lista brakujących nagrań lektora (demo/lektor_pelny/<klucz>.mp3)
python demo/film_pelny.py                       # demo_trash-fairy_pelne.mp4 + rozdzialy.txt (serwer na 127.0.0.1:5050)
```

Slajdy 1–5 → scenariusz 1 (kod QR), 2 (przycisk na panelu), 3 (dzikie wysypisko) → slajdy 8–10. Bez przyspieszania: kursor
dojeżdża do przycisku, kroki idą przyciskiem „Dalej” z paska scenariusza, napis trwa co najmniej 4 s. Teksty lektora są w
`TEKSTY` w `film_pelny.py`; nagrania robi łącznik ElevenLabs (głos „Piotr Dokumentalny”). `rozdzialy.txt` to znaczniki czasu do opisu filmu.

`animacja/` — próba ujęcia AI (obraz z ElevenLabs + najazd kamery ffmpeg); wideo AI wymaga płatnego planu ElevenLabs.

## Film 3 min (do wysyłki)

`python demo/film_3min.py` → `demo_trash-fairy_3min.mp4`: slajdy 1–3, scena AI (skan QR), scenariusz 1, scena AI (przycisk),
scenariusz 3, slajd 9, plansza końcowa. Nowa scena AI = plik w `demo/animacja/` + wpis w `SCENY` (punkt najazdu kamery).
