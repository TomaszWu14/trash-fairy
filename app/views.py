import os
import random

from flask import Blueprint, jsonify, redirect, render_template, url_for
from sqlalchemy import text

from . import clock, db
from .geo import distance_m
from .methodology import page_context
from .models import Point
from .osm_import import RYNEK

JURY_POOL = 6  # tyle koszy najbliżej Rynku losujemy dla jury — punkty dobrze widoczne na mapie

bp = Blueprint("main", __name__)


@bp.get("/")
def panel():
    return render_template("panel.html", public_url=os.environ.get("PUBLIC_URL", ""))


def jury_pool():
    bins = Point.query.filter_by(kind="bin").all()
    return sorted(bins, key=lambda p: distance_m(p.lat, p.lon, *RYNEK))[:JURY_POOL]


@bp.get("/jury")
def jury():
    """Kod QR w panelu prowadzi tutaj: losowy kosz przy Rynku, żeby jury naciskało różne przyciski."""
    pool = jury_pool()
    if not pool:
        return redirect(url_for("main.panel"))
    return redirect(url_for("main.button", point_id=random.choice(pool).id, jury=1))


@bp.get("/metodologia")
def methodology():
    return render_template("metodologia.html", **page_context(clock.now()))


@bp.get("/przycisk/<int:point_id>")
def button(point_id):
    return render_template("przycisk.html", point=db.get_or_404(Point, point_id))


@bp.get("/ekipa")
def crew():
    return render_template("ekipa.html")


@bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        return jsonify(status="error", db="down"), 503
    return jsonify(status="ok", db="ok")


@bp.get("/program")
def program():
    from .residents import DISTRICTS
    return render_template("program.html", districts=sorted(set(DISTRICTS.values())))


@bp.get("/program/regulamin")
def program_rules():
    from .residents import HEARTBEAT_LOST, POINTS
    return render_template("regulamin.html", points=POINTS, heartbeat_h=int(HEARTBEAT_LOST.total_seconds() // 3600))
