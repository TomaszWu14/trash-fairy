"""Strażnik trybu „Podpowiedzi” (app/static/ui/help.js + podpowiedzi.json) na żywym serwerze 127.0.0.1:5050.

Sprawdza na każdej stronie: (1) widoczne elementy interaktywne w <main> mają przodka [data-help] (raport braków),
(2) każdy klucz data-help ma pełną treść w JSON, (3) klucze JSON niewidziane nigdzie i nieistniejące selektory przewodników
i powitania (ostrzeżenia), (4) po wyłączeniu podpowiedzi nie ma widocznych ikonek „i”, (5) automat (navigator.webdriver)
bez ?powitanie=1 nie dostaje powitania ani propozycji przewodnika, (6) _powitanie: 5–7 kroków, każdy z tytul i tekst.
Kod wyjścia 1: (2), (4), (5) albo (6); z --scisle także (1).   Użycie: python scripts/check_help.py [--scisle]
"""
import json
import pathlib
import sys
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5050"
QR = "/zglos/18?qr={qr}"  # dzisiejszy token kosza 18 z kodu QR na jego panelu (data-qr w #kiosk)
PAGES = ["/", "/panel/18", "/zglos", QR, "/wysypisko", "/kierowca", "/kierowca/kosz/18", "/dyspozytor", "/dashboard",
         "/dashboard/urzadzenia", "/dashboard/projekty/odbiory-na-zadanie-stare-miasto", "/metodologia"]
INTERACTIVE = "button, a.btn, input:not([type=hidden]), select, textarea, [role=radiogroup], .kpi, [data-chart]"
TXT = json.loads((pathlib.Path(__file__).resolve().parent.parent / "app/static/ui/podpowiedzi.json").read_text(encoding="utf-8"))
TOURS = TXT.pop("_przewodniki", {})
WELCOME = TXT.pop("_powitanie", [])

MISSING_JS = """sel => [...document.querySelectorAll(`main :is(${sel})`)]
  .filter(e => !e.matches('.help-i') && e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden' && !e.closest('[data-help]'))
  .map(e => `${e.tagName.toLowerCase()}${e.id ? '#' + e.id : ''}${[...e.classList].map(c => '.' + c).join('')}`
          + ` „${(e.getAttribute('aria-label') || e.textContent || e.value || '').trim().replace(/\\s+/g, ' ').slice(0, 40)}”`)"""
VISIBLE_ICONS = "() => [...document.querySelectorAll('.help-i')].filter(e => e.getClientRects().length).length"


def load(pg, url):
    """Serwer dev przeładowuje się po każdej zmianie pliku: kilka prób zamiast fałszywego alarmu."""
    for attempt in range(5):
        try:
            pg.goto(url, wait_until="networkidle")
            return pg.wait_for_function("window.TF?.help?.ready", timeout=15000)
        except Exception:
            if attempt == 4:
                raise
            pg.wait_for_timeout(4000)


def bad_entry(v):
    return not isinstance(v, dict) or not all(v.get(k) for k in ("tytul", "cel", "zrodlo")) or not (v.get("przyklad") or v.get("jak_czytac"))


def welcome_errors(steps):
    errs = [] if 5 <= len(steps) <= 7 else [f"JSON: _powitanie ma {len(steps)} kroków (ma mieć 5–7)"]
    return errs + [f"JSON: _powitanie, krok {i + 1} bez tytul albo tekst" for i, s in enumerate(steps) if not (s.get("tytul") and s.get("tekst"))]


def main():
    strict = "--scisle" in sys.argv
    errors, warnings, seen = [], [], set()
    errors += [f"JSON: „{k}” bez tytul/cel/zrodlo albo bez przyklad|jak_czytac" for k, v in TXT.items() if bad_entry(v)]
    errors += welcome_errors(WELCOME)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1366, "height": 900})
        missing_total = 0
        for path in PAGES:
            pg = ctx.new_page()
            if path == QR:
                load(pg, BASE + "/panel/18")
                qr = urlsplit(pg.get_attribute("#kiosk", "data-qr"))
                path = f"{qr.path}?{qr.query}"
            load(pg, BASE + path)
            pg.wait_for_timeout(1500)  # treść renderowana w JS (dashboard, trasa), ponowne skanowanie i zwłoka propozycji przewodnika
            keys = set(pg.evaluate("() => [...document.querySelectorAll('[data-help]')].map(e => e.dataset.help)"))
            seen |= keys
            errors += [f"{path}: data-help=„{k}” nie ma treści w podpowiedzi.json" for k in sorted(keys) if k not in TXT]
            if pg.evaluate("!!document.querySelector('.tour, .tour-offer')"):
                errors.append(f"{path}: automat bez ?powitanie=1 dostał powitanie albo propozycję przewodnika")
            page_id = pg.evaluate("TF.help.page()")
            for s in TOURS.get(page_id, []):
                if not pg.query_selector(s["sel"]):
                    warnings.append(f"{path}: przewodnik „{page_id}” — selektor {s['sel']} nie istnieje")
            if path == "/":
                warnings += [f"/: powitanie — selektor {s['sel']} nie istnieje (krok pokaże się bez podświetlenia)"
                             for s in WELCOME if s.get("sel") and not pg.query_selector(s["sel"])]
            missing = pg.evaluate(MISSING_JS, INTERACTIVE)
            missing_total += len(missing)
            print(f"\n{path}  (strona „{page_id}”, kluczy: {len(keys)}, ikonek: {pg.evaluate(VISIBLE_ICONS)}, bez data-help: {len(missing)})")
            for m in missing:
                print("   brak:", m)
            toggle = pg.query_selector(".help-toggle:not([hidden])")
            if toggle:
                toggle.click()
            else:  # panel kosza nie ma nagłówka: ten sam stan przez localStorage
                pg.evaluate("localStorage.setItem('tf-podpowiedzi', '0')")
                load(pg, BASE + path)
            pg.wait_for_timeout(300)
            if (n := pg.evaluate(VISIBLE_ICONS)):
                errors.append(f"{path}: po wyłączeniu podpowiedzi widać {n} ikonek „i”")
            pg.evaluate("localStorage.setItem('tf-podpowiedzi', '1')")
            pg.close()
        b.close()
    warnings += [f"JSON: klucz „{k}” nie występuje na żadnej sprawdzanej stronie" for k in sorted(set(TXT) - seen)]
    print()
    for w in warnings:
        print("UWAGA:", w)
    for e in errors:
        print("BŁĄD:", e)
    print(f"\nPodsumowanie: {len(errors)} błędów, {len(warnings)} ostrzeżeń, {missing_total} elementów bez data-help"
          + (" (tryb --scisle)" if strict else ""))
    return 1 if errors or (strict and missing_total) else 0


if __name__ == "__main__":
    sys.exit(main())
