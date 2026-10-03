from datetime import UTC, datetime, timedelta

from pathlib import Path

import os

from flask import Blueprint, abort, jsonify, request, send_file, session
from sqlalchemy import func

from . import auth, clock, db, fairy, http, llm, osrm, photos, rate, residents, sms, traffic, weather
from .comparison import compare
from .events import AFTER, RADIUS_M
from .forecast import THRESHOLD, forecast_quality, point_series
from .misuse import misuse_overview
from .models import Device, Emptying, Event, PhotoAnalysis, Point, Press, Report, StopIssue
from .recommendations import recommendations
from .reports import MERGE_WINDOW, record_press, resolve_reports
from .geo import distance_m
from .models import Resident
from .routes import DEPOT, next_runs, plan_routes
from .simulation import DEMO_NOW, hour_floor
from .state import CREW_ISSUES, current_routes, data_version, point_states

bp = Blueprint("api", __name__, url_prefix="/api")

# Limit naciśnięć na IP. Łagodny, bo na sali cała publiczność wychodzi zwykle z jednego adresu (NAT).
SAME_POINT_GAP = timedelta(seconds=2)
PER_IP_HOUR = 120
JURY_POINT_ID = 18  # kosz z /telefony i QR jury (app/views.py)
JURY_PER_PHONE_HOUR = 20
GEO_RADIUS_M = 150  # zgłoszenie z telefonu z położeniem dalej niż 150 m od kosza odrzucamy (spec, pkt 4)

WEEKDAYS = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
WEEKDAYS_SHORT = ["pon.", "wt.", "śr.", "czw.", "pt.", "sob.", "niedz."]


LEVELS = (0, 25, 50, 75, 100)


def version():
    """Wersja danych dla pollingu (app/state.data_version); ta sama służy za klucz cache stanu i tras."""
    return data_version()


# Pola tylko dla dyspozytora: wiarygodność przycisków, nadużycia ze zdjęć, problemy zgłoszone przez kierowcę.
# Filtrujemy na serwerze (decyzja 7), bo ukrycie w JS i tak zostawiłoby je w odpowiedzi.
DISPATCHER_ONLY = {"reliability", "check_reason", "misuse", "crew_issue", "photo_note", "photo_error"}


def public_view(props):
    return props if auth.is_dispatcher() else {k: v for k, v in props.items() if k not in DISPATCHER_ONLY}


def conditions(now):
    """Pogoda (mnożnik prognozy) i ruch (mnożnik czasu przejazdu) — panel i /api/v1/conditions."""
    return {"weather": weather.conditions(now), "traffic": traffic.conditions()}


def _eta(run_at):
    """(ETA kursu z opóźnieniem dojazdu w korku, opóźnienie w min). Bez danych o ruchu opóźnienie = 0."""
    delay = traffic.delay_min(traffic.city_ratio())
    return run_at + timedelta(minutes=delay), delay


