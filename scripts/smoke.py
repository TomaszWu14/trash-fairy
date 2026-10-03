"""Smoke test pokazu (decyzja 37): 10 przepływów w prawdziwej przeglądarce, kod wyjścia 1 przy błędzie.

Użycie: DEMO_PASSWORD=… python scripts/smoke.py [BASE_URL]   (domyślnie http://127.0.0.1:5050)
Poza pytest i requirements.txt: wymaga lokalnie `pip install playwright && playwright install chromium`.
Uwaga: przewija zegar demo i zgłasza kosz 18 — na produkcji demo wraca do 13:30 samo po 30 min.
"""
import os
import sys

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5050").rstrip("/")
PASSWORD = os.environ.get("DEMO_PASSWORD", "")
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'OK  ' if ok else 'BŁĄD'} {name}{' — ' + str(detail) if detail else ''}")


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.goto(BASE + "/", wait_until="networkidle")
    page.wait_for_timeout(2000)
    check("1. / ma liczby i piny", page.text_content("#v1") not in ("–", None) and page.locator(".leaflet-marker-icon").count() > 0)
    before = page.text_content("#clock")
    page.click("#btn-advance")
    try:  # odpowiedź liczy trasy (OR-Tools + OSRM), więc czekamy na zmianę, a nie stały czas
        page.wait_for_function("b => document.getElementById('clock').textContent !== b", arg=before, timeout=10000)
    except Exception:
        pass
    after = page.text_content("#clock")
    check("2. Przewiń +1 h zmienia zegar (albo koniec scenariusza)", after != before or page.is_disabled("#btn-advance"), after)

    phone = browser.new_page(viewport={"width": 390, "height": 844})
    phone.goto(BASE + "/zglos/18?jury=1", wait_until="networkidle")
    phone.wait_for_timeout(1000)
    phone.click(".z-opt.full")
    phone.wait_for_timeout(3500)
    fresh = phone.evaluate("fetch('/api/points').then(r => r.json()).then(d => d.features.find(f => f.properties.id === 18).properties.fresh)")
    check("3. zgłoszenie kosza 18 jest świeże w API", fresh is True)

    page.goto(BASE + "/telefony", wait_until="networkidle")
    page.wait_for_timeout(3000)
    check("4. /telefony ma 3 ramki", page.locator("iframe").count() == 3)
    props = page.evaluate("fetch('/api/changes').then(r => r.json()).then(d => Object.keys(d.features[0].properties))")
    check("5. podgląd bez pól dyspozytora", not {"reliability", "check_reason", "crew_issue"} & set(props))

    if PASSWORD:
        page.goto(BASE + "/logowanie?next=/kierowca")
        page.fill("#login", "driver_bin")
        page.fill("#password", PASSWORD)
        page.click("button[type=submit]")
        page.wait_for_timeout(2500)
        check("6. driver_bin → /kierowca ze startem kursu", page.url.endswith("/kierowca") and page.locator("#begin").count() == 1, page.url)
    else:
        check("6. logowanie kierowcy (pominięte: brak DEMO_PASSWORD)", True)

    c = page.evaluate("fetch('/api/v1/conditions').then(r => r.json())")
    check("7. /api/v1/conditions z meta.synthetic", c.get("meta", {}).get("synthetic") is True)
    page.goto(BASE + "/api/docs", wait_until="networkidle")
    check("8. /api/docs wypisuje 4 endpointy", page.locator("section.c-doc-ep h2 code").count() == 4)
    page.goto(BASE + "/zglos/99999")
    check("9. 404 po polsku", "Nie znaleźliśmy" in page.content())

    widths = []
    for w in (390, 1440):
        pg = browser.new_page(viewport={"width": w, "height": 844})
        pg.goto(BASE + "/", wait_until="networkidle")
        widths.append(pg.evaluate("document.documentElement.scrollWidth") <= w)
        pg.close()
    check("10. bez poziomego scrolla na 390 i 1440 px", all(widths))
    check("brak błędów JS", not errors, errors[:2])
    browser.close()

print(f"\n{sum(results)}/{len(results)} OK")
sys.exit(0 if all(results) else 1)
