"""Stan punktu — reguły w kodzie (koncepcja, sekcja 6.2). Etap 1: tylko poziom z symulacji."""
from sqlalchemy import func

from . import db
from .models import Forecast

WARN_FROM = 60
BAD_ABOVE = 85

# kolor nigdy nie jest jedynym nośnikiem informacji: każdy stan ma też symbol i opis
STATES = {
    "ok": {"symbol": "✓", "label": "w porządku"},
    "warn": {"symbol": "~", "label": "zapełnia się"},
    "bad": {"symbol": "!", "label": "do opróżnienia"},
}


def level_state(level):
    if level > BAD_ABOVE:
        return "bad"
    if level >= WARN_FROM:
        return "warn"
    return "ok"


def current_levels():
    """{point_id: ostatni poziom z symulacji}"""
    latest = (db.session.query(Forecast.point_id, func.max(Forecast.at).label("at"))
              .filter(Forecast.source == "sim").group_by(Forecast.point_id).subquery())
    rows = (db.session.query(Forecast.point_id, Forecast.level)
            .join(latest, (Forecast.point_id == latest.c.point_id) & (Forecast.at == latest.c.at))
            .filter(Forecast.source == "sim"))
    return dict(rows.all())