def snapshot():
    now = clock.now()
    states = point_states(now)
    mo = misuse_overview(now)
    features = []
    for p in Point.query.order_by(Point.id):
        s = states.get(p.id)
        if s is None:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [p.lon, p.lat]},
            "properties": public_view({"id": p.id, "kind": p.kind, "name": p.name, "area": p.area, **s,
                                       **mo["points"].get(p.id, {}), "recommendation": mo["recommendations"].get(p.id)}),
        })
    count = lambda st: sum(f["properties"]["state"] == st for f in features)
    return {
        "type": "FeatureCollection",
        "version": version(),
        "conditions": conditions(now),
        "clock": {"now": now.isoformat(), "label": f"{now:%d.%m.%Y}, {WEEKDAYS[now.weekday()]} {now:%H:%M}",
                  "can_advance": now < clock.MAX_NOW},
        "summary": {
            "bad": count("bad"), "warn": count("warn"), "ok": count("ok"),
            "live_presses": Press.query.filter(Press.wall_at.isnot(None)).count(),
            "live_reports": Report.query.filter(Report.first_at >= DEMO_NOW).count(),
        },
        "events": [{"name": e.name, "venue": e.venue, "lat": e.lat, "lon": e.lon, "scale": e.scale, "source": e.source,
                    "radius_m": RADIUS_M[e.scale], "active": e.start <= now < e.end + AFTER,
                    "hours": f"{e.start:%d.%m %H:%M}–{e.end:%H:%M}"}
                   for e in Event.query.order_by(Event.start)
                   if e.end + AFTER > now and e.start < now + timedelta(hours=24)],
        "forecast_quality": forecast_quality(hour_floor(now)),
        "links": mo["links"] if auth.is_dispatcher() else [],
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
    mo = misuse_overview(now)
    analyses = (PhotoAnalysis.query.filter(PhotoAnalysis.point_id == point.id, PhotoAnalysis.at <= now)
                .order_by(PhotoAnalysis.at.desc(), PhotoAnalysis.id.desc()).limit(5))
    return jsonify(
        **public_view({**point_states(now)[point.id], **mo["points"].get(point.id, {})}),
        id=point.id, name=point.name, kind=point.kind, area=point.area, recommendation=mo["recommendations"].get(point.id),
        investment=next((r for r in recommendations(now, mo["recommendations"]) if r["point_id"] == point.id), None),
        analyses=[_analysis(pa) for pa in analyses] if auth.is_dispatcher() else [],
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
    states = point_states(now)
    fleets = current_routes(now)
    for f in fleets:
        for s in f["stops"]:  # PWA kierowcy: domyślny poziom zastany i znacznik stanu bez drugiego zapytania
            st = states[s["id"]]
            s.update(level=st["value"], state=st["state"], fresh=st["fresh"])  # przebieg po ulicach tylko do rysowania; km zostają z road_m
        out, approx_out = osrm.street_path(f["path"][:-1])
        back, approx_back = osrm.street_path(f["path"][-2:]) if f["stops"] else ([], False)
        f["geometry"] = {"out": out, "back": back, "approx": approx_out or approx_back}
    k = traffic.city_ratio()
    for f in fleets:  # ruch zmienia tylko czas przejazdu, nigdy punktów ani km
        f["progress"] = crew_progress(f["kind"])
        f["drive_min"] = traffic.drive_min(f["km"], k)
        f["drive_min_free"] = traffic.drive_min(f["km"])
    return jsonify(depot=DEPOT, fleets=fleets, now=now.isoformat(),
                   traffic={"ratio": k, "delay_min": traffic.delay_min(k)} if k else None)


@bp.get("/kierowca/kurs")
def driver_run():
    """PWA kierowcy: tylko kurs jego floty (decyzja 2), z przebiegiem po ulicach i korektą czasu z ruchu.
    ?podglad=1 bez logowania: kurs floty koszy do odczytu (ramka dla jury); trasy i tak są publiczne na /."""
    preview = request.args.get("podglad") == "1" and auth.role() != "driver"
    if not preview and auth.role() != "driver":
        return jsonify(ok=False, login_required=True, message="Zaloguj się jako kierowca."), 401
    now = clock.now()
    states = point_states(now)
    fleet = "bin" if preview else auth.fleet()
    f = next(f for f in current_routes(now) if f["kind"] == fleet)
    for s in f["stops"]:
        st = states[s["id"]]
        s.update(level=st["value"], state=st["state"], fresh=st["fresh"])
    out, approx_out = osrm.street_path(f["path"][:-1])
    back, approx_back = osrm.street_path(f["path"][-2:]) if f["stops"] else ([], False)
    f["geometry"] = {"out": out, "back": back, "approx": approx_out or approx_back}
    k = traffic.city_ratio()
    f["drive_min"], f["drive_min_free"] = traffic.drive_min(f["km"], k), traffic.drive_min(f["km"])
    return jsonify(depot=DEPOT, fleet=f, now=now.isoformat(), login=session.get("login"))


@bp.get("/recommendations")
def recommendations_list():
    now = clock.now()
    return jsonify(recommendations(now, misuse_overview(now)["recommendations"]))


@bp.get("/fairy")
def fairy_get():
    now = clock.now()
    report = fairy.latest(now)
    return jsonify(report=fairy.to_dict(report), fresh=fairy.is_fresh(report, now), available=llm.available())


@bp.post("/fairy")
@auth.require("dispatcher")
def fairy_refresh():
    """Nowy raport. Przy błędzie API: komunikat + ostatni raport (nigdy 500)."""
    now = clock.now()
    try:
        report, error = fairy.generate(now), None
    except llm.LLMError as e:
        report, error = fairy.latest(now), str(e)
    return jsonify(report=fairy.to_dict(report), fresh=fairy.is_fresh(report, now), error=error, available=llm.available())


@bp.get("/comparison")
def comparison():
    # porównanie dotyczy 4 tygodni przed startem scenariusza — nie zależy od przewijania zegara
    return jsonify(compare(DEMO_NOW))


def _r(v):
    return None if v is None else round(v, 1)


def _analysis(pa):
    return {"id": pa.id, "at": pa.at.isoformat(), "status": pa.status, "error": pa.error, "source": pa.source,
            "fill_level": pa.fill_level, "crew_level": pa.crew_level, "misuse": [photos.MISUSE_LABELS[m] for m in pa.misuse or []],
            "overflow_outside": pa.overflow_outside, "damage": pa.damage, "confidence": pa.confidence, "note": pa.note,
            "flag": photos.discrepancy(pa), "photo_url": f"/api/photos/{pa.id}" if pa.photo_path else None}


def _point_or_none(value):
    try:
        return db.session.get(Point, int(value))
    except (TypeError, ValueError):
        return None


def _photo_from_request(point, crew_level=None):
    """Zapisuje zdjęcie z formularza i uruchamia analizę. Zwraca (analiza, komunikat błędu)."""
    upload = request.files.get("photo")
    if not upload or not upload.filename:
        return None, None
    data = upload.read(photos.MAX_BYTES + 1)
    mt, error = photos.validate(data)
    if error:
        return None, error
    pa = photos.save(point.id, clock.now(), data, mt, crew_level=crew_level)
    photos.analyze_in_background(pa.id)
    return pa, None


@bp.post("/emptying")
@auth.require("dispatcher", "driver")
def emptying():
    """Ekipa MPO: punkt opróżniony, poziom zastany przed opróżnieniem, opcjonalne zdjęcie."""
    point = _point_or_none(request.form.get("point_id"))
    if point is None:
        return jsonify(ok=False, message="Nie ma takiego punktu."), 404
    if not auth.can_touch(point):
        return jsonify(ok=False, message="Ten punkt nie należy do Twojej floty."), 403
    try:
        level = int(request.form.get("level"))
    except (TypeError, ValueError):
        level = None
    if level not in LEVELS:
        return jsonify(ok=False, message="Wybierz poziom: 0, 25, 50, 75 albo 100%."), 400
    e = Emptying(point_id=point.id, at=clock.now(), level=level, source="crew", far_m=_far_m(point, request.form))
    db.session.add(e)
    resolve_reports(e)
    db.session.commit()
    clock.touch()
    pa, error = _photo_from_request(point, crew_level=level)
    message = "Zapisano opróżnienie." + (" Zdjęcie przekazane do analizy." if pa else "")
    return jsonify(ok=True, message=message, photo_error=error, analysis_id=pa.id if pa else None)


@bp.post("/stop-issue")
@auth.require("dispatcher", "driver")
def stop_issue():
    """Kierowca: nie da się podjechać albo problem z koszem (+ opcjonalne zdjęcie). Trasy nie zmienia, decyduje dyspozytor."""
    point = _point_or_none(request.form.get("point_id"))
    if point is None:
        return jsonify(ok=False, message="Nie ma takiego punktu."), 404
    if not auth.can_touch(point):
        return jsonify(ok=False, message="Ten punkt nie należy do Twojej floty."), 403
    kind = request.form.get("kind")
    if kind not in CREW_ISSUES and kind != "skip":  # skip = „Pomiń” z PWA kierowcy (postęp kursu, decyzja 30)
        return jsonify(ok=False, message="Wybierz rodzaj problemu."), 400
    note = (request.form.get("note") or "").strip()[:200] or None
    db.session.add(StopIssue(point_id=point.id, at=clock.now(), kind=kind, note=note))
    db.session.commit()
    clock.touch()
    pa, error = _photo_from_request(point)
    return jsonify(ok=True, message="Pominięto przystanek." if kind == "skip" else f"Przekazano dyspozytorowi: {CREW_ISSUES[kind]}.", photo_error=error,
                   analysis_id=pa.id if pa else None)


def _far_m(point, form):
    """Odległość telefonu kierowcy od kosza minus dokładność GPS (jak u mieszkańca); None bez położenia. Nie blokuje (decyzja 28)."""
    try:
        d = distance_m(float(form["lat"]), float(form["lon"]), point.lat, point.lon)
    except (KeyError, TypeError, ValueError):
        return None
    return max(0, round(d - _accuracy_m(form)))


def crew_progress(kind):
    """Postęp kierowcy floty od resetu demo (decyzja 30): opróżnienia, problemy, pominięcia, oznaczenia daleko od kosza."""
    pts = {p.id: p.name for p in Point.query.filter_by(kind=kind)}
    em = Emptying.query.filter(Emptying.source == "crew", Emptying.point_id.in_(pts)).order_by(Emptying.id).all()
    iss = StopIssue.query.filter(StopIssue.point_id.in_(pts)).order_by(StopIssue.id).all()
    last = max([(e.at, "opróżniony", e.point_id) for e in em] + [(i.at, "pominięty" if i.kind == "skip" else "problem", i.point_id) for i in iss],
               default=None)
    return {"done": len(em), "issues": sum(i.kind != "skip" for i in iss), "skipped": sum(i.kind == "skip" for i in iss),
            "far": [pts[e.point_id] for e in em if e.far_m is not None and e.far_m > GEO_RADIUS_M],
            "last": {"at": f"{last[0]:%H:%M}", "what": last[1], "name": pts[last[2]]} if last else None}


def _nearest_point(lat, lon):
    best = min(Point.query, key=lambda q: distance_m(lat, lon, q.lat, q.lon), default=None)
    return (best, round(distance_m(lat, lon, best.lat, best.lon))) if best else (None, None)


@bp.post("/photo")
@auth.require("dispatcher")
def photo():
    """Zdjęcie bez opróżnienia. Bez `point_id` kosz dobieramy z GPS w EXIF (zdjęcia z miasta wgrywane paczką)."""
    point = _point_or_none(request.form.get("point_id"))
    files = [f for f in request.files.getlist("photo") + request.files.getlist("photos") if f and f.filename]
    if not files:
        return jsonify(ok=False, message="Wybierz zdjęcie."), 400
    results = []
    for upload in files:
        data = upload.read(photos.MAX_BYTES + 1)
        mt, error = photos.validate(data)
        target, dist = point, None
        if not error and target is None:
            gps = photos.gps_from_exif(data)
            if gps is None:
                error = "Brak lokalizacji w zdjęciu — wskaż kosz ręcznie."
            else:
                target, dist = _nearest_point(*gps)
                if target is None or dist > photos.MATCH_M:
                    error, target = f"Najbliższy kosz jest {dist} m od miejsca zdjęcia (limit {photos.MATCH_M} m).", None
        if error:
            results.append({"file": upload.filename, "ok": False, "message": error})
            continue
        pa = photos.save(target.id, clock.now(), data, mt)
        photos.analyze_in_background(pa.id)
        results.append({"file": upload.filename, "ok": True, "analysis_id": pa.id, "point_id": target.id, "point_name": target.name,
                        "distance_m": dist, "matched_by": "exif" if dist is not None else "form"})
    if len(results) == 1 and request.files.get("photo") is not None:
        r = results[0]
        return (jsonify(message="Zdjęcie przekazane do analizy.", **r) if r["ok"]
                else (jsonify(ok=False, message=r["message"]), 400))
    return jsonify(ok=any(r["ok"] for r in results), results=results)


@bp.get("/photos/<int:analysis_id>")
def photo_file(analysis_id):
    pa = db.get_or_404(PhotoAnalysis, analysis_id)
    if not pa.photo_path or not Path(pa.photo_path).exists():
        abort(404)
    return send_file(pa.photo_path, mimetype=pa.media_type)


@bp.get("/changes")
def changes():
    clock.maybe_auto_reset()  # po 30 min bez akcji następny widz zaczyna od 13:30
    if request.args.get("since") == version():
        return jsonify(changed=False)
    return jsonify(changed=True, **snapshot())


def current_resident():
    rid = session.get("resident_id")
    r = db.session.get(Resident, rid) if rid else None
    return r if r and r.verified else None


REPORT_KINDS = ("full", "overflow", "damaged")  # rodzaje zgłoszenia z ekranu /zglos
BIN_CAPACITY_L = {"bin": 120, "shelter": 1100}
NEIGHBOR_PUBLIC_M = 200


def _retry_at(now, recent_same, ip, wall):
    """Kiedy ten telefon może zgłosić znowu (w czasie zegara demo)."""
    if recent_same:
        return now + SAME_POINT_GAP
    oldest = db.session.query(func.min(Press.wall_at)).filter(Press.ip == ip, Press.wall_at > wall - timedelta(hours=1)).scalar()
    return now + ((oldest + timedelta(hours=1)) - wall if oldest else timedelta(minutes=30))


def _accuracy_m(data):
    """Dokładność GPS z telefonu (m), obcięta do 150 m: słaby GPS w kamienicy nie blokuje zgłoszenia przy koszu,
    a podane „accuracy 5 km” nie wyłącza kontroli odległości."""
    try:
        return min(max(float(data.get("accuracy_m") or 0), 0.0), GEO_RADIUS_M)
    except (TypeError, ValueError):
        return 0.0


@bp.post("/press")
def press():
    data = request.get_json(silent=True) or request.form
    point = _point_or_none(data.get("point_id"))
    if point is None:
        return jsonify(ok=False, message="Nie ma takiego punktu."), 404
    source = "qr" if data.get("source") == "qr" else "button"
    kind = data.get("kind") if data.get("kind") in REPORT_KINDS else None
    lat, lon = data.get("lat"), data.get("lon")
    if lat is not None and lon is not None:
        try:
            dist = distance_m(float(lat), float(lon), point.lat, point.lon)
        except (TypeError, ValueError):
            dist = None
        if dist is None or dist - _accuracy_m(data) > GEO_RADIUS_M:
            return jsonify(ok=False, reason="too_far", distance_m=round(dist) if dist else None,
                           message="Jesteś za daleko od tego kosza (ponad 150 m)."), 403
    elif source == "qr" and os.environ.get("REQUIRE_GEO") == "1":
        return jsonify(ok=False, reason="no_location", message="Włącz udostępnianie lokalizacji, żeby zgłosić z telefonu."), 403

    wall = datetime.now(UTC).replace(tzinfo=None)
    now = clock.now()
    ip = request.remote_addr
    # kosz jury (decyzja 13): cała sala ma jedno IP z Wi-Fi, więc liczymy po identyfikatorze telefonu, nie po IP
    jury_client = (data.get("jury") and point.id == JURY_POINT_ID and str(data.get("client_id") or "")[:64]) or None
    if jury_client:
        blocked = (not rate.hit(f"jury-gap:{jury_client}", 1, int(SAME_POINT_GAP.total_seconds()))
                   or not rate.hit(f"jury-hour:{jury_client}", JURY_PER_PHONE_HOUR, 3600))
        recent_same = None
    else:
        recent_same = Press.query.filter(Press.ip == ip, Press.point_id == point.id,
                                         Press.wall_at > wall - SAME_POINT_GAP).first()
        hourly = Press.query.filter(Press.ip == ip, Press.wall_at > wall - timedelta(hours=1)).count()
        blocked = recent_same or hourly >= PER_IP_HOUR
    if blocked:
        return jsonify(ok=False, retry_at=f"{_retry_at(now, recent_same, ip, wall):%H:%M}",
                       message="Wróżka już wie! Spróbuj za chwilę."), 429

    resident = current_resident()
    run_at, _ = next_runs(point.kind, now)
    eta, delay = _eta(run_at)
    if source == "button":  # fizyczny przycisk nadaje: urządzenie żyje
        dev = db.session.get(Device, point.id)
        if dev:
            dev.last_heartbeat = max(dev.last_heartbeat, now)
    if kind == "damaged":  # uszkodzenie to zadanie dla ekipy, nie sygnał zapełnienia: bez Report, bez wpływu na stan
        others = Press.query.filter(Press.point_id == point.id, Press.kind == "damaged", Press.at > now - timedelta(hours=48)).count()
        db.session.add(Press(point_id=point.id, at=now, ip=ip, wall_at=wall, source=source, kind=kind,
                             resident_id=resident.id if resident else None))
        db.session.commit()
        clock.touch()
        return jsonify(ok=True, message="Dziękujemy, ekipa sprawdzi kosz.", report_id=None, presses=others + 1, confirmed=False,
                       registered=resident is not None, status="merged" if others else "accepted", accepted_at=f"{now:%H:%M}",
                       merged_with_at=None, eta=f"{eta:%H:%M}", traffic_delay_min=delay, route=f"kurs {run_at:%H:%M}",
                       others_count=others)
    report = record_press(point.id, now, ip=ip, wall_at=wall,
                          resident_id=resident.id if resident else None, source=source, kind=kind)
    clock.touch()
    merged = report.presses > 1
    return jsonify(ok=True, message="Wróżka już leci!", report_id=report.id, presses=report.presses,
                   confirmed=report.confirmed, registered=resident is not None,
                   status="merged" if merged else "accepted", accepted_at=f"{report.first_at:%H:%M}",
                   merged_with_at=f"{report.first_at:%H:%M}" if merged else None,
                   eta=f"{eta:%H:%M}", traffic_delay_min=delay, route=f"kurs {run_at:%H:%M}",
                   others_count=report.presses - 1)


@bp.get("/zglos/<int:point_id>")
def zglos_public(point_id):
    """Dane kosza dla publicznego ekranu zgłoszenia. Bez danych wewnętrznych (wiarygodność, powody)."""
    point = db.get_or_404(Point, point_id)
    now = clock.now()
    states = point_states(now)
    s = states[point.id]
    run_at, _ = next_runs(point.kind, now)
    open_report = (Report.query.filter(Report.point_id == point.id, Report.hit.is_(None),
                                       Report.first_at > now - MERGE_WINDOW, Report.first_at <= now)
                   .order_by(Report.first_at.desc()).first())
    from .residents import device_flags
    resident = current_resident()
    return jsonify(
        id=point.id, name=point.name, address=point.osm_tags.get("addr:street") or point.area,
        type="kosz uliczny" if point.kind == "bin" else "altana osiedlowa", capacity_l=BIN_CAPACITY_L[point.kind],
        lat=point.lat, lon=point.lon, fill_pct=s["level"], state=s["state"],
        next_pickup=f"{_eta(run_at)[0]:%H:%M}", next_route=f"kurs {run_at:%H:%M}", traffic_delay_min=_eta(run_at)[1],
        button_offline=point.id in device_flags(now),
        open_report_at=f"{open_report.first_at:%H:%M}" if open_report else None,
        neighbors=[{"id": q.id, "name": q.name, "lat": q.lat, "lon": q.lon, "state": states[q.id]["state"],
                    "distance_m": round(distance_m(point.lat, point.lon, q.lat, q.lon))}
                   for q in Point.query.filter(Point.id != point.id)
                   if q.id in states and distance_m(point.lat, point.lon, q.lat, q.lon) <= NEIGHBOR_PUBLIC_M],
        clock_label=f"{WEEKDAYS_SHORT[now.weekday()]} {now:%d.%m, %H:%M}",
        member={"nick": resident.nick, "district": resident.district} if resident else None,
    )


@bp.get("/zglos/status/<int:report_id>")
def zglos_status(report_id):
    """Status zgłoszenia dla „Śledź status”: przyjęte → zaplanowane → opróżnione."""
    report = db.get_or_404(Report, report_id)
    point = db.get_or_404(Point, report.point_id)
    now = clock.now()
    run_at, _ = next_runs(point.kind, now)
    planned = report.hit is None and point_states(now)[point.id]["state"] == "bad"
    return jsonify(report_id=report.id, point=point.name, accepted_at=f"{report.first_at:%H:%M}", planned=planned,
                   run_label=f"kurs {run_at:%H:%M}", others_count=report.presses - 1,
                   emptied_at=f"{report.resolved_at:%H:%M}" if report.resolved_at else None)


@bp.get("/epapier/<int:point_id>")
def epaper_keys(point_id):
    """Stan ekranu na koszu: state_key (pełne odświeżenie) i values_key (okno częściowe). Polling co 1 s."""
    from . import epaper
    point = db.get_or_404(Point, point_id)
    state, data = epaper.display_state(point, clock.now())
    state_key, values_key = epaper.keys(state, data)
    return jsonify(state=state, state_key=state_key, values_key=values_key)


@bp.get("/display/<int:point_id>")
def display(point_id):
    """Treść wyświetlacza e-papierowego przy koszu."""
    point = db.get_or_404(Point, point_id)
    now = clock.now()
    report = (Report.query.filter(Report.point_id == point.id, Report.hit.is_(None), Report.first_at <= now)
              .order_by(Report.first_at.desc()).first())
    state = point_states(now)[point.id]
    run_at, _ = next_runs(point.kind, now)
    lines = ([f"Zgłoszono {report.first_at:%H:%M}" + (" · potwierdzone" if report.confirmed else ""),
              f"Ekipa ok. {run_at:%H:%M}" if state["state"] != "ok" else "Ekipa sprawdzi przy kursie"]
             if report else ["Kosz w porządku", "Dziękujemy!"])
    return jsonify(lines=lines, registered=current_resident() is not None, name=point.name)


@bp.post("/residents")
def residents_register():
    data = request.get_json(silent=True) or request.form
    try:
        r = residents.register(data.get("nick"), data.get("phone"), data.get("district"))
    except residents.RegistrationError as e:
        return jsonify(ok=False, message=str(e)), 400
    session["pending_resident_id"] = r.id
    session.pop("verification_sid", None)
    if sms.configured():
        try:
            session["verification_sid"] = sms.send_code(residents.normalize_phone(data.get("phone")), r.phone_hash)
            return jsonify(ok=True, message="Wysłaliśmy kod SMS. Wpisz go poniżej.", demo_code=None)
        except sms.SmsError as e:
            if e.status == 429 or http.config("SMS_DEMO_FALLBACK") != "1":
                return jsonify(ok=False, message=str(e)), e.status
    # bez bramki albo przy jej awarii (SMS_DEMO_FALLBACK=1): kod na ekranie, wyraźnie oznaczony jako demo
    return jsonify(ok=True, message="Tryb demo: zamiast SMS-a pokazujemy kod tutaj.", demo_code=r.code)


@bp.post("/residents/verify")
def residents_verify():
    data = request.get_json(silent=True) or request.form
    r = db.session.get(Resident, session.get("pending_resident_id") or 0)
    code, sid = (data.get("code") or "").strip(), session.get("verification_sid")
    if r is not None and sid:
        try:
            ok = sms.check_code(sid, code)
        except sms.SmsError as e:
            return jsonify(ok=False, message=str(e)), e.status
        if ok:
            residents.mark_verified(r)
    else:
        ok = r is not None and residents.verify(r, code)
    if not ok:
        return jsonify(ok=False, message="Nieprawidłowy kod."), 400
    session.pop("verification_sid", None)
    session.pop("pending_resident_id", None)
    session["resident_id"] = r.id
    return jsonify(ok=True, message=f"Witaj w programie, {r.nick}!")


@bp.get("/me")
def me():
    r = current_resident()
    return jsonify(profile=residents.profile(r) if r else None)


@bp.post("/me/logout")
def logout():
    session.pop("resident_id", None)
    return jsonify(ok=True)


@bp.get("/rankings")
def rankings_view():
    return jsonify(residents.rankings())


@bp.get("/devices")
def devices():
    return jsonify(residents.devices_overview(clock.now()))


@bp.post("/devices/<int:point_id>/selftest")
@auth.require("dispatcher")
def device_selftest(point_id):
    d = residents.selftest(point_id, clock.now())
    if d is None:
        return jsonify(ok=False, message="Brak urządzenia."), 404
    return jsonify(ok=True, message="Autotest OK — bez wpływu na zgłoszenia.")


@bp.post("/clock/advance")
def clock_advance():
    clock.advance(1)
    return jsonify(snapshot())


@bp.post("/clock/reset")
@auth.require("dispatcher")
def clock_reset():
    clock.reset()
    return jsonify(snapshot())
