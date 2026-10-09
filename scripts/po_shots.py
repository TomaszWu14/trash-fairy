"""Zrzuty „po” do audit/PRZED-PO.html i README: każda perspektywa w 4 rozdzielczościach → audit/zrzuty/po/<vp>/<nazwa>.png.

Użycie (serwer lokalny na 5050, ta sama SECRET_KEY co serwer): python scripts/po_shots.py [adres]
Podgląd motywu: python scripts/po_shots.py --motyw ciemny|jasny [--tylko przeglad,panel-18] [adres]
  → audit/motyw/<motyw>/<vp>/<nazwa>.png, całe strony, laptop i telefon (panel także kiosk)
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from app import create_app  # noqa: E402
from app.api_pl import qr_token  # noqa: E402

args = sys.argv[1:]


def opt(k):
    """Wyjmuje z argumentów parę „--k wartość”."""
    if k not in args:
        return None
    i = args.index(k)
    v = args[i + 1]
    del args[i:i + 2]
    return v


MOTYW, TYLKO = opt("--motyw"), opt("--tylko")
assert MOTYW in (None, "ciemny", "jasny"), "--motyw ciemny|jasny"
BASE = args[0].rstrip("/") if args else "http://127.0.0.1:5050"
VP = {"desktop": (1920, 1080), "laptop": (1366, 768), "telefon": (390, 844), "kiosk": (1280, 800)}
if MOTYW:
    VP.pop("desktop")
with create_app().app_context():
    QR = qr_token(18)
PAGES = {  # nazwa → adres
    "przeglad": "/",
    "panel-18": "/panel/18",
    "panel-18-urzadzenie": "/panel/18?urzadzenie=1",
    "zglos-wybor": "/zglos",
    "zglos-18": f"/zglos/18?qr={QR}",
    "kierowca": "/kierowca",
    "kierowca-kosz-18": "/kierowca/kosz/18",
    "dashboard": "/dashboard",
    "dashboard-projekt": "/dashboard/projekty/odbiory-na-zadanie-stare-miasto",
    "urzadzenia": "/dashboard/urzadzenia",
    "metodologia": "/metodologia",
}
if TYLKO:
    PAGES = {k: v for k, v in PAGES.items() if k in TYLKO.split(",")}
root = pathlib.Path(__file__).resolve().parent.parent / "audit"
out = root / "motyw" / MOTYW if MOTYW else root / "zrzuty" / "po"
with sync_playwright() as p:
    b = p.chromium.launch()
    for vp, (w, h) in VP.items():
        (out / vp).mkdir(parents=True, exist_ok=True)
        ctx = b.new_context(viewport={"width": w, "height": h})
        if MOTYW:  # motyw jak po kliknięciu przełącznika (base.html czyta localStorage przed CSS)
            ctx.add_init_script(f"try {{ localStorage.setItem('tf-motyw', '{'dark' if MOTYW == 'ciemny' else 'light'}'); }} catch (e) {{}}")
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e, errs=errs: errs.append(str(e)[:160]))
        for name, path in PAGES.items():
            if MOTYW and vp == "kiosk" and not name.startswith("panel"):
                continue
            errs.clear()
            for proba in range(3):  # serwer --debug przeładowuje się po zmianach w kodzie: krótka przerwa i ponowienie
                try:
                    pg.goto(BASE + path, wait_until="networkidle", timeout=90000)
                    break
                except Exception:
                    if proba == 2:
                        raise
                    pg.wait_for_timeout(5000)
            pg.wait_for_timeout(1200)
            pg.screenshot(path=out / vp / f"{name}.png", full_page=bool(MOTYW))
            print(vp, name, "błędy:", errs or "brak")
        ctx.close()
    b.close()
