"""Zrzuty „po” do audit/PRZED-PO.html i README: każda perspektywa w 4 rozdzielczościach → audit/zrzuty/po/<vp>/<nazwa>.png.

Użycie (serwer lokalny na 5050, ta sama SECRET_KEY co serwer): python scripts/po_shots.py [adres]
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from app import create_app  # noqa: E402
from app.api_pl import qr_token  # noqa: E402

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:5050"
VP = {"desktop": (1920, 1080), "laptop": (1366, 768), "telefon": (390, 844), "kiosk": (1280, 800)}
with create_app().app_context():
    QR = qr_token(18)
PAGES = {  # nazwa → adres
    "przeglad": "/",
    "panel-18": "/panel/18",
    "zglos-wybor": "/zglos",
    "zglos-18": f"/zglos/18?qr={QR}",
    "kierowca": "/kierowca",
    "kierowca-kosz-18": "/kierowca/kosz/18",
    "dashboard": "/dashboard",
    "dashboard-projekt": "/dashboard/projekty/odbiory-na-zadanie-stare-miasto",
    "urzadzenia": "/dashboard/urzadzenia",
    "metodologia": "/metodologia",
}
out = pathlib.Path(__file__).resolve().parent.parent / "audit" / "zrzuty" / "po"
with sync_playwright() as p:
    b = p.chromium.launch()
    for vp, (w, h) in VP.items():
        (out / vp).mkdir(parents=True, exist_ok=True)
        pg = b.new_page(viewport={"width": w, "height": h})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        for name, path in PAGES.items():
            errs.clear()
            pg.goto(BASE + path, wait_until="networkidle")
            pg.wait_for_timeout(1200)
            pg.screenshot(path=out / vp / f"{name}.png")
            print(vp, name, "błędy:", errs or "brak")
        pg.close()
    b.close()
