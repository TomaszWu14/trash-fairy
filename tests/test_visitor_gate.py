from datetime import UTC, datetime, timedelta

import pytest

from app import db
from app.models import DemoVisitor
from app.visitor_gate import safe_next

OK = {"first_name": "Jan", "last_name": "Kowalski", "company": "ACME", "consent": "1", "next": "/metodologia"}


@pytest.fixture
def gate(app):
    app.config["DEMO_VISITOR_GATE"] = True
    return app


def test_domyslnie_wylaczona_w_testach(client):
    assert client.get("/metodologia").status_code == 200


def test_bez_danych_formularz(gate, client):
    r = client.get("/metodologia")
    assert r.status_code == 200 and "przedstaw się, proszę" in r.get_data(as_text=True)
    assert "Prezesa UODO" in r.get_data(as_text=True)
    assert ("powiadomień push ntfy. Zapisuję też, ile i jakie ekrany wersji demonstracyjnej obejrzałeś (bez adresu IP), "
            "żeby wiedzieć, co zainteresowało gości. Poza tym nikomu danych nie przekazuję.") in r.get_data(as_text=True)


def test_adres_wlasciciela_ukryty_przed_botami(gate, client):
    for path in ("/metodologia", "/prywatnosc"):
        html = client.get(path).get_data(as_text=True)
        assert "tomasz.wierzbowski" "@op.pl" not in html
        assert "tomasz.wierzbowski [at] op.pl" in html


def test_z_danymi_zapis_i_dostep(gate, client):
    r = client.post("/wizytowka", data=OK)
    assert r.status_code == 303 and r.headers["Location"] == "/metodologia"
    v = DemoVisitor.query.one()
    assert (v.first_name, v.last_name, v.company) == ("Jan", "Kowalski", "ACME")
    assert "Set-Cookie" in r.headers and "HttpOnly" in r.headers["Set-Cookie"] and "SameSite=Lax" in r.headers["Set-Cookie"]
    assert "przedstaw się" not in client.get("/metodologia").get_data(as_text=True)


@pytest.mark.parametrize("patch", [{"first_name": " a "}, {"company": ""}, {"last_name": "Ko\x07w"}, {"company": "x" * 101},
                                   {"consent": ""}])
def test_niepoprawne_pola(gate, client, patch):
    r = client.post("/wizytowka", data={**OK, **patch})
    assert r.status_code == 400 and 'role="alert"' in r.get_data(as_text=True)
    assert DemoVisitor.query.count() == 0


def test_honeypot(gate, client):
    assert client.post("/wizytowka", data={**OK, "website": "http://spam"}).status_code == 400
    assert DemoVisitor.query.count() == 0
    assert "przedstaw się" in client.get("/metodologia").get_data(as_text=True)


@pytest.mark.parametrize("bad", ["//evil.com", "https://evil.com", "/\\evil.com", "javascript:x", "/a\nb"])
def test_bezpieczny_next(bad):
    assert safe_next(bad) == "/"


def test_api_health_statyki_nie_blokowane(gate, client):
    assert client.get("/health").status_code == 200
    assert client.get("/static/ui/app.css").status_code == 200
    assert "przedstaw się" not in client.get("/api/v1/openapi.json").get_data(as_text=True)
    assert client.get("/api/docs").status_code == 200
    privacy = client.get("/prywatnosc")
    assert privacy.status_code == 200 and "push ntfy" in privacy.get_data(as_text=True)
    assert "ile i jakie ekrany wersji demonstracyjnej obejrzałeś (bez adresu IP)" in privacy.get_data(as_text=True)


def test_retencja_90_dni(gate, client):
    old = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=91)
    db.session.add(DemoVisitor(first_name="Stary", last_name="Wpis", company="X", created_at=old))
    db.session.commit()
    client.post("/wizytowka", data=OK)
    assert [v.first_name for v in DemoVisitor.query.all()] == ["Jan"]


def test_lista_bez_tokenu_404(gate, client):
    assert client.get("/odwiedzajacy").status_code == 404
    assert client.get("/odwiedzajacy?token=").status_code == 404
    gate.config["VISITORS_TOKEN"] = "sekret"
    assert client.get("/odwiedzajacy?token=zly").status_code == 404


def test_lista_z_tokenem_i_csv(gate, client):
    gate.config["VISITORS_TOKEN"] = "sekret"
    db.session.add(DemoVisitor(first_name="=CMD()", last_name="Nowak", company="+X", created_at=datetime.now(UTC).replace(tzinfo=None)))
    db.session.commit()
    html = client.get("/odwiedzajacy", headers={"X-Visitors-Token": "sekret"})
    assert html.status_code == 200 and "Nowak" in html.get_data(as_text=True)
    csv_text = client.get("/odwiedzajacy?token=sekret&format=csv").get_data(as_text=True)
    assert "'=CMD()" in csv_text and "'+X" in csv_text
