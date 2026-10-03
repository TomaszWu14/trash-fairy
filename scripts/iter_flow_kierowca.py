"""Pętla jakości: przepływ kierowcy (lista → karta kosza → Jadę z nawigacją → Opróżniono), zrzuty do audit/iteracje/."""
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5050"
rnd = sys.argv[1] if len(sys.argv) > 1 else "1"
out = pathlib.Path(__file__).resolve().parent.parent / "audit" / "iteracje"
with sync_playwright() as p:
    b = p.chromium.launch()
    for vp, size in (("desktop", (1920, 1080)), ("telefon", (390, 844))):
        pg = b.new_page(viewport={"width": size[0], "height": size[1]})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:200]))
        shot = lambda n: pg.screenshot(path=out / f"kierowca-{n}-r{rnd}-{vp}.png")
        pg.goto(BASE + "/kierowca", wait_until="networkidle"); pg.wait_for_timeout(2000); shot("1-trasa")
        pg.goto(BASE + "/kierowca/kosz/18", wait_until="networkidle"); pg.wait_for_timeout(1500); shot("2-kosz")
        pg.click("[data-akcja=jade]"); pg.wait_for_timeout(3000); shot("3-nawigacja")
        pg.wait_for_timeout(15000); shot("4-na-miejscu")
        pg.click("[data-akcja=oprozniono]"); pg.wait_for_timeout(1200); shot("5-oprozniono")
        print(vp, "błędy:", errs or "brak")
        pg.close()
    b.close()
