"""Trash Fairy – renderer ekranu e-papierowego 800×480 (1-bit, opcjonalnie 3 kolory).

Zgodny z projektem z kanwy (strona „Wyświetlacz na koszu”).
Użycie:
    python epaper_render.py                # zapisuje out/stan-*.png dla wszystkich stanów
    from epaper_render import render, render_partial, STATES
    img = render("confirm", data)          # PIL.Image, tryb "1" (lub "P" dla tri=True)
    win = render_partial("confirm", data)  # tylko okno odświeżania częściowego

Zależności: Pillow, qrcode. Fonty: IBMPlexSans-Medium.ttf i IBMPlexSans-Bold.ttf obok skryptu.
"""
from __future__ import annotations
import os
from PIL import Image, ImageDraw, ImageFont
import qrcode

W, H = 800, 480
BLACK, WHITE, RED = 0, 1, 2          # indeksy palety (tryb "P" dla tri)
HERE = os.path.dirname(os.path.abspath(__file__))
BASE_URL = os.environ.get("TF_BASE_URL", "http://10.250.192.133:5050")

# --- siatka (px) -------------------------------------------------------------
HEADER = (0, 0, 800, 64)          # statyczny
BAND = (0, 64, 584, 344)          # stan – pełne odświeżenie przy zdarzeniu
QRCOL = (584, 64, 800, 344)       # QR + podpis – razem ze stanem
PARTIAL = (24, 344, 776, 432)     # JEDYNE okno odświeżania częściowego (x wyrównane do 8)
FOOTER = (0, 432, 800, 480)       # raz na godzinę
LINE = 3

# --- dane stanów (te same teksty co w projekcie) ----------------------------
DEVICE = {"name": "Kosz Rynek 03", "device_no": "1183", "address": "Rynek Główny 3, róg Szewskiej"}
STATES = {
    "calm": dict(ic="ok", head="W porządku", big="Kosz nie wymaga zgłoszenia",
                 sub="Kurs: kosze uliczne. Planowy odbiór i zapełnienie poniżej.",
                 qr="report", qr_cap="Pełny? Zeskanuj albo naciśnij przycisk.",
                 fill=62, b=("Następny odbiór", "ok. 14:00"), c=("Zgłoszenia", "brak")),
    "confirm": dict(ic="report", head="Zgłoszono", big="Zgłoszenie przyjęte o 13:24",
                    sub="Dyspozytor już wie. Dziękujemy. Czas przyjazdu ekipy poniżej.", invert=True,
                    qr="status", qr_cap="Zeskanuj, aby śledzić status tego kosza.",
                    fill=62, b=("Ekipa", "ok. 14:00"), c=("Zgłosiły", "2 osoby")),
    "enroute": dict(ic="report", head="Ekipa w drodze", big="Ten kosz jest na trasie",
                    sub="Przystanek i czas przyjazdu poniżej.",
                    qr="status", qr_cap="Zeskanuj, aby śledzić status tego kosza.",
                    fill=62, b=("Przyjazd", "ok. 12 min"), c=("Przystanek", "34 z 53")),
    "emptied": dict(ic="ok", head="Opróżniono", big="14:02 · dziękujemy",
                    sub="Następny odbiór jutro 06:00. Zarejestrowani dostają +10 pkt.",
                    qr="program", qr_cap="Przyjaciele Wróżki: zeskanuj, aby dołączyć.",
                    fill=0, b=("Następny odbiór", "jutro 06:00"), c=("Zgłoszenia", "zamknięte")),
    "overflow": dict(ic="full", head="Przepełniony", big="Zgłoszenie przyjęte 13:24",
                     sub="Trwa wydarzenie, kosz zapełnia się szybciej. Czas odbioru może się wydłużyć.",
                     qr="status", qr_cap="Zeskanuj, aby śledzić status tego kosza.",
                     fill=100, b=("Odbiór planowo", "ok. 14:00"), c=("Zgłosiły", "2 osoby")),
    "fault": dict(ic="warn", head="Usterka", big="Przycisk może nie działać",
                  sub="Brak sygnału od 48 h, bateria 12 %. Zgłoszenie przez QR działa.",
                  qr="report", qr_cap="Zeskanuj, aby zgłosić stan kosza telefonem.",
                  fill=None, b=("Serwis", "za 2 dni rob."), c=("Bateria", "12 %"),
                  foot="Bateria 12 % · ostatni sygnał 01.10, 13:20"),
    "night": dict(ic="ok", head="W porządku", big="Odbiór jutro 06:00",
                  qr="report", qr_cap="Pełny? Zeskanuj albo naciśnij przycisk.",
                  foot="Tryb oszczędny · odświeżanie co godzinę"),
}
QR_TARGETS = {
    "report": "{base}/kosz/{dev}/zglos",
    "status": "{base}/kosz/{dev}/status",
    "program": "{base}/przyjaciele",
}


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    name = "IBMPlexSans-Bold.ttf" if weight == "bold" else "IBMPlexSans-Medium.ttf"
    return ImageFont.truetype(os.path.join(HERE, name), size)


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _text_block(draw, xy, text, font, max_w, lh, fill):
    x, y = xy
    for ln in _wrap(draw, text, font, max_w):
        draw.text((x, y), ln, font=font, fill=fill)
        y += lh
    return y


