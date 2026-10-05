"""Materiały na HackTribe jedną komendą: prezentacja PDF (dokładnie 10 stron) i film MP4 (≤ 2:00) z działającej aplikacji.

Użycie:  python demo/build_all.py [--base URL] [--tylko pdf|film]      (domyślnie http://127.0.0.1:5050)
Zależności: pip install -r demo/requirements.txt && python -m playwright install chromium (ffmpeg z imageio-ffmpeg).

Każda liczba na slajdach i w napisach pochodzi z aplikacji pod --base: /api/dashboard/kpi (oszczędności wobec planu,
stawki) i /metodologia (porównanie 4 tygodni, skala Krakowa, pilotaż). Brak liczby = błąd, nie wartość na sztywno.
Film zmienia dane demo: przed nagraniem i po nim resetuje je tym samym API co przycisk „Resetuj dane demo”.
Lektor: ElevenLabs (eleven_multilingual_v2), klucz ELEVENLABS_API_KEY i głos ELEVENLABS_VOICE_ID ze zmiennych środowiska
albo z .env w katalogu repo. Bez klucza film powstaje bez dźwięku (ostrzeżenie w logu).
"""
import argparse
import base64
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "demo"
PREVIEW = OUT / "podglad"
PDF = OUT / "prezentacja_trash-fairy.pdf"
MP4 = OUT / "demo_trash-fairy.mp4"
STATIC = ROOT / "app" / "static"
W, H = 1920, 1080
VW, VH = 1280, 720  # nagrywany ekran: docelowy laptop, w filmie powiększony do 1920×1080 (czytelny w małym odtwarzaczu)
SLIDES = 10
MAX_WORDS = 40
FILM_MAX_S = 180  # autor 4.10 10:20: maks. 3 minuty na dwa scenariusze, z lektorem
SCENARIO_S = 80  # docelowa długość S1 i S2; dłuższy przebieg przyspieszamy, krótszego nie rozciągamy
REPO = "github.com/TomaszWu14/trash-fairy"
PROD = "trashfairy.twapp.pl"


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------- liczby z API
def fetch(base, path):
    with urlopen(Request(base + path, headers={"Accept-Language": "pl"}), timeout=180) as r:
        return r.read().decode("utf-8")


def cells(page):
    """Tekst strony z „ | ” w miejscu znaczników: komórki tabel i liczby nie sklejają się ze sobą."""
    page = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    t = html.unescape(re.sub(r"<[^>]+>", "|", page)).replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s*\|[\s|]*", " | ", re.sub(r"[ \t\r\n]+", " ", t))


def grab(text, pattern, what):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(f"Nie znalazłem liczby „{what}” na /metodologia (wzorzec {pattern!r}). Zmienił się tekst strony?")
    return [g.strip() for g in m.groups()]


def numbers(base):
    met = cells(fetch(base, "/metodologia"))
    n = {}
    n["empty_from"], n["empty_to"] = grab(met, r"(\d+)% → (\d+)%[ |]*pustych przyjazdów", "puste przyjazdy")
    n["shelter_from"], n["shelter_to"], n["weeks"] = grab(
        met, r"([\d ]+) h → ([\d ]+) h[ |]*przepełnień altan śmietnikowych w (\d+) tygodnie", "przepełnienia altan")
    n["pln_min"], n["pln_max"] = grab(met, r"([\d,]+)–([\d,]+) mln zł[ |]*rocznie w skali Krakowa", "skala Krakowa")
    n["visit_cut"], n["km_cut"] = grab(met, r"\((\d+)% mniej odbiorów, (\d+)% mniej km", "spadek odbiorów")
    (n["mpo"],) = grab(met, r"MPO (\d{2}/\d{4})", "data harmonogramu MPO")
    n["odbior_zl"], n["km_zl"] = grab(met, r"Odbiór ([\d,]+) zł, kilometr ([\d,]+) zł", "stawki")
    n["bins_all"], _, _, _ = grab(met, r"Pełny: wszystkie kosze w Krakowie \| ([\d ]+) \| ([\d ]+) \| ([\d ]+) zł \| ([\d,]+) mln zł",
                                  "kosze w Krakowie")
    n["pilot_bins"], n["pilot_where"] = grab(met, r"Koszt pilotażu i zwrot \((\d+) koszy w ([^)|]+)\)", "pilotaż")
    (n["sim_bins"],) = grab(met, r"Kosze uliczne \([^)]*\) \| (\d+)", "kosze w symulacji")
    (n["sim_shelters"],) = grab(met, r"Altany osiedlowe[^|]*\| (\d+)", "altany w symulacji")
    kpi = {k["id"]: k for k in json.loads(fetch(base, "/api/dashboard/kpi"))["kpi"]}
    s = kpi["oszczednosci"]
    rate = s.get("stawki", {}).get("odbior_zl")
    if rate is None or float(rate) != float(n["odbior_zl"].replace(",", ".")):
        raise SystemExit(f"Stawka odbioru różni się: /api/dashboard/kpi {rate} zł, /metodologia {n['odbior_zl']} zł")
    n["month_zl"], n["year_zl"] = pl(s["miesiac"]), pl(s["rok"])
    n["visits_less"], n["crew_h"], n["days"] = pl(s["odbiory_mniej"]), pl(s["godziny_ekip"], 1), pl(s["okres"]["dni"])
    return n


def pl(v, nd=0):
    """Liczba po polsku: spacja nierozdzielająca w tysiącach, przecinek dziesiętny, bez zbędnego „,0”."""
    s = f"{float(v):,.{nd}f}".replace(",", " ").replace(".", ",")
    return s[:-2] if nd == 1 and s.endswith(",0") else s


# ---------------------------------------------------------------- wygląd: tokeny i fonty aplikacji
def b64(path, mime):
    return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def tokens_css():
    """tokens.css z fontami osadzonymi w base64 (fonty przez file:// i set_content się nie ładują)."""
    css = (STATIC / "ui" / "tokens.css").read_text(encoding="utf-8")
    return re.sub(r'url\("\.\./fonts/([^"]+)"\)', lambda m: f'url("{b64(STATIC / "fonts" / m.group(1), "font/woff2")}")', css)


def sprite():
    return (STATIC / "ui" / "icons.svg").read_text(encoding="utf-8").split("-->", 1)[-1].replace("</svg>", "")


