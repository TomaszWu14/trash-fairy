import urllib.error

import pytest

from app import portfolio_pass
from app.models import DemoVisitor
from tests.fakes import FakeOpener

URL = "http://portfolio.test"


@pytest.fixture
def gate(app, monkeypatch):
    app.config.update({"DEMO_VISITOR_GATE": True, "PORTFOLIO_URL": URL, "NTFY_URL": "https://ntfy.test/t"})
    portfolio_pass.clear_cache()
    return app


def fake(monkeypatch, answer):
    op = FakeOpener({"/api/gosc": answer})
    monkeypatch.setattr(portfolio_pass, "opener", op)
    return op


def test_wazna_przepustka_bez_formularza_i_pusha(gate, client, monkeypatch):
    from app import http
    ntfy = FakeOpener({"ntfy.test": (200, {})})
    monkeypatch.setattr(http, "opener", ntfy)
    op = fake(monkeypatch, (200, {"ok": True}))
    client.set_cookie("gosc", "tok123", domain="localhost")
    r = client.get("/metodologia")
    assert r.status_code == 200 and "przedstaw się" not in r.get_data(as_text=True)
    assert "portfolio.twapp.pl/px/trash-fairy" in r.get_data(as_text=True)
    v = DemoVisitor.query.one()
    assert (v.first_name, v.company) == (portfolio_pass.GUEST_NAME, "")
    assert op.requests[0].full_url == f"{URL}/api/gosc" and op.requests[0].get_header("Cookie") == "gosc=tok123"
    assert ntfy.requests == []
    # kolejne żądania: sesja dema, bez ponownego pytania portfolio ani nowego rekordu
    client.get("/prywatnosc")
    client.get("/metodologia")
    assert len(op.requests) == 1 and DemoVisitor.query.count() == 1
    assert DemoVisitor.query.one().page_views >= 1


def test_aktywnosc_goscia_z_portfolio_nie_daje_pusha(gate, client, monkeypatch):
    from app import http
    gate.config["NTFY_ENGAGED_VIEWS"] = "1"
    ntfy = FakeOpener({"ntfy.test": (200, {})})
    monkeypatch.setattr(http, "opener", ntfy)
    fake(monkeypatch, (200, {"ok": True}))
    client.set_cookie("gosc", "tok123", domain="localhost")
    client.get("/metodologia")
    assert DemoVisitor.query.one().page_views == 1 and ntfy.requests == []


def test_odmowa_401_formularz(gate, client, monkeypatch):
    fake(monkeypatch, (401, {"ok": False}))
    client.set_cookie("gosc", "tok123", domain="localhost")
    assert "przedstaw się, proszę" in client.get("/metodologia").get_data(as_text=True)
    assert DemoVisitor.query.count() == 0


@pytest.mark.parametrize("err", [TimeoutError(), urllib.error.URLError("x"), RuntimeError("x")])
def test_blad_sieci_formularz(gate, client, monkeypatch, err):
    fake(monkeypatch, err)
    client.set_cookie("gosc", "tok123", domain="localhost")
    r = client.get("/metodologia")
    assert r.status_code == 200 and "przedstaw się, proszę" in r.get_data(as_text=True)


def test_formularz_bez_piksela_portfolio(gate, client):
    assert "/px/" not in client.get("/metodologia").get_data(as_text=True)


def test_brak_ciasteczka_bez_wywolania_sieci(gate, client, monkeypatch):
    op = fake(monkeypatch, (200, {"ok": True}))
    assert "przedstaw się, proszę" in client.get("/metodologia").get_data(as_text=True)
    assert op.requests == []


@pytest.mark.parametrize("value", ["", "x" * 201, "a b", "a;b=c"])
def test_zle_ciasteczko_bez_wywolania_sieci(gate, monkeypatch, value):
    op = fake(monkeypatch, (200, {"ok": True}))
    assert portfolio_pass.valid(value) is False and op.requests == []


def test_wylaczone_przez_env(gate, client, monkeypatch):
    gate.config["PORTFOLIO_PASS"] = "0"
    op = fake(monkeypatch, (200, {"ok": True}))
    client.set_cookie("gosc", "tok123", domain="localhost")
    assert "przedstaw się, proszę" in client.get("/metodologia").get_data(as_text=True)
    assert op.requests == []


def test_url_bez_https_poza_testami_wylaczony(gate, monkeypatch):
    gate.testing = False
    gate.config["PORTFOLIO_URL"] = "http://portfolio.test"
    op = fake(monkeypatch, (200, {"ok": True}))
    assert portfolio_pass.valid("tok123") is False and op.requests == []


def test_cache_pozytywny(gate, monkeypatch):
    op = fake(monkeypatch, (200, {"ok": True}))
    assert portfolio_pass.valid("tok123") and portfolio_pass.valid("tok123")
    assert len(op.requests) == 1


def test_wynik_negatywny_nie_jest_cache(gate, monkeypatch):
    op = fake(monkeypatch, (401, {"ok": False}))
    assert not portfolio_pass.valid("tok123") and not portfolio_pass.valid("tok123")
    assert len(op.requests) == 2


def test_przekierowanie_to_odmowa():
    handler = portfolio_pass._NoRedirect()
    assert handler.redirect_request(None, None, 302, "Found", {}, "http://x") is None
