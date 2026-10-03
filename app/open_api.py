"""Otwarte API tylko do odczytu (/api/v1) dla miasta, MPO i innych zespołów. Kontrakt: app/static/openapi.json.

Celowo bez danych wewnętrznych: wiarygodności przycisków, powodów nadużyć, danych mieszkańców i zgłoszeń kierowców.
CORS * (to dane publiczne), `meta.synthetic` mówi wprost, że poziomy pochodzą z symulacji.
ponytail: bez kluczy i limitów — przed pilotażem klucze i limit na klienta (ROADMAPA.md).
"""
from flask import Blueprint, jsonify, url_for

from . import clock, db
from .api import BIN_CAPACITY_L, conditions
from .forecast import point_series
from .models import Point
from .routes import DEPOT, next_runs
from .state import current_routes, point_states

bp = Blueprint("open_api", __name__, url_prefix="/api/v1")
PUBLIC = ("level", "state", "label", "fresh", "crossing")


@bp.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Cache-Control"] = "public, max-age=60"
    return resp


def _meta(now):
    return {"synthetic": True, "clock": now.isoformat(), "docs": url_for("main.api_docs"),
            "license": "Pozycje koszy: © OpenStreetMap contributors (ODbL 1.0). Poziomy i trasy: symulacja Trash Fairy."}


def _bin(p, s, now):
    run_at, _ = next_runs(p.kind, now)
    return {"id": p.id, "kind": p.kind, "name": p.name, "area": p.area, "capacity_l": BIN_CAPACITY_L[p.kind],
            **{k: s[k] for k in PUBLIC}, "next_run": run_at.isoformat()}


@bp.get("/bins.geojson")
def bins():
    now = clock.now()
    states = point_states(now)
    features = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [p.lon, p.lat]},
                 "properties": _bin(p, states[p.id], now)}
                for p in Point.query.order_by(Point.id) if p.id in states]
    return jsonify(type="FeatureCollection", meta=_meta(now), features=features)


@bp.get("/bins/<int:point_id>")
def bin_detail(point_id):
    now = clock.now()
    p = db.get_or_404(Point, point_id)
    forecast = [{"at": at.isoformat(), "level": round(est), "low": round(low), "high": round(high)}
                for at, est, low, high in point_series(p, now, hours_back=0) if at > now and est is not None]
    return jsonify(meta=_meta(now), bin={**_bin(p, point_states(now)[p.id], now), "lat": p.lat, "lon": p.lon},
                   forecast=forecast)


@bp.get("/routes")
def routes():
    now = clock.now()
    fleets = [{"kind": f["kind"], "label": f["label"], "run_at": f["run_at"], "km": f["km"],
               "stops": [{"order": s["order"], "id": s["id"], "name": s["name"], "lat": s["lat"], "lon": s["lon"]}
                         for s in f["stops"]]}
              for f in current_routes(now)]
    return jsonify(meta=_meta(now), depot=DEPOT, fleets=fleets)


@bp.get("/conditions")
def conditions_view():
    now = clock.now()
    return jsonify(meta=_meta(now), **conditions(now))
