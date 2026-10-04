"""Pętla jakości: zrzuty ekranu w kolejnych rundach do audit/iteracje/ (1920×1080, 390×844, 1280×800, opcjonalnie 1366×768).

Użycie: python scripts/iter_shots.py <nazwa> <runda> <ścieżka> [desktop,telefon,kiosk,laptop] [--full]
Motyw: zmienna TF_MOTYW=dark|light (domyślnie motyw aplikacji); nazwa pliku dostaje wtedy sufiks -dark/-light.
Wypisuje błędy JS i odpowiedzi ≥ 400, żeby każda runda od razu pokazywała regresje.
"""
import os
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5050"
VP = {"desktop": (1920, 1080), "telefon": (390, 844), "kiosk": (1280, 800), "laptop": (1366, 768)}
name, rnd, path = sys.argv[1], sys.argv[2], sys.argv[3]
vps = (sys.argv[4] if len(sys.argv) > 4 and not sys.argv[4].startswith("--") else "desktop,telefon").split(",")
full = "--full" in sys.argv
motyw = os.environ.get("TF_MOTYW", "")
out = pathlib.Path(__file__).resolve().parent.parent / "audit" / "iteracje"
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    for vp in vps:
        w, h = VP[vp]
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        if motyw:
            pg.add_init_script(f"try {{ localStorage.setItem('tf-motyw', '{motyw}') }} catch (e) {{}}")
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text[:200]))
        pg.on("response", lambda r: r.status >= 400 and errs.append(f"{r.status} {r.url}"))
        pg.goto(BASE + path, wait_until="networkidle")
        pg.wait_for_timeout(1500)
        f = out / f"{name}-r{rnd}-{vp}{'-' + motyw if motyw else ''}.png"
        pg.screenshot(path=f, full_page=full)
        hs = pg.evaluate("document.documentElement.scrollWidth") > w
        print(f, "| poziomy scroll!" if hs else "", "| błędy:", errs[:4] if errs else "brak")
        pg.close()
    b.close()
