"""API urządzeń na koszach (/api/urzadzenia). Reguły i założenia: app/devices.py. DANE SYNTETYCZNE (meta.syntetyczne).

Błędy jak w panelu miasta: {"blad": "<komunikat po polsku>", "kod": "<kod>"} z HTTP 400 (zły filtr) albo 404.
"""
import hashlib
import hmac

from flask import Blueprint, current_app, jsonify, request

from . import clock, db, devices, rate
from .dashboard_api import ApiError
from .models import Device, DeviceInfo, Point

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
           # krytyczna bateria (< 15%) to też wymiana teraz, choć z wieku zostałoby jej np. 40 dni
           "do_wymiany_30_dni": sum(i["dni_do_wymiany"] <= devices.REPLACE_WITHIN_DAYS
                                    or i["bateria_pct"] < devices.CRITICAL_BATTERY for i in items),
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


READING_GAP_S = 10  # jedno urządzenie: najwyżej jeden odczyt na 10 s (czujnik wysyła co 15 min, panel co godzinę)


def device_token(serial):
    """Token urządzenia (nagłówek X-Token-Urzadzenia): HMAC numeru seryjnego, wgrywany do urządzenia przy montażu."""
    key = current_app.config["SECRET_KEY"].encode()
    return hmac.new(key, f"urzadzenie:{serial}".encode(), hashlib.sha256).hexdigest()[:24]


def _pct(data, name, required=False):
    v = data.get(name)
    if v is None and not required:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 100:
        raise ApiError(400, "zly_odczyt", f"Pole „{name}” musi być liczbą od 0 do 100.")
    return round(v)


@bp.post("/odczyty")
def reading():
    """Odczyt z urządzenia na koszu (IoT): czujnik podaje zapełnienie, panel sygnał życia; oba opcjonalnie baterię i autotest.

    Body JSON: {"numer_seryjny": "TF-US-000123", "zapelnienie": 0–100, "bateria": 0–100, "autotest_ok": true}.
    Czas odczytu = zegar demo (urządzenie nie ustawia czasu serwera). Status urządzenia liczą reguły z app/devices.py."""
    data = request.get_json(silent=True) or {}
    serial = str(data.get("numer_seryjny") or "")[:20]
    info = DeviceInfo.query.filter_by(serial=serial).first() if serial else None
    token = request.headers.get("X-Token-Urzadzenia", "")
    if info is None or not hmac.compare_digest(token, device_token(serial)):
        raise ApiError(401, "nieznane_urzadzenie", "Nieznany numer seryjny albo zły token urządzenia.")
    fill = _pct(data, "zapelnienie", required=info.kind == "czujnik")
    battery = _pct(data, "bateria")
    selftest = data.get("autotest_ok")
    if selftest is not None and not isinstance(selftest, bool):
        raise ApiError(400, "zly_odczyt", "Pole „autotest_ok” musi być true albo false.")
    if not rate.hit(f"odczyt:{serial}", 1, READING_GAP_S):
        raise ApiError(429, "za_czesto", f"Urządzenie może wysłać odczyt raz na {READING_GAP_S} s.")
    now = clock.now()
    if info.kind == "czujnik":
        info.last_seen = now
        db.session.get(Point, info.point_id).snapshot_fill = fill
        if selftest is not None:
            info.selftest_ok = selftest
    else:
        dev = db.session.get(Device, info.point_id)
        dev.last_heartbeat = now
        if battery is not None:
            dev.battery = battery
        if selftest is not None:
            dev.selftest_ok, dev.last_selftest = selftest, now
    db.session.commit()
    d = devices.detail(info.point_id, now)
    return jsonify(przyjeto=True, urzadzenie={k: d[k] for k in ("numer_seryjny", "status", "status_etykieta", "bateria_pct",
                                                                 "ostatni_odczyt")}), 201
