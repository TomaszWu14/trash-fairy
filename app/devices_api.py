"""API urządzeń na koszach (/api/urzadzenia). Reguły i założenia: app/devices.py. DANE SYNTETYCZNE (meta.syntetyczne).

Błędy jak w panelu miasta: {"blad": "<komunikat po polsku>", "kod": "<kod>"} z HTTP 400 (zły filtr) albo 404.
"""
from flask import Blueprint, jsonify, request

from . import clock, devices
from .dashboard_api import ApiError

bp = Blueprint("devices_api", __name__, url_prefix="/api")
META = {"syntetyczne": True, "zrodlo": "Dane syntetyczne (app/devices.py); żywotność i pojemność baterii to założenia demo."}


@bp.errorhandler(ApiError)
def _api_error(e):
    return jsonify(blad=e.blad, kod=e.kod), e.status


def _choice(name, allowed, kod):
    v = request.args.get(name) or None
    if v is not None and v not in allowed:
        raise ApiError(400, kod, f"Nieznana wartość „{name}”. Dozwolone: {', '.join(allowed)}.")
    return v


@bp.get("/urzadzenia")
def device_list():
    now = clock.now()
    kind = _choice("typ", list(devices.KINDS), "nieznany_typ")
    district = _choice("dzielnica", devices.districts(), "nieznana_dzielnica")
    st = _choice("status", list(devices.STATUS), "nieznany_status")
    items = devices.overview(now, kind, district)
    n = len(items)
    kpi = {"lacznie": n, "aktywne": sum(i["online"] for i in items),
           "do_wymiany_30_dni": sum(i["dni_do_wymiany"] <= devices.REPLACE_WITHIN_DAYS for i in items),
           "bez_sygnalu": sum(not i["online"] for i in items), "odczyty_24h": sum(i["odczyty_24h"] for i in items),
           "srednia_bateria": round(sum(i["bateria_pct"] for i in items) / n) if n else None,
           "wg_typu": devices.counts_by_kind(kind, district)}
    statusy = [{"status": k, "etykieta": lab, "liczba": sum(i["status"] == k for i in items)}
               for k, (lab, _) in devices.STATUS.items()]
    return jsonify(meta={**META, "teraz": now.isoformat(), "zegar": now.isoformat(),
                         "filtry": {"typ": kind, "dzielnica": district, "status": st},
                         "typy": {k: v["label"] for k, v in devices.KINDS.items()}, "dzielnice": devices.districts()},
                   kpi=kpi, statusy=statusy, urzadzenia=[i for i in items if not st or i["status"] == st])


@bp.get("/urzadzenia/<int:point_id>")
def device_detail(point_id):
    now = clock.now()
    d = devices.detail(point_id, now)
    if d is None:
        raise ApiError(404, "nieznane_urzadzenie", f"Przy koszu {point_id} nie ma urządzenia.")
    return jsonify(meta={**META, "teraz": now.isoformat(), "zegar": now.isoformat()}, urzadzenie=d)
