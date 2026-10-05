"""Symulacja jury (audit/JURY.md): zrzuty i metryki każdego ekranu + budżety kliknięć kluczowych ścieżek.

Użycie (serwer lokalny na 5050): python scripts/jury_check.py <runda> [axe.min.js|-] [adres] [--budzety]  (--budzety: tylko ścieżki)
Wynik w audit/jury/<runda>/: {laptop,telefon,kiosk}/<ekran>.png (+ -cala.png), metryki.json, budzety.json.
Metryki: poziomy scroll (też przy powiększeniu 200%), cele dotykowe < 44 px, czcionki, kolory spoza tokens.css,
ucięty tekst, fokus klawiatury, axe-core (WCAG 2.1 A/AA), żargon i angielskie wtrącenia, błędy JS i odpowiedzi ≥ 400.
"""
import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
RND = sys.argv[1]
AXE = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8") if len(sys.argv) > 2 and sys.argv[2] != "-" else None
BASE = (sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "http://127.0.0.1:5050").rstrip("/")
OUT = ROOT / "audit" / "jury" / RND
VP = {"laptop": (1366, 768), "telefon": (390, 844), "kiosk": (1280, 800)}
PAGES = {
    "przeglad": "/", "panel-18": "/panel/18", "zglos-wybor": "/zglos", "zglos-18": "/kosz/18/zglos",
    "kierowca": "/kierowca", "kierowca-kosz-18": "/kierowca/kosz/18", "dyspozytor": "/dyspozytor", "dashboard": "/dashboard",
    "projekt": "/dashboard/projekty/odbiory-na-zadanie-stare-miasto", "urzadzenia": "/dashboard/urzadzenia",
    "metodologia": "/metodologia", "api-docs": "/api/docs", "dostepnosc": "/dostepnosc", "prywatnosc": "/prywatnosc",
    "404": "/nie-ma-takiej-strony",
}
TOKENS = {tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
          for h in re.findall(r"#([0-9A-Fa-f]{6})\b", (ROOT / "app/static/ui/tokens.css").read_text(encoding="utf-8"))}
TOKENS |= {(255, 255, 255), (0, 0, 0)}
JARGON = r"\b(KPI|MVP|API|CSV|IoT|OSM|OSRM|OR-Tools|SLA|ETA|HMAC|GeoJSON|Open311|MAE|p\.p\.|token\w*|masterdane|frakcj\w*|geofenc\w*)\b"
ENGLISH = r"\b(Loading|Error|Submit|Cancel|Save|Settings|Search|Login|Logout|Next|Back|Close|Details|Overview|Driver|Bin|Total|undefined|null|NaN|TODO|Lorem|lorem)\b|\[object"

