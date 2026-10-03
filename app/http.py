"""Wspólny klient HTTP integracji (Open-Meteo, TomTom, Twilio): urllib ze stdlib, bez nowych zależności.

Testy podmieniają `opener` (tests/fakes.py), więc żaden test nie wychodzi do sieci.
"""
import base64
import json
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "TrashFairy/1.0 (HackYeah 2026)"
opener = urllib.request.build_opener()


def config(key, default=""):
    """Ustawienie integracji: najpierw config aplikacji (testy je zerują), potem zmienna środowiskowa."""
    import os
    from flask import current_app, has_app_context
    if has_app_context() and key in current_app.config:
        return current_app.config[key]
    return os.environ.get(key, default)


def _send(req, timeout):
    """(status, json). Błąd HTTP z treścią JSON (np. Twilio 400/429) zwracamy jako wynik, sieć i timeout jako wyjątek."""
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read() or b"null")
        except ValueError:
            body = None
        return e.code, body


def get_json(url, params=None, timeout=4):
    full = f"{url}?{urllib.parse.urlencode(params)}" if params else url
    return _send(urllib.request.Request(full, headers={"User-Agent": USER_AGENT}), timeout)


def post_form(url, data, auth=None, timeout=6):
    headers = {"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
    if auth:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    body = urllib.parse.urlencode(data).encode()
    return _send(urllib.request.Request(url, data=body, headers=headers, method="POST"), timeout)
