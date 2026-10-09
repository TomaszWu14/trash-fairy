"""Logo ostateczne i PWA: manifest (poprawny JSON) i ikony odpowiadają 200, logo w nagłówku bez zdublowanych id gradientu."""
import io
import json

from PIL import Image


def test_manifest_and_icons(client):
    c = client
    m = json.loads(c.get("/static/ui/manifest.webmanifest").get_data(as_text=True))
    assert m["name"] == "Trash Fairy" and m["start_url"] == "/" and m["display"] == "standalone"
    assert {i["purpose"] for i in m["icons"]} == {"any", "maskable"}
    for src in {i["src"] for i in m["icons"]} | {"/static/ui/apple-touch-icon.png", "/static/ui/logo.svg"}:
        r = c.get(src)
        assert r.status_code == 200 and r.data, src
        if src.endswith(".png"):
            assert r.data[:8] == b"\x89PNG\r\n\x1a\n", src
    # „any” (pulpit, pasek zadań): zaokrąglony kafel z przezroczystymi rogami; „maskable”: pełny spad pod maskę systemu
    for i in m["icons"]:
        corner = Image.open(io.BytesIO(c.get(i["src"]).data)).convert("RGBA").getpixel((0, 0))[3]
        assert (corner == 0) == (i["purpose"] == "any"), i


def test_logo_macro_has_no_gradient_id(client):
    c = client
    html = c.get("/prywatnosc").get_data(as_text=True)
    assert 'class="logo"' in html and "var(--logo-glyph)" in html and "url(#" not in html
