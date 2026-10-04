"""Otwarte API tylko do odczytu (/api/v1) dla miasta, MPO i innych zespołów. Kontrakt: app/static/openapi.json.

Celowo bez danych wewnętrznych: wiarygodności przycisków, powodów nadużyć, danych mieszkańców i zgłoszeń kierowców.
CORS * (to dane publiczne), `meta.synthetic` mówi wprost, że poziomy pochodzą z symulacji.
ponytail: bez kluczy i limitów — przed pilotażem klucze i limit na klienta (ROADMAPA.md).
"""
import csv
import io
from datetime import datetime, timedelta

from flask import Blueprint, Response, jsonify, request, url_for
from sqlalchemy import func, select

from . import clock, db, traffic, weather
from .api_pl import numer
from .dashboard import last_months, month_of, pickups, reports
from .forecast import point_series
from .models import Point, Press, Report
from .routes import DEPOT, next_runs
from .state import current_routes, point_states

bp = Blueprint("open_api", __name__, url_prefix="/api/v1")
PUBLIC = ("level", "state", "label", "fresh", "crossing")
BIN_CAPACITY_L = {"bin": 120, "shelter": 1100}


def conditions(now):
    """Pogoda (mnożnik prognozy) i ruch (mnożnik czasu przejazdu)."""
    return {"weather": weather.conditions(now), "traffic": traffic.conditions()}


@bp.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Cache-Control"] = "public, max-age=60"
    return resp


@bp.errorhandler(404)
def not_found(_e):
    # kontrakt openapi.json (Error): {ok: false, message}; reszta /api/* ma format {blad, kod}
    return jsonify(ok=False, message="Nie znaleziono."), 404


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
                for p in Point.live_query().order_by(Point.id) if p.id in states]
    return jsonify(type="FeatureCollection", meta=_meta(now), features=features)


@bp.get("/bins/<int:point_id>")
def bin_detail(point_id):
    now = clock.now()
    p = Point.live_or_404(point_id)
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


# --- otwarte dane miesięczne (agregaty, bez pojedynczych zdarzeń) ---

OPEN_DATA_SOURCE = "Dane syntetyczne (generator app/history.py) i zdarzenia demo na żywo, agregaty miesięczne bez danych osobowych."
OPEN_DATA_HEADER = ["miesiac", "dzielnica", "frakcja", "odbiory", "masa_kg", "zgloszenia"]


def _monthly_open_data(now):
    """Wiersze {miesiac, dzielnica, frakcja, odbiory, masa_kg, zgloszenia} z 12 ostatnich miesięcy (dwa GROUP BY)."""
    months = last_months(now)
    od = datetime.strptime(months[0], "%Y-%m")
    o, z = pickups(now), reports(now)
    om, zm = month_of(o.c.at), month_of(z.c.created_at)
    rows = {}

    def row(m, d, f):
        return rows.setdefault((m, d or "", f or ""), {"miesiac": m, "dzielnica": d or "", "frakcja": f or "",
                                                        "odbiory": 0, "masa_kg": 0.0, "zgloszenia": 0})

    q = (select(om, o.c.district, o.c.fraction, func.count(), func.coalesce(func.sum(o.c.mass_kg), 0))
         .where(o.c.at >= od).group_by(om, o.c.district, o.c.fraction))
    for m, d, f, n, kg in db.session.execute(q):
        row(m, d, f).update(odbiory=n, masa_kg=round(float(kg), 1))
    q = (select(zm, z.c.district, z.c.fraction, func.count())
         .where(z.c.created_at >= od).group_by(zm, z.c.district, z.c.fraction))
    for m, d, f, n in db.session.execute(q):
        row(m, d, f)["zgloszenia"] = n
    return [rows[k] for k in sorted(rows)]