def ic(name, cls="ic"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true"><use href="#{name}"/></svg>'


LOGO = ROOT / "docs" / "logo" / "trash-fairy-ikona.svg"

CSS = """
@page { size: 1920px 1080px; margin: 0; }
html, body { margin: 0; background: var(--bg); -webkit-print-color-adjust: exact; print-color-adjust: exact; }
section { width: 1920px; height: 1080px; box-sizing: border-box; padding: 112px 128px 168px; position: relative; overflow: hidden;
  display: flex; flex-direction: column; gap: 56px; color: var(--ink); font-family: var(--font); break-after: page;
  background: radial-gradient(1100px 700px at 92% -8%, var(--brand-soft), transparent 70%), var(--bg); }
section:last-of-type { break-after: auto; }
h1, h2, h3, .big { font-family: var(--font-display); margin: 0; letter-spacing: -.015em; font-weight: 600; }
h2 { font-size: 68px; line-height: 1.08; max-width: 1500px; }
h3 { font-size: 36px; line-height: 1.15; }
p { margin: 0; font-size: 30px; line-height: 1.4; color: var(--ink-2); }
.kicker { font: 600 24px/1 var(--font); color: var(--brand); text-transform: uppercase; letter-spacing: .12em; }
.head { display: flex; flex-direction: column; gap: 20px; }
.body { flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 40px; min-height: 0; }
.ic { width: 44px; height: 44px; fill: none; stroke: currentColor; stroke-width: 1.75; stroke-linecap: round; stroke-linejoin: round; flex: none; }
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 20px; padding: 44px; display: flex; flex-direction: column; gap: 16px; }
.grid { display: grid; gap: 32px; }
.g2 { grid-template-columns: repeat(2, 1fr); } .g3 { grid-template-columns: repeat(3, 1fr); } .g4 { grid-template-columns: repeat(4, 1fr); }
.big { font-size: 104px; line-height: 1; font-variant-numeric: tabular-nums; white-space: nowrap; }
.card.row { flex-direction: row; align-items: baseline; gap: 32px; padding: 36px 44px; }
.big small { font-size: .5em; color: var(--ink-2); }
.to { color: var(--brand); }
.foot { position: absolute; left: 128px; right: 128px; bottom: 56px; display: flex; align-items: center; gap: 16px; font-size: 22px; color: var(--ink-3); }
.foot img { width: 40px; height: 40px; }
.foot b { color: var(--ink-2); font-family: var(--font-display); font-weight: 600; }
.foot .pg { margin-left: auto; font-family: var(--font-display); font-variant-numeric: tabular-nums; }
.note { font-size: 22px; color: var(--ink-3); }
.badge { width: 72px; height: 72px; border-radius: 18px; display: grid; place-items: center; background: var(--brand-soft); color: var(--brand);
  border: 1px solid var(--brand-line); }
.n { font: 600 28px/1 var(--font-display); color: var(--on-brand); background: var(--brand); width: 52px; height: 52px; border-radius: 50%;
  display: grid; place-items: center; flex: none; }
/* 1 tytuł */
.title { justify-content: center; gap: 40px; }
.title .logo { width: 200px; height: 200px; }
.title > :not(.hero) { max-width: 860px; }
.title .hero { position: absolute; left: 1010px; top: 50%; transform: translateY(-50%); width: 782px; border-radius: 20px;
  border: 1px solid var(--line-strong); box-shadow: var(--shadow-3); }
.title h1 { font-size: 150px; line-height: 1; }
.title .sub { font-size: 48px; color: var(--ink); font-family: var(--font-display); }
/* 5 przepływ */
.flow { display: flex; align-items: stretch; gap: 0; }
.flow .card { flex: 1; padding: 40px 32px; }
.flow .arr { align-self: center; color: var(--brand); padding: 0 8px; }
.flow .arr .ic { width: 40px; height: 40px; }
/* 6–7 zrzuty */
.shot { display: grid; gap: 40px; align-items: center; }
.shot img { display: block; border-radius: 16px; border: 1px solid var(--line-strong); box-shadow: var(--shadow-3); }
.pic { position: relative; }
.pic .hl { position: absolute; margin: -9px 0 0 -9px; padding: 6px; border: 3px solid var(--brand); border-radius: 14px;
  box-shadow: 0 0 0 3px var(--bg); }
.pic .n { position: absolute; width: 44px; height: 44px; font-size: 24px; transform: translate(0, -100%);
  box-shadow: 0 0 0 4px var(--bg), var(--shadow-3); }
.notes { display: flex; flex-direction: column; gap: 32px; }
.notes > div { display: flex; gap: 20px; align-items: flex-start; }
.notes p { color: var(--ink); font-size: 28px; }
.sts { display: flex; gap: 14px; margin-top: 14px; }
.sts svg { width: 40px; height: 40px; }
.si-ok { color: var(--fill-ok); } .si-warn { color: var(--fill-warn); } .si-full { color: var(--fill-full); }
.si-report { color: var(--st-report); } .si-sensor { color: var(--st-sensor); }
/* 8 architektura */
.arch { display: grid; grid-template-columns: 1fr 72px 1.15fr 72px 1fr; align-items: center; }
.arch .col { display: flex; flex-direction: column; gap: 16px; }
.arch .item { display: flex; gap: 16px; align-items: center; font-size: 28px; background: var(--surface); border: 1px solid var(--line);
  border-radius: 14px; padding: 20px 24px; }
.arch .item .ic { width: 32px; height: 32px; color: var(--brand); }
.arch .core { background: var(--surface-2); border: 2px solid var(--brand-line); border-radius: 20px; padding: 40px; display: flex;
  flex-direction: column; gap: 18px; }
.arch .arr { color: var(--brand); display: grid; place-items: center; }
.ai { display: flex; gap: 20px; align-items: center; font-size: 28px; color: var(--ink); background: var(--st-report-soft);
  border: 1px solid var(--st-report); border-radius: 14px; padding: 20px 28px; align-self: center; }
.ai .ic { color: var(--st-report-ink); }
/* 10 */
.contact { display: flex; gap: 48px; font: 600 34px/1.2 var(--font-display); color: var(--brand-ink); }
.contact span { display: flex; gap: 16px; align-items: center; }
.tag { font: 600 44px/1.2 var(--font-display); color: var(--ink); }
/* plansze filmu */
.card-film { justify-content: center; align-items: center; text-align: center; gap: 36px; padding: 128px; }
.card-film .logo { width: 160px; height: 160px; }
.card-film h1 { font-size: 104px; line-height: 1.05; }
.card-film p { font-size: 40px; }
"""


def doc(sections):
    return (f'<!doctype html><html lang="pl" data-theme="dark"><head><meta charset="utf-8"><title>Trash Fairy</title>'
            f'<style>{tokens_css()}{CSS}</style></head><body>'
            f'<svg xmlns="http://www.w3.org/2000/svg" style="display:none">{sprite()}</svg>{"".join(sections)}</body></html>')


def foot(i, logo):
    return (f'<div class="foot"><img src="{logo}" alt=""><b>Trash Fairy</b><span>HackYeah 2026 · Smart City</span>'
            f'<span class="pg">{i} / {SLIDES}</span></div>')


def slides(n, shots, marks):
    logo = b64(LOGO, "image/svg+xml")
    img = {k: b64(v, "image/png") for k, v in shots.items()}
    S = []

    def add(body, cls=""):
        if cls != "title":  # treść pod nagłówkiem wyśrodkowana w pionie: nagłówek zawsze w tym samym miejscu
            head, _, rest = body.partition("</div>")
            body = f'{head}</div><div class="body">{rest}</div>'
        S.append(f'<section class="{cls}">{body}{foot(len(S) + 1, logo) if cls != "title" else ""}</section>')

    add(f'<img class="logo" src="{logo}" alt="Logo Trash Fairy"><h1>Trash Fairy</h1>'
        f'<p class="sub">Mózg odbioru odpadów dla Krakowa</p>'
        f'<p>Kosze opróżniane według potrzeb, nie kalendarza.</p>'
        f'<p class="note">HackYeah 2026 · Smart City · {PROD}</p><img class="hero" src="{img["kiosk"]}" alt="">', "title")
    add(f'<div class="head"><span class="kicker">Problem</span><h2>Kraków opróżnia kosze według kalendarza, nie według potrzeb</h2></div>'
        f'<div class="grid g3">'
        f'<div class="card"><span class="big">{n["bins_all"]}</span><p>koszy w harmonogramie MPO</p></div>'
        f'<div class="card"><span class="big">{n["empty_from"]}%</span><p>pustych przyjazdów (symulacja)</p></div>'
        f'<div class="card"><span class="big">{n["shelter_from"]}<small> h</small></span><p>przepełnień altan (symulacja)</p></div>'
        f'</div><p class="note">Symulacja: {n["sim_bins"]} koszy, {n["sim_shelters"]} altan, {n["weeks"]} tygodnie, '
        f'harmonogram MPO {n["mpo"]} · /metodologia</p>')
    add('<div class="head"><span class="kicker">Rozwiązanie</span><h2>Odbiór wtedy, kiedy kosz tego potrzebuje</h2></div>'
        '<div class="grid g3">'
        f'<div class="card"><span class="badge">{ic("radar")}</span><h3>Sygnały</h3><p>Prognoza zapełnienia, panel kosza z kodem QR, przycisk, czujniki.</p></div>'
        f'<div class="card"><span class="badge">{ic("route")}</span><h3>Reguły</h3><p>Jawne reguły w kodzie wybierają kosze i układają trasę.</p></div>'
        f'<div class="card"><span class="badge">{ic("shield-check")}</span><h3>Dowód</h3><p>Położenie śmieciarki i zdjęcie kosza potwierdzają odbiór.</p></div>'
        '</div>')
    tiles = [("tablet-smartphone", "Panel kosza", "Zapełnienie, kod QR, przycisk"), ("smartphone", "Mieszkaniec", "Zgłoszenie bez instalowania aplikacji"),
             ("truck", "Kierowca", "Priorytety, nawigacja, dowód odbioru"), ("radio-tower", "Dyspozytor", "Mapa, pilne kosze, ekipy"),
             ("layout-dashboard", "Dashboard miasta", "Oszczędności i rekomendacje"), ("map-pin", "Dzikie wysypiska", "Pinezka, zdjęcie, punkty")]
    add('<div class="head"><span class="kicker">Funkcje</span><h2>Jedne dane dla mieszkańców, ekip i miasta</h2></div><div class="grid g3">'
        + "".join(f'<div class="card"><span class="badge">{ic(i)}</span><h3>{t}</h3><p>{d}</p></div>' for i, t, d in tiles) + '</div>')
    steps = [("qr-code", "Zgłoszenie", "Kod QR albo przycisk na panelu"), ("gauge", "Reguła", "Stan i priorytet kosza"),
             ("route", "Trasa", "Tylko kosze, które tego potrzebują"), ("camera", "Odbiór", "Położenie i zdjęcie kosza"),
             ("bell-ring", "Status", "Mieszkaniec i miasto widzą wynik")]
    flow = f'<span class="arr">{ic("arrow-right")}</span>'.join(
        f'<div class="card"><span class="badge">{ic(i)}</span><h3>{t}</h3><p>{d}</p></div>' for i, t, d in steps)
    add(f'<div class="head"><span class="kicker">Przepływ</span><h2>Od zgłoszenia do odbioru</h2></div><div class="flow">{flow}</div>')

    def notes(items):
        return '<div class="notes">' + "".join(f'<div><span class="n">{k}</span><p>{t}</p></div>' for k, t in enumerate(items, 1)) + '</div>'
    states = '<span class="sts">' + "".join(ic(f"st-{k}", f"si-{k}") for k in ("ok", "warn", "full", "report", "sensor")) + '</span>'
    pins = "".join(f'<span class="hl" style="left:{x:.2f}%;top:{y:.2f}%;width:{w:.2f}%;height:{h:.2f}%"></span>'
                   f'<span class="n" style="left:{x + w:.2f}%;top:{y:.2f}%">{k}</span>' for k, (x, y, w, h) in sorted(marks.items()))
    add('<div class="head"><span class="kicker">Dyspozytor</span><h2>Mapa na żywo, decyzja człowieka</h2></div>'
        f'<div class="shot" style="grid-template-columns:1080px 1fr"><div class="pic">'
        f'<img src="{img["dyspozytor"]}" alt="Panel dyspozytora" style="width:1080px">{pins}</div>'
        + notes([f"Stan kosza: kształt, znak i kolor{states}", "Pilne: kosz do kursu dodaje dyspozytor", "Ekipy i trasy na żywo"]) + '</div>')
    add('<div class="head"><span class="kicker">Zgłoszenie</span><h2>Przy koszu, bez instalowania aplikacji</h2></div>'
        f'<div class="shot" style="grid-template-columns:880px 280px 1fr">'
        f'<img src="{img["panel"]}" alt="Panel kosza" style="width:880px"><img src="{img["zglos"]}" alt="Zgłoszenie na telefonie" style="width:280px">'
        + notes(["Kod QR zmienia się codziennie", "Albo przycisk „Przepełniony”", "Numer i status od razu"]) + '</div>')
    ins = [("qr-code", "Panel kosza i QR"), ("smartphone", "Telefon mieszkańca"), ("cpu", "Czujniki"), ("sun", "Pogoda i ruch")]
    outs = [("truck", "Kierowca"), ("radio-tower", "Dyspozytor"), ("layout-dashboard", "Dashboard"), ("external-link", "Open311, dane otwarte")]
    col = lambda xs: '<div class="col">' + "".join(f'<div class="item">{ic(i)}{t}</div>' for i, t in xs) + '</div>'  # noqa: E731
    arr = f'<div class="arr">{ic("arrow-right")}</div>'
    add('<div class="head"><span class="kicker">Architektura</span><h2>Reguły decydują, AI tylko opisuje</h2></div>'
        f'<div class="arch">{col(ins)}{arr}<div class="core"><h3>Flask + reguły</h3><p>Stan, priorytet, trasa (OR-Tools)</p>'
        f'<p>PostgreSQL</p></div>{arr}{col(outs)}</div>'
        f'<div class="ai">{ic("sparkles")}AI (Claude) opisuje zdjęcia, nigdy nie decyduje</div>')
    add('<div class="head"><span class="kicker">Korzyści</span><h2>Mniej pustych przyjazdów, mniej przepełnień</h2></div>'
        '<div class="grid g2">'
        f'<div class="card"><span class="big" style="font-size:88px">{n["empty_from"]}→<span class="to">{n["empty_to"]}%</span></span><p>pustych przyjazdów</p></div>'
        f'<div class="card"><span class="big" style="font-size:88px">{n["shelter_from"]}→<span class="to">{n["shelter_to"]}</span><small> h</small></span><p>przepełnień altan</p></div>'
        f'<div class="card"><span class="big" style="font-size:88px"><span class="to">−{n["visit_cut"]}%</span></span><p>odbiorów koszy</p></div>'
        f'<div class="card"><span class="big" style="font-size:88px"><span class="to">{n["pln_min"]}–{n["pln_max"]}</span></span><p>mln zł rocznie w Krakowie (szacunek)</p></div>'
        '</div>'
        f'<p class="note">Symulacja {n["weeks"]} tygodni; {n["odbior_zl"]} zł za odbiór, {n["km_zl"]} zł za km (założenia). '
        f'Dashboard demo: {n["month_zl"]} zł mniej niż plan w {n["days"]} dni, {n["visits_less"]} odbiorów mniej.</p>')
    road = [("flag", f'Pilotaż: {n["pilot_bins"]} koszy w {n["pilot_where"]}'), ("building-2", "Integracja z systemami MPO"),
            ("cpu", "Czujniki tam, gdzie się opłacają")]
    add('<div class="head"><span class="kicker">Co dalej</span><h2>Pilotaż i kontakt</h2></div>'
        '<div class="grid g3">' + "".join(f'<div class="card"><span class="badge">{ic(i)}</span><h3>{t}</h3></div>' for i, t in road) + '</div>'
        f'<p class="tag">Kraków nie potrzebuje więcej koszy. Potrzebuje wróżki.</p>'
        f'<div class="contact"><span>{ic("external-link")}{PROD}</span><span>{ic("file-text")}{REPO}</span></div>')
    assert len(S) == SLIDES, len(S)
    return doc(S)


# ---------------------------------------------------------------- zrzuty aplikacji
DARK = "try { localStorage.setItem('tf-motyw', 'dark'); } catch (e) {}"


def app_shots(browser, base):
    PREVIEW.mkdir(parents=True, exist_ok=True)
    out = {}

    def ctx(w, h, scale=1):
        c = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=scale, color_scheme="dark", locale="pl-PL")
        c.add_init_script(DARK)
        return c

    c = ctx(1280, 800, 2)  # laptop w skali 2: tekst ostry po zmniejszeniu do 1080 px na slajdzie
    p = c.new_page()
    p.goto(base + "/dyspozytor", wait_until="networkidle")
    p.wait_for_timeout(2500)
    if p.locator(".leaflet-container").count() == 0:
        log("UWAGA: /dyspozytor nie ma jeszcze mapy — slajd 6 pokaże obecny stan strony")
    out["dyspozytor"] = PREVIEW / "app-dyspozytor.png"
    p.screenshot(path=out["dyspozytor"])
    marks = {k: v for k, v in p.evaluate(MARKS_JS).items() if v}  # numery 1–3 na zrzucie = notatki obok
    if len(marks) < 3:
        log(f"UWAGA: slajd 6 bez części numerów na zrzucie (znalezione: {sorted(marks)})")
    c.close()

    c = ctx(1280, 800, 2)
    p = c.new_page()
    p.goto(base + "/panel/18", wait_until="networkidle")
    p.wait_for_timeout(1500)
    out["panel"] = PREVIEW / "app-panel.png"
    p.screenshot(path=out["panel"])
    out["kiosk"] = PREVIEW / "app-kiosk.png"  # samo urządzenie, bez nawigacji aplikacji: slajd 1
    p.locator("#kiosk").screenshot(path=out["kiosk"])
    qr = urlparse(p.get_attribute("#kiosk", "data-qr"))  # link pod kodem jest tylko w trwającym scenariuszu
    c.close()

    c = ctx(390, 844, 2)
    p = c.new_page()
    p.goto(base + qr.path + "?" + qr.query, wait_until="networkidle")
    p.click(".m-type:has(input[value=przepelniony])")
    p.wait_for_timeout(600)
    out["zglos"] = PREVIEW / "app-zglos.png"
    p.screenshot(path=out["zglos"])
    c.close()
    return out, marks


