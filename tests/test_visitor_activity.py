import json
import time
from datetime import UTC, datetime, timedelta

import pytest
from flask import Flask
from flask.sessions import SecureCookieSessionInterface

from app import db, http, visitor_activity
from app.models import DemoVisitor
from tests.fakes import FakeOpener

OK = {"first_name": "Jan", "last_name": "Kowalski", "company": "ACME", "consent": "1", "next": "/metodologia"}
URL = "https://ntfy.example/tajny-temat"


@pytest.fixture
def gate(app):
    app.config["DEMO_VISITOR_GATE"] = True
    return app


@pytest.fixture
def ntfy(gate, monkeypatch):
    gate.config["NTFY_URL"] = URL
    fake = FakeOpener({"ntfy.example": (200, {"id": "x"})})
    monkeypatch.setattr(http, "opener", fake)
    return fake


def _now():
    return datetime.now(UTC).replace(tzinfo=None)


def _visitor():
    db.session.expire_all()
    return DemoVisitor.query.one()


def test_trzy_ekrany_policzone(gate, client):
    assert client.post("/wizytowka", data=OK).status_code == 303
    for path in ("/metodologia", "/metodologia", "/dostepnosc"):
        assert client.get(path).status_code == 200
    v = _visitor()
    assert v.page_views == 3 and v.last_seen_at is not None and v.last_seen_at >= v.created_at
    assert json.loads(v.sections) == {"metodologia": 2, "dostepnosc": 1}
    assert v.top_sections() == ["metodologia", "dostepnosc"]


def test_statyki_bez_vary_cookie_dla_anonimowych(gate, client):
    assert "Cookie" not in client.get("/static/ui/app.css").headers.get("Vary", "")  # bramka nie psuje cache statyk


def test_statyki_health_api_404_post_nie_liczone(gate, client):
    client.post("/wizytowka", data=OK)
    client.get("/static/ui/app.css")
    client.get("/health")
    client.get("/api/v1/openapi.json")
    client.get("/api/docs")
    assert client.get("/nie-ma-takiej-strony").status_code == 404
    client.head("/metodologia")
    client.get("/odwiedzajacy")
    v = _visitor()
    assert v.page_views == 0 and v.last_seen_at is None and v.sections is None


def test_gosc_bez_flagi_nie_liczony(gate, client):
    db.session.add(DemoVisitor(first_name="A", last_name="B", company="C", created_at=_now()))
    db.session.commit()
    client.get("/metodologia")  # formularz bramki (200, HTML), ale bez flagi
    assert _visitor().page_views == 0


def test_flaga_sprzed_zmiany_bez_id_nie_liczona(gate, client):
    db.session.add(DemoVisitor(first_name="A", last_name="B", company="C", created_at=_now()))
    db.session.commit()
    with client.session_transaction() as s:
        s["demo_visitor_ok"] = int(time.time())
    assert "przedstaw się" not in client.get("/metodologia").get_data(as_text=True)
    assert _visitor().page_views == 0


def test_podrobiona_flaga_nie_liczona(gate, client):
    client.post("/wizytowka", data=OK)
    vid = _visitor().id
    other = gate.test_client()
    forged = {"demo_visitor_ok": int(time.time()), "demo_visitor_id": vid}
    foreign = Flask("obcy", root_path=".")
    foreign.secret_key = "inny-klucz"
    signer = SecureCookieSessionInterface().get_signing_serializer(foreign)
    for value in (json.dumps(forged), signer.dumps(forged)):  # bez podpisu i z podpisem innym kluczem
        other.set_cookie("session", value)
        assert "przedstaw się" in other.get("/metodologia").get_data(as_text=True)
    assert _visitor().page_views == 0


def test_wygasla_flaga_nie_liczona(gate, client):
    client.post("/wizytowka", data=OK)
    with client.session_transaction() as s:
        s["demo_visitor_ok"] -= 31 * 24 * 3600
    client.get("/metodologia")
    assert _visitor().page_views == 0


def test_prog_zaangazowania_jeden_push(ntfy, client):
    client.application.config["NTFY_ENGAGED_VIEWS"] = "3"
    client.post("/wizytowka", data=OK)
    for _ in range(5):
        client.get("/dostepnosc")
    engaged = [r for r in ntfy.requests if r.get_header("Tags") == "eyes"]
    assert len(ntfy.requests) == 2 and len(engaged) == 1
    req = engaged[0]
    assert req.get_header("Title") == "Gosc oglada demo: Trash Fairy" and req.get_header("Priority") == "default"
    assert req.data.decode("utf-8") == "Jan Kowalski (ACME) obejrzał już 3 ekranów w Trash Fairy"