def _shape(draw, kind, x, y, s, fill, glyph):
    """Kształt stanu wypełniony `fill`, znak w kolorze `glyph`. s = bok w px."""
    k = s / 40.0
    P = lambda px, py: (x + px * k, y + py * k)
    if kind == "ok":
        draw.ellipse([P(1, 1), P(39, 39)], fill=fill)
        draw.line([P(11, 20.5), P(17, 26.5), P(29, 13.5)], fill=glyph, width=max(3, round(4.5 * k)), joint="curve")
    elif kind == "near":
        draw.polygon([P(20, 1), P(39, 20), P(20, 39), P(1, 20)], fill=fill)
        draw.line([P(20, 30), P(20, 12)], fill=glyph, width=max(3, round(4.5 * k)))
        draw.line([P(13, 18.5), P(20, 11.5), P(27, 18.5)], fill=glyph, width=max(3, round(4.5 * k)))
    elif kind == "full":
        draw.rectangle([P(1, 1), P(39, 39)], fill=fill)
        draw.rectangle([P(17, 7), P(23, 24)], fill=glyph)
        draw.rectangle([P(17, 28), P(23, 34)], fill=glyph)
    elif kind == "report":
        draw.rounded_rectangle([P(2, 2), P(38, 30)], radius=4 * k, fill=fill)
        draw.polygon([P(2, 24), P(14, 30), P(2, 39)], fill=fill)
        for cx in (9, 17.5, 26):
            draw.rectangle([P(cx, 14), P(cx + 5, 19)], fill=glyph)
    elif kind == "warn":
        draw.polygon([P(20, 1), P(39, 38), P(1, 38)], fill=fill)
        draw.rectangle([P(17.5, 13), P(22.5, 26)], fill=glyph)
        draw.rectangle([P(17.5, 29), P(22.5, 34)], fill=glyph)


def _qr(draw, img, url, x, y):
    """168×168: obrys 3 px, biała ramka 8 px, kod wpisany w 152 px."""
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    q.add_data(url)
    q.make(fit=True)
    m = q.get_matrix()
    n = len(m)
    box = 152 // n
    size = box * n
    off = (152 - size) // 2
    draw.rectangle([x, y, x + 167, y + 167], fill=WHITE, outline=BLACK, width=LINE)
    ox, oy = x + 8 + off, y + 8 + off
    for r, row in enumerate(m):
        for c, v in enumerate(row):
            if v:
                draw.rectangle([ox + c * box, oy + r * box, ox + (c + 1) * box - 1, oy + (r + 1) * box - 1], fill=BLACK)


