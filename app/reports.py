"""Zgłoszenia z przycisku: scalanie, rozstrzyganie, wiarygodność (koncepcja, sekcja 6.1).

Czyste funkcje (reliability, is_hit, low_reliability) są wspólne dla symulatora i dla żywych naciśnięć.
"""
from datetime import timedelta

from sqlalchemy import select

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
    # wykluczamy zgłoszenia z naciśnięciem „uszkodzony”/„inne” (nie mówią o zapełnieniu); wykluczanie, nie wybór „pełnych”,
    # bo naciśnięcia z symulacji nie mają report_id i wybór zgubiłby całą historię przycisku
    odd = select(Press.report_id).where(Press.report_id.isnot(None), Press.kind.in_(("damaged", "other")))
    rows = (Report.query.filter(Report.point_id == point_id, Report.hit.isnot(None), Report.id.notin_(odd))
            .order_by(Report.first_at.desc()).limit(RELIABILITY_WINDOW).all())
    return reliability([r.hit for r in reversed(rows)])


def record_press(point_id, at, ip=None, wall_at=None, resident_id=None, source="button", kind=None):
    """Zapisuje naciśnięcie i dolicza je do otwartego zgłoszenia z ostatnich 15 min albo tworzy nowe.

    Zarejestrowany mieszkaniec podnosi wagę zgłoszenia do swojej wiarygodności, a dołączając do zgłoszenia
    zaczętego przez kogoś innego — potwierdza je.
    """
    from .residents import resident_reliability  # import lokalny: residents importuje ten moduł
    press = Press(point_id=point_id, at=at, ip=ip, wall_at=wall_at, resident_id=resident_id, source=source, kind=kind)
    report = (Report.query.filter(Report.point_id == point_id, Report.hit.is_(None),
                                  Report.first_at > at - MERGE_WINDOW, Report.first_at <= at)
              .order_by(Report.first_at.desc()).first())
    if report:
        report.presses += 1
        report.last_at = max(report.last_at, at)
        if resident_id and Press.query.filter(Press.report_id == report.id,
                                              (Press.resident_id != resident_id) | Press.resident_id.is_(None)).first():
            report.confirmed = True
    else:
        report = Report(point_id=point_id, first_at=at, last_at=at, presses=1,
                        weight=point_reliability(point_id), confirmed=False)
        db.session.add(report)
        db.session.flush()
    if resident_id:
        report.weight = max(report.weight, resident_reliability(resident_id))
    press.report_id = report.id
    db.session.add(press)
    db.session.commit()
    return report


def resolve_reports(emptying):
    """Opróżnienie rozstrzyga otwarte zgłoszenia punktu: poziom >= 75% → trafne, inaczej fałszywe.
    Trafne zgłoszenia dają punkty zarejestrowanym naciskającym."""
    from .models import Point
    from .residents import award
    kind = db.session.get(Point, emptying.point_id).kind
    open_reports = Report.query.filter(Report.point_id == emptying.point_id, Report.hit.is_(None),
                                       Report.first_at <= emptying.at)
    for r in open_reports:
        r.hit = is_hit(emptying.level)
        r.resolved_at = emptying.at
        award(r, kind)
