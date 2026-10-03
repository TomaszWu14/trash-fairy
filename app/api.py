from datetime import UTC, datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from . import clock, db
from .models import Point, Press, Report
from .reports import record_press
from .simulation import DEMO_NOW
from .state import point_states

bp = Blueprint("api", __name__, url_prefix="/api")

# Limit naciśnięć na IP. Łagodny, bo na sali cała publiczność wychodzi zwykle z jednego adresu (NAT).
SAME_POINT_GAP = timedelta(seconds=2)
PER_IP_HOUR = 120

WEEKDAYS = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]


def version():
    """Zmienia się przy każdym naciśnięciu i przewinięciu zegara — wystarcza do pollingu."""
    last_press = db.session.query(func.max(Press.id)).scalar() or 0
    return f"{clock.now():%Y%m%d%H%M}-{last_press}"


def snapshot():
    now = clock.now()
    states = point_states(now)
    features = []
    for p in Point.query.order_by(Point.id):
        s = states.get(p.id)
        if s is None:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [p.lon, p.lat]},
            "properties": {"id": p.id, "kind": p.kind, "name": p.name, "area": p.area, **s},
        })
    count = lambda st: sum(f["properties"]["state"] == st for f in features)
    return {
        "type": "FeatureCollection",
        "version": version(),
        "clock": {"now": now.isoformat(), "label": f"{now:%d.%m.%Y}, {WEEKDAYS[now.weekday()]} {now:%H:%M}",
                  "can_advance": now < clock.MAX_NOW},
        "summary": {
            "bad": count("bad"), "warn": count("warn"), "ok": count("ok"),
            "live_presses": Press.query.filter(Press.wall_at.isnot(None)).count(),
            "live_reports": Report.query.filter(Report.first_at >= DEMO_NOW).count(),
        },
        "features": features,
    }


@bp.get("/points")
def points():
    return jsonify(snapshot())


@bp.get("/changes")
def changes():
    if request.args.get("since") == version():
        return jsonify(changed=False)
    return jsonify(changed=True, **snapshot())


@bp.post("/press")
def press():
    data = request.get_json(silent=True) or request.form
    try:
        point = db.session.get(Point, int(data.get("point_id")))
    except (TypeError, ValueError):
        point = None
    if point is None:
        return jsonify(ok=False, message="Nie ma takiego punktu."), 404

    wall = datetime.now(UTC).replace(tzinfo=None)
    ip = request.remote_addr
    recent_same = Press.query.filter(Press.ip == ip, Press.point_id == point.id,
                                     Press.wall_at > wall - SAME_POINT_GAP).first()
    hourly = Press.query.filter(Press.ip == ip, Press.wall_at > wall - timedelta(hours=1)).count()
    if recent_same or hourly >= PER_IP_HOUR:
        return jsonify(ok=False, message="Wróżka już wie! Spróbuj za chwilę."), 429

    report = record_press(point.id, clock.now(), ip=ip, wall_at=wall)
    return jsonify(ok=True, message="Wróżka już leci!", report_id=report.id, presses=report.presses)


@bp.post("/clock/advance")
def clock_advance():
    clock.advance(1)
    return jsonify(snapshot())


@bp.post("/clock/reset")
def clock_reset():
    clock.reset()
    return jsonify(snapshot())
