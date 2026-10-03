from datetime import datetime

from . import db


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
    """Pojedyncze naciśnięcie przycisku (scalanie w zgłoszenia robi logika, nie tabela)."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip = db.Column(db.String(45))


class Emptying(db.Model):
    """Opróżnienie punktu przez ekipę MPO, z poziomem zastanym przed opróżnieniem."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    level = db.Column(db.Integer, nullable=False)  # 0/25/50/75/100


class Forecast(db.Model):
    """Szereg czasowy poziomu zapełnienia punktu.

    source='sim'  — historia z symulatora (etap 1),
    source='pred' — prognoza (etap 3).
    """
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False)
    at = db.Column(db.DateTime, nullable=False)
    level = db.Column(db.Float, nullable=False)  # %, może przekroczyć 100 (przepełnienie)
    source = db.Column(db.String(8), nullable=False, default="sim")

    __table_args__ = (db.Index("ix_forecast_point_at", "point_id", "at"),)
