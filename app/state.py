"""Stan punktu — wyłącznie reguły w kodzie (koncepcja, sekcje 6.1–6.2).

stan = max(szacunek, sygnał zgłoszenia), gdzie szacunek pochodzi z prognozy (app/forecast.py),
a sygnał = 100 × wiarygodność przycisku. Prawdziwego poziomu z symulacji tu nie czytamy:
system bez czujników go nie zna. Opróżnienie zeruje szacunek i rozstrzyga zgłoszenia.
"""
import copy
from collections import defaultdict
from datetime import timedelta

from sqlalchemy import func

from . import db
from .forecast import point_forecasts
from .geo import distance_m
from .models import Device, Emptying, PhotoAnalysis, Point, Press, Report, StopIssue
from .reports import MERGE_WINDOW, low_reliability, reliability
from .simulation import hour_floor

WARN_FROM = 60
BAD_ABOVE = 85
FRESH_BAD_WEIGHT = 0.7  # świeże zgłoszenie z przycisku o takiej wadze = od razu czerwony
WEAK_AFTER_EMPTYING = timedelta(hours=2)
WEAK_BELOW_LEVEL = 30
OVERFLOW_HOURS = 6  # przepełniony (wg szacunku) tyle godzin bez naciśnięcia → przycisk może nie działać
CREW_ISSUE_WINDOW = timedelta(hours=12)  # zgłoszenie kierowcy z przystanku widać w panelu do opróżnienia, najwyżej 12 h
CREW_ISSUES = {"no_access": "nie da się podjechać", "damaged": "kosz uszkodzony", "blocked": "zablokowany dojazd",
               "overflow": "odpady obok kosza"}
DAMAGE_WINDOW = timedelta(hours=48)  # zgłoszenie „uszkodzony” z /zglos trzyma flagę do opróżnienia, najwyżej 48 h
NEIGHBOR_RADIUS_M = 100
NEIGHBORS_EMPTY_BELOW = 30
NEIGHBORS_FACTOR = 0.7  # pojedyncze zgłoszenie przy pustych sąsiadach waży mniej (spec, pkt 4)
TROLL_WINDOW = timedelta(days=14)
TROLL_MIN_FALSE = 3
TROLL_FACTOR = 0.5  # ≥3 fałszywe zgłoszenia o tej samej porze (±1 h) w 14 dni

# kolor nigdy nie jest jedynym nośnikiem informacji: każdy stan ma też symbol i opis
STATES = {
    "ok": {"symbol": "✓", "label": "w porządku"},
    "warn": {"symbol": "~", "label": "zapełnia się"},
    "bad": {"symbol": "!", "label": "do opróżnienia"},
}


def level_state(value, fresh_strong_report=False):
    if value > BAD_ABOVE or fresh_strong_report:
        return "bad"
    if value >= WARN_FROM:
        return "warn"
    return "ok"


def troll_pattern(resolved, at):
    """Czy ten przycisk ma ≥3 fałszywe zgłoszenia o tej samej godzinie (±1 h) w ostatnich 14 dniach."""
    same_time = [t for t, hit in resolved
                 if hit is False and t > at - TROLL_WINDOW and min(abs(t.hour - at.hour), 24 - abs(t.hour - at.hour)) <= 1]
    return len(same_time) >= TROLL_MIN_FALSE


def neighbors_map():
    points = Point.query.all()
    return {p.id: [q.id for q in points if q.id != p.id and distance_m(p.lat, p.lon, q.lat, q.lon) <= NEIGHBOR_RADIUS_M]
            for p in points}


def effective_weight(report, resolved, neighbor_levels):
    """Waga zgłoszenia po regułach antyspamowych (potwierdzone przez mieszkańca nie są osłabiane)."""
    weight, notes = report.weight, []
    if report.confirmed:
        return weight, ["potwierdzone przez mieszkańca"]
    if neighbor_levels and max(neighbor_levels) < NEIGHBORS_EMPTY_BELOW:
        weight *= NEIGHBORS_FACTOR
        notes.append("sąsiednie kosze puste")
    if troll_pattern(resolved, report.first_at):
        weight *= TROLL_FACTOR
        notes.append("powtarzalne fałszywe zgłoszenia o tej porze")
    return weight, notes