@bp.get("/open-data/miesieczne.csv")
def open_data_csv():
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")
    w.writerow([f"# {OPEN_DATA_SOURCE} Dzielnice i adresy: © OpenStreetMap contributors (ODbL 1.0)."])
    w.writerow(OPEN_DATA_HEADER)
    for r in _monthly_open_data(clock.now()):
        w.writerow([str(r[k]).replace(".", ",") if k == "masa_kg" else r[k] for k in OPEN_DATA_HEADER])
    return Response("﻿" + out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="trash-fairy-otwarte-dane-miesieczne.csv"'})


@bp.get("/open-data/miesieczne.json")
def open_data_json():
    now = clock.now()
    return jsonify(meta={**_meta(now), "source": OPEN_DATA_SOURCE}, rows=_monthly_open_data(now))


# --- Open311 GeoReport v2 (tylko odczyt, bez komentarzy, IP, zdjęć i identyfikatorów mieszkańców) ---

SERVICES = {"przepelniony": "Przepełniony kosz", "odpady_obok": "Odpady obok kosza",
            "uszkodzony": "Uszkodzony kosz", "inne": "Inny problem"}
PRESS_KIND = {"overflow": "odpady_obok", "damaged": "uszkodzony", "other": "inne"}  # None / full = przepelniony
OPEN311_LIMIT = 500


class BadParam(Exception):
    pass


@bp.errorhandler(BadParam)
def bad_param(e):
    return jsonify(blad=str(e), kod="zly_parametr"), 400


def _iso_arg(name, end=False):
    raw = request.args.get(name)
    if not raw:
        return None
    try:
        at = datetime.fromisoformat(raw).replace(tzinfo=None)  # ponytail: strefa ignorowana, zegar demo jest naiwny
    except ValueError:
        raise BadParam(f"Parametr {name} musi być datą ISO 8601, np. 2026-10-04 albo 2026-10-04T12:00.") from None
    return at + timedelta(days=1) if end and len(raw) == 10 else at  # sama data końca = cały dzień


@bp.get("/open311/services.json")
def open311_services():
    return jsonify([{"service_code": c, "service_name": n, "metadata": False, "type": "realtime", "group": "Odpady"}
                    for c, n in SERVICES.items()])


@bp.get("/open311/requests.json")
def open311_requests():
    now = clock.now()
    start, end, status = _iso_arg("start_date"), _iso_arg("end_date", end=True), request.args.get("status")
    if status not in (None, "", "open", "closed"):
        raise BadParam("Parametr status przyjmuje wartości open albo closed.")
    if start and end and start >= end:
        raise BadParam("start_date musi być wcześniejsza niż end_date.")
    first_kind = (select(Press.kind).where(Press.report_id == Report.id).order_by(Press.at, Press.id).limit(1)
                  .correlate(Report).scalar_subquery())
    closed = Report.resolved_at.isnot(None) & (Report.resolved_at <= now)
    q = (select(Report.id, Report.first_at, Report.last_at, Report.resolved_at, first_kind, Point.lat, Point.lon,
                Point.address, Point.name)
         .join(Point, Point.id == Report.point_id).where(Point.live, Report.first_at <= now))
    if start:
        q = q.where(Report.first_at >= start)
    if end:
        q = q.where(Report.first_at < end)
    if status:
        q = q.where(closed if status == "closed" else ~closed)
    out = []
    for rid, first_at, last_at, resolved_at, kind, lat, lon, address, name in db.session.execute(
            q.order_by(Report.first_at.desc(), Report.id.desc()).limit(OPEN311_LIMIT)):
        done = resolved_at is not None and resolved_at <= now
        code = PRESS_KIND.get(kind, "przepelniony")
        out.append({"service_request_id": numer(rid), "status": "closed" if done else "open", "service_code": code,
                    "service_name": SERVICES[code], "requested_datetime": first_at.isoformat(),
                    "updated_datetime": (resolved_at if done else last_at).isoformat(),
                    "lat": lat, "long": lon, "address": address or name})
    return jsonify(out)
