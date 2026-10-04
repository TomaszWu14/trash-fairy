"""Buduje audit/PRZED-PO.html: zrzuty przed (audit/zrzuty/przed/) i po (audit/zrzuty/po/, scripts/po_shots.py) każdej perspektywy."""
import html
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "audit"
PAIRS = [  # (perspektywa, zrzut przed, zrzut po, co się zmieniło)
    ("Przegląd", "start-pokaz", "przeglad", "Jedna rola bez logowania, pięć perspektyw i losowany scenariusz demo (trzy warianty) zamiast widoku jury z 4 krokami."),
    ("Panel kosza", "epapier-18", "panel-18", "Kiosk 1280×800 czytelny z daleka: kosz-wskaźnik, termin odbioru, „Co tu wrzucać”, kod QR do zgłoszenia."),
    ("Mieszkaniec: wybór kosza", "zglos-wybor", "zglos-wybor", "Skan kodu QR z Panelu kosza i „Twoje zgłoszenia”, bez mapy i listy koszy."),
    ("Mieszkaniec: zgłoszenie", "zglos-18", "zglos-18", "Zgłoszenie na jednym ekranie, tylko z dziennym kodem QR kosza; zdjęcie bez EXIF z weryfikacją AI."),
    ("Kierowca: trasa", "kierowca-zalogowany", "kierowca", "Lista po priorytecie z powodem (liczba zgłoszeń i zapełnienie), postęp kursu, prognoza 85%."),
    ("Kierowca: kosz", None, "kierowca-kosz-18", "Nowy ekran: nawigacja w aplikacji, „Opróżniono” jednym dotknięciem, analiza AI zdjęcia."),
    ("Dashboard miasta", "dyspozytor-zalogowany", "dashboard", "KPI ze zmianą i trendem, koszty vs plan, frakcje, dzielnice, eksport CSV; mapa na żywo jest w panelu dyspozytora."),
    ("Projekt miejski", None, "dashboard-projekt", "Nowy ekran: efekt projektu liczony z historii przed i po starcie."),
    ("Urządzenia", None, "urzadzenia", "Nowy ekran: bateria, status i odczyty paneli i czujników (endpoint IoT POST /api/odczyty)."),
    ("Metodologia", "metodologia", "metodologia", "Założenia z kodu, skala Krakowa, koszt pilotażu i zwrot, rola AI."),
]
VPS = [("desktop", "Desktop 1920×1080"), ("laptop", "Laptop 1366×768"), ("telefon", "Telefon 390×844"), ("kiosk", "Kiosk 1280×800")]


def img(side, vp, name, alt):
    p = ROOT / "zrzuty" / side / vp / f"{name}.png"
    if not name or not p.exists():
        return '<div class="none">Brak zrzutu: ekranu nie było przed przebudową.</div>' if side == "przed" else '<div class="none">Brak zrzutu.</div>'
    rel = p.relative_to(ROOT).as_posix()
    return f'<a href="{rel}"><img src="{rel}" alt="{html.escape(alt)}" loading="lazy"></a>'


sections = []
for vp, vp_label in VPS:
    rows = "".join(
        f'<section class="pair"><h3>{html.escape(title)}</h3><p>{html.escape(note)}</p><div class="cols">'
        f'<figure><figcaption>Przed</figcaption>{img("przed", vp, before, f"{title}, przed, {vp_label}")}</figure>'
        f'<figure><figcaption>Po</figcaption>{img("po", vp, after, f"{title}, po, {vp_label}")}</figure></div></section>'
        for title, before, after, note in PAIRS)
    sections.append(f'<details{" open" if vp == "desktop" else ""}><summary>{vp_label}</summary>{rows}</details>')

(ROOT / "PRZED-PO.html").write_text(f"""<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trash Fairy: przed i po przebudowie</title>
<style>
:root {{ --bg:#F4F5F8; --surface:#fff; --ink:#0D1126; --ink-2:#4A5070; --line:#E3E5EE; --brand:#5B3DF5; --brand-soft:#EEEAFE; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.5 "Plus Jakarta Sans", system-ui, sans-serif; }}
main {{ max-width:1280px; margin:0 auto; padding:32px 16px 64px; }}
h1 {{ font-size:32px; margin:0 0 4px; }} .lead {{ color:var(--ink-2); margin:0 0 24px; max-width:70ch; }}
details {{ background:var(--surface); border:1px solid var(--line); border-radius:16px; margin:0 0 16px; padding:0 20px; }}
summary {{ cursor:pointer; font-weight:700; font-size:18px; padding:16px 0; color:var(--brand); }}
.pair {{ border-top:1px solid var(--line); padding:16px 0 20px; }} .pair h3 {{ margin:0; font-size:18px; }} .pair p {{ margin:4px 0 12px; color:var(--ink-2); }}
.cols {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
figure {{ margin:0; }} figcaption {{ font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:var(--ink-2); margin-bottom:6px; }}
figure:last-child figcaption {{ color:var(--brand); }}
img {{ width:100%; height:auto; display:block; border:1px solid var(--line); border-radius:10px; background:#fff; }}
.none {{ display:grid; place-items:center; min-height:160px; border:1px dashed var(--line); border-radius:10px; color:var(--ink-2); font-size:14px; padding:16px; text-align:center; }}
a:focus-visible, summary:focus-visible {{ outline:3px solid var(--brand); outline-offset:3px; border-radius:6px; }}
@media (max-width:720px) {{ .cols {{ grid-template-columns:1fr; }} }}
</style></head>
<body><main>
<h1>Przed i po przebudowie UI</h1>
<p class="lead">Ta sama aplikacja przed audytem UX (sobota 3.10, wieczór: sześć ekranów, cztery arkusze CSS, logowanie) i po przebudowie
(niedziela 4.10: jeden design system, pięć perspektyw z panelem dyspozytora, dashboard miasta i urządzenia). Kliknij zrzut, żeby otworzyć pełny rozmiar.
Audyt: <code>audit/AUDYT-UX.md</code>, rundy poprawek: <code>audit/iteracje/</code>.</p>
{''.join(sections)}
</main></body></html>
""", encoding="utf-8")
print(ROOT / "PRZED-PO.html")
