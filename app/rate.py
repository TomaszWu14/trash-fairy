"""Limity wspólne dla wszystkich workerów: liczniki w bazie (tabela Counter), okno stałe.

Jedna funkcja dla SMS-ów, wywołań AI, logowania i zgłoszeń z kosza jury, żeby limit nie podwajał się przy 2 workerach.
"""
import time

from sqlalchemy.exc import IntegrityError

from . import db
from .models import Counter


def _window(window_s, now=None):
    now = time.time() if now is None else now
    return int(now // window_s * window_s)


def count(key, window_s):
    row = db.session.get(Counter, (key, _window(window_s)))
    return row.count if row else 0


def hit(key, limit, window_s):
    """Liczy zdarzenie i zwraca True, gdy mieści się w limicie; przy przekroczeniu nic nie liczy i zwraca False."""
    start = _window(window_s)
    for _ in range(2):  # drugi obieg tylko po wyścigu przy wstawianiu pierwszego wiersza okna
        updated = (Counter.query.filter(Counter.key == key, Counter.window_start == start, Counter.count < limit)
                   .update({Counter.count: Counter.count + 1}, synchronize_session=False))
        if updated:
            db.session.commit()
            return True
        if db.session.get(Counter, (key, start)):
            db.session.rollback()
            return False  # okno istnieje i jest pełne
        try:
            Counter.query.filter(Counter.window_start < start - 86400).delete(synchronize_session=False)
            db.session.add(Counter(key=key, window_start=start, count=1))
            db.session.commit()
            return limit >= 1
        except IntegrityError:
            db.session.rollback()
    return False