def report_signal(report, level, last_emptying, weight=None):
    """Sygnał zgłoszenia w %; zgłoszenie tuż po opróżnieniu przy niskim poziomie liczy się w połowie."""
    signal = 100 * (report.weight if weight is None else weight)
    weak = (last_emptying is not None and report.first_at - last_emptying < WEAK_AFTER_EMPTYING
            and level < WEAK_BELOW_LEVEL)
    return (signal / 2 if weak else signal), weak


def time_label(at, now):
    if at is None:
        return None
    day = "" if at.date() == now.date() else ("jutro " if at.date() > now.date() else "wczoraj ")
    return f"{day}{at:%H:%M}"


def forecast_reason(f, now):
    text = f"prognoza {round(f['est'])}%"
    crossing = f["crossing"]
    if crossing is None:
        return text + ", bez przekroczenia 85% w 24 h"
    if crossing <= now:
        return text + f", powyżej 85% od ok. {time_label(crossing, now)}"
    span = ""
    if f["early"] and f["late"]:
        span = f" ({time_label(f['early'], now)}–{time_label(f['late'], now)})"
    elif f["early"]:
        span = f" (najwcześniej {time_label(f['early'], now)})"
    return text + f", 85% ok. {time_label(crossing, now)}{span}"


def data_version():
    """Zmienia się przy każdej zmianie danych, od której zależy stan: zgłoszenie, opróżnienie, zdjęcie i jego analiza,
    problem kierowcy, urządzenie, przewinięcie zegara, nowa prognoza pogody. Klucz cache i wersja dla pollingu."""
    from . import clock, weather
    last = [db.session.query(func.max(m.id)).scalar() or 0 for m in (Press, Emptying, PhotoAnalysis, StopIssue)]
    rows = [db.session.query(func.count(m.id)).scalar() for m in (Press, Emptying)]  # SQLite potrafi powtórzyć id po resecie
    analysed = PhotoAnalysis.query.filter(PhotoAnalysis.status != "pending").count()
    dev = db.session.query(func.max(Device.last_heartbeat), func.max(Device.last_selftest)).one()
    w = int(((weather._state.get("data") or {}).get("fetched_at")) or 0)
    devices = "-".join(f"{d:%d%H%M}" if d else "0" for d in dev)
    return f"{clock.now():%Y%m%d%H%M}-" + "-".join(map(str, last + rows + [analysed])) + f"-{devices}-{w}"


_cache = {}


def clear_cache():
    """Po resecie demo i między testami: wersja danych może się powtórzyć na nowej bazie."""
    _cache.clear()


def _cached(name, now, compute):
    """Jeden wynik na proces dla (zegar, wersja danych): 300–600 ms liczymy raz na zmianę danych, nie raz na zapytanie.
    Zwracamy kopię, bo wywołujący dopisują pola (trasy: geometria, poziom przystanku)."""
    key = (name, now, data_version())
    if key not in _cache:
        for k in [k for k in _cache if k[0] == name]:
            del _cache[k]
        _cache[key] = compute()
    return copy.deepcopy(_cache[key])


def point_states(now):
    """{point_id: dict ze stanem} dla chwili `now` zegara demo (z cache po wersji danych)."""
    return _cached("states", now, lambda: _point_states(now))


def current_routes(now):
    """Trasy na najbliższe kursy obu flot (z cache po wersji danych)."""
    from .routes import plan_routes
    return _cached("routes", now, lambda: plan_routes(now, point_states(now)))


