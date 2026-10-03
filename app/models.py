from . import db

# Wszystkie znaczniki czasu w czasie demo (zegar scenariusza), naiwne datetime.
# Wyjątek: Press.wall_at to prawdziwy czas UTC, potrzebny do limitu naciśnięć na IP.


class Point(db.Model):
    """Kosz uliczny (kind='bin') albo altana osiedlowa (kind='shelter')."""
    id = db.Column(db.Integer, primary_key=True)
    osm_id = db.Column(db.String(32), unique=True, nullable=False)
    kind = db.Column(db.String(10), nullable=False)
    area = db.Column(db.String(20), nullable=False)  # Rynek / Kazimierz / Grzegórzki
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    osm_tags = db.Column(db.JSON, nullable=False, default=dict)
    base_rate = db.Column(db.Float, nullable=False)  # średnie tempo zapełniania, % na godzinę
    overloaded = db.Column(db.Boolean, nullable=False, default=False)  # celowo przeciążona altana (demo)


class Press(db.Model):
    """Pojedyncze naciśnięcie przycisku. Scalanie w zgłoszenia: app/reports.py."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    at = db.Column(db.DateTime, nullable=False)
    ip = db.Column(db.String(45))
    wall_at = db.Column(db.DateTime, index=True)  # None = naciśnięcie z symulacji
    source = db.Column(db.String(10), nullable=False, default="button")  # button / qr
    kind = db.Column(db.String(10))  # full / overflow / damaged (None = fizyczny przycisk, czyli „pełny”)
    resident_id = db.Column(db.Integer, db.ForeignKey("resident.id"), index=True)  # None = anonimowe
    report_id = db.Column(db.Integer, db.ForeignKey("report.id"), index=True)


class StopIssue(db.Model):
    """Kierowca na przystanku: nie da się podjechać albo problem z koszem (PWA /kierowca)."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    at = db.Column(db.DateTime, nullable=False, index=True)
    kind = db.Column(db.String(12), nullable=False)  # no_access / damaged / blocked / overflow
    note = db.Column(db.String(200))


class Report(db.Model):
    """Zgłoszenie: naciśnięcia jednego punktu w oknie 15 minut od pierwszego naciśnięcia."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    first_at = db.Column(db.DateTime, nullable=False)
    last_at = db.Column(db.DateTime, nullable=False)
    presses = db.Column(db.Integer, nullable=False, default=1)
    weight = db.Column(db.Float, nullable=False)  # wiarygodność przycisku w chwili zgłoszenia
    hit = db.Column(db.Boolean)  # None = otwarte; po opróżnieniu: trafne / fałszywe
    resolved_at = db.Column(db.DateTime)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)  # potwierdzone przez zarejestrowanego mieszkańca


class Emptying(db.Model):
    """Opróżnienie punktu przez ekipę MPO, z poziomem zastanym przed opróżnieniem."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    at = db.Column(db.DateTime, nullable=False, index=True)
    level = db.Column(db.Integer, nullable=False)  # 0/25/50/75/100
    source = db.Column(db.String(10))  # None = symulacja, "crew" = zapis z PWA kierowcy lub panelu
    far_m = db.Column(db.Integer)  # odległość telefonu od kosza minus dokładność GPS (None = bez położenia)


class Forecast(db.Model):
    """Szereg czasowy poziomu zapełnienia punktu.

    source='sim'  — symulacja (historia + 24 h „przyszłości” odsłanianej przewijaniem zegara),
    source='pred' — prognoza (etap 3).
    """
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False)
    at = db.Column(db.DateTime, nullable=False)
    level = db.Column(db.Float, nullable=False)  # %, może przekroczyć 100 (przepełnienie)
    source = db.Column(db.String(8), nullable=False, default="sim")

    __table_args__ = (db.Index("ix_forecast_point_at", "point_id", "at"),)


