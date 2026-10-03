"""Zegar demo: zamrożona sobota 13:30, przewijany o godzinę. Przewinięcie rozstrzyga zgłoszenia
na opróżnieniach z harmonogramu, które „wydarzyły się” w przewiniętym czasie."""
from datetime import timedelta

from . import db
from .models import DemoClock, Emptying
from .reports import resolve_reports
from .simulation import DEMO_NOW, FUTURE_HOURS, simulate

MAX_NOW = DEMO_NOW + timedelta(hours=FUTURE_HOURS - 1)  # dalej symulacja nie sięga


def now():
    clock = db.session.get(DemoClock, 1)
    return clock.now if clock else DEMO_NOW


def advance(hours=1):
    clock = db.session.get(DemoClock, 1) or DemoClock(id=1, now=DEMO_NOW)
    new = min(clock.now + timedelta(hours=hours), MAX_NOW)
    for e in Emptying.query.filter(Emptying.at > clock.now, Emptying.at <= new).order_by(Emptying.at):
        resolve_reports(e)
    clock.now = new
    db.session.add(clock)
    db.session.commit()
    return new


def reset(weeks=8):
    """Odtwarza symulację od zera i cofa zegar do startu scenariusza (kasuje naciśnięcia z demo)."""
    stats = simulate(weeks=weeks, now=DEMO_NOW)
    clock = db.session.get(DemoClock, 1) or DemoClock(id=1)
    clock.now = DEMO_NOW
    db.session.add(clock)
    db.session.commit()
    return stats