def _point_states(now):
    """{point_id: dict ze stanem} dla chwili `now` zegara demo."""
    hour = hour_floor(now)

    open_reports = {}
    for r in Report.query.filter(Report.hit.is_(None), Report.first_at <= now).order_by(Report.first_at):
        open_reports[r.point_id] = r  # najnowsze otwarte

    resolved = defaultdict(list)
    for pid, at, hit in (db.session.query(Report.point_id, Report.first_at, Report.hit)
                         .filter(Report.hit.isnot(None), Report.first_at <= now).order_by(Report.first_at)):
        resolved[pid].append((at, hit))

    last_emptying = dict(db.session.query(Emptying.point_id, func.max(Emptying.at))
                         .filter(Emptying.at <= now).group_by(Emptying.point_id).all())

    window_start = hour - timedelta(hours=OVERFLOW_HOURS - 1)
    pressed_recently = {pid for (pid,) in db.session.query(Press.point_id).distinct()
                        .filter(Press.at >= window_start, Press.at <= now)}

    from .residents import device_flags  # import lokalny: residents importuje reports → bez cykli przy starcie
    forecasts = point_forecasts(now, last_emptying)
    neighbors = neighbors_map()
    offline = device_flags(now)
    # zgłoszenia z ekranu /zglos: „uszkodzony” nie podnosi poziomu (flaga dla ekipy), „odpady obok” to notatka przy zgłoszeniu
    damaged = {pid: at for pid, at in db.session.query(Press.point_id, func.max(Press.at))
               .filter(Press.kind == "damaged", Press.at > now - DAMAGE_WINDOW, Press.at <= now).group_by(Press.point_id)
               if last_emptying.get(pid) is None or last_emptying[pid] < at}
    overflow_reported = {pid for (pid,) in db.session.query(Press.point_id).distinct()
                         .filter(Press.kind == "overflow", Press.at > now - MERGE_WINDOW, Press.at <= now)}
    crew_issue = {}
    for i in StopIssue.query.filter(StopIssue.at > now - CREW_ISSUE_WINDOW, StopIssue.at <= now).order_by(StopIssue.at):
        if last_emptying.get(i.point_id) is None or last_emptying[i.point_id] < i.at:
            crew_issue[i.point_id] = {"kind": i.kind, "label": CREW_ISSUES[i.kind], "at": i.at.isoformat(), "note": i.note}
    out = {}
    for pid, f in forecasts.items():
        level = f["est"]
        report = open_reports.get(pid)
        signal, weak, fresh, weight, notes = 0.0, False, False, 0.0, []
        if report:
            weight, notes = effective_weight(report, resolved[pid], [forecasts[n]["est"] for n in neighbors.get(pid, [])])
            signal, weak = report_signal(report, level, last_emptying.get(pid), weight)
            fresh = now - report.last_at <= MERGE_WINDOW
        value = max(level, signal)
        state = level_state(value, fresh and not weak and weight >= FRESH_BAD_WEIGHT)

        check_reason = offline.get(pid)
        overflow_hours = sum(v is not None and v > 100 for v in f["recent"])
        if check_reason:
            pass
        elif low_reliability(resolved[pid], now):
            check_reason = "mało trafnych zgłoszeń w ostatnich 7 dniach"
        elif overflow_hours == OVERFLOW_HOURS and pid not in pressed_recently:
            check_reason = f"wg prognozy przepełniony od {OVERFLOW_HOURS} h, a nikt nie nacisnął"

        if report and signal >= level:
            reason = (f"zgłoszenie: {report.presses}× naciśnięty, waga {round(weight * 100)}%"
                      + (" (słaby sygnał: tuż po opróżnieniu)" if weak else "")
                      + (f" ({', '.join(notes)})" if notes else ""))
        else:
            reason = forecast_reason(f, now)

        out[pid] = {
            "level": round(level), "value": round(value), "state": state, **STATES[state],
            "reason": reason, "fresh": fresh, "reliability": round(reliability([h for _, h in resolved[pid]]) * 100),
            "check_button": check_reason is not None, "check_reason": check_reason,
            "damaged_at": damaged[pid].isoformat() if pid in damaged else None,
            "overflow_reported": pid in overflow_reported,
            "crew_issue": crew_issue.get(pid),
            "crossing": f["crossing"].isoformat() if f["crossing"] else None,
            "crossing_label": time_label(f["crossing"], now),
        }
    return out