def _partial(draw, d):
    x0, y0, x1, y1 = PARTIAL
    draw.rectangle([x0, y0, x1 - 1, y1 - 1], outline=BLACK, width=LINE, fill=WHITE)
    lab, val = _font("medium", 20), _font("bold", 30)
    # zapełnienie
    fill = d.get("fill")
    draw.text((x0 + 16, y0 + 8), "Szacowane zapełnienie" if fill is not None else "Zapełnienie: brak danych", font=lab, fill=BLACK)
    filled = 0 if fill is None else max(0, min(10, int(fill // 10)))
    bx, by = x0 + 16, y0 + 40
    for i in range(10):
        draw.rectangle([bx, by, bx + 17, by + 33], outline=BLACK, width=LINE, fill=BLACK if i < filled else WHITE)
        bx += 22
    draw.text((bx + 8, by - 2), "—" if fill is None else f"{fill} %", font=_font("bold", 28), fill=BLACK)
    # dwa pola
    seg_w = (x1 - (x0 + 340)) // 2
    for i, (l, v) in enumerate((d["b"], d["c"])):
        sx = x0 + 340 + i * seg_w
        draw.rectangle([sx, y0, sx + LINE - 1, y1 - 1], fill=BLACK)
        draw.text((sx + 16, y0 + 8), l, font=lab, fill=BLACK)
        draw.text((sx + 16, y0 + 36), v, font=val, fill=BLACK)


def render(state: str, data: dict | None = None, tri: bool = False) -> Image.Image:
    d = dict(STATES[state])
    d.update(data or {})
    dev = {**DEVICE, **(data or {}).get("device", {})}
    if tri:
        img = Image.new("P", (W, H), WHITE)
        img.putpalette([0, 0, 0, 255, 255, 255, 196, 22, 28] + [0] * 759)
    else:
        img = Image.new("1", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # nagłówek (statyczny)
    f22b, f22 = _font("bold", 22), _font("medium", 22)
    draw.text((24, 18), "MPO Kraków · Trash Fairy", font=f22b, fill=BLACK)
    right = f"{dev['name']} · nr {dev['device_no']}"
    draw.text((W - 24 - draw.textlength(right, font=f22), 18), right, font=f22, fill=BLACK)
    draw.rectangle([0, 61, W, 63], fill=BLACK)

    url = QR_TARGETS[d["qr"]].format(base=BASE_URL, dev=dev["device_no"])
    if state == "night":
        _shape(draw, "ok", 24, 120, 96, BLACK, WHITE)
        draw.text((144, 128), d["head"].upper(), font=_font("bold", 60), fill=BLACK)
        draw.text((24, 264), d["big"], font=_font("bold", 48), fill=BLACK)
        draw.rectangle([584, 64, 586, 431], fill=BLACK)
        _qr(draw, img, url, 608, 96)
        _text_block(draw, (608, 274), d["qr_cap"], _font("medium", 20), 172, 24, BLACK)
    else:
        inv = d.get("invert")
        band_bg = (RED if tri else BLACK) if inv else WHITE
        fg = WHITE if inv else BLACK
        draw.rectangle([BAND[0], BAND[1], BAND[2] - 1, BAND[3] - 1], fill=band_bg)
        _shape(draw, d["ic"], 24, 88, 88, WHITE if inv else BLACK, band_bg if inv else WHITE)
        hfont = _font("bold", 56)
        lines = _wrap(draw, d["head"].upper(), hfont, 584 - 24 - 88 - 20 - 16)
        hy = 88 + (88 - 60 * len(lines)) // 2 if len(lines) == 1 else 80
        for ln in lines:
            draw.text((132, hy), ln, font=hfont, fill=fg)
            hy += 60
        y = max(192, hy + 8)
        draw.text((24, y), d["big"], font=_font("bold", 32), fill=fg)
        _text_block(draw, (24, y + 50), d["sub"], _font("medium", 24), 536, 30, fg)
        draw.rectangle([584, 64, 586, 343], fill=BLACK)
        _qr(draw, img, url, 608, 84)
        _text_block(draw, (608, 262), d["qr_cap"], _font("medium", 20), 172, 24, BLACK)
        _partial(draw, d)

    # stopka (co godzinę)
    f16 = _font("medium", 16)
    draw.text((24, 446), dev["address"], font=f16, fill=BLACK)
    foot = d.get("foot", "Bateria 78 % · ostatni sygnał 13:20")
    draw.text((W - 24 - draw.textlength(foot, font=f16), 446), foot, font=f16, fill=BLACK)
    return img


def render_partial(state: str, data: dict | None = None) -> Image.Image:
    """Wycinek okna PARTIAL (752×88) do odświeżenia częściowego."""
    return render(state, data).crop(PARTIAL)


if __name__ == "__main__":
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    order = ["calm", "confirm", "enroute", "emptied", "overflow", "fault", "night"]
    for i, s in enumerate(order, 1):
        render(s).save(os.path.join(out, f"stan-{i}-{s}.png"))
    render("confirm", tri=True).convert("RGB").save(os.path.join(out, "stan-8-confirm-3kolor.png"))
    render_partial("enroute").save(os.path.join(out, "okno-czesciowe-enroute.png"))
    print("zapisano do", out)
