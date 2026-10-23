"""Bramka przed wersją demonstracyjną: grzeczne, obowiązkowe przedstawienie się (miękka kontrola odwiedzin portfolio).

Dotyczy tylko stron HTML (GET) oglądanych w przeglądarce. Nie blokuje /api/*, plików statycznych (w tym PWA i service
workera), /health, urządzeń IoT (przycisk, e-papier) ani kodów QR przy koszu. Ciasteczko sesji 30 dni; w bazie imię,
nazwisko i firma bez IP i user-agenta, 90 dni; o każdym wpisie push ntfy (app/visitor_notify.py). Lista dla właściciela: /odwiedzajacy z tokenem VISITORS_TOKEN."""
import csv
import hmac
import io
import os
import time
import unicodedata
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

from flask import Blueprint, Response, abort, current_app, redirect, render_template, request, session

from . import db, rate, visitor_notify
from .models import DemoVisitor

bp = Blueprint("visitor_gate", __name__)

RETENTION = timedelta(days=90)
SESSION_TTL_S = 30 * 24 * 3600
FLAG = "demo_visitor_ok"  # moment wpisu (sekundy epoki) – ważny SESSION_TTL_S
POSTS_PER_HOUR = 300  # globalny limit zapisów (bez IP w bazie), żeby nikt nie zapchał tabeli
# przedrostki ścieżek, których bramka nie dotyka: API, statyki/PWA, zdrowie, urządzenia, QR, strony o prywatności
EXEMPT_PREFIXES = ("/api/", "/static/", "/health", "/epapier/", "/przycisk/", "/kosz/", "/prywatnosc", "/dostepnosc",
                   "/odwiedzajacy", "/wizytowka")
_FALSE = {"", "0", "false", "off", "no", "nie"}


def enabled():
    # domyślnie włączona; w testach (TESTING) wyłączona, dopóki test sam nie ustawi config["DEMO_VISITOR_GATE"]
    value = current_app.config.get("DEMO_VISITOR_GATE", "0" if current_app.testing else os.environ.get("DEMO_VISITOR_GATE", "1"))
    return str(value).strip().lower() not in _FALSE


def clean(value):
    """Przycięte, pojedyncze spacje, 2–100 znaków, bez znaków sterujących; None gdy niepoprawne."""
    text = " ".join((value or "").split())
    if not 2 <= len(text) <= 100 or any(unicodedata.category(ch).startswith("C") for ch in text):
        return None
    return text


def safe_next(target):
    """Tylko ścieżka względna tej samej strony (bez //host, schematu, backslasha, znaków sterujących)."""
    target = target or "/"
    parts = urlsplit(target)
    if (not target.startswith("/") or target.startswith("//") or "\\" in target or parts.scheme or parts.netloc
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in target)):
        return "/"
    return target


def _passed():
    stamp = session.get(FLAG)
    return isinstance(stamp, int) and 0 <= time.time() - stamp < SESSION_TTL_S


def _render(next_url, errors=None, values=None, status=200):
    resp = render_template("ui/wizytowka.html", next_url=next_url, errors=errors or {}, values=values or {})
    return Response(resp, status=status, headers={"Cache-Control": "no-store"})


@bp.before_app_request
def gate():
    if request.method not in ("GET", "HEAD") or request.endpoint is None or not enabled() or _passed():
        return None
    if request.path.startswith(EXEMPT_PREFIXES) or request.path in ("/sw.js", "/favicon.ico", "/robots.txt"):
        return None
    return _render(request.full_path.rstrip("?"))


@bp.post("/wizytowka")
def submit():
    next_url = safe_next(request.form.get("next"))
    if request.form.get("website"):  # pułapka na boty: człowiek tego pola nie widzi
        abort(400)
    values = {k: " ".join(request.form.get(k, "").split()) for k in ("first_name", "last_name", "company")}
    labels = {"first_name": "imię", "last_name": "nazwisko", "company": "firmę"}
    errors = {k: f"Podaj {labels[k]} (2–100 znaków, bez znaków sterujących)." for k in values if clean(values[k]) is None}
    if not request.form.get("consent"):
        errors["consent"] = "Potwierdź, że zapoznajesz się z informacją o danych osobowych."
    if errors:
        return _render(next_url, errors, values, 400)
    if not rate.hit("visitor-gate", POSTS_PER_HOUR, 3600):
        return _render(next_url, {"form": "Zbyt wiele prób. Spróbuj za chwilę."}, values, 429)
    now = datetime.now(UTC).replace(tzinfo=None)
    DemoVisitor.query.filter(DemoVisitor.created_at < now - RETENTION).delete(synchronize_session=False)
    visitor = DemoVisitor(created_at=now, **{k: clean(v) for k, v in values.items()})
    db.session.add(visitor)
    db.session.commit()
    visitor_notify.notify(visitor.first_name, visitor.last_name, visitor.company)
    session[FLAG], session.permanent = int(time.time()), True
    return redirect(next_url, 303)


def _cell(value):
    """Ochrona przed wstrzyknięciem formuły w Excelu/Sheets (CSV injection)."""
    value = str(value)
    return "'" + value if value[:1] in ("=", "+", "-", "@", "\t", "\r") else value


@bp.get("/odwiedzajacy")
def visitors():
    """Lista dla właściciela. Bez VISITORS_TOKEN w env: 404 (endpoint nie istnieje). Token w nagłówku X-Visitors-Token
    albo ?token=; ?format=csv daje CSV."""
    expected = current_app.config.get("VISITORS_TOKEN", os.environ.get("VISITORS_TOKEN", ""))
    if not expected:
        abort(404)
    given = request.headers.get("X-Visitors-Token") or request.args.get("token", "")
    if not hmac.compare_digest(given.encode(), expected.encode()):
        abort(404)
    cutoff = datetime.now(UTC).replace(tzinfo=None) - RETENTION
    rows = DemoVisitor.query.filter(DemoVisitor.created_at >= cutoff).order_by(DemoVisitor.created_at.desc()).all()
    headers = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex"}
    if request.args.get("format") == "csv":
        buf = io.StringIO()
        out = csv.writer(buf)
        out.writerow(["data_utc", "imie", "nazwisko", "firma"])
        for r in rows:
            out.writerow([r.created_at.isoformat(sep=" ", timespec="seconds"), _cell(r.first_name), _cell(r.last_name),
                          _cell(r.company)])
        return Response(buf.getvalue(), mimetype="text/csv", headers={**headers, "Content-Disposition":
                                                                        'attachment; filename="odwiedzajacy.csv"'})
    return Response(render_template("ui/odwiedzajacy.html", rows=rows), headers=headers)
