"""Zdjęcia od ekipy MPO: walidacja, zapis, analiza Claude Vision w tle, retencja 7 dni (koncepcja, sekcje 5 i 10).

Wynik analizy to tylko opis (poziom, nadużycia, uszkodzenia). Co z nim zrobić, decydują reguły (app/misuse.py).
"""
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
    },
    "required": ["fill_level", "overflow_outside", "misuse", "damage", "confidence", "note"],
    "additionalProperties": False,
}

SYSTEM = (
    "Oceniasz zdjęcia koszy na śmieci i altan śmietnikowych w Krakowie dla firmy oczyszczania miasta (MPO). "
    "Opisujesz wyłącznie pojemnik i odpady: poziom zapełnienia (0, 25, 50, 75 lub 100%), czy odpady leżą obok pojemnika, "
    "rodzaj niewłaściwych odpadów (worki z domowymi śmieciami, ubrania, gabaryty, gruz) i widoczne uszkodzenia. "
    "Nie opisuj osób, twarzy, tablic rejestracyjnych ani niczego, co pozwala kogoś zidentyfikować — nawet jeśli są na zdjęciu. "
    "Nie oceniaj ludzi ani ich zachowania. Pole note: jedno lub dwa krótkie zdania po polsku. "
    "Jeśli zdjęcie nie przedstawia kosza ani altany, ustaw confidence poniżej 0.3 i napisz to w note."
)


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


def photo_dir():
    path = Path(current_app.instance_path) / "photos"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save(point_id, at, data, mt, crew_level=None):
    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[mt]
    path = photo_dir() / f"{uuid.uuid4().hex}.{ext}"
    path.write_bytes(data)
    pa = PhotoAnalysis(point_id=point_id, at=at, wall_at=datetime.now(UTC).replace(tzinfo=None),
                       photo_path=str(path), media_type=mt, crew_level=crew_level)
    db.session.add(pa)
    db.session.commit()
    return pa


def analyze(analysis_id):
    """Wywołuje Claude Vision i zapisuje wynik albo komunikat błędu — nigdy nie rzuca wyjątku dalej."""
    pa = db.session.get(PhotoAnalysis, analysis_id)
    try:
        data = Path(pa.photo_path).read_bytes()
        result = llm.ask_json("Oceń to zdjęcie według schematu.", SCHEMA, system=SYSTEM,
                              images=[llm.image_block(data, pa.media_type)], max_tokens=2000)
    except (llm.LLMError, OSError) as e:
        pa.status, pa.error = "error", str(e)[:255]
    else:
        pa.status = "done"
        pa.fill_level, pa.overflow_outside = result["fill_level"], result["overflow_outside"]
        pa.misuse = [m for m in result["misuse"] if m != "none"]
        pa.damage, pa.confidence, pa.note = result["damage"], float(result["confidence"]), result["note"][:500]
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
