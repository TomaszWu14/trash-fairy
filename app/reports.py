"""Zgłoszenia z przycisku: scalanie, rozstrzyganie, wiarygodność (koncepcja, sekcja 6.1).

Czyste funkcje (reliability, is_hit, low_reliability) są wspólne dla symulatora i dla żywych naciśnięć.
"""
from datetime import timedelta

from . import db
from .models import Press, Report

MERGE_WINDOW = timedelta(minutes=15)  # liczone od pierwszego naciśnięcia, więc spam nie przedłuża okna
HIT_LEVEL = 75
DEFAULT_RELIABILITY = 0.7
RELIABILITY_WINDOW = 10
FLAG_BELOW = 0.4
FLAG_DAYS = 7
FLAG_MIN_REPORTS = 3


def reliability(outcomes):
    """Odsetek trafnych wśród ostatnich 10 rozstrzygniętych zgłoszeń (outcomes: od najstarszego)."""
    last = outcomes[-RELIABILITY_WINDOW:]
    return sum(last) / len(last) if last else DEFAULT_RELIABILITY


def is_hit(level):
    return level >= HIT_LEVEL


def low_reliability(resolved, now):
    """Flaga „sprawdź przycisk”: < 40% trafnych wśród zgłoszeń z 7 dni (min. 3 zgłoszenia).

    resolved: [(first_at, hit), ...]
    """
    recent = [hit for at, hit in resolved if at > now - timedelta(days=FLAG_DAYS)]
    return len(recent) >= FLAG_MIN_REPORTS and sum(recent) / len(recent) < FLAG_BELOW


def point_reliability(point_id):
    rows = (Report.query.filter(Report.point_id == point_id, Report.hit.isnot(None))
            .order_by(Report.first_at.desc()).limit(RELIABILITY_WINDOW).all())
    return reliability([r.hit for r in reversed(rows)])


def record_press(point_id, at, ip=None, wall_at=None):
    """Zapisuje naciśnięcie i dolicza je do otwartego zgłoszenia z ostatnich 15 min albo tworzy nowe."""
    db.session.add(Press(point_id=point_id, at=at, ip=ip, wall_at=wall_at))
    report = (Report.query.filter(Report.point_id == point_id, Report.hit.is_(None),
                                  Report.first_at > at - MERGE_WINDOW, Report.first_at <= at)
              .order_by(Report.first_at.desc()).first())
    if report:
        report.presses += 1
        report.last_at = max(report.last_at, at)
    else:
        report = Report(point_id=point_id, first_at=at, last_at=at, presses=1,
                        weight=point_reliability(point_id))
        db.session.add(report)
    db.session.commit()
    return report


def resolve_reports(emptying):
    """Opróżnienie rozstrzyga otwarte zgłoszenia punktu: poziom >= 75% → trafne, inaczej fałszywe."""
    open_reports = Report.query.filter(Report.point_id == emptying.point_id, Report.hit.is_(None),
                                       Report.first_at <= emptying.at)
    for r in open_reports:
        r.hit = is_hit(emptying.level)
        r.resolved_at = emptying.at
