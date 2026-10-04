"""axe-core (WCAG 2.1 A/AA) na kluczowych ekranach; wynik do audit/lighthouse/axe.json, kod wyjścia 1 przy naruszeniach critical/serious.

Użycie: python scripts/axe_check.py <ścieżka do axe.min.js> [adres]   (axe-core z npm: node_modules/axe-core/axe.min.js)
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

AXE = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
BASE = sys.argv[2].rstrip("/") if len(sys.argv) > 2 else "http://127.0.0.1:5050"
PAGES = ["/", "/dashboard", "/dashboard/urzadzenia", "/panel/18", "/zglos", "/kierowca", "/kierowca/kosz/18", "/metodologia"]
report, bad = {}, 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for vp in ((1366, 768), (390, 844)):
        pg = b.new_page(viewport={"width": vp[0], "height": vp[1]})
        for path in PAGES:
            pg.goto(BASE + path, wait_until="networkidle")
            pg.wait_for_timeout(800)
            pg.add_script_tag(content=AXE)
            res = pg.evaluate("axe.run(document, {runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']})")
            v = [{"id": x["id"], "impact": x["impact"], "n": len(x["nodes"]),
                  "przyklad": x["nodes"][0]["target"] if x["nodes"] else None} for x in res["violations"]]
            report[f"{vp[0]}{path}"] = v
            bad += sum(1 for x in v if x["impact"] in ("critical", "serious"))
            print(f"{vp[0]:>5} {path:<22}", "OK" if not v else v)
        pg.close()
    b.close()
out = pathlib.Path(__file__).resolve().parent.parent / "audit" / "lighthouse" / "axe.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print("critical/serious:", bad)
sys.exit(1 if bad else 0)
