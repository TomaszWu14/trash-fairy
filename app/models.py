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


class Emptying(db.Model):
    """Opróżnienie punktu przez ekipę MPO, z poziomem zastanym przed opróżnieniem."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    at = db.Column(db.DateTime, nullable=False, index=True)
    level = db.Column(db.Integer, nullable=False)  # 0/25/50/75/100


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


class DemoClock(db.Model):
    """Zegar scenariusza demo (jeden wiersz). W bazie, bo gunicorn ma kilka procesów."""
    id = db.Column(db.Integer, primary_key=True)
    now = db.Column(db.DateTime, nullable=False)
