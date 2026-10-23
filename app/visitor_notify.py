"""Powiadomienie push (ntfy) właściciela o nowym gościu demo, po udanym zapisie w bramce (app/visitor_gate.py).

Bez `NTFY_URL` (pełny URL tematu, np. https://ntfy.sh/<tajny-temat>) nic się nie dzieje: zero ruchu sieciowego, także w
testach (conftest zeruje zmienną). Opcjonalny `NTFY_TOKEN` → `Authorization: Bearer`. Wysyłka w wątku w tle (gość nie
czeka); każdy błąd to tylko ostrzeżenie w logu. W testach (TESTING) wysyłamy od razu, żeby wynik był deterministyczny."""
import logging
import threading
import urllib.request

from flask import current_app

from . import http

APP = "Trash Fairy"
TIMEOUT_S = 5
MAX_BODY = 300
log = logging.getLogger(__name__)


def message(first_name, last_name, company):
    return f"{first_name} {last_name} ({company}) wszedł do {APP}"[:MAX_BODY]


def request_for(url, token, body):
    # nagłówki tylko ASCII (polskie znaki idą w treści UTF-8)
    headers = {"User-Agent": http.USER_AGENT, "Content-Type": "text/plain; charset=utf-8",
               "Title": f"Nowy gosc: {APP}", "Tags": "bell", "Priority": "high"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, data=body.encode("utf-8"), headers=headers, method="POST")


def send(req):
    try:
        # schemat (tylko http/https) sprawdza notify()
        with http.opener.open(req, timeout=TIMEOUT_S) as r:  # nosec B310
            r.read()
    except Exception as e:  # noqa: BLE001 – powiadomienie nigdy nie psuje odpowiedzi dla gościa
        log.warning("ntfy: nie wysłano powiadomienia o gościu: %s", e)


def notify(first_name, last_name, company):
    url = (http.config("NTFY_URL") or "").strip()
    if not url:
        return
    if not url.lower().startswith(("https://", "http://")):  # bez file:// i innych schematów urllib (Bandit B310)
        log.warning("ntfy: NTFY_URL musi zaczynać się od https:// albo http:// – powiadomienie pominięte")
        return
    req = request_for(url, (http.config("NTFY_TOKEN") or "").strip(), message(first_name, last_name, company))
    if current_app.config.get("TESTING"):
        send(req)
    else:
        threading.Thread(target=send, args=(req,), daemon=True).start()