METRICS_JS = r"""() => {
  const vis = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0'; };
  const name = el => (el.getAttribute('aria-label') || el.innerText || el.value || el.title || el.tagName).trim().replace(/\s+/g, ' ').slice(0, 50);
  const skip = el => el.closest('.leaflet-container, .chart-body, canvas, .kiosk-qr-code');
  const inter = [...document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button]')]
    .filter(el => !skip(el));
  const small = [];
  for (const el of inter) {
    const box = (el.matches('input') && el.closest('label')) ? el.closest('label') : el;
    if (!vis(box) || getComputedStyle(el).display === 'inline' && el.closest('p, li, dd, td, span.hint')) continue;
    const r = box.getBoundingClientRect();
    if (r.width < 44 || r.height < 44) small.push(`${name(el)} (${Math.round(r.width)}×${Math.round(r.height)})`);
  }
  const textEls = [...document.querySelectorAll('body *')].filter(el => !skip(el) && vis(el)
    && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()));
  const count = (arr) => arr.reduce((m, k) => (m[k] = (m[k] || 0) + 1, m), {});
  const colors = [], bgs = [];
  for (const el of [...document.querySelectorAll('body *')].filter(el => !skip(el) && vis(el))) {
    const s = getComputedStyle(el);
    if ([...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) colors.push(s.color);
    if (s.backgroundColor !== 'rgba(0, 0, 0, 0)') bgs.push(s.backgroundColor);
  }
  const clipped = textEls.filter(el => { const s = getComputedStyle(el);
    return (s.overflow !== 'visible' || s.textOverflow === 'ellipsis') && (el.scrollWidth > el.clientWidth + 1); })
    .map(el => name(el)).slice(0, 12);
  const sel = q => [...document.querySelectorAll(q)].filter(vis);
  return {
    title: document.title,
    hscroll: document.documentElement.scrollWidth > innerWidth,
    pageHeight: document.documentElement.scrollHeight,
    headings: sel('h1, h2, h3').map(h => `${h.tagName}: ${name(h)}`).slice(0, 25),
    fonts: count(textEls.map(el => getComputedStyle(el).fontFamily.split(',')[0].replace(/"/g, ''))),
    fontSizes: count(textEls.map(el => getComputedStyle(el).fontSize)),
    colors: count(colors), backgrounds: count(bgs),
    radii: count(sel('.btn, .card, .input, .select, .badge, .chip').map(el => getComputedStyle(el).borderRadius)),
    btnHeights: count(sel('.btn').map(el => Math.round(el.getBoundingClientRect().height) + 'px')),
    smallTargets: small.slice(0, 25), smallTargetsN: small.length,
    clipped, imgsNoAlt: sel('img:not([alt])').length,
    unnamedButtons: sel('button, a[href]').filter(el => !name(el) || name(el) === el.tagName).length,
    text: document.body.innerText.replace(/\s+/g, ' ').slice(0, 6000),
  };
}"""

FOCUS_JS = r"""() => { const el = document.activeElement; if (!el || el === document.body) return null;
  const s = getComputedStyle(el), r = el.getBoundingClientRect();
  return { el: (el.getAttribute('aria-label') || el.innerText || el.value || el.tagName).trim().replace(/\s+/g, ' ').slice(0, 40),
           visible: (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || s.boxShadow !== 'none',
           onScreen: r.bottom > 0 && r.top < innerHeight }; }"""


def rgb(c):
    m = re.match(r"rgba?\((\d+), (\d+), (\d+)(?:, ([\d.]+))?\)", c)
    return (tuple(map(int, m.groups()[:3])), float(m.group(4) or 1)) if m else (None, 0)


def off_token(counts):
    """Kolory pełne (alfa 1) spoza tokens.css: kandydaci na „kolory wpisane na sztywno”."""
    return {c: n for c, n in counts.items() if (v := rgb(c))[0] and v[1] == 1 and v[0] not in TOKENS}


def watch(pg, errs):
    pg.on("pageerror", lambda e: errs.append("JS: " + str(e)[:160]))
    pg.on("console", lambda m: m.type == "error" and errs.append("konsola: " + m.text[:160]))
    pg.on("response", lambda r: r.status >= 400 and "favicon" not in r.url and errs.append(f"{r.status} {r.url.replace(BASE, '')}"))


