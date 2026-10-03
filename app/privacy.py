"""Retencja danych (decyzja 32): IP zgłoszenia potrzebne jest tylko do limitu na godzinę, więc po 24 h je usuwamy.

Wołane przy starcie aplikacji i z komendy `flask cleanup-photos`, żeby nie zależeć od crona w Coolify."""
from datetime import UTC, datetime, timedelta

from . import db
from .models import Press

IP_RETENTION = timedelta(hours=24)


def forget_old_ips(now=None):
    now = now or datetime.now(UTC).replace(tzinfo=None)
    n = (Press.query.filter(Press.ip.isnot(None), Press.wall_at < now - IP_RETENTION)
         .update({Press.ip: None}, synchronize_session=False))
    db.session.commit()
    return n
