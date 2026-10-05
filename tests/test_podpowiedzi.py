"""Treści trybu „Podpowiedzi” (app/static/ui/podpowiedzi.json) i wejścia do powitania. Zachowanie w przeglądarce: scripts/check_help.py."""
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
UI = ROOT / "app/static/ui"
TXT = json.loads((UI / "podpowiedzi.json").read_text(encoding="utf-8"))
BASE = (ROOT / "app/templates/ui/base.html").read_text(encoding="utf-8")


def test_wpisy_maja_pelna_tresc():
    wpisy = {k: v for k, v in TXT.items() if not k.startswith("_")}
    assert len(wpisy) > 50
    zle = [k for k, v in wpisy.items()
           if not all(v.get(p) for p in ("tytul", "cel", "zrodlo")) or not (v.get("przyklad") or v.get("jak_czytac"))]
    assert zle == []


def test_powitanie_ma_5_do_7_krokow_z_trescia():
    kroki = TXT["_powitanie"]
    assert 5 <= len(kroki) <= 7
    assert all(k.get("tytul") and k.get("tekst") for k in kroki)
    assert not kroki[0].get("sel"), "krok 1 (problem i obietnica) jest na środku ekranu, bez podświetlenia"
    assert all(k.get("link_tekst") for k in kroki if k.get("link"))


@pytest.mark.parametrize("sel, plik", [(".switcher", "base.html"), (".help-toggle", "base.html"), (".help-tour", "base.html"),
                                       (".demo-tag", "base.html"), ("data-start-scenario", "start.html")])
def test_selektory_powitania_istnieja_w_szablonach(sel, plik):
    assert any(sel in (k.get("sel") or "") for k in TXT["_powitanie"])
    assert sel.strip(".") in (ROOT / "app/templates/ui" / plik).read_text(encoding="utf-8")


def test_przewodniki_po_stronach_maja_3_do_7_krokow():
    tours = TXT["_przewodniki"]
    assert {"start", "kierowca", "dashboard"} <= set(tours)
    for page, kroki in tours.items():
        assert 3 <= len(kroki) <= 7, page
        assert all(k.get("sel") and k.get("tytul") and k.get("tekst") for k in kroki), page


def test_naglowek_ma_przycisk_powitania_a_start_link():
    end = BASE.split('class="topbar-end"', 1)[1].split("</div>", 1)[0]
    btn = end.split('class="help-welcome"', 1)[1].split("</button>", 1)[0]
    assert "icon('sparkles')" in btn and 'aria-label="Powitanie' in btn and "Powitanie</span>" in btn
    assert "data-show-welcome" in (ROOT / "app/templates/ui/start.html").read_text(encoding="utf-8")


def test_automaty_bez_powitania():
    js = (UI / "help.js").read_text(encoding="utf-8")
    assert "navigator.webdriver" in js and "powitanie') === '1'" in js
    assert "'tf-powitanie'" in js and "'tf-strony'" in js


def test_powitanie_nie_startuje_samo_u_mieszkanca_z_qr():
    js = (UI / "help.js").read_text(encoding="utf-8")
    no_auto = js.split("const NO_AUTO = new Set([", 1)[1].split("])", 1)[0]
    assert all(f"'{p}'" in no_auto for p in ("zglos_kosz", "zgloszenie", "wysypisko", "wysypisko_status"))
    assert "!NO_AUTO.has(TF.help.page())" in js


def test_plakietka_demo_nie_udaje_ikonki_podpowiedzi():
    tag = BASE.split('class="demo-tag"', 1)[1].split("</a>", 1)[0]
    assert "icon('info')" not in tag, "„i” to ikonka podpowiedzi; plakietka demo ma inną ikonę"


def test_help_icon_never_static():
    """Obszar dotyku ikonki „i” to ::before z inset −12 px: przy position: static rozlałby się na cały przodek i zasłonił jego przyciski
    (tak było z filtrami dashboardu: „Kwartał” nie dawał się kliknąć)."""
    import pathlib
    import re
    for css in pathlib.Path("app/static/ui").glob("*.css"):
        for sel, body in re.findall(r"([^{}]*help-i[^{}]*)\{([^}]*)\}", css.read_text(encoding="utf-8")):
            assert "position: static" not in body, f"{css.name}: {sel.strip()}"
