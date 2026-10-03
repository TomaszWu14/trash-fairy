import pytest

from app import http, residents, sms
from app.models import Resident
from tests.fakes import FakeOpener

SENT = (201, {"sid": "VE123", "status": "pending", "channel": "sms", "to": "+48600100200"})
KEY = "test-hash-600100200"  # HMAC numeru; dla limitu liczy się tylko, że jest stały


@pytest.fixture
def twilio(app, monkeypatch):
    app.config.update(TWILIO_ACCOUNT_SID="AC1", TWILIO_AUTH_TOKEN="tok", TWILIO_VERIFY_SID="VA1", SMS_DEMO_FALLBACK="")

    def use(routes):
        fake = FakeOpener(routes)
        monkeypatch.setattr(http, "opener", fake)
        return fake
    return use


def test_without_gateway_not_configured():
    assert not sms.configured()  # bez bramki rejestracja pokazuje kod demo (residents.register zwraca code)


def test_twilio_send_and_check(twilio):
    fake = twilio({"/Verifications": SENT, "/VerificationCheck": (200, {"status": "approved", "valid": True})})
    assert sms.configured()
    sid = sms.send_code("600100200", KEY)
    sent = fake.requests[0]
    assert sid == "VE123"
    assert sent.data == b"To=%2B48600100200&Channel=sms" and sent.headers["Authorization"].startswith("Basic ")
    assert sms.check_code(sid, "123456")
    assert b"VerificationSid=VE123" in fake.requests[1].data


def test_wrong_code_and_retry_for_unverified_number(twilio):
    twilio({"/Verifications": SENT, "/VerificationCheck": (200, {"status": "pending", "valid": False})})
    residents.register("Wróżka_Testowa", "600 100 200", "Stare Miasto")
    assert sms.check_code(sms.send_code("600100200", KEY), "000000") is False
    residents.register("Nowy_Nick", "600 100 200", "Stare Miasto")  # nowy kod dla niepotwierdzonego numeru, to samo konto
    assert Resident.query.count() == 1 and Resident.query.one().nick == "Nowy_Nick"


def test_limits_per_number(twilio):
    twilio({"/Verifications": SENT})
    for _ in range(sms.PER_NUMBER_H):
        sms.send_code("600100200", KEY)
    with pytest.raises(sms.SmsError, match="3 kody") as e:
        sms.send_code("600100200", KEY)
    assert e.value.status == 429


def test_gateway_failure_is_503(twilio):
    twilio({"/Verifications": OSError("brak sieci")})
    with pytest.raises(sms.SmsError) as e:
        sms.send_code("600100200", KEY)
    assert e.value.status == 503
