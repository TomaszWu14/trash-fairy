from collections import defaultdict, deque

import pytest

from app import http, sms
from app.models import Resident
from tests.fakes import FakeOpener

SENT = (201, {"sid": "VE123", "status": "pending", "channel": "sms", "to": "+48600100200"})


@pytest.fixture
def twilio(app, monkeypatch):
    app.config.update(TWILIO_ACCOUNT_SID="AC1", TWILIO_AUTH_TOKEN="tok", TWILIO_VERIFY_SID="VA1", SMS_DEMO_FALLBACK="")
    monkeypatch.setattr(sms, "_sent", defaultdict(deque))
    monkeypatch.setattr(sms, "_global", deque())

    def use(routes):
        fake = FakeOpener(routes)
        monkeypatch.setattr(http, "opener", fake)
        return fake
    return use


def register(client, phone="600 100 200", nick="Wróżka_Testowa"):
    return client.post("/api/residents", json={"nick": nick, "phone": phone, "district": "Stare Miasto"})


def test_without_gateway_demo_code_on_screen(client):
    d = register(client).json
    assert d["ok"] and d["demo_code"]
    assert client.post("/api/residents/verify", json={"code": d["demo_code"]}).json["ok"]


def test_twilio_send_and_check(client, twilio):
    fake = twilio({"/Verifications": SENT, "/VerificationCheck": (200, {"status": "approved", "valid": True})})
    d = register(client).json
    assert d["ok"] and d["demo_code"] is None
    sent = fake.requests[0]
    assert sent.data == b"To=%2B48600100200&Channel=sms" and sent.headers["Authorization"].startswith("Basic ")
    with client.session_transaction() as s:
        assert s["verification_sid"] == "VE123" and "600100200" not in str(dict(s))  # w sesji tylko SID
    assert client.post("/api/residents/verify", json={"code": "123456"}).json["ok"]
    assert b"VerificationSid=VE123" in fake.requests[1].data and Resident.query.one().verified


def test_wrong_code_and_retry_for_unverified_number(client, twilio):
    twilio({"/Verifications": SENT, "/VerificationCheck": (200, {"status": "pending", "valid": False})})
    register(client)
    assert client.post("/api/residents/verify", json={"code": "000000"}).status_code == 400
    assert register(client, nick="Nowy_Nick").json["ok"]  # nowy kod dla niepotwierdzonego numeru, to samo konto
    assert Resident.query.count() == 1 and Resident.query.one().nick == "Nowy_Nick"


def test_limits_per_number(client, twilio):
    twilio({"/Verifications": SENT})
    assert all(register(client).status_code == 200 for _ in range(sms.PER_NUMBER_H))
    r = register(client)
    assert r.status_code == 429 and "3 kody" in r.json["message"]


def test_gateway_failure_503_or_demo_fallback(client, app, twilio):
    twilio({"/Verifications": OSError("brak sieci")})
    assert register(client).status_code == 503
    app.config["SMS_DEMO_FALLBACK"] = "1"
    d = register(client).json
    assert d["ok"] and d["demo_code"]
