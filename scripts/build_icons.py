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
moon sun
""".split()
# 5 własnych symboli stanu (wariant A): kształt w currentColor z ciemną obwódką + znak w --on-state (romb: zawsze ciemny).
# Użycie: makro state_icon(k) w _ui.html i TF.stateIcon(k) w app.js; kolor kształtu nadaje klasa .si-<k> (app.css).
EDGE = 'stroke="#0B0F1A" stroke-width="1.25" stroke-linejoin="round"'
GLYPH = 'fill="none" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="stroke:var(--on-state,#fff)"'
DOT = 'style="fill:var(--on-state,#fff)" stroke="none"'
STATES = f"""
<symbol id="st-ok" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10.2" fill="currentColor" {EDGE}/><path d="m7.6 12.4 3 3 5.8-6.2" {GLYPH}/></symbol>
<symbol id="st-warn" viewBox="0 0 24 24"><path d="M12 1.4 22.6 12 12 22.6 1.4 12z" fill="currentColor" {EDGE}/><path d="M12 16.6V7.8m-3.4 3.4L12 7.8l3.4 3.4" fill="none" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="stroke:var(--on-warn,#0B0F1A)"/></symbol>
<symbol id="st-full" viewBox="0 0 24 24"><rect x="2.2" y="2.2" width="19.6" height="19.6" rx="3.2" fill="currentColor" {EDGE}/><path d="M12 6.8v6.4" {GLYPH}/><circle cx="12" cy="17" r="1.5" {DOT}/></symbol>
<symbol id="st-report" viewBox="0 0 24 24"><path d="M12 2.4c5.4 0 9.6 3.7 9.6 8.4s-4.2 8.4-9.6 8.4c-1.1 0-2.2-.2-3.2-.5L3 21.6l1.6-4.8c-1.4-1.6-2.2-3.6-2.2-6C2.4 6.1 6.6 2.4 12 2.4z" fill="currentColor" {EDGE}/><circle cx="7.9" cy="10.8" r="1.45" {DOT}/><circle cx="12" cy="10.8" r="1.45" {DOT}/><circle cx="16.1" cy="10.8" r="1.45" {DOT}/></symbol>
<symbol id="st-sensor" viewBox="0 0 24 24"><path d="M12 2.2 22.8 21H1.2z" fill="currentColor" {EDGE}/><path d="M12 9v5.2" {GLYPH}/><circle cx="12" cy="17.6" r="1.4" {DOT}/></symbol>
"""

src = urllib.request.urlopen(f"https://cdn.jsdelivr.net/npm/lucide-static@{VERSION}/sprite.svg", timeout=30).read().decode()
found = {m.group(2): m.group(1) for m in re.finditer(r'(<symbol\s+id="([^"]+)".*?</symbol>)', src, re.S)}
missing = [i for i in ICONS if i not in found]
if missing:
    raise SystemExit(f"Brak ikon w Lucide {VERSION}: {missing}")
body = "\n".join(re.sub(r"\s+", " ", found[i]) for i in ICONS) + STATES.rstrip()
out = pathlib.Path(__file__).resolve().parent.parent / "app" / "static" / "ui" / "icons.svg"
out.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n<!-- Lucide {VERSION}, ISC: LICENSE-lucide.txt -->\n{body}\n</svg>\n', encoding="utf-8")
print(f"{len(ICONS)} ikon → {out} ({out.stat().st_size // 1024} KB)")