# ramki elementów w % ekranu [x, y, szer., wys.]: 1 pinezka stanu, 2 przycisk w Pilnych, 3 punkt na linii trasy (null = brak)
MARKS_JS = """() => {
  const vw = innerWidth, vh = innerHeight, inside = (x, y) => x > 40 && y > 80 && x < vw - 60 && y < vh - 40;
  const box = (x, y, w, h) => [100 * x / vw, 100 * y / vh, 100 * w / vw, 100 * h / vh];
  const el = sel => { for (const e of document.querySelectorAll(sel)) { const b = e.getBoundingClientRect();
    if (b.width && inside(b.left + b.width / 2, b.top + b.height / 2)) return box(b.left, b.top, b.width, b.height); } return null; };
  const route = () => { for (const e of document.querySelectorAll('.leaflet-overlay-pane path[class*=route-]')) {
    const L = e.getTotalLength(), m = e.getScreenCTM(); if (!L || !m) continue;
    for (const f of [.5, .35, .65, .2, .8]) { const q = e.getPointAtLength(L * f), x = q.x * m.a + q.y * m.c + m.e, y = q.x * m.b + q.y * m.d + m.f;
      if (inside(x, y) && !document.elementFromPoint(x, y)?.closest('.leaflet-marker-icon')) return box(x - 12, y - 12, 24, 24); } } return null; };
  return {1: el('.leaflet-marker-icon.tf-pin:not(.tf-cluster):not(.is-num)') || el('.leaflet-marker-icon.tf-pin'), 2: el('[data-add]'), 3: route()};
}"""


