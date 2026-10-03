"""Buduje app/static/ui/icons.svg: podzbiór ikon Lucide (ISC) używanych w UI. Jedna grubość kreski i jeden styl.

Użycie: python scripts/build_icons.py   (pobiera sprite lucide-static z jsDelivr; nowe ikony dopisz do ICONS)
"""
import pathlib
import re
import urllib.request

VERSION = "0.469.0"
ICONS = """
arrow-left arrow-right arrow-up-right chevron-right chevron-down x check check-check circle-check-big circle-alert triangle-alert info
house layout-dashboard monitor smartphone truck trash-2 map-pin map navigation route locate-fixed qr-code camera message-square-text
play rotate-ccw sparkles clock timer calendar filter download list-ordered layers recycle leaf coins banknote gauge
trending-up trending-down users radar zap graduation-cap wrench package bell flag circle-dot wifi-off loader-circle
newspaper wine milk apple trash scan-line hand external-link refresh-cw circle-play footprints building-2 file-text bell-ring
shield-check circle-help ban
battery battery-low battery-warning battery-full signal radio-tower cpu wifi activity tablet-smartphone
""".split()

src = urllib.request.urlopen(f"https://cdn.jsdelivr.net/npm/lucide-static@{VERSION}/sprite.svg", timeout=30).read().decode()
found = {m.group(2): m.group(1) for m in re.finditer(r'(<symbol\s+id="([^"]+)".*?</symbol>)', src, re.S)}
missing = [i for i in ICONS if i not in found]
if missing:
    raise SystemExit(f"Brak ikon w Lucide {VERSION}: {missing}")
body = "\n".join(re.sub(r"\s+", " ", found[i]) for i in ICONS)
out = pathlib.Path(__file__).resolve().parent.parent / "app" / "static" / "ui" / "icons.svg"
out.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n<!-- Lucide {VERSION}, ISC: LICENSE-lucide.txt -->\n{body}\n</svg>\n', encoding="utf-8")
print(f"{len(ICONS)} ikon → {out} ({out.stat().st_size // 1024} KB)")
