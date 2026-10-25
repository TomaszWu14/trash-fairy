"""Aktywność gościa demo po wejściu przez bramkę (app/visitor_gate.py): ile ekranów, jak długo, które sekcje.

Liczymy tylko udane (status < 400) GET-y stron HTML od gościa z ważną flagą sesji niosącą id wpisu (podpisane ciasteczko
Flaska, nie da się go podrobić). Bez IP. Sekcja = pierwszy segment ścieżki (`/` → `start`), max 40 znaków, tylko
[a-z0-9_-]; najwyżej 20 sekcji na gościa. Każdy błąd = ostrzeżenie w logu, odpowiedź bez zmian."""
import json
import logging
import re
from datetime import UTC, datetime

from . import db, portfolio_pass, visitor_notify
from .models import DemoVisitor

MAX_SECTIONS = 20
SECTION_RE = re.compile(r"[a-z0-9_-]{1,40}")
SKIP_PREFIXES = ("/api/", "/static/", "/health", "/odwiedzajacy", "/wizytowka")
log = logging.getLogger(__name__)


def section_of(path):
    """Pierwszy segment ścieżki; None, gdy ma znaki spoza [a-z0-9_-]."""
    first = (path or "/").strip("/").split("/", 1)[0][:40]
    if not first:
        return "start"
    return first if SECTION_RE.fullmatch(first) else None


def countable(method, path, response):
    return (method == "GET" and response.status_code < 400 and response.mimetype == "text/html"
            and not path.startswith(SKIP_PREFIXES) and path not in ("/sw.js", "/favicon.ico", "/robots.txt"))


def record(visitor_id, path):
    """page_views += 1 i last_seen_at jednym UPDATE (blokuje wiersz do commitu), potem sekcja +1; push przy progu."""
    now = datetime.now(UTC).replace(tzinfo=None)
    updated = (DemoVisitor.query.filter(DemoVisitor.id == visitor_id)
               .update({DemoVisitor.page_views: DemoVisitor.page_views + 1, DemoVisitor.last_seen_at: now},
                       synchronize_session=False))
    if not updated:  # wpis usunięty (retencja 90 dni)
        db.session.rollback()
        return
    visitor = db.session.get(DemoVisitor, visitor_id, populate_existing=True)
    section = section_of(path)
    if section:
        try:
            counts = json.loads(visitor.sections or "{}")
        except ValueError:
            counts = {}
        counts = counts if isinstance(counts, dict) else {}
        if section in counts or len(counts) < MAX_SECTIONS:
            counts[section] = int(counts.get(section, 0)) + 1
            visitor.sections = json.dumps(counts, ensure_ascii=True, sort_keys=True)
    views, who = visitor.page_views, (visitor.first_name, visitor.last_name, visitor.company)
    db.session.commit()
    threshold = visitor_notify.engaged_threshold()
    if threshold and views == threshold and who[0] != portfolio_pass.GUEST_NAME:  # gość z portfolio: push robi portfolio
        visitor_notify.notify_engaged(*who, views)


def track(visitor_id, path):
    """Wywoływane z after_request bramki, gdy countable() i sesja ma id; None (flaga wygasła) = nic."""
    if visitor_id is None:
        return
    try:
        record(visitor_id, path)
    except Exception as e:  # noqa: BLE001 – licznik nigdy nie psuje odpowiedzi dla gościa
        db.session.rollback()
        log.warning("aktywność gościa: nie zapisano wejścia: %s", e)
