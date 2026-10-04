"""Zegar demo: zamrożona sobota 13:30, przewijany o godzinę. Przewinięcie rozstrzyga zgłoszenia
na opróżnieniach z harmonogramu, które „wydarzyły się” w przewiniętym czasie."""
import threading
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from . import db, devices, history, photos, residents
from .models import DemoClock, Emptying, FairyReport, StopIssue
from .reports import resolve_reports
from .simulation import DEMO_NOW, FUTURE_HOURS, hour_floor, simulate

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
    """Reset demo, gdy od ostatniej akcji minęło IDLE. Warunkowy UPDATE: przy kilku workerach resetuje tylko jeden.
    Przy okazji retencja z /prywatnosc (IP po 24 h, zdjęcia po 7 dniach) raz na godzinę, nie tylko przy starcie."""
    _retention()
    clock = db.session.get(DemoClock, 1)
    if clock is None or clock.last_activity is None or _wall() - clock.last_activity < IDLE:
        return False
    claimed = (DemoClock.query.filter(DemoClock.id == 1, DemoClock.last_activity == clock.last_activity)
               .update({DemoClock.last_activity: None}, synchronize_session=False))
    db.session.commit()
    from . import rate
    if not claimed or not rate.hit("demo-reset", 1, 20):  # ten sam licznik co ręczny reset (api_pl.RESET_GAP_S)
        return False
    _reset_in_background()
    return True


_resetting = threading.Lock()


def _retention():
    from . import rate
    from .privacy import forget_old_ips
    try:
        if rate.hit("retencja", 1, 3600):
            forget_old_ips()
            photos.cleanup()
    except Exception:  # retencja nie może zepsuć strony startowej
        from flask import current_app
        current_app.logger.exception("Retencja nie powiodła się")
        db.session.rollback()


RESET_LOCK_ID = 4242  # pg_advisory_lock: jeden reset naraz we wszystkich workerach


def _locked_reset():
    """reset() pod blokadą bazy (PostgreSQL): False, gdy inny worker właśnie resetuje. Osobne połączenie, bo reset()
    robi kilka commitów i sesja może zmienić połączenie z puli, a blokada advisory należy do połączenia. SQLite: jeden proces."""
    if db.engine.dialect.name != "postgresql":
        reset()
        return True
    with db.engine.connect() as conn:
        if not conn.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": RESET_LOCK_ID}).scalar():
            return False
        try:
            reset()
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": RESET_LOCK_ID})
    return True


def reset_exclusive():
    """Reset ręczny: False, gdy reset już trwa (w tym procesie albo w innym workerze)."""
    if not _resetting.acquire(blocking=False):
        return False
    try:
        return _locked_reset()
    finally:
        _resetting.release()


def _reset_in_background():
    """Auto-reset w tle: widz nie czeka ~13 s (PostgreSQL) na stronę. Jeden naraz na proces; między workerami
    pilnuje warunkowy UPDATE wyżej. W testach (TESTING) od razu, żeby wynik był deterministyczny."""
    from flask import current_app
    app = current_app._get_current_object()
    if app.config.get("TESTING"):
        reset()
        return
    if not _resetting.acquire(blocking=False):
        return

    def run():
        try:
            with app.app_context():
                try:
                    _locked_reset()
                except Exception:  # bez tego last_activity zostaje None i auto-reset nie wróci aż do kolejnej akcji
                    app.logger.exception("Auto-reset demo nie powiódł się")
                    db.session.rollback()
                    touch()
        finally:
            _resetting.release()

    threading.Thread(target=run, daemon=True).start()


def reset(weeks=8):
    """Odtwarza symulację od zera i cofa zegar do startu scenariusza (kasuje naciśnięcia z demo)."""
    from .state import clear_cache
    clear_cache()
    stats = simulate(weeks=weeks, now=DEMO_NOW)
    from .models import Pickup
    if db.session.query(Pickup.id).first() is None:  # historia nie zależy od akcji z pokazu: reset jej nie odtwarza (szybki auto-reset)
        stats["history"] = history.generate_history(sim_start=hour_floor(DEMO_NOW) - timedelta(weeks=weeks))
    photos.seed_demo(DEMO_NOW)
    residents.seed_demo(DEMO_NOW)
    devices.seed_demo(DEMO_NOW)  # masterdane urządzeń: po Device (residents) i punktach miasta
    db.session.query(FairyReport).delete()  # raporty z poprzedniego przebiegu demo opisywały inne naciśnięcia
    db.session.query(StopIssue).delete()  # problemy zgłoszone z PWA kierowcy w poprzednim przebiegu demo
    clock = db.session.get(DemoClock, 1) or DemoClock(id=1)
    clock.now, clock.last_activity = DEMO_NOW, None  # None = demo w stanie startowym, auto-reset niepotrzebny
    db.session.add(clock)
    db.session.commit()
    return stats
