"""Stan punktu — wyłącznie reguły w kodzie (koncepcja, sekcje 6.1–6.2).

stan = max(poziom, sygnał zgłoszenia), gdzie sygnał = 100 × wiarygodność przycisku.
Opróżnienie rozstrzyga zgłoszenia, więc sygnał znika („reset po opróżnieniu”).
"""
from collections import defaultdict
from datetime import timedelta

from sqlalchemy import func

from . import db
from .models import Emptying, Forecast, Press, Report
from .reports import MERGE_WINDOW, low_reliability, reliability
from .simulation import hour_floor

WARN_FROM = 60
BAD_ABOVE = 85
FRESH_BAD_WEIGHT = 0.7  # świeże zgłoszenie z przycisku o takiej wadze = od razu czerwony
WEAK_AFTER_EMPTYING = timedelta(hours=2)
WEAK_BELOW_LEVEL = 30
OVERFLOW_HOURS = 6  # przepełniony tyle godzin bez naciśnięcia → przycisk może nie działać

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


def point_states(now):
    """{point_id: dict ze stanem} dla chwili `now` zegara demo."""
    hour = hour_floor(now)
    levels = dict(db.session.query(Forecast.point_id, Forecast.level).filter_by(source="sim", at=hour).all())

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
    overflow_hours = defaultdict(int)
    for pid, level in (db.session.query(Forecast.point_id, Forecast.level)
                       .filter(Forecast.source == "sim", Forecast.at >= window_start, Forecast.at <= hour)):
        overflow_hours[pid] += level > 100
    pressed_recently = {pid for (pid,) in db.session.query(Press.point_id).distinct()
                        .filter(Press.at >= window_start, Press.at <= now)}

    out = {}
    for pid, level in levels.items():
        rel = reliability([hit for _, hit in resolved[pid]])
        report = open_reports.get(pid)
        signal, weak, fresh = 0.0, False, False
        if report:
            signal, weak = report_signal(report, level, last_emptying.get(pid))
            fresh = now - report.last_at <= MERGE_WINDOW
        value = max(level, signal)
        state = level_state(value, fresh and not weak and report.weight >= FRESH_BAD_WEIGHT)

        check_reason = None
        if low_reliability(resolved[pid], now):
            check_reason = "mało trafnych zgłoszeń w ostatnich 7 dniach"
        elif overflow_hours[pid] == OVERFLOW_HOURS and pid not in pressed_recently:
            check_reason = f"przepełniony od {OVERFLOW_HOURS} h, a nikt nie nacisnął"

        if report and signal >= level:
            reason = (f"zgłoszenie: {report.presses}× naciśnięty, wiarygodność {round(report.weight * 100)}%"
                      + (" (słaby sygnał: tuż po opróżnieniu)" if weak else ""))
        else:
            reason = f"poziom {round(level)}%"

        out[pid] = {
            "level": round(level), "value": round(value), "state": state, **STATES[state],
            "reason": reason, "fresh": fresh, "reliability": round(rel * 100),
            "check_button": check_reason is not None, "check_reason": check_reason,
        }
    return out
