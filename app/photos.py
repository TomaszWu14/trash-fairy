"""Zdjęcia od ekipy MPO i mieszkańców: walidacja, usuwanie metadanych, zapis, analiza Claude Vision w tle, retencja 7 dni.

Wynik analizy to tylko opis (poziom, nadużycia, uszkodzenia, stan kosza). Co z nim zrobić, decydują reguły:
app/misuse.py dla zdjęć ekipy, verification() niżej dla zdjęć ze zgłoszeń mieszkańców.
"""
import io
import threading
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from flask import current_app

from . import db, llm
from .models import PhotoAnalysis, Point

MAX_BYTES = 8 * 1024 * 1024
MATCH_M = 80  # zdjęcie z GPS dopasowujemy do kosza najwyżej tyle metrów od pozycji (punkty są ≥ 80 m od siebie)


def gps_from_exif(data):
    """(lat, lon) z EXIF zdjęcia albo None. Telefon z włączoną lokalizacją w aparacie zapisuje to sam."""
    import io
    from PIL import Image
    try:
        gps = Image.open(io.BytesIO(data)).getexif().get_ifd(0x8825)  # GPSInfo IFD
        lat, lon = gps[2], gps[4]
        dms = lambda v: float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
        lat, lon = dms(lat), dms(lon)
        if gps.get(1) == "S":
            lat = -lat
        if gps.get(3) == "W":
            lon = -lon
        return (lat, lon) if lat and lon else None
    except Exception:  # brak EXIF, brak GPS, uszkodzony plik — zdjęcie i tak można wgrać ręcznie
        return None
RETENTION = timedelta(days=7)
DISCREPANCY_PP = 25  # różnica poziomu ze zdjęcia i od ekipy, powyżej której flagujemy
MISUSE = ["household_bag", "clothes", "bulky", "construction", "none"]
MISUSE_LABELS = {"household_bag": "worki z domowymi śmieciami", "clothes": "ubrania lub buty",
                 "bulky": "odpady wielkogabarytowe", "construction": "gruz lub odpady budowlane"}

SCHEMA = {
    "type": "object",
    "properties": {
        "fill_level": {"type": "integer", "enum": [0, 25, 50, 75, 100]},
        "overflow_outside": {"type": "boolean"},
        "misuse": {"type": "array", "items": {"type": "string", "enum": MISUSE}},
        "damage": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "note": {"type": "string", "maxLength": 500},
        "people_or_plates": {"type": "boolean"},
    },
    "required": ["fill_level", "overflow_outside", "misuse", "damage", "confidence", "note"],  # bez people_or_plates = niepubliczne
    "additionalProperties": False,
}

SYSTEM = (
    "Oceniasz zdjęcia koszy na śmieci i altan śmietnikowych w Krakowie dla firmy oczyszczania miasta (MPO). "
    "Opisujesz wyłącznie pojemnik i odpady: poziom zapełnienia (0, 25, 50, 75 lub 100%), czy odpady leżą obok pojemnika, "
    "rodzaj niewłaściwych odpadów (worki z domowymi śmieciami, ubrania, gabaryty, gruz) i widoczne uszkodzenia. "
    "Nie opisuj osób, twarzy, tablic rejestracyjnych ani niczego, co pozwala kogoś zidentyfikować — nawet jeśli są na zdjęciu. "
    "Nie oceniaj ludzi ani ich zachowania. Pole note: jedno lub dwa krótkie zdania po polsku. "
    "people_or_plates = true, jeśli na zdjęciu da się rozpoznać osobę (twarz, sylwetkę) albo tablicę rejestracyjną. "
    "Jeśli zdjęcie nie przedstawia kosza ani altany, ustaw confidence poniżej 0.3 i napisz to w note."
)


