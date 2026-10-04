"""Etap 5: pełny scenariusz demo w prawdziwej przeglądarce + smoke wszystkich ekranów. Kod wyjścia 1 przy błędzie.

Użycie: python scripts/e2e_demo.py [BASE_URL]   (domyślnie http://127.0.0.1:5050; Playwright poza requirements.txt)
Uwaga: resetuje dane demo na początku i na końcu.
"""
import sys
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5050").rstrip("/")
SCREENS = ["/", "/panel/18", "/zglos", "/zglos/18", "/kierowca", "/kierowca/kosz/18", "/dashboard",
           "/dashboard/projekty/odbiory-na-zadanie-stare-miasto", "/metodologia", "/dostepnosc", "/prywatnosc", "/api/docs", "/nie-ma-takiej"]
VIEWPORTS = {"desktop": (1920, 1080), "laptop": (1366, 768), "telefon": (390, 844), "kiosk": (1280, 800)}
VP = {k: {"width": w, "height": h} for k, (w, h) in VIEWPORTS.items()}
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(f"{'OK  ' if ok else 'BŁĄD'} {name}{' — ' + str(detail) if detail else ''}")


def watch(page):
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)[:160]))
    page.on("console", lambda m: m.type == "error" and "404" not in m.text and errs.append(m.text[:160]))
    page.on("response", lambda r: r.status >= 500 and errs.append(f"{r.status} {r.url}"))
    return errs


def kpi(page, kid):
    return page.evaluate(f"fetch('/api/dashboard/kpi').then(r => r.json()).then(d => d.kpi.find(k => k.id === '{kid}').wartosc)")


