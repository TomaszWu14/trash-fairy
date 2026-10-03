"""Stan punktu — wyłącznie reguły w kodzie (koncepcja, sekcje 6.1–6.2).

stan = max(szacunek, sygnał zgłoszenia), gdzie szacunek pochodzi z prognozy (app/forecast.py),
a sygnał = 100 × wiarygodność przycisku. Prawdziwego poziomu z symulacji tu nie czytamy:
system bez czujników go nie zna. Opróżnienie zeruje szacunek i rozstrzyga zgłoszenia.
"""
from collections import defaultdict
from datetime import timedelta

from sqlalchemy import func

from . import db
from .forecast import point_forecasts
from .models import Emptying, Press, Report
from .reports import MERGE_WINDOW, low_reliability, reliability
from .simulation import hour_floor

WARN_FROM = 60
BAD_ABOVE = 85
FRESH_BAD_WEIGHT = 0.7  # świeże zgłoszenie z przycisku o takiej wadze = od razu czerwony
WEAK_AFTER_EMPTYING = timedelta(hours=2)
WEAK_BELOW_LEVEL = 30
OVERFLOW_HOURS = 6  # przepełniony (wg szacunku) tyle godzin bez naciśnięcia → przycisk może nie działać

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


def report_signal(report, level, last_emptying):
    """Sygnał zgłoszenia w %; zgłoszenie tuż po opróżnieniu przy niskim poziomie liczy się w połowie."""
    signal = 100 * report.weight
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


def point_states(now):
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

    out = {}
    for pid, f in point_forecasts(now, last_emptying).items():
        level = f["est"]
        report = open_reports.get(pid)
        signal, weak, fresh = 0.0, False, False
        if report:
            signal, weak = report_signal(report, level, last_emptying.get(pid))
            fresh = now - report.last_at <= MERGE_WINDOW
        value = max(level, signal)
        state = level_state(value, fresh and not weak and report.weight >= FRESH_BAD_WEIGHT)

        check_reason = None
        overflow_hours = sum(v is not None and v > 100 for v in f["recent"])
        if low_reliability(resolved[pid], now):
            check_reason = "mało trafnych zgłoszeń w ostatnich 7 dniach"
        elif overflow_hours == OVERFLOW_HOURS and pid not in pressed_recently:
            check_reason = f"wg prognozy przepełniony od {OVERFLOW_HOURS} h, a nikt nie nacisnął"

        if report and signal >= level:
            reason = (f"zgłoszenie: {report.presses}× naciśnięty, wiarygodność {round(report.weight * 100)}%"
                      + (" (słaby sygnał: tuż po opróżnieniu)" if weak else ""))
        else:
            reason = forecast_reason(f, now)

        out[pid] = {
            "level": round(level), "value": round(value), "state": state, **STATES[state],
            "reason": reason, "fresh": fresh, "reliability": round(reliability([h for _, h in resolved[pid]]) * 100),
            "check_button": check_reason is not None, "check_reason": check_reason,
            "crossing": f["crossing"].isoformat() if f["crossing"] else None,
            "crossing_label": time_label(f["crossing"], now),
        }
    return out