class Event(db.Model):
    """Wydarzenie, które zwiększa tempo zapełniania koszy w promieniu zależnym od skali tłumu."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    scale = db.Column(db.String(10), nullable=False)  # small / medium / large
    source = db.Column(db.String(10), nullable=False, default="manual")  # manual / karnet (etap 6)


class PhotoAnalysis(db.Model):
    """Zdjęcie od ekipy MPO i wynik analizy Claude Vision (koncepcja, sekcja 5).

    Zdjęcie usuwamy po 7 dniach (photo_path → None), wynik analizy zostaje.
    """
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    at = db.Column(db.DateTime, nullable=False)  # czas zegara demo
    wall_at = db.Column(db.DateTime, nullable=False)  # prawdziwy czas UTC (retencja zdjęć)
    photo_path = db.Column(db.String(255))
    media_type = db.Column(db.String(20))
    crew_level = db.Column(db.Integer)  # poziom kliknięty przez ekipę
    status = db.Column(db.String(10), nullable=False, default="pending")  # pending / done / error
    error = db.Column(db.String(255))
    fill_level = db.Column(db.Integer)
    overflow_outside = db.Column(db.Boolean)
    misuse = db.Column(db.JSON)  # ["household_bag", ...]
    damage = db.Column(db.Boolean)
    confidence = db.Column(db.Float)
    note = db.Column(db.String(500))
    source = db.Column(db.String(10), nullable=False, default="crew")  # crew / demo


class FairyReport(db.Model):
    """Raport „Wróżka podpowiada”: fakty policzone w kodzie + tekst od Claude (cache na wypadek błędu API)."""
    id = db.Column(db.Integer, primary_key=True)
    at = db.Column(db.DateTime, nullable=False)  # czas zegara demo
    facts = db.Column(db.JSON, nullable=False)
    sections = db.Column(db.JSON, nullable=False)  # [{"title", "text"}]
    model = db.Column(db.String(60), nullable=False)
    unknown_numbers = db.Column(db.JSON, nullable=False, default=list)  # liczby w tekście, których nie ma w faktach


class Resident(db.Model):
    """Uczestnik programu „Przyjaciele Wróżki”. Bez danych osobowych: pseudonim + hash telefonu."""
    id = db.Column(db.Integer, primary_key=True)
    nick = db.Column(db.String(40), unique=True, nullable=False)
    phone_hash = db.Column(db.String(64), unique=True, nullable=False)
    district = db.Column(db.String(20), nullable=False)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    code = db.Column(db.String(6))  # kod „SMS” (w demo pokazywany na ekranie)
    source = db.Column(db.String(10), nullable=False, default="live")  # live / demo


class PointAward(db.Model):
    """Punkty za trafne zgłoszenie (jedna nagroda na mieszkańca, punkt i dzień)."""
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey("resident.id"), nullable=False, index=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey("report.id"))
    at = db.Column(db.DateTime, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    kind = db.Column(db.String(10), nullable=False)  # bin / shelter


class Device(db.Model):
    """Fizyczny przycisk z wyświetlaczem e-papierowym przy punkcie (stan symulowany w demo)."""
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), primary_key=True)
    last_heartbeat = db.Column(db.DateTime, nullable=False)  # czas zegara demo
    battery = db.Column(db.Integer, nullable=False)  # %
    last_selftest = db.Column(db.DateTime)
    selftest_ok = db.Column(db.Boolean, nullable=False, default=True)


class DemoClock(db.Model):
    """Zegar scenariusza demo (jeden wiersz). W bazie, bo gunicorn ma kilka procesów."""
    id = db.Column(db.Integer, primary_key=True)
    now = db.Column(db.DateTime, nullable=False)
    last_activity = db.Column(db.DateTime)  # prawdziwy czas UTC ostatniej akcji w demo (auto-reset po bezczynności)


class Counter(db.Model):
    """Liczniki limitów (SMS, AI, logowanie) wspólne dla wszystkich workerów Gunicorna: okno stałe, klucz + początek okna."""
    key = db.Column(db.String(120), primary_key=True)
    window_start = db.Column(db.Integer, primary_key=True)  # sekundy epoki, początek okna
    count = db.Column(db.Integer, nullable=False, default=0)