# ---------- zdjęcie ze zgłoszenia mieszkańca ----------
CONDITIONS = {"w_porzadku": "W porządku", "pelny": "Pełny", "odpady_obok": "Odpady obok kosza", "uszkodzony": "Uszkodzony"}
RESIDENT_SCHEMA = {
    "type": "object",
    "properties": {
        "bin_visible": {"type": "boolean"},
        "condition": {"type": "string", "enum": list(CONDITIONS)},
        "fill_level": {"type": "integer", "enum": [0, 25, 50, 75, 100]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string", "maxLength": 200},
        "people_or_plates": {"type": "boolean"},
    },
    "required": ["bin_visible", "condition", "fill_level", "confidence", "reason", "people_or_plates"],
    "additionalProperties": False,
}
RESIDENT_SYSTEM = (
    "Oceniasz zdjęcie dołączone przez mieszkańca Krakowa do zgłoszenia problemu z koszem na śmieci. "
    "Opisujesz wyłącznie kosz: czy jest widoczny (bin_visible), jego stan (condition: w_porzadku, pelny, odpady_obok, uszkodzony), "
    "szacowane zapełnienie (0, 25, 50, 75 lub 100%) i pewność oceny (confidence 0–1). "
    "Pole reason: jedno krótkie zdanie po polsku, tylko o koszu i odpadach. "
    "people_or_plates = true, jeśli na zdjęciu da się rozpoznać osobę (twarz, sylwetkę) albo tablicę rejestracyjną; "
    "nie opisuj ich w reason. Jeśli kosza nie widać, ustaw bin_visible = false i confidence poniżej 0.3."
)
VERIFY_MIN_CONFIDENCE = 0.7
PENDING_MAX = timedelta(minutes=2)  # dłużej „w toku” = analiza nie wróci, status „Do weryfikacji”
MAX_PIXELS = 40_000_000  # ok. 7000×5700; więcej to podejrzany plik (bomba dekompresyjna: mały PNG, gigabajty w pamięci)
# typ zgłoszenia (Press.kind) → stany ze zdjęcia, które go potwierdzają; „inne” nie ma czego potwierdzać
CONSISTENT = {"full": {"pelny", "odpady_obok"}, "overflow": {"odpady_obok"}, "damaged": {"uszkodzony"}}


def verification(pa, kind):
    """Reguła (nie AI): wynik analizy + typ zgłoszenia → status weryfikacji. Nigdy nie odrzuca mieszkańca.

    „Zweryfikowane AI”: kosz widoczny, stan zgodny z typem zgłoszenia, pewność ≥ 0.7. Wszystko inne (niska pewność,
    brak kosza, brak klucza, błąd API, „inne”) → „Do weryfikacji” przez dyspozytora. None = zgłoszenie bez zdjęcia."""
    if pa is None:
        return None
    out = {"status": "do_weryfikacji", "etykieta": "Do weryfikacji", "pewnosc": None, "stan": None,
           "uzasadnienie": "Analiza AI niedostępna. Zdjęcie sprawdzi dyspozytor.", "zdjecie_publiczne": False}
    if pa.status == "pending" and datetime.now(UTC).replace(tzinfo=None) - pa.wall_at > PENDING_MAX:
        return out  # wątek analizy padł (restart workera): dyspozytor sprawdzi zdjęcie sam
    if pa.status == "pending":
        return out | {"status": "w_toku", "etykieta": "Analiza AI w toku", "uzasadnienie": "Sprawdzamy zdjęcie, to potrwa kilka sekund."}
    if pa.status != "done":
        return out
    conf = pa.confidence or 0
    out.update(pewnosc=round(conf, 2), stan=CONDITIONS.get(pa.condition), uzasadnienie=pa.note or "",
               zdjecie_publiczne=not pa.people)
    if not pa.bin_visible:
        out["uzasadnienie"] = "Na zdjęciu nie widać kosza. " + out["uzasadnienie"]
    elif conf >= VERIFY_MIN_CONFIDENCE and pa.condition in CONSISTENT.get(kind, ()):
        out.update(status="zweryfikowane", etykieta="Zweryfikowane AI")
    return out


def strip_metadata(data, mt):
    """Ponowne zakodowanie obrazu bez EXIF/XMP (GPS, model aparatu, czas). Orientację z EXIF nanosimy na piksele.
    Duże zdjęcia zmniejszamy do 2048 px: tyle wystarcza analizie i kierowcy. Rzuca wyjątek dla uszkodzonego pliku."""
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(data)) as src:
        if src.width * src.height > MAX_PIXELS:  # rozmiar z nagłówka, zanim zdekodujemy piksele
            raise ValueError("obraz za duży")
        img = ImageOps.exif_transpose(src)
        img.thumbnail((2048, 2048))
        fmt = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}[mt]
        if fmt == "JPEG" and img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        clean = Image.frombytes(img.mode, img.size, img.tobytes())  # nowy obraz: nie niesie info ani EXIF źródła
        if img.mode == "P":
            clean.putpalette(img.getpalette())
        out = io.BytesIO()
        clean.save(out, fmt, quality=88)
    return out.getvalue()


