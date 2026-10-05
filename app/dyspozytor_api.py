"""Panel dyspozytora (/dyspozytor): kafle, pilne kosze, ekipy i trasy, zgłoszenia na żywo oraz „Dodaj do kursu”.

Liczby biorą się z tych samych reguł co reszta aplikacji (state.py, routes.py, comparison.py), nic nie liczymy od nowa.
„Dodaj do kursu” to decyzja człowieka: wpis StopIssue „dyspozytor” (cofnięcie: „dysp_cofnij”), nie zgłoszenie mieszkańca,
więc nie zmienia statystyk zgłoszeń, wiarygodności przycisku ani punktów mieszkańców. Trasa (routes.plan_routes)
stawia dodany kosz na początku najbliższego kursu jego floty.
"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify

from . import clock, db, osrm
from .api_pl import KIND_LABEL, _address, _done_ids, _json_body, _point, blad, meta, numer
from .comparison import compare
from .models import Point, Press, Report, StopIssue
from .routes import DEPOT, DISPATCH, DISPATCH_UNDO, dispatched_ids
from .simulation import DEMO_NOW
from .state import BAD_ABOVE, current_routes, point_states, time_label

bp = Blueprint("dyspozytor", __name__, url_prefix="/api/dyspozytor")
FULL_FROM = 80  # „przepełnione” = poziom ≥ 80%, jak kształt ■ na mapach i w legendzie
URGENT_LIMIT = 12
LIVE_HOURS = 24
LIVE_LIMIT = 12
SOURCE = {"qr": "kod QR z panelu", "button": "przycisk na panelu kosza"}


def _fleets(now):
    return {f["kind"]: f for f in current_routes(now)}


def _urgent(now, states, fleets, added):
    """Kosze do decyzji przed najbliższym kursem swojej floty: stan „do opróżnienia” teraz (także po świeżym zgłoszeniu
    mieszkańca) albo prognoza przekroczenia 85% przed kursem. Najpierw te, które już są ponad progiem."""
    points = {p.id: p for p in Point.live_query()}
    out = []
    for pid, s in states.items():
        crossing = datetime.fromisoformat(s["crossing"]) if s.get("crossing") else None
        p, fleet = points.get(pid), fleets.get(points[pid].kind) if pid in points else None
        if p is None or fleet is None:
            continue
        bad = s["state"] == "bad"
        if not bad and (crossing is None or crossing > datetime.fromisoformat(fleet["run_at"])):
            continue
        stops = [st for r in [fleet, *fleet["extra_routes"]] for st in r["stops"]]
        pos = next((i for i, st in enumerate(stops, 1) if st["id"] == pid), None)
        juz = bad or s["value"] > BAD_ABOVE or (crossing is not None and crossing <= now)
        out.append({"id": pid, "nazwa": p.name, "adres": _address(p), "rodzaj": p.kind, "poziom": round(s["value"]),
                    "lat": p.lat, "lon": p.lon, "prog_o": crossing.isoformat() if crossing else None,
                    "prog": time_label(crossing, now) if crossing else None, "juz": juz,
                    "za_min": max(0, round((crossing - now).total_seconds() / 60)) if crossing else 0,
                    "powod": s["reason"], "priorytet": "krytyczne" if juz else "wysokie",
                    "kurs": time_label(datetime.fromisoformat(fleet["run_at"]), now), "kurs_o": fleet["run_at"],
                    "na_kursie": pos is not None, "pozycja": pos, "punktow": len(stops), "dodany": pid in added})
    out.sort(key=lambda k: (not k["juz"], k["prog_o"] or "", k["id"]))
    return out


def _live_reports(now):
    """Ostatnie zgłoszenia mieszkańców przy koszach (24 h zegara demo), najnowsze pierwsze."""
    rows = (db.session.query(Report, Point).join(Point, Point.id == Report.point_id)
            .filter(Point.live.is_(True), Report.first_at <= now, Report.first_at > now - timedelta(hours=LIVE_HOURS))
            .order_by(Report.first_at.desc(), Report.id.desc()).limit(LIVE_LIMIT).all())
    out = []
    for r, p in rows:
        first = Press.query.filter(Press.report_id == r.id).order_by(Press.at, Press.id).first()
        kind = first.kind if first else None  # None = przycisk „pełny” na panelu kosza (symulacja, seed)
        out.append({"numer": numer(r.id), "kosz_id": p.id, "nazwa": p.name, "o": r.first_at.isoformat(), "osob": r.presses,
                    "typ": KIND_LABEL.get(kind, "Zgłoszenie") if kind else "Przepełniony",
                    "zrodlo": SOURCE.get(first.source) if first and first.wall_at else SOURCE["button"],
                    "zamkniete": r.hit is not None})
    return out


@bp.get("")
def overview():
    now = clock.now()
    states, fleets = point_states(now), _fleets(now)
    added = dispatched_ids(now)
    urgent = _urgent(now, states, fleets, added)
    bins = fleets["bin"]
    cmp_ = compare(DEMO_NOW)
    fixed, fairy = cmp_["fixed"]["total"]["visits"], cmp_["fairy"]["total"]["visits"]
    floty = []
    for kind, f in fleets.items():
        done = _done_ids(kind)
        ids = {s["id"] for r in [f, *f["extra_routes"]] for s in r["stops"]}
        line, approx = osrm.street_path(f["path"][:-1])
        floty.append({"rodzaj": kind, "etykieta": f["label"], "pojazd": f["vehicle"], "kurs_o": f["run_at"],
                      "kurs": time_label(datetime.fromisoformat(f["run_at"]), now), "punkty": len(ids), "km": f["km"],
                      "pojazdy": f["vehicles"], "zrobione": len(done), "wszystkie": len(ids | done),
                      "linia": line, "przyblizona": approx})
    return jsonify(
        kafle={"pilne": len(urgent), "juz": sum(1 for k in urgent if k["juz"]), "zagrozone": sum(1 for k in urgent if not k["juz"]),
               "przepelnione": sum(1 for s in states.values() if (s.get("value") or 0) >= FULL_FROM),
               "km": bins["km"], "kurs": time_label(datetime.fromisoformat(bins["run_at"]), now),
               "punkty": sum(len(r["stops"]) for r in [bins, *bins["extra_routes"]]),
               "odbiory_mniej_pct": round(100 * (fixed - fairy) / fixed) if fixed else 0, "tygodnie": cmp_["weeks"]},
        pilne=urgent[:URGENT_LIMIT], pilne_liczba=len(urgent), floty=floty, zgloszenia=_live_reports(now),
        dodane=sorted(added), baza=DEPOT, meta=meta())


@bp.get("/dodane")
def added_view():
    """Kosze dodane przez dyspozytora (lista kierowcy stawia je na górze)."""
    return jsonify(dodane=sorted(dispatched_ids(clock.now())), meta=meta())


def _change(kind):
    data = _json_body()
    raw = data.get("kosz")
    if isinstance(raw, bool) or not isinstance(raw, (int, str)) or not str(raw).strip().isdigit():
        return blad("Podaj numer kosza.", "zly_kosz")
    p = _point(raw)
    if p is None:
        return blad("Nie ma takiego kosza.", "kosz_nie_istnieje", 404)
    now = clock.now()
    fleet = _fleets(now)[p.kind]
    run = time_label(datetime.fromisoformat(fleet["run_at"]), now)
    is_added = p.id in dispatched_ids(now)
    if is_added != (kind == DISPATCH):  # idempotentne: drugi klik niczego nie dopisuje
        db.session.add(StopIssue(point_id=p.id, at=now, kind=kind))
        db.session.commit()
        clock.touch()
        status = 201
    else:
        status = 200
    msg = (f"{p.name}: dodany do kursu {run}, pierwszy na liście kierowcy." if kind == DISPATCH
           else f"{p.name}: cofnięto dodanie do kursu {run}.")
    return jsonify(ok=True, komunikat=msg, kosz=p.id, dodany=kind == DISPATCH, kurs=run, meta=meta()), status


@bp.post("/dodaj")
def add():
    """Dyspozytor dodaje kosz do najbliższego kursu jego floty (decyzja człowieka). Body: {"kosz": 18}."""
    return _change(DISPATCH)


@bp.post("/cofnij")
def undo():
    """Cofnięcie „Dodaj do kursu” (wpis „dysp_cofnij”, historia decyzji zostaje)."""
    return _change(DISPATCH_UNDO)
