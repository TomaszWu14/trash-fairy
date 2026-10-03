"""Audyt UX: zrzuty każdego ekranu na 6 szerokościach + konsola, poziomy scroll, wolne żądania, czas zgłoszenia → mapa.

Użycie: python scripts/audit_screens.py [BASE_URL] [OUT_DIR]   (domyślnie http://127.0.0.1:5050, docs/audit/screens)
Wynik: PNG-i oraz docs/audit/screens/_findings.json z surowymi pomiarami do raportu.
"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5050"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "docs/audit/screens")
OUT.mkdir(parents=True, exist_ok=True)
WIDTHS = [360, 390, 768, 1024, 1440, 1920]
HEIGHTS = {360: 780, 390: 844, 768: 1024, 1024: 768, 1440: 900, 1920: 1080}
SLOW_MS = 300

# ekran → (ścieżka, akcje po załadowaniu: lista (nazwa_wariantu, js))
SCREENS = {
    "pokaz": ("/", [("krok3", None), ("krok1", "document.querySelector('.step[data-step=\"1\"]').click()"),
                    ("krok2", "document.querySelector('.step[data-step=\"2\"]').click()"),
                    ("krok4", "document.querySelector('.step[data-step=\"4\"]').click()")]),
    "dyspozytor": ("/dyspozytor", [("sytuacja", "showTab('sytuacja')"), ("trasy", "showTab('trasy')"),
                                   ("wrozka", "showTab('wrozka')"), ("program", "showTab('program')"),
                                   ("szczegoly", "document.querySelector('#point-list button[data-id]').click()")]),
    "zglos": ("/zglos/18?jury=1", [("start", None), ("sending", "pick('full')"),
                                   ("far", "S.dist=280; setScreen('far')"), ("limit", "S.retryAt='13:54'; setScreen('limit')"),
                                   ("error", "setScreen('error')"), ("offline", "S.queuedAt='13:24'; setScreen('offline')"),
                                   ("nosignal", "setScreen('nosignal')"),
                                   ("sent", "S.result={status:'accepted',accepted_at:'13:30',eta:'14:00',route:'kurs 14:00',others_count:0,report_id:1}; setScreen('sent')"),
                                   ("dup", "S.result={status:'merged',merged_with_at:'13:11',accepted_at:'13:11',eta:'14:00',route:'kurs 14:00',others_count:2,report_id:1}; setScreen('dup')")]),
    "zglos-wybor": ("/zglos", [("lista", None)]),
    "epapier": ("/epapier/18", [("ekran", None)]),
    "ekipa": ("/ekipa", [("start", None)]),
    "kierowca": ("/kierowca", [("start", "localStorage.removeItem('tf-kierowca'); snap = null; go('start')"),
                               ("trasa", "document.getElementById('begin').click()"),
                               ("przystanek", "document.querySelector('[data-open]').click()"),
                               ("podsumowanie", "go('summary')")]),
    "404": ("/zglos/99999", [("start", None)]),
    "program": ("/program", [("start", None)]),
    "regulamin": ("/program/regulamin", [("start", None)]),
    "metodologia": ("/metodologia", [("start", None)]),
    "przycisk-stary": ("/przycisk/18", [("start", None)]),
}

findings = {"console": {}, "hscroll": [], "slow": [], "press_to_map_ms": None, "double_click": None, "errors": []}


def shot(page, name, width, dark=False):
    page.screenshot(path=OUT / f"{name}-{width}{'-dark' if dark else ''}.png", full_page=width < 1024)


with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in WIDTHS:
        ctx = browser.new_context(viewport={"width": width, "height": HEIGHTS[width]}, device_scale_factor=1,
                                  geolocation={"latitude": 50.0618, "longitude": 19.936}, permissions=["geolocation"])
        page = ctx.new_page()
        page.on("console", lambda m, w=width: m.type in ("error", "warning") and findings["console"].setdefault(f"{w}", []).append(m.text[:200]))
        page.on("pageerror", lambda e, w=width: findings["errors"].append(f"{w}: {str(e)[:200]}"))
        page.on("requestfinished", lambda r, w=width: (lambda t: t and t > SLOW_MS and findings["slow"].append({"w": w, "url": r.url.replace(BASE, ""), "ms": round(t)}))(
            (r.timing["responseEnd"] - r.timing["requestStart"]) if r.timing and r.timing["responseEnd"] > 0 else None))
        for name, (path, variants) in SCREENS.items():
            try:
                page.goto(BASE + path, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1500)
                for vname, js in variants:
                    if js:
                        try:
                            page.evaluate(js)
                            page.wait_for_timeout(700)
                        except Exception as e:
                            findings["errors"].append(f"{name}/{vname}@{width}: {str(e)[:120]}")
                            continue
                    shot(page, f"{name}-{vname}", width)
                    sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
                    if sw > cw + 1:
                        findings["hscroll"].append({"screen": f"{name}/{vname}", "w": width, "scrollWidth": sw})
            except Exception as e:
                findings["errors"].append(f"{name}@{width}: {str(e)[:160]}")
        ctx.close()

    # tryb ciemny ekranu zgłaszającego (390)
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark")
    page = ctx.new_page()
    page.goto(BASE + "/zglos/18?jury=1", wait_until="networkidle")
    page.wait_for_timeout(1500)
    shot(page, "zglos-start", 390, dark=True)
    page.goto(BASE + "/kierowca", wait_until="networkidle")
    page.wait_for_timeout(1500)
    page.evaluate("document.getElementById('begin').click(); document.querySelector('[data-open]').click()")
    page.wait_for_timeout(700)
    shot(page, "kierowca-przystanek", 390, dark=True)
    ctx.close()

    # czas: zgłoszenie z /zglos → punkt „fresh” w /api/points (polling panelu co 2 s dochodzi do tego)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(BASE + "/zglos/18?jury=1", wait_until="networkidle")
    page.wait_for_timeout(1200)
    t0 = time.time()
    page.evaluate("UNDO_MS_TEST = 0; clearTimeout(S.timer); S.chosen='full'; send()")
    seen = None
    for _ in range(60):
        page.wait_for_timeout(100)
        fresh = page.evaluate("fetch('/api/points').then(r => r.json()).then(d => d.features.find(f => f.properties.id === 18).properties.fresh)")
        if fresh:
            seen = round((time.time() - t0) * 1000)
            break
    findings["press_to_map_ms"] = seen
    # podwójne kliknięcie przycisku zgłoszenia
    page.goto(BASE + "/zglos/21?jury=1", wait_until="networkidle")
    page.wait_for_timeout(1200)
    page.evaluate("document.querySelector('.z-opt.full').click(); document.querySelector('.z-opt.full')?.click()")
    page.wait_for_timeout(2500)
    findings["double_click"] = page.evaluate("[document.body.dataset.screen, document.querySelectorAll('.z-sending').length]")
    ctx.close()
    browser.close()

(OUT / "_findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: (v if k != "console" else {w: len(x) for w, x in v.items()}) for k, v in findings.items()}, ensure_ascii=False)[:1500])
