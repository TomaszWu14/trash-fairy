from datetime import UTC, datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from . import clock, db
from .comparison import compare
from .events import AFTER, RADIUS_M
from .forecast import THRESHOLD, forecast_quality, point_series
from .models import Emptying, Event, Point, Press, Report
from .reports import record_press
from .routes import DEPOT, plan_routes
from .simulation import DEMO_NOW, hour_floor
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
        "events": [{"name": e.name, "venue": e.venue, "lat": e.lat, "lon": e.lon, "scale": e.scale,
                    "radius_m": RADIUS_M[e.scale], "active": e.start <= now < e.end + AFTER,
                    "hours": f"{e.start:%d.%m %H:%M}–{e.end:%H:%M}"}
                   for e in Event.query.order_by(Event.start)
                   if e.end + AFTER > now and e.start < now + timedelta(hours=24)],
        "forecast_quality": forecast_quality(hour_floor(now)),
        "features": features,
    }


@bp.get("/points")
def points():
    return jsonify(snapshot())


@bp.get("/points/<int:point_id>")
def point_detail(point_id):
    point = db.get_or_404(Point, point_id)
    now = clock.now()
    series = point_series(point, now)
    since = series[0][0] if series else now
    return jsonify(
        id=point.id, name=point.name, kind=point.kind, area=point.area, **point_states(now)[point.id],
        threshold=THRESHOLD, now=now.isoformat(),
        series=[{"at": at.isoformat(), "label": f"{at:%H}:00", "est": _r(est), "low": _r(low), "high": _r(high),
                 "future": at > hour_floor(now)} for at, est, low, high in series],
        emptyings=[{"at": e.at.isoformat(), "level": e.level} for e in Emptying.query
                   .filter(Emptying.point_id == point.id, Emptying.at >= since, Emptying.at <= now).order_by(Emptying.at)],
        presses=[p.at.isoformat() for p in Press.query
                 .filter(Press.point_id == point.id, Press.at >= since, Press.at <= now).order_by(Press.at)],
    )


@bp.get("/routes")
def routes():
    now = clock.now()
    return jsonify(depot=DEPOT, fleets=plan_routes(now, point_states(now)))


@bp.get("/comparison")
def comparison():
    # porównanie dotyczy 4 tygodni przed startem scenariusza — nie zależy od przewijania zegara
    return jsonify(compare(DEMO_NOW))


def _r(v):
    return None if v is None else round(v, 1)


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