def probe(b, vp, name, path, out_dir, report):
    w, h = VP[vp]
    ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=vp == "telefon", has_touch=vp == "telefon")
    pg, errs = ctx.new_page(), []
    watch(pg, errs)
    pg.goto(BASE + path, wait_until="networkidle")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=out_dir / vp / f"{name}.png")
    pg.screenshot(path=out_dir / vp / f"{name}-cala.png", full_page=True)
    m = pg.evaluate(METRICS_JS)
    m["offTokenColors"], m["offTokenBackgrounds"] = off_token(m.pop("colors")), off_token(m.pop("backgrounds"))
    text = m.pop("text")
    m["jargon"] = sorted(set(x.group(0) for x in re.finditer(JARGON, text)))
    m["english"] = sorted(set(x.group(0) for x in re.finditer(ENGLISH, text)))
    pg.mouse.click(1, 1)
    tabs = []
    for _ in range(12):
        pg.keyboard.press("Tab")
        if (f := pg.evaluate(FOCUS_JS)):
            tabs.append(f)
    m["tabOrder"] = tabs
    m["focusInvisible"] = [t["el"] for t in tabs if not t["visible"]]
    if AXE:
        pg.add_script_tag(content=AXE)
        res = pg.evaluate("axe.run(document, {runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']})")
        m["axe"] = [{"id": x["id"], "impact": x["impact"], "n": len(x["nodes"]), "cel": x["nodes"][0]["target"] if x["nodes"] else None}
                    for x in res["violations"]]
    m["errors"] = errs[:10]
    if vp == "laptop":  # powiększenie 200% = połowa szerokości laptopa przy skali 2
        z = b.new_context(viewport={"width": w // 2, "height": h // 2}, device_scale_factor=2).new_page()
        z.goto(BASE + path, wait_until="networkidle")
        z.wait_for_timeout(800)
        m["zoom200_hscroll"] = z.evaluate("document.documentElement.scrollWidth > innerWidth")
        z.context.close()
    ctx.close()
    report.setdefault(name, {})[vp] = m
    print(f"{vp:<8} {name:<18} scroll={m['hscroll']!s:<5} małe={m['smallTargetsN']:<3} axe={len(m.get('axe', []))} błędy={len(errs)}")


class Flow:
    """Jedna ścieżka jury w nowej sesji: liczy kliknięcia od strony startowej."""

    def __init__(self, b, vp):
        w, h = VP[vp]
        self.ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=vp == "telefon", has_touch=vp == "telefon")
        self.pg, self.errs, self.clicks, self.steps = self.ctx.new_page(), [], 0, []
        watch(self.pg, self.errs)

    def go(self, path):
        self.pg.goto(BASE + path, wait_until="networkidle")
        self.steps.append(path)

    def click(self, sel, what=None):
        loc = self.pg.locator(sel).first
        loc.wait_for(state="visible", timeout=20000)
        loc.click(timeout=10000)
        self.clicks += 1
        self.steps.append(what or sel)
        self.pg.wait_for_timeout(500)

    def result(self, name, budget, ok, note=""):
        r = {"sciezka": name, "budzet": budget, "klikniecia": self.clicks, "ok": ok, "w_budzecie": ok and self.clicks <= budget,
             "kroki": self.steps, "uwagi": note, "bledy": self.errs[:6]}
        self.ctx.close()
        return r


def flows(b, vp):
    out = []

    def run(name, budget, fn):
        f = Flow(b, vp)
        try:
            note = fn(f) or ""
            out.append(f.result(name, budget, True, note))
        except Exception as e:  # noqa: BLE001 – nieudany krok to znalezisko, nie awaria sondy
            out.append(f.result(name, budget, False, f"przerwane: {str(e).splitlines()[0][:160]}"))
        r = out[-1]
        print(f"{vp:<8} {name:<58} {r['klikniecia']}/{budget} {'OK' if r['w_budzecie'] else 'PONAD' if r['ok'] else 'BŁĄD'} {r['uwagi'][:80]}")

    for label in ("Panel kosza", "Mieszkaniec", "Kierowca", "Dyspozytor", "Dashboard"):
        run(f"Wejść w perspektywę: {label}", 1, lambda f, l=label: (f.go("/"), f.click(f'.switcher a[title="{l}"]', l))[-1])

    nr = {}

    def send_report(f, count=True):
        f.go("/kosz/18/zglos")  # skan kodu QR aparatem: 0 kliknięć w aplikacji (stały adres demo daje dzisiejszy token)
        if count:
            f.click('label.m-type:has(input[value="przepelniony"])', "Przepełniony")
            f.click("#m-send", "Wyślij zgłoszenie")
        else:
            f.pg.click('label.m-type:has(input[value="przepelniony"])')
            f.pg.click("#m-send")
        f.pg.locator("#m-success").wait_for(state="visible", timeout=15000)
        return f.pg.locator("#m-nr").inner_text()

    def report_qr(f):
        nr["nr"] = send_report(f)
        return f"numer {nr['nr']}"
    run("Mieszkaniec: zgłosić przepełniony kosz (QR)", 2, report_qr)

    def report_panel(f):
        f.go("/")
        f.click('.switcher a[title="Panel kosza"]', "Panel kosza")
        f.click('[data-typ="przepelniony"]', "Przepełniony (przycisk na panelu)")
        f.pg.locator("#k-ack.ok").wait_for(state="visible", timeout=8000)
        return f.pg.locator("#k-ack").inner_text().splitlines()[0]
    run("Mieszkaniec: zgłosić z panelu kosza", 3, report_panel)

    def status(f):
        mine = send_report(f, count=False)  # przygotowanie w tym samym kontekście (localStorage), bez liczenia kliknięć
        f.steps = [f"(przygotowanie: wysłane {mine})"]
        f.go("/")
        f.click('.switcher a[title="Mieszkaniec"]', "Mieszkaniec")
        f.click(f'#m-mine a[href="/zgloszenie/{mine}"]', "moje zgłoszenie na liście „Twoje zgłoszenia”")
        f.pg.locator("#st-title[data-status]").wait_for(state="visible", timeout=8000)
        return f"status: {f.pg.locator('#st-title').inner_text().strip()}"
    run("Mieszkaniec: sprawdzić status swojego zgłoszenia", 2, status)

    def empty(f):
        f.go("/")
        f.click('.switcher a[title="Kierowca"]', "Kierowca")
        f.click("#k-stops a", "pierwszy kosz na trasie")
        f.click('[data-akcja="oprozniono"]', "Opróżniono")
        f.pg.wait_for_timeout(800)
        if f.pg.locator("#k-doneok").is_hidden():
            f.click(".k-lv", "poziom w koszu")
            f.click('[data-akcja="oprozniono"]', "Opróżniono (ponownie)")
            f.pg.locator("#k-doneok").wait_for(state="visible", timeout=8000)
            return "„Opróżniono” wymaga najpierw wybrania poziomu"
    run("Kierowca: oznaczyć kosz jako opróżniony", 2, empty)

    def dispatch(f):
        f.go("/")
        f.click('.switcher a[title="Dyspozytor"]', "Dyspozytor")
        f.pg.locator(".dp-item .btn-add").first.wait_for(state="visible", timeout=10000)
        f.click(".dp-item .btn-add", "„Dodaj do kursu” przy pierwszym pilnym koszu")
        f.pg.locator(".dp-added").first.wait_for(state="visible", timeout=8000)
        note = f.pg.locator(".dp-added").first.inner_text().strip()
        with f.pg.expect_response(lambda r: "/api/dyspozytor/cofnij" in r.url):  # sprzątanie po sondzie (bez liczenia)
            f.pg.click("[data-undo]")  # czekamy na zapis: przerwane żądanie zostawiłoby kosz na trasie na 24 h
        assert f.pg.request.get(BASE + "/api/dyspozytor/dodane").json()["dodane"] == [], "sonda nie cofnęła „Dodaj do kursu”"
        return note
    run("Dyspozytor: dodać pilny kosz do najbliższego kursu", 2, dispatch)

    def dash_filter(f):
        f.go("/")
        f.click('.switcher a[title="Dashboard"]', "Dashboard")
        f.click('.seg label:has(input[value="kwartal"])', "Okres: Kwartał")
        f.pg.locator("#f-dzielnica option").nth(1).wait_for(state="attached", timeout=6000)
        f.pg.select_option("#f-dzielnica", index=1)
        f.clicks += 1
        f.steps.append("Dzielnica (lista: 2 dotknięcia fizycznie)")
    run("Dashboard: przefiltrować po dzielnicy i okresie", 2, dash_filter)

    def project(f):
        f.go("/")
        f.click('.switcher a[title="Dashboard"]', "Dashboard")
        f.click("#d-projects a", "karta projektu")
        f.pg.wait_for_url("**/dashboard/projekty/**", timeout=6000)
    run("Dashboard: przejść do szczegółów projektu", 2, project)

    def scenario(f):
        f.go("/")
        f.click("[data-start-scenario]", "Zacznij scenariusz demo")
        f.click('#sc-pick .sc-var:has(input[value="A"])', "Wariant A (kod QR)")  # losowanie wybiera wariant; ścieżka mierzy A
        f.click("#sc-pick [data-go]", "Zacznij")
        f.pg.wait_for_url("**/panel/**", timeout=8000)
        f.click("a.kiosk-qr-code", "Kod QR na panelu (zamiast aparatu)")
        f.pg.wait_for_url("**/zglos/**", timeout=8000)
        f.click('label.m-type:has(input[value="przepelniony"])', "Przepełniony")
        f.click("#m-send", "Wyślij")
        f.pg.locator("#m-success").wait_for(state="visible", timeout=15000)
        for _ in range(4):  # panel → dyspozytor → trasa kierowcy → karta kosza
            f.click('[data-sc="next"]', "Scenariusz: Dalej")
        f.click('[data-akcja="jade"]', "Jadę")
        f.pg.wait_for_timeout(1500)
        if f.pg.locator(".k-lv input:checked").count() == 0:
            f.click(".k-lv", "poziom w koszu")
        f.click('[data-akcja="oprozniono"]', "Opróżniono")
        f.click('[data-sc="next"]', "Scenariusz: Dalej")
        f.click('[data-sc="next"]', "Scenariusz: Dalej")
        f.click('[data-sc="end"]', "Zakończ")
        return "wariant A, 7 kroków"
    run("Scenariusz demo do końca (wariant A)", 3 + 8, scenario)  # +1: krok „Dyspozytor widzi zgłoszenie”

    def switch_any(f):
        bad = []
        for name, path in PAGES.items():
            f.go(path)
            if f.pg.locator(".switcher a").filter(has=f.pg.locator("span")).count() < 4 or not f.pg.locator(".switcher").is_visible():
                bad.append(name)
        f.steps = [f"bez przełącznika perspektyw: {', '.join(bad) or 'brak'}"]
        f.clicks = 2 if bad else 1
        return f"ekrany bez przełącznika: {bad}" if bad else ""
    run("Z dowolnego ekranu do innej perspektywy", 1, switch_any)
    return out, nr.get("nr")


with sync_playwright() as p:
    for vp in VP:
        (OUT / vp).mkdir(parents=True, exist_ok=True)
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    print("reset demo:", pg.evaluate("fetch('/api/demo/reset', {method: 'POST'}).then(r => r.status)"))
    pg.close()
    report = {}
    for name, path in ({} if "--budzety" in sys.argv else PAGES).items():
        for vp in (("kiosk", "telefon") if name == "panel-18" else ("laptop", "telefon")):
            probe(b, vp, name, path, OUT, report)
    budgets = {}
    for vp in ("laptop", "telefon"):
        budgets[vp], nr = flows(b, vp)
        if nr and vp == "laptop":
            for v in ("laptop", "telefon"):
                probe(b, v, "zgloszenie-status", f"/zgloszenie/{nr}", OUT, report)
            probe(b, "kiosk", "panel-18-po-akcjach", "/panel/18", OUT, report)
    b.close()
if "--budzety" in sys.argv and (OUT / "metryki.json").exists():  # tylko ścieżki: dopisz, nie nadpisuj ekranów
    report = {**json.loads((OUT / "metryki.json").read_text(encoding="utf-8")), **report}
if report:
    (OUT / "metryki.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "budzety.json").write_text(json.dumps(budgets, ensure_ascii=False, indent=1), encoding="utf-8")
print("zapisano", OUT)
