from flask import Blueprint, jsonify, render_template
from sqlalchemy import text

from . import db
from .models import Point

bp = Blueprint("main", __name__)


@bp.get("/")
def panel():
    return render_template("panel.html")


@bp.get("/przycisk/<int:point_id>")
def button(point_id):
    return render_template("przycisk.html", point=db.get_or_404(Point, point_id))


@bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        return jsonify(status="error", db="down"), 503
    return jsonify(status="ok", db="ok")