def media_type(data):
    """Typ obrazu po sygnaturze pliku (nie ufamy nazwie ani nagłówkowi od przeglądarki)."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate(data):
    """Zwraca typ obrazu albo komunikat błędu (None, komunikat)."""
    if not data:
        return None, "Pusty plik."
    if len(data) > MAX_BYTES:
        return None, "Zdjęcie jest za duże (max 8 MB)."
    mt = media_type(data)
    return (mt, None) if mt else (None, "Dozwolone są tylko zdjęcia JPEG, PNG lub WebP.")


def read_upload(upload):
    """Plik z formularza → (bajty bez EXIF, typ, None) albo (None, None, komunikat). Brak pliku → (None, None, None)."""
    if not upload or not upload.filename:
        return None, None, None
    raw = upload.read(MAX_BYTES + 1)
    mt, error = validate(raw)
    if not error:
        try:
            raw = strip_metadata(raw, mt)  # bez GPS i danych aparatu, zanim cokolwiek trafi na dysk
        except Exception:  # sygnatura się zgadza, ale obrazu nie da się odczytać
            error = "Nie udało się odczytać zdjęcia. Spróbuj innego pliku."
    return (None, None, error) if error else (raw, mt, None)


def photo_dir():
    path = Path(current_app.instance_path) / "photos"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save(point_id, at, data, mt, crew_level=None, source="crew"):
    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[mt]
    path = photo_dir() / f"{uuid.uuid4().hex}.{ext}"
    path.write_bytes(data)
    pa = PhotoAnalysis(point_id=point_id, at=at, wall_at=datetime.now(UTC).replace(tzinfo=None),
                       photo_path=str(path), media_type=mt, crew_level=crew_level, source=source)
    db.session.add(pa)
    db.session.commit()
    return pa


def analyze(analysis_id):
    """Wywołuje Claude Vision i zapisuje wynik albo komunikat błędu — nigdy nie rzuca wyjątku dalej."""
    pa = db.session.get(PhotoAnalysis, analysis_id)
    resident = pa.source == "resident"
    try:
        data = Path(pa.photo_path).read_bytes()
        result = llm.ask_json("Oceń to zdjęcie według schematu.", RESIDENT_SCHEMA if resident else SCHEMA,
                              system=RESIDENT_SYSTEM if resident else SYSTEM,
                              images=[llm.image_block(data, pa.media_type)], max_tokens=2000)
    except Exception as e:  # LLMError, OSError i każdy inny błąd: analiza nie może zostać „w toku” na zawsze
        pa.status, pa.error = "error", str(e)[:255] or type(e).__name__
    else:
        pa.status = "done"
    if pa.status == "done" and resident:
        pa.bin_visible, pa.condition, pa.fill_level = result["bin_visible"], result["condition"], result["fill_level"]
        pa.people, pa.confidence, pa.note = result["people_or_plates"], float(result["confidence"]), result["reason"][:500]
        pa.misuse, pa.damage, pa.overflow_outside = [], result["condition"] == "uszkodzony", result["condition"] == "odpady_obok"
    elif pa.status == "done":
        pa.fill_level, pa.overflow_outside = result["fill_level"], result["overflow_outside"]
        pa.misuse = [m for m in result["misuse"] if m != "none"]
        pa.damage, pa.confidence, pa.note = result["damage"], float(result["confidence"]), result["note"][:500]
        pa.people = result.get("people_or_plates")  # brak pola = nie wiemy, więc zdjęcie nie jest publiczne
    db.session.commit()
    return pa


def analyze_in_background(analysis_id):
    """Analiza nie blokuje ekipy na telefonie. W testach (TESTING) liczymy od razu, żeby wynik był deterministyczny."""
    app = current_app._get_current_object()
    if app.config.get("TESTING"):
        return analyze(analysis_id)

    def run():
        with app.app_context():
            analyze(analysis_id)

    threading.Thread(target=run, daemon=True).start()


def discrepancy(pa):
    return (pa.status == "done" and pa.crew_level is not None and pa.fill_level is not None
            and abs(pa.fill_level - pa.crew_level) > DISCREPANCY_PP)


def cleanup(now_wall=None):
    """Usuwa pliki zdjęć starszych niż 7 dni; wynik analizy zostaje w bazie (RODO). Zwraca liczbę usuniętych."""
    now_wall = now_wall or datetime.now(UTC).replace(tzinfo=None)
    removed = 0
    for pa in PhotoAnalysis.query.filter(PhotoAnalysis.photo_path.isnot(None), PhotoAnalysis.wall_at < now_wall - RETENTION):
        Path(pa.photo_path).unlink(missing_ok=True)
        pa.photo_path = None
        removed += 1
    db.session.commit()
    return removed


DEMO_NOTES = ["Dwa worki z domowymi śmieciami obok kosza, kosz pełny.",
              "Kosz przepełniony, obok worek z odpadami domowymi i karton."]


def seed_demo(now):
    """Reset scenariusza: usuwa analizy (i pliki), dodaje gotowe analizy przy koszach obok przeciążonych altan.

    Dzięki temu powiązanie altana → kosz widać od startu demo; na żywo dochodzi wgranie nowego zdjęcia.
    """
    for pa in PhotoAnalysis.query:
        if pa.photo_path:
            Path(pa.photo_path).unlink(missing_ok=True)
    db.session.query(PhotoAnalysis).delete()
    bins = Point.live_query().filter_by(kind="bin", area="Grzegórzki").order_by(Point.id).all()
    wall = datetime.now(UTC).replace(tzinfo=None)
    for i, b in enumerate(bins[::3][:len(DEMO_NOTES)]):  # po jednym koszu przy każdej przeciążonej altanie
        db.session.add(PhotoAnalysis(
            point_id=b.id, at=now - timedelta(hours=2 + 3 * i), wall_at=wall, status="done", source="demo",
            crew_level=100, fill_level=100, overflow_outside=True, misuse=["household_bag"], damage=False,
            confidence=0.9, note=DEMO_NOTES[i]))
    db.session.commit()