# ---------------------------------------------------------------- PDF
WORDS_JS = """[...document.querySelectorAll('section')].map(s => {
  const c = s.cloneNode(true); c.querySelectorAll('.foot').forEach(f => f.remove());
  const words = (c.textContent.match(/\\S+/g) || []).filter(w => /[\\p{L}\\p{N}]/u.test(w)).length;
  const r = s.getBoundingClientRect();
  const over = [...s.querySelectorAll('*')].filter(e => { const b = e.getBoundingClientRect();
    return b.width && !e.closest('.foot, .hero') && (b.right > r.right + 1 || b.bottom > r.top + 960 || e.scrollWidth > e.clientWidth + 2 && getComputedStyle(e).overflow !== 'visible'); }).length;
  return {words, over};
})"""


def build_pdf(browser, base):
    from pypdf import PdfReader
    n = numbers(base)
    log("Liczby z API: " + ", ".join(f"{k}={v}" for k, v in n.items()))
    shots, marks = app_shots(browser, base)
    page = browser.new_page(viewport={"width": W, "height": H})
    page.set_content(slides(n, shots, marks), wait_until="load")
    page.evaluate("document.fonts.ready")
    stats = page.evaluate(WORDS_JS)
    bad = [f"slajd {i}: {s['words']} słów" for i, s in enumerate(stats, 1) if s["words"] > MAX_WORDS]
    bad += [f"slajd {i}: {s['over']} elementów poza slajdem" for i, s in enumerate(stats, 1) if s["over"]]
    for i, sec in enumerate(page.locator("section").all(), 1):
        sec.screenshot(path=PREVIEW / f"slajd-{i:02d}.png")
    page.pdf(path=str(PDF), width=f"{W}px", height=f"{H}px", print_background=True, prefer_css_page_size=True,
             margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
    page.close()
    pages = len(PdfReader(PDF).pages)
    assert pages == SLIDES, f"PDF ma {pages} stron zamiast {SLIDES}"
    log(f"PDF: {PDF} ({pages} stron), podgląd: {PREVIEW / 'slajd-01.png'} … slajd-{SLIDES:02d}.png; słowa: "
        + ", ".join(str(s["words"]) for s in stats))
    if bad:
        raise SystemExit("Popraw slajdy: " + "; ".join(bad))
    return n


# ---------------------------------------------------------------- film
def ffmpeg(*args):
    import imageio_ffmpeg
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", *map(str, args)],
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("ffmpeg: " + r.stderr[-800:])
    return r


def duration(path):
    import imageio_ffmpeg
    err = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


VIDEO = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30"]
X264 = VIDEO + ["-an"]

# napisy i kółko kliknięcia: nakładka HTML w nagrywanej stronie (drawtext z imageio nie ma polskich znaków
# w fontach woff2 aplikacji, a nakładka używa tych samych fontów i tokenów co aplikacja). Napis i kółko są popoverami:
# pokazane po okienku showModal() trafiają do top layer nad nim, a nie pod jego przyciemnione tło.
# Pasek „Krok x z y” scenariusza dubluje napisy, więc w filmie go nie ma; toasty idą na górę, żeby nie wchodziły na napis.
OVERLAY = DARK + """
(() => {
  const css = `#tf-cap{position:fixed;inset:auto;left:50%;bottom:40px;margin:0;transform:translateX(-50%);width:max-content;max-width:1040px;
    padding:12px 24px;border-radius:12px;background:var(--glass);color:var(--ink);border:1px solid var(--brand-line);overflow:visible;
    font:600 24px/1.3 var(--font-display);text-align:center;pointer-events:none;box-shadow:var(--shadow-3)}
    .tf-ring{position:fixed;inset:auto;width:44px;height:44px;margin:-22px 0 0 -22px;padding:0;background:transparent;overflow:visible;
    border:4px solid var(--brand);border-radius:50%;pointer-events:none;animation:tf-ring .7s ease-out forwards}
    @keyframes tf-ring{from{transform:scale(.3);opacity:1}to{transform:scale(1.5);opacity:0}}
    #scenario-slot{display:none!important} body.has-scenario{--scenario-h:0px!important}
    .toasts{top:88px!important;bottom:auto!important}`;
  const top = el => { try { if (el.matches(':popover-open')) el.hidePopover(); el.showPopover(); } catch (e) {} };
  window.tfCap = t => { const c = document.getElementById('tf-cap'); if (!c) return; c.textContent = t;
    if (t) top(c); else try { c.hidePopover(); } catch (e) {} };
  const put = () => {
    if (document.getElementById('tf-cap')) return;
    const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    const c = document.createElement('div'); c.id = 'tf-cap'; c.popover = 'manual'; document.body.appendChild(c);
    window.tfCap(sessionStorage.getItem('tf-cap') || '');
  };
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', put) : put();
  addEventListener('pointerdown', e => {
    const r = document.createElement('div'); r.className = 'tf-ring'; r.popover = 'manual';
    r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px';
    document.body.appendChild(r); top(r); setTimeout(() => r.remove(), 800);
  }, true);
})();
"""

ELEVEN_URL = "https://api.elevenlabs.io/v1/text-to-speech/{}?output_format=mp3_44100_128"
ELEVEN_VOICE = "pNInz6obpgDQGcFmaJgB"  # „Adam”: męski głos z biblioteki ElevenLabs (nie imitacja prawdziwej osoby)


def env(name):
    """Zmienna środowiska albo wpis z .env w repo (wartości nigdy nie wypisujemy)."""
    if not os.environ.get(name) and (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            k, sep, v = line.partition("=")
            if sep and k.strip() == name:
                return v.strip().strip("\"'")
    return os.environ.get(name, "")


class Voice:
    """Lektor: tekst → mp3 z ElevenLabs (eleven_multilingual_v2), z pamięcią po tekście; (ścieżka, sekundy) albo None."""

    def __init__(self, key, voice_id, tmp):
        self.key, self.voice_id, self.tmp, self.cache = key, voice_id, tmp, {}

    def clip(self, text):
        if text not in self.cache:
            path = self.tmp / f"lektor-{len(self.cache):02d}.mp3"
            body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                               "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": 1.05}}).encode()
            req = Request(ELEVEN_URL.format(self.voice_id), data=body, method="POST",
                          headers={"xi-api-key": self.key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
            try:
                with urlopen(req, timeout=90) as r:
                    path.write_bytes(r.read())
                self.cache[text] = (path, duration(path))
            except (URLError, OSError) as e:  # HTTPError też; komunikat bez nagłówków, więc bez klucza
                log(f"  UWAGA: lektor nie nagrał „{text[:40]}…”: {getattr(e, 'code', '')} {getattr(e, 'reason', e)}")
                self.cache[text] = None
        return self.cache[text]


LEKTOR = ROOT / "demo" / "lektor"  # nagrania z łącznika MCP ElevenLabs (bez klucza API): NN.mp3 + teksty.json {tekst: plik}


def lektor_texts():
    """Teksty lektora w kolejności filmu: plansze, potem take.say w scenariuszach (`spoken`, a bez niego napis)."""
    import ast
    calls = []
    for fn in ast.parse(Path(__file__).read_text(encoding="utf-8")).body:
        if isinstance(fn, ast.FunctionDef) and fn.name.startswith("scenario_"):
            calls += [n for n in ast.walk(fn) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "say"]
    out = [c[3] for c in CARDS]
    for n in sorted(calls, key=lambda n: n.lineno):
        node = {k.arg: k.value for k in n.keywords}.get("spoken", n.args[0])
        if not isinstance(node, ast.Constant):
            raise SystemExit(f"build_all.py:{n.lineno}: tekst lektora zależy od danych — dodaj stały spoken=")
        out.append(node.value)
    return list(dict.fromkeys(out))


def lektor_list():
    """--tylko lektor: teksty.json z planem plików (istniejące przypisania zostają) i lista brakujących nagrań."""
    LEKTOR.mkdir(parents=True, exist_ok=True)
    f = LEKTOR / "teksty.json"
    old = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    used = set(old.values())
    files, n = {}, 1
    for t in lektor_texts():
        if t not in old:
            while f"{n:02d}.mp3" in used:
                n += 1
            used.add(f"{n:02d}.mp3")
        files[t] = old.get(t, f"{n:02d}.mp3")
    f.write_text(json.dumps(files, ensure_ascii=False, indent=1), encoding="utf-8")
    missing = [(m, t) for t, m in files.items() if not (LEKTOR / m).exists()]
    log(f"Lektor: {len(files)} tekstów, brak nagrań: {len(missing)}")
    for m, t in missing:
        log(f"  {m}: {t}")


class FileVoice:
    """Lektor z plików demo/lektor (teksty.json); brak nagrania = napis bez głosu i ostrzeżenie."""

    def __init__(self, files):
        self.files, self.cache = files, {}

    def clip(self, text):
        if text not in self.cache:
            path = LEKTOR / self.files.get(text, "-")
            self.cache[text] = (path, duration(path)) if path.is_file() else None
            if not path.is_file():
                log(f"  UWAGA: brak nagrania lektora dla „{text[:50]}” — uruchom --tylko lektor")
        return self.cache[text]


def voice(tmp):
    if (LEKTOR / "teksty.json").exists():
        log("Lektor: nagrania z demo/lektor")
        return FileVoice(json.loads((LEKTOR / "teksty.json").read_text(encoding="utf-8")))
    key = env("ELEVENLABS_API_KEY")
    if not key:
        log("UWAGA: brak ELEVENLABS_API_KEY (zmienna albo .env) — film bez lektora")
        return None
    v = Voice(key, env("ELEVENLABS_VOICE_ID") or ELEVEN_VOICE, tmp)
    if v.clip(CARDS[0][3]) is None:
        log("UWAGA: ElevenLabs nie odpowiada poprawnie — film bez lektora")
        return None
    return v


class Take:
    """Jedna strona nagrywana do webm + odcinki, które zostają w filmie (ładowanie stron i długie czekanie wycinamy)
    + napisy z czasem nagrania i klipem lektora. Z lektorem napis trwa co najmniej tyle, ile jego nagranie."""

    def __init__(self, browser, base, tmp, lektor=None):
        self.base, self.lektor, self.caps = base, lektor, []
        self.ctx = browser.new_context(viewport={"width": VW, "height": VH}, record_video_dir=str(tmp),
                                       record_video_size={"width": VW, "height": VH}, color_scheme="dark", locale="pl-PL")
        self.ctx.add_init_script(OVERLAY)
        self.page = self.ctx.new_page()
        self.t0, self.keep, self.since = time.monotonic(), [], None
        self.page.set_default_timeout(15000)

    def on(self):
        self.since = time.monotonic() - self.t0

    def off(self):
        if self.since is not None:
            self.keep.append((self.since, time.monotonic() - self.t0))
        self.since = None

    def go(self, path):
        self.off()
        self.page.evaluate("() => { try { sessionStorage.removeItem('tf-cap'); } catch (e) {} }")  # nowa scena bez starego napisu
        self.page.goto(self.base + path, wait_until="networkidle")
        self.page.wait_for_timeout(500)
        self.on()

    def waiting(self, fn):
        """Czekanie bez obrazu (np. dojazd nawigacji, analiza zdjęcia) — wycinamy z filmu."""
        self.off()
        fn()
        self.on()

    def say(self, text, hold=0, spoken=None):
        """Napis na ekranie; `spoken` = tekst lektora, gdy różni się od napisu (np. bez numeru TF-…)."""
        clip = None
        if self.lektor:
            rec = self.since is not None
            self.off()  # zapytanie do ElevenLabs nie trafia do filmu
            clip = self.lektor.clip(spoken or text)
            if rec:
                self.on()
        self.page.evaluate("t => { sessionStorage.setItem('tf-cap', t); window.tfCap && window.tfCap(t); }", text)
        if clip:
            self.caps.append((time.monotonic() - self.t0, clip[0]))
            hold = max(hold, clip[1] + 0.35)
        if hold:
            self.page.wait_for_timeout(int(hold * 1000))

    def finish(self):
        self.off()
        video = self.page.video
        self.ctx.close()
        return Path(video.path()), self.keep, self.caps


def ok(cond, what):
    if not cond:
        raise SystemExit(f"Krok filmu nie wyszedł: {what}")
    log(f"  OK {what}")


def optional(take, sel):
    return take.page.locator(sel).count() > 0


def scenario_1(take, photo):
    p = take.page
    take.go("/")
    take.say("Kraków opróżnia kosze według kalendarza. Trash Fairy: według potrzeb.", 3)
    take.go("/?scenariusz=A&kosz=18")
    p.wait_for_selector("#sc-pick[open]")
    take.say("Scenariusz demo: mieszkanka przy koszu nr 18", 2, spoken="Scenariusz demo: mieszkanka przy koszu numer osiemnaście.")
    p.click("#sc-pick [data-go]")
    take.waiting(lambda: p.wait_for_url("**/panel/18"))
    ok("/panel/18" in p.url, "panel kosza 18")
    pct = p.text_content("#k-pct").strip()  # prognoza z aplikacji: zgłoszenie mieszkanki to sygnał, którego prognoza nie zna
    take.say(f"Prognoza: {pct}%. Kosz jest pełny – zgłoszenie to sygnał spoza prognozy", 3.5,
             spoken="Prognoza nie widzi jeszcze pełnego kosza. Mieszkanka widzi. Jej zgłoszenie to sygnał, którego prognoza nie zna.")
    take.say("Kod QR na panelu zmienia się codziennie", 1)
    p.click("a.kiosk-qr-code")
    take.waiting(lambda: (p.wait_for_load_state("networkidle"), p.wait_for_selector("#chk-qr.ok")))
    take.say("Skan otwiera zgłoszenie tego kosza", 1.5)
    p.click(".m-type:has(input[value=przepelniony])")
    take.say("„Przepełniony” i Wyślij", 1, spoken="Przepełniony. Wyślij.")
    p.click("#m-send")
    take.waiting(lambda: p.wait_for_selector("#m-success:not([hidden])"))
    nr = p.text_content("#m-nr").strip()
    ok(nr.startswith("TF-"), f"zgłoszenie {nr}")
    if "Dziękujemy" not in p.text_content("#m-success"):
        log("  UWAGA: brak „Dziękujemy” po zgłoszeniu (pakiet mieszkańca jeszcze nie wdrożony)")
    take.say(f"Zgłoszenie {nr} przyjęte: numer i status od razu", 3, spoken="Zgłoszenie przyjęte: numer i status od razu.")
    take.go("/panel/18")
    take.say("Panel kosza potwierdza zgłoszenie", 3.5)
    take.go("/dyspozytor")
    if optional(take, ".leaflet-container"):
        take.say("Dyspozytor widzi pilne kosze, trasy i ekipy na żywo", 6)
    else:
        log("  UWAGA: /dyspozytor bez mapy — pomijam krok")
    take.go("/kierowca")
    take.say("Kierowca: zgłoszony kosz na liście, z powodem", 3)
    link = p.locator("#k-stops a[href$='/kierowca/kosz/18']")
    ok(link.count() > 0, "kosz 18 na liście kierowcy")
    take.off()
    link.first.click()
    p.wait_for_load_state("networkidle")
    take.on()
    take.say("„Jadę”: nawigacja w aplikacji, bez przełączania do map", 0.5)
    p.click("[data-akcja=jade]")
    p.wait_for_timeout(2500)
    take.waiting(lambda: p.wait_for_selector("#k-navbar.arrived", timeout=40000))
    take.say("„Opróżniono” ze zdjęciem kosza: dowód odbioru", 1)
    p.click("input[name=poziom][value='100']", force=True)
    p.set_input_files("#k-photo-in", str(photo))
    p.wait_for_timeout(1200)
    p.click("[data-akcja=oprozniono]")
    take.waiting(lambda: p.wait_for_selector("#k-doneok:not([hidden])", timeout=30000))
    ok(True, "kierowca: Opróżniono")
    take.say("Odbiór potwierdzony: położenie śmieciarki i zdjęcie", 3)
    take.go(f"/zgloszenie/{nr}")
    take.waiting(lambda: p.wait_for_function("document.getElementById('st-title')?.textContent.includes('Zrealizowane')", timeout=20000))
    ok(True, "status u mieszkańca: zrealizowane")
    take.say("Mieszkanka widzi: zrealizowane", 3.5)
    take.go("/dashboard")
    p.wait_for_timeout(1500)
    take.say("Miasto: oszczędności wobec planu, odbiory i zgłoszenia", 5.5)


def scenario_2(take):
    p = take.page
    take.go("/?scenariusz=C&miejsce=0")
    p.wait_for_selector("#sc-pick[open]")
    take.say("Dzikie wysypisko poza koszem: zgłasza mieszkaniec", 2)
    p.click("#sc-pick [data-go]")
    take.waiting(lambda: (p.wait_for_url("**/wysypisko"), p.wait_for_load_state("networkidle")))
    where = p.text_content("#wd-where").strip()
    ok(bool(where), f"miejsce: {where}")
    take.say("Miejsce na mapie, rodzaje odpadów, liczba worków", 5)
    p.click(".wd-demo-photo")
    p.wait_for_function("document.getElementById('wd-zdjecie').files.length === 1")
    take.say("Zdjęcie: AI opisuje, reguła decyduje", 1.5, spoken="Zdjęcie opisuje sztuczna inteligencja, a decyduje reguła.")
    p.click("#wd-send")
    take.waiting(lambda: p.wait_for_selector("#wd-ok:not([hidden])", timeout=40000))
    wd = p.text_content("#wd-nr").strip()
    ok(wd.startswith("WD-"), f"zgłoszenie {wd}")
    take.say(f"Przyjęte: {wd}", 2.5, spoken="Zgłoszenie przyjęte.")
    take.go(f"/wysypisko/{wd}")
    take.say("Status zgłoszenia dzikiego wysypiska", 4)
    take.go("/dyspozytor")
    if optional(take, ".leaflet-container"):
        take.say("Dyspozytor: gorące obszary i pilne zgłoszenia", 4.5)
        if optional(take, "#dp-t-pilne"):  # scenariusz C otwiera zakładkę „Zgłoszenia”; przycisk dodania jest w „Pilne”
            p.click("#dp-t-pilne")
        add = p.get_by_role("button", name=re.compile("Dodaj do kursu|Na początek kursu"))
        if add.count():
            take.say("Dyspozytor dodaje kosz do kursu: decyzja człowieka", 0.5)
            add.first.click()
            p.wait_for_timeout(2500)
        else:
            log("  UWAGA: brak przycisku dodania do kursu w /dyspozytor")
    else:
        log("  UWAGA: /dyspozytor bez mapy — pomijam krok")
    take.go(f"/wysypisko/{wd}?ekipa=1")
    take.say("Ekipa sprząta i oznacza „Uprzątnięte”", 1)
    p.wait_for_selector("#wd-clear:not([hidden])")
    p.click("#wd-clear")
    p.wait_for_timeout(2000)
    take.go("/zglos")
    take.waiting(lambda: p.wait_for_selector("#m-pts-sum b"))
    pts = int(re.sub(r"\D", "", p.text_content("#m-pts-sum b")) or 0)
    ok(pts > 0, f"punkty mieszkańca: {pts}")
    take.say(f"Mieszkaniec dostaje punkty: {pts} pkt", 4, spoken="Za trafne zgłoszenie mieszkaniec dostaje punkty.")
    take.go("/dashboard")
    p.wait_for_timeout(1000)
    take.say("Miasto: oszczędności dziennie, w miesiącu i w roku", 4.5)
    rec = p.locator("#rekomendacje, [data-help^='dashboard.rekomend'], h2:has-text('Rekomendacje')")
    if rec.count():
        rec.first.evaluate("e => e.scrollIntoView({behavior: 'smooth', block: 'start'})")
        take.say("Rekomendacje z reguł: od tablicy po fotopułapkę", 6)
    else:
        log("  UWAGA: nie znalazłem rekomendacji na dashboardzie")


def demo_photo(path):
    """Przykładowe zdjęcie kosza do „Opróżniono” (rysunek, jawnie podpisany jako demo)."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (960, 1280), (118, 122, 128))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 900, 960, 1280], fill=(92, 96, 102))
    d.rounded_rectangle([290, 380, 670, 1060], radius=36, fill=(38, 92, 70))
    d.rounded_rectangle([260, 330, 700, 410], radius=24, fill=(30, 74, 56))
    d.rectangle([380, 520, 580, 560], fill=(220, 224, 230))
    d.text((40, 40), "ZDJECIE PRZYKLADOWE (DEMO)", fill=(240, 240, 240), font_size=48)
    im.save(path, "JPEG", quality=85)
    return path


def card(browser, path, title, sub, big=False):
    logo = b64(LOGO, "image/svg+xml")
    body = (f'<section class="card-film"><img class="logo" src="{logo}" alt="">'
            f'{"<span class=kicker>" + sub + "</span>" if not big else ""}<h1>{title}</h1>{"<p>" + sub + "</p>" if big else ""}</section>')
    page = browser.new_page(viewport={"width": W, "height": H})
    page.set_content(doc([body]), wait_until="load")
    page.evaluate("document.fonts.ready")
    page.screenshot(path=path)
    page.close()


def on_cut(t, keep, speed=1.0):
    """Czas t surowego nagrania → czas w filmie po wycięciu (zostają odcinki keep) i przyspieszeniu ×speed.
    Chwila z wyciętej przerwy trafia na początek następnego odcinka."""
    acc = 0.0
    for a, b in keep:
        if t < b:
            return (acc + max(0.0, t - a)) / speed
        acc += b - a
    return acc / speed


def cut(webm, keep, caps, out, target):
    """Wycina ładowanie i czekanie; bez lektora dłuższy przebieg przyspiesza do `target` s. Z lektorem tempo zostaje
    (głos nie może się rozjechać z obrazem). Zwraca [(sekunda w tym odcinku filmu, mp3 lektora)]."""
    kept = sum(b - a for a, b in keep)
    speed = 1.0 if caps else max(1.0, kept / target)
    sel = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in keep)
    ffmpeg("-i", webm, "-vf", f"fps=30,select='{sel}',setpts=N/30/TB,setpts=PTS/{speed:.3f},fps=30,scale={W}:{H}:flags=lanczos",
           *X264, out)
    log(f"  {out.name}: {kept:.1f} s nagrania → {kept / speed:.1f} s (×{speed:.2f})")
    return [(on_cut(t, keep, speed), mp3) for t, mp3 in caps]


def mix(video, clips, out, total):
    """Klipy lektora [(sekunda, mp3)] na oś filmu: adelay każdego klipu, amix bez normalizacji, obraz bez przekodowania."""
    ins, fl = [], []
    for i, (t, mp3) in enumerate(clips, 1):
        ins += ["-i", mp3]
        fl.append(f"[{i}:a]adelay=delays={int(t * 1000)}:all=1[a{i}]")
    fl.append("".join(f"[a{i}]" for i in range(1, len(clips) + 1)) + f"amix=inputs={len(clips)}:normalize=0:duration=longest[a]")
    ffmpeg("-i", video, *ins, "-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]", "-c:v", "copy",
           "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.2f}", "-movflags", "+faststart", out)


def fit(src, out, total, audio):
    """Ostatnia deska: film dłuższy niż limit przyspieszamy w całości (obraz setpts, głos atempo — bez zmiany wysokości)."""
    f = total / (FILM_MAX_S - 1)
    if f > 1.12:
        log(f"UWAGA: film {total:.1f} s, przyspieszam ×{f:.2f} — skróć napisy, jeśli lektor brzmi za szybko")
    fl = f"[0:v]setpts=PTS/{f:.4f}[v]" + (f";[0:a]atempo={f:.4f}[a]" if audio else "")
    ffmpeg("-i", src, "-filter_complex", fl, "-map", "[v]", *(["-map", "[a]", "-c:a", "aac", "-b:a", "160k"] if audio else ["-an"]),
           *VIDEO, "-movflags", "+faststart", out)


def reset(req, base, strict=True):
    """POST /api/demo/reset; 429 = reset przed chwilą (np. po e2e_demo), więc czekamy i ponawiamy. Brudne dane = brak filmu."""
    r = req.post(base + "/api/demo/reset", timeout=180000)
    if r.status == 429:
        log("  reset: HTTP 429 (reset przed chwilą), czekam 25 s…")
        time.sleep(25)
        r = req.post(base + "/api/demo/reset", timeout=180000)
    if not r.ok:
        if strict:
            raise SystemExit(f"Reset demo: HTTP {r.status}")
        log(f"UWAGA: reset demo po nagraniu: HTTP {r.status} — zresetuj ręcznie")


# plansze: (plik, tytuł, podtytuł, tekst lektora, minimum sekund, duży tytuł)
CARDS = [("c0", "Trash Fairy", "Mózg odbioru odpadów dla Krakowa", "Trash Fairy: mózg odbioru odpadów dla Krakowa.", 3, True),
         ("c1", "Przepełniony kosz: od zgłoszenia do odbioru", "Scenariusz 1", "Scenariusz pierwszy: przepełniony kosz.", 2, False),
         ("c2", "Dzikie wysypisko i decyzje dla miasta", "Scenariusz 2", "Scenariusz drugi: dzikie wysypisko.", 2, False),
         ("c3", "Kraków nie potrzebuje więcej koszy. Potrzebuje wróżki.", f"{PROD} · {REPO}",
          "Kraków nie potrzebuje więcej koszy. Potrzebuje wróżki.", 3, True)]


def build_film(browser_type, base):
    from playwright.sync_api import Error as PwError
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        lektor = voice(tmp)
        chrome = browser_type.launch(slow_mo=350)
        for img, title, sub, _, _, big in CARDS:
            card(chrome, tmp / f"{img}.png", title, sub, big=big)
        photo = demo_photo(tmp / "kosz.jpg")
        req = chrome.new_context().request
        log("Reset danych demo (POST /api/demo/reset)…")
        reset(req, base)
        takes = []
        try:
            for name, run in (("S1", lambda t: scenario_1(t, photo)), ("S2", scenario_2)):
                log(f"Nagranie {name}")
                t = Take(chrome, base, tmp / name, lektor)
                try:
                    run(t)
                except PwError as e:
                    t.finish()
                    raise SystemExit(f"{name}: {str(e).splitlines()[0]}")
                takes.append(t.finish())
        finally:
            reset(req, base, strict=False)
            chrome.close()
        segs, clips, at = [], [], 0.0

        def plansza(k):
            nonlocal at
            img, _, _, spoken, secs, _ = CARDS[k]
            clip = lektor.clip(spoken) if lektor else None
            secs = max(secs, clip[1] + 0.8) if clip else secs
            segs.append(tmp / f"{img}.mp4")
            ffmpeg("-loop", 1, "-framerate", 30, "-t", f"{secs:.2f}", "-i", tmp / f"{img}.png", *X264, segs[-1])
            if clip:
                clips.append((at + 0.3, clip[0]))
            at += duration(segs[-1])

        def scena(k):
            nonlocal at
            segs.append(tmp / f"s{k + 1}.mp4")
            clips.extend((at + t, mp3) for t, mp3 in cut(*takes[k], segs[-1], SCENARIO_S))
            at += duration(segs[-1])

        plansza(0), plansza(1), scena(0), plansza(2), scena(1), plansza(3)
        (tmp / "lista.txt").write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), encoding="utf-8")
        film = tmp / "film.mp4"
        ffmpeg("-f", "concat", "-safe", 0, "-i", tmp / "lista.txt", *X264, "-movflags", "+faststart", film)
        total = duration(film)
        if clips:
            voiced = tmp / "lektor.mp4"
            mix(film, clips, voiced, total)
            film = voiced
            log(f"  lektor: {len(clips)} klipów")
        if total > FILM_MAX_S - 0.5:
            fit(film, MP4, total, bool(clips))
        else:
            MP4.write_bytes(film.read_bytes())
    total = duration(MP4)
    assert total <= FILM_MAX_S, f"Film ma {total:.1f} s (limit {FILM_MAX_S} s)"
    PREVIEW.mkdir(parents=True, exist_ok=True)
    for k, t in enumerate([1.5, total * .2, total * .4, total * .6, total * .8, total - 1.5], 1):
        ffmpeg("-ss", f"{t:.2f}", "-i", MP4, "-frames:v", 1, PREVIEW / f"film-{k}.png")
    log(f"Film: {MP4} ({total:.1f} s, {'z lektorem' if clips else 'BEZ lektora'}), klatki: {PREVIEW / 'film-1.png'} … film-6.png")


def leftovers():
    """Strażnik: znaczniki do uzupełnienia w README/DEMO nie mogą trafić do zgłoszenia."""
    for f in ("README.md", "DEMO.md"):
        for i, line in enumerate((ROOT / f).read_text(encoding="utf-8").splitlines(), 1):
            if "[z produkcji]" in line or "[from production]" in line:
                log(f"OSTRZEŻENIE: {f}:{i} ma znacznik „[z produkcji]” — wpisz liczbę z logu „Liczby z API”")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="http://127.0.0.1:5050")
    ap.add_argument("--tylko", choices=["pdf", "film", "lektor"])
    a = ap.parse_args()
    base = a.base.rstrip("/")
    if a.tylko == "lektor":
        return lektor_list()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        if a.tylko != "film":
            b = pw.chromium.launch()
            try:
                build_pdf(b, base)
            finally:
                b.close()
        if a.tylko != "pdf":
            build_film(pw.chromium, base)
    leftovers()


if __name__ == "__main__":
    sys.exit(main())
