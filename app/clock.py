"""Zegar demo: zamrożona sobota 13:30, przewijany o godzinę. Przewinięcie rozstrzyga zgłoszenia
na opróżnieniach z harmonogramu, które „wydarzyły się” w przewiniętym czasie."""
from datetime import UTC, datetime, timedelta

from . import db, photos, residents
from .models import DemoClock, Emptying, FairyReport, StopIssue
from .reports import resolve_reports
from .simulation import DEMO_NOW, FUTURE_HOURS, simulate

MAX_NOW = DEMO_NOW + timedelta(hours=FUTURE_HOURS - 1)  # dalej symulacja nie sięga
IDLE = timedelta(minutes=30)  # po tylu minutach bez akcji kolejny widz zaczyna pokaz od 13:30 (decyzja 39)


def now():
    clock = db.session.get(DemoClock, 1)
    return clock.now if clock else DEMO_NOW


def advance(hours=1):
    clock = db.session.get(DemoClock, 1) or DemoClock(id=1, now=DEMO_NOW)
    new = min(clock.now + timedelta(hours=hours), MAX_NOW)
    for e in Emptying.query.filter(Emptying.at > clock.now, Emptying.at <= new).order_by(Emptying.at):
        resolve_reports(e)
    clock.now = new
    clock.last_activity = _wall()
    db.session.add(clock)
    db.session.commit()
    return new


def _wall():
    return datetime.now(UTC).replace(tzinfo=None)


def touch():
    """Akcja w demo (zgłoszenie, opróżnienie, problem): przesuwa start odliczania do auto-resetu."""
    clock = db.session.get(DemoClock, 1)
    if clock:
        clock.last_activity = _wall()
        db.session.commit()


def maybe_auto_reset():
    """Reset demo, gdy od ostatniej akcji minęło IDLE. Warunkowy UPDATE: przy kilku workerach resetuje tylko jeden."""
    clock = db.session.get(DemoClock, 1)
    if clock is None or clock.last_activity is None or _wall() - clock.last_activity < IDLE:
        return False
    claimed = (DemoClock.query.filter(DemoClock.id == 1, DemoClock.last_activity == clock.last_activity)
               .update({DemoClock.last_activity: None}, synchronize_session=False))
    db.session.commit()
    if not claimed:
        return False
    reset()
    return True


def reset(weeks=8):
    """Odtwarza symulację od zera i cofa zegar do startu scenariusza (kasuje naciśnięcia z demo)."""
    from .state import clear_cache
    clear_cache()
    stats = simulate(weeks=weeks, now=DEMO_NOW)
    photos.seed_demo(DEMO_NOW)
    residents.seed_demo(DEMO_NOW)
    db.session.query(FairyReport).delete()  # raporty z poprzedniego przebiegu demo opisywały inne naciśnięcia
    db.session.query(StopIssue).delete()  # problemy zgłoszone z PWA kierowcy w poprzednim przebiegu demo
    clock = db.session.get(DemoClock, 1) or DemoClock(id=1)
    clock.now, clock.last_activity = DEMO_NOW, None  # None = demo w stanie startowym, auto-reset niepotrzebny
    db.session.add(clock)
    db.session.commit()
    return stats
