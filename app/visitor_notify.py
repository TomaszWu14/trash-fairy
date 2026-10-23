"""Powiadomienie push (ntfy) właściciela o nowym gościu demo, po udanym zapisie w bramce (app/visitor_gate.py).

Bez `NTFY_URL` (pełny URL tematu, np. https://ntfy.sh/<tajny-temat>) nic się nie dzieje: zero ruchu sieciowego, także w
testach (conftest zeruje zmienną). Opcjonalny `NTFY_TOKEN` → `Authorization: Bearer`. Wysyłka w wątku w tle (gość nie
czeka); każdy błąd to tylko ostrzeżenie w logu. W testach (TESTING) wysyłamy od razu, żeby wynik był deterministyczny.

`NTFY_WATCH_COMPANIES` (frazy po przecinku, tylko w env): firma gościa zawierająca którąś z fraz (bez wielkości liter
i polskich znaków) daje push `urgent`. `NTFY_ENGAGED_VIEWS` (domyślnie 10, 0 = wyłączone): jeden push, gdy gość obejrzy
tyle ekranów (licznik w app/visitor_activity.py)."""
import logging
import threading
import unicodedata
import urllib.request

from flask import current_app

from . import http

APP = "Trash Fairy"
TIMEOUT_S = 5
MAX_BODY = 300
ENGAGED_VIEWS_DEFAULT = 10
log = logging.getLogger(__name__)


def message(first_name, last_name, company):
    return f"{first_name} {last_name} ({company}) wszedł do {APP}"[:MAX_BODY]


def normalize(text):
    """casefold, bez polskich znaków diakrytycznych (NFKD + ł→l), pojedyncze spacje."""
    text = unicodedata.normalize("NFKD", (text or "").casefold().replace("ł", "l"))
    return " ".join("".join(ch for ch in text if not unicodedata.combining(ch)).split())


def watched(company):
    """Czy firma zawiera którąś z fraz NTFY_WATCH_COMPANIES (po normalizacji, fraza min. 2 znaki)."""
    name = normalize(company)
    phrases = (normalize(p) for p in (http.config("NTFY_WATCH_COMPANIES") or "").split(","))
    return any(len(p) >= 2 and p in name for p in phrases)


def engaged_threshold():
    try:
        return max(int(str(http.config("NTFY_ENGAGED_VIEWS", "") or ENGAGED_VIEWS_DEFAULT).strip()), 0)
    except ValueError:
        return ENGAGED_VIEWS_DEFAULT


def request_for(url, token, body, title=f"Nowy gosc: {APP}", tags="bell", priority="high"):
    # nagłówki tylko ASCII (polskie znaki idą w treści UTF-8)
    headers = {"User-Agent": http.USER_AGENT, "Content-Type": "text/plain; charset=utf-8",
               "Title": title, "Tags": tags, "Priority": priority}
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


def _dispatch(body, **headers):
    url = (http.config("NTFY_URL") or "").strip()
    if not url:
        return
    if not url.lower().startswith(("https://", "http://")):  # bez file:// i innych schematów urllib (Bandit B310)
        log.warning("ntfy: NTFY_URL musi zaczynać się od https:// albo http:// – powiadomienie pominięte")
        return
    req = request_for(url, (http.config("NTFY_TOKEN") or "").strip(), body[:MAX_BODY], **headers)
    if current_app.config.get("TESTING"):
        send(req)
    else:
        threading.Thread(target=send, args=(req,), daemon=True).start()


def notify(first_name, last_name, company):
    body = message(first_name, last_name, company)
    if watched(company):
        _dispatch("⚠️ " + body, title=f"UWAGA firma z listy: {APP}", tags="rotating_light", priority="urgent")
    else:
        _dispatch(body)


def notify_engaged(first_name, last_name, company, views):
    """Jeden push, gdy gość obejrzał NTFY_ENGAGED_VIEWS ekranów; firma z listy → urgent."""
    _dispatch(f"{first_name} {last_name} ({company}) obejrzał już {views} ekranów w {APP}", title=f"Gosc oglada demo: {APP}",
              tags="eyes", priority="urgent" if watched(company) else "default")
