import urllib.error

import pytest

from app import http, visitor_notify
from app.models import DemoVisitor
from tests.fakes import FakeOpener

OK = {"first_name": "Józef", "last_name": "Kowalski", "company": "ACME", "consent": "1", "next": "/metodologia"}
URL = "https://ntfy.example/tajny-temat"


@pytest.fixture
def ntfy(app, monkeypatch):
    app.config.update(DEMO_VISITOR_GATE=True, NTFY_URL=URL)
    fake = FakeOpener({"ntfy.example": (200, {"id": "x"})})
    monkeypatch.setattr(http, "opener", fake)
    return fake


def test_poprawny_formularz_wysyla_jedno_powiadomienie(ntfy, client):
    assert client.post("/wizytowka", data=OK).status_code == 303
    assert len(ntfy.requests) == 1
    req = ntfy.requests[0]
    assert req.full_url == URL and req.get_method() == "POST"
    assert req.data.decode("utf-8") == "Józef Kowalski (ACME) wszedł do Trash Fairy"
    assert req.get_header("Title") == "Nowy gosc: Trash Fairy"
    assert req.get_header("Tags") == "bell" and req.get_header("Priority") == "high"
    assert req.get_header("Content-type") == "text/plain; charset=utf-8"
    assert req.get_header("Authorization") is None
    assert all(v.isascii() for v in req.headers.values())


@pytest.mark.parametrize("patch", [{"website": "http://spam"}, {"first_name": "a"}, {"consent": ""}])
def test_honeypot_i_niepoprawne_dane_bez_wysylki(ntfy, client, patch):
    assert client.post("/wizytowka", data={**OK, **patch}).status_code == 400
    assert ntfy.requests == []


def test_limit_bez_wysylki(ntfy, client, monkeypatch):
    monkeypatch.setattr("app.visitor_gate.rate.hit", lambda *a, **k: False)
    assert client.post("/wizytowka", data=OK).status_code == 429
    assert ntfy.requests == []


def test_bez_ntfy_url_bez_wysylki(ntfy, app, client):
    app.config["NTFY_URL"] = ""
    assert client.post("/wizytowka", data=OK).status_code == 303
    assert ntfy.requests == [] and DemoVisitor.query.count() == 1


@pytest.mark.parametrize("bad", ["file:///etc/passwd", "ftp://ntfy.example/t", "ntfy.example/t"])
def test_url_bez_http_pominiety(ntfy, app, client, bad):
    app.config["NTFY_URL"] = bad
    assert client.post("/wizytowka", data=OK).status_code == 303
    assert ntfy.requests == []


def test_blad_wysylki_nie_psuje_odpowiedzi(app, client, monkeypatch):
    app.config.update(DEMO_VISITOR_GATE=True, NTFY_URL=URL)
    fake = FakeOpener({"ntfy.example": urllib.error.URLError("timeout")})
    monkeypatch.setattr(http, "opener", fake)
    r = client.post("/wizytowka", data=OK)
    assert r.status_code == 303 and r.headers["Location"] == "/metodologia"
    assert len(fake.requests) == 1 and DemoVisitor.query.count() == 1


def test_token_daje_naglowek_authorization(ntfy, app, client):
    app.config["NTFY_TOKEN"] = "tk_sekret"
    client.post("/wizytowka", data=OK)
    assert ntfy.requests[0].get_header("Authorization") == "Bearer tk_sekret"


def test_tresc_przycieta_do_300_znakow():
    assert len(visitor_notify.message("x" * 100, "y" * 100, "z" * 100)) == visitor_notify.MAX_BODY


def test_poza_testami_wysylka_w_watku(ntfy, app, client, monkeypatch):
    started = []

    class SyncThread:
        def __init__(self, target, args, daemon):
            started.append(daemon)
            self.target, self.args = target, args

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(visitor_notify.threading, "Thread", SyncThread)
    app.config["TESTING"] = False
    try:
        assert client.post("/wizytowka", data=OK).status_code == 303
    finally:
        app.config["TESTING"] = True
    assert started == [True] and len(ntfy.requests) == 1
