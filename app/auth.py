"""Role na pokaz (docs/PRZEGLAD.md, decyzje 1–8): publiczna, dyspozytor, kierowca floty.

Uproszczenie świadome: trzy loginy ze wspólnym hasłem demo z env (DEMO_PASSWORD), sesja w ciasteczku na 12 h.
Bez hasła w env logowanie jest wyłączone (wszystko, co wymaga roli, zwraca 401).
ponytail: wspólne hasło i brak kont osobowych — konta, grafik i numery pojazdów w ROADMAPA.md.
"""
import hmac
from datetime import timedelta
from functools import wraps

from flask import has_request_context, jsonify, redirect, request, session, url_for

from . import http, rate

SESSION_HOURS = 12
LOGIN_FAILS, LOGIN_WINDOW_S = 5, 900
USERS = {  # login → (rola, flota kierowcy)
    "dyspozytor": ("dispatcher", None),
    "driver_bin": ("driver", "bin"),
    "driver_altana": ("driver", "shelter"),
}
FLEET_LABEL = {"bin": "kosze uliczne", "shelter": "altany"}


def role():
    """Rola z sesji; poza żądaniem HTTP (wątek analizy, testy wywołujące funkcje wprost) nikt nie jest zalogowany."""
    return session.get("role") if has_request_context() else None


def fleet():
    return session.get("fleet") if has_request_context() else None


def user():
    """Dla szablonów: kto jest zalogowany (albo None)."""
    login = session.get("login") if has_request_context() else None
    return {"login": login, "role": role(), "fleet": fleet()} if login else None


def is_dispatcher():
    return role() == "dispatcher"


def login(name, password, ip):
    """None, gdy się udało; inaczej komunikat do pokazania."""
    secret = http.config("DEMO_PASSWORD")
    if not secret:
        return "Logowanie jest wyłączone: brak hasła demo w konfiguracji serwera."
    key = f"login-fail:{ip}"
    if rate.count(key, LOGIN_WINDOW_S) >= LOGIN_FAILS:
        return "Za dużo nieudanych prób. Spróbuj ponownie za 15 minut."
    name = (name or "").strip().lower()
    if name not in USERS or not hmac.compare_digest((password or "").encode(), secret.encode()):
        rate.hit(key, LOGIN_FAILS, LOGIN_WINDOW_S)
        return "Nieprawidłowy login lub hasło."
    session.clear()
    session.permanent = True
    session["login"] = name
    session["role"], session["fleet"] = USERS[name]
    return None


def logout():
    for k in ("login", "role", "fleet"):
        session.pop(k, None)


def home_for_role():
    return url_for("main.driver") if role() == "driver" else url_for("main.panel")


def require(*roles):
    """Dekorator: tylko podane role. API dostaje 401 (brak sesji) albo 403 (zła rola), strona przekierowanie na logowanie."""
    def deco(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if role() in roles:
                return view(*args, **kwargs)
            if request.path.startswith("/api/"):
                status = 403 if role() else 401
                return jsonify(ok=False, login_required=status == 401,
                               message="Zaloguj się, żeby to zrobić." if status == 401
                               else "To działanie jest dostępne dla innej roli."), status
            return redirect(url_for("main.login", next=request.full_path.rstrip("?")))
        return wrapper
    return deco


def can_touch(point):
    """Kierowca zapisuje tylko punkty swojej floty (kosze albo altany); dyspozytor wszystkie.

    Floty, a nie bieżącego planu: po opróżnieniu planer liczy trasę od nowa i punkt z niej wypada, a zapis z kolejki
    offline czy „Cofnij” musi nadal przejść."""
    return is_dispatcher() or (role() == "driver" and point.kind == fleet())


def init_app(app):
    app.permanent_session_lifetime = timedelta(hours=SESSION_HOURS)
    app.context_processor(lambda: {"user": user(), "is_dispatcher": is_dispatcher()})
