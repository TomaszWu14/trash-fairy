"""Pętla jakości: przepływ mieszkańca na telefonie (390×844), zrzuty każdego kroku do audit/iteracje/."""
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5050"
rnd = sys.argv[1] if len(sys.argv) > 1 else "1"
out = pathlib.Path(__file__).resolve().parent.parent / "audit" / "iteracje"
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    for vp, size in (("telefon", (390, 844)), ("desktop", (1920, 1080))):
        pg = b.new_page(viewport={"width": size[0], "height": size[1]})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:200]))
        pg.request.post(BASE + "/api/demo/reset")
        shot = lambda n: pg.screenshot(path=out / f"mieszkaniec-{n}-r{rnd}-{vp}.png")
        pg.goto(BASE + "/zglos", wait_until="networkidle"); pg.wait_for_timeout(1500); shot("1-wybor")
        pg.click("[data-scan]"); pg.wait_for_timeout(500); shot("2-skan")
        pg.click("#scan-dialog a.btn-primary"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(800); shot("3-krok1")
        pg.click("[data-geo-sim]"); pg.wait_for_timeout(300); shot("4-krok1-ok")
        pg.click("[data-next='2']"); pg.wait_for_timeout(400)
        pg.click(".m-type:has(input[value=przepelniony])"); pg.fill("#m-komentarz", "Worki z domowymi śmieciami obok kosza"); shot("5-krok2")
        pg.click("#to-3"); pg.wait_for_timeout(400); shot("6-krok3")
        pg.click("#m-send"); pg.wait_for_timeout(1200); shot("7-sukces")
        pg.click("#m-status-link"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(1200); shot("8-status")
        print(vp, "błędy:", errs or "brak")
        pg.close()
    b.close()
