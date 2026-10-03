from flask import Blueprint, jsonify, render_template
from sqlalchemy import text

from . import db
from .models import Point
from .simulation import DEMO_NOW
from .state import STATES, current_levels, level_state

bp = Blueprint("main", __name__)


@bp.get("/")
def panel():
    return render_template("panel.html", demo_now=DEMO_NOW)


@bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        return jsonify(status="error", db="down"), 503
    return jsonify(status="ok", db="ok")


@bp.get("/api/points")
def points():
    levels = current_levels()
    features = []
    for p in Point.query.order_by(Point.id):
        level = levels.get(p.id, 0.0)
        state = level_state(level)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [p.lon, p.lat]},
            "properties": {
                "id": p.id, "kind": p.kind, "name": p.name, "area": p.area,
                "level": round(level), "state": state, **STATES[state],
            },
        })
    return jsonify(type="FeatureCollection", features=features)