with sync_playwright() as p:
    b = p.chromium.launch()
    # ---------- scenariusz: telefon mieszkańca + desktop ----------
    desk = b.new_page(viewport=VP["desktop"]); derr = watch(desk)
    desk.request.post(BASE + "/api/demo/reset")  # przycisk „Resetuj” przeładowuje stronę; tu reset przez API
    desk.goto(BASE + "/", wait_until="networkidle")
    z0, w0 = kpi(desk, "zgloszenia"), kpi(desk, "wywozy")
    desk.click(".hero [data-start-scenario]"); desk.wait_for_load_state("networkidle"); desk.wait_for_selector("#chk-qr.ok", timeout=8000)
    check("1. scenariusz otwiera zgłoszenie z potwierdzonym kodem QR i od razu wyborem problemu",
          "/zglos/18?qr=" in desk.url and desk.locator("#chk-qr.ok").count() == 1 and desk.locator("input[name=typ]").count() == 4, desk.url)

    phone = b.new_page(viewport=VP["telefon"]); perr = watch(phone)
    phone.goto(desk.url, wait_until="networkidle")
    phone.click(".m-type:has(input[value=przepelniony])")
    phone.click(".m-more summary"); phone.fill("#m-komentarz", "Worki obok kosza")
    phone.click("#m-send"); phone.wait_for_selector("#m-success:not([hidden])", timeout=8000)
    nr = phone.text_content("#m-nr")
    check("2. mieszkaniec dostaje numer zgłoszenia", nr.startswith("TF-"), nr)
    phone.click("#m-status-link"); phone.wait_for_selector("#st-badge.badge.report", timeout=8000)
    check("3. status: przyjęte", "Przyjęte" in phone.text_content("#st-badge"))

    desk.goto(BASE + "/panel/18", wait_until="networkidle"); desk.wait_for_timeout(1500)
    check("4. panel kosza pokazuje zgłoszenie", "Zgłoszono" in desk.text_content("#k-msg") or "kierowca" in desk.text_content("#k-msg"),
          desk.text_content("#k-msg").strip()[:60])
    desk.goto(BASE + "/kierowca", wait_until="networkidle"); desk.wait_for_timeout(1500)
    ids = desk.eval_on_selector_all("#k-stops a", "a => a.map(x => x.getAttribute('href'))")
    check("5. kosz 18 na liście kierowcy wśród zgłoszonych", "/kierowca/kosz/18" in ids[:15], ids[:3])
    desk.goto(BASE + "/kierowca/kosz/18", wait_until="networkidle")
    desk.click("[data-akcja=jade]"); desk.wait_for_selector("#k-navbar.arrived", timeout=25000)
    check("6. nawigacja w aplikacji dojeżdża do kosza", "na miejscu" in desk.text_content("#k-nav-t"))
    desk.click("input[name=poziom][value='100']", force=True); desk.click("[data-akcja=oprozniono]")
    desk.wait_for_selector("#k-doneok:not([hidden])", timeout=8000)
    check("7. kierowca oznacza „Opróżniono”", True)

    phone.wait_for_timeout(4000)
    check("8. status u mieszkańca: zrealizowane (bez przeładowania)", "Zrealizowane" in phone.text_content("#st-badge"), phone.text_content("#st-badge"))
    desk.goto(BASE + "/panel/18", wait_until="networkidle"); desk.wait_for_timeout(1200)
    check("9. panel: opróżniono", "Opróżniono" in desk.text_content("#k-msg"), desk.text_content("#k-msg").strip()[:60])
    z1, w1 = kpi(desk, "zgloszenia"), kpi(desk, "wywozy")
    check("10. dashboard liczy zgłoszenie i wywóz ze scenariusza", z1 == z0 + 1 and w1 == w0 + 1, f"zgłoszenia {z0}→{z1}, wywozy {w0}→{w1}")
    check("brak błędów JS w scenariuszu", not derr and not perr, (derr + perr)[:3])
    phone.close()

    # ---------- smoke: każdy ekran × każda rozdzielczość ----------
    links = set()
    for vp, size in VIEWPORTS.items():
        pg = b.new_page(viewport={"width": size[0], "height": size[1]}); errs = watch(pg)
        for path in SCREENS:
            r = pg.goto(BASE + path, wait_until="networkidle"); pg.wait_for_timeout(600)
            want = 404 if path == "/nie-ma-takiej" else 200
            hs = pg.evaluate("document.documentElement.scrollWidth") > size[0]
            if r.status != want or hs:
                check(f"{vp} {path}", False, f"HTTP {r.status}{', poziomy scroll' if hs else ''}")
            if vp == "desktop":
                links |= {urljoin(pg.url, h).split("#")[0] for h in pg.eval_on_selector_all("a[href]", "a => a.map(x => x.getAttribute('href'))")}
        check(f"smoke {vp}: {len(SCREENS)} ekranów bez 5xx i błędów JS", not errs, errs[:3])
        pg.close()
    dead = [u for u in links - {BASE + "/nie-ma-takiej"} if urlparse(u).netloc == urlparse(BASE).netloc and desk.request.get(u).status >= 400]
    check(f"brak martwych linków ({len(links)} sprawdzonych)", not dead, dead[:5])

    # ---------- dashboard: każdy filtr, także pusty wynik ----------
    pg = b.new_page(viewport=VP["desktop"]); errs = watch(pg)
    for q in ["", "?okres=kwartal", "?okres=rok", "?dzielnica=Krowodrza", "?frakcja=szklo", "?projekt=odbiory-na-zadanie-stare-miasto",
              "?od=2026-09-01&do=2026-09-30", "?od=2020-01-01&do=2020-01-31", "?dzielnica=Nowa%20Huta&frakcja=bio"]:
        pg.goto(BASE + "/dashboard" + q, wait_until="networkidle"); pg.wait_for_timeout(1200)
        drawn = pg.evaluate("""[...document.querySelectorAll('.chart-body')].every(el =>
            el.querySelector('.chart-empty') || el.querySelector('svg, canvas, .leaflet-pane'))""")
        check(f"dashboard{q or ' (domyślnie)'}: każdy wykres narysowany albo pusty stan", drawn)
    check("dashboard: brak błędów JS przy filtrach", not errs, errs[:3])
    pg.request.post(BASE + "/api/demo/reset")
    b.close()

print(f"\n{sum(results)}/{len(results)} OK")
sys.exit(0 if all(results) else 1)