def test_prog_firma_z_listy_pilny(ntfy, client):
    client.application.config.update(NTFY_ENGAGED_VIEWS="1", NTFY_WATCH_COMPANIES="acme")
    client.post("/wizytowka", data=OK)
    client.get("/dostepnosc")
    assert [r.get_header("Priority") for r in ntfy.requests] == ["urgent", "urgent"]
    assert ntfy.requests[1].get_header("Tags") == "eyes"


def test_prog_zero_wylaczony(ntfy, client):
    client.application.config["NTFY_ENGAGED_VIEWS"] = "0"
    client.post("/wizytowka", data=OK)
    for _ in range(3):
        client.get("/dostepnosc")
    assert len(ntfy.requests) == 1


def test_wyjatek_nie_psuje_odpowiedzi(gate, client, monkeypatch, caplog):
    client.post("/wizytowka", data=OK)

    def boom(*a, **k):
        raise RuntimeError("baza padła")

    monkeypatch.setattr(visitor_activity, "record", boom)
    r = client.get("/dostepnosc")
    assert r.status_code == 200 and "przedstaw się" not in r.get_data(as_text=True)
    assert "nie zapisano wejścia" in caplog.text


def test_usuniety_wpis_nie_psuje(gate, client):
    client.post("/wizytowka", data=OK)
    DemoVisitor.query.delete()
    db.session.commit()
    assert client.get("/dostepnosc").status_code == 200


def test_limit_20_sekcji(gate, client):
    client.post("/wizytowka", data=OK)
    v = _visitor()
    v.sections = json.dumps({f"s{i}": 1 for i in range(20)})
    db.session.commit()
    client.get("/dostepnosc")
    client.get("/metodologia")
    v = _visitor()
    counts = json.loads(v.sections)
    assert len(counts) == 20 and "dostepnosc" not in counts and v.page_views == 2


def test_istniejaca_sekcja_liczona_przy_limicie(gate, client):
    client.post("/wizytowka", data=OK)
    v = _visitor()
    v.sections = json.dumps({**{f"s{i}": 1 for i in range(19)}, "dostepnosc": 4})
    db.session.commit()
    client.get("/dostepnosc")
    assert json.loads(_visitor().sections)["dostepnosc"] == 5


@pytest.mark.parametrize("path, expected", [("/", "start"), ("/palety/123", "palety"), ("/Metodologia", None),
                                            ("/zgłoś", None), ("/" + "a" * 50, "a" * 40), ("/a.b/c", None),
                                            ("/x_y-1/", "x_y-1")])
def test_sekcja_ze_sciezki(path, expected):
    assert visitor_activity.section_of(path) == expected


def test_lista_pokazuje_aktywnosc(gate, client):
    gate.config["VISITORS_TOKEN"] = "sekret"
    now = _now()
    db.session.add(DemoVisitor(first_name="Ewa", last_name="Nowak", company="X", created_at=now - timedelta(minutes=7),
                               page_views=12, last_seen_at=now, sections=json.dumps({"a": 1, "b": 5, "c": 3, "d": 2})))
    db.session.add(DemoVisitor(first_name="Bez", last_name="Ruchu", company="Y", created_at=now))
    db.session.commit()
    html = client.get("/odwiedzajacy?token=sekret").get_data(as_text=True)
    for text in ("Ekrany", "Czas", "Najczęściej", "<td>12</td>", "ok. 7 min", "b, c, d", "<td>—</td>"):
        assert text in html
    csv_text = client.get("/odwiedzajacy?token=sekret&format=csv").get_data(as_text=True)
    assert csv_text.splitlines()[0] == "data_utc,imie,nazwisko,firma,ekrany,czas,najczesciej"
    assert "12,ok. 7 min,b c d" in csv_text


def test_kolumny_dokladane_do_starej_bazy(app):
    from sqlalchemy import inspect, text
    from app import _add_missing_columns
    db.session.execute(text("DROP TABLE demo_visitor"))
    db.session.execute(text("CREATE TABLE demo_visitor (id INTEGER PRIMARY KEY, first_name VARCHAR(100) NOT NULL, "
                            "last_name VARCHAR(100) NOT NULL, company VARCHAR(100) NOT NULL, created_at DATETIME NOT NULL)"))
    db.session.commit()
    _add_missing_columns()
    cols = {c["name"] for c in inspect(db.engine).get_columns("demo_visitor")}
    assert {"page_views", "last_seen_at", "sections"} <= cols
