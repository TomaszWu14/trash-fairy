"""Kod SMS przy rejestracji w programie „Przyjaciele Wróżki”: Twilio Verify przez REST (bez SDK).

Twilio generuje, wysyła i sprawdza kod; my trzymamy w sesji tylko SID weryfikacji (VE…), a numer telefonu
tylko jako HMAC w bazie (residents.phone_hash). Limity chronią konto przed nabiciem kosztów:
3 kody na numer na godzinę i 30 na godzinę dla całej aplikacji.
ponytail: limity w pamięci procesu — przy kilku workerach Gunicorna trzeba wspólnego magazynu (ROADMAPA.md).
"""
import time
from collections import defaultdict, deque

from . import http

BASE = "https://verify.twilio.com/v2/Services/{sid}/"
PER_NUMBER_H, GLOBAL_H = 3, 30
_sent = defaultdict(deque)
_global = deque()


class SmsError(Exception):
    def __init__(self, message, status=503):
        super().__init__(message)
        self.status = status


def configured():
    return all(http.config(k) for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_VERIFY_SID"))


def _auth():
    return http.config("TWILIO_ACCOUNT_SID"), http.config("TWILIO_AUTH_TOKEN")


def _url(path):
    return BASE.format(sid=http.config("TWILIO_VERIFY_SID")) + path


def _within_limits(key, now):
    for q in (_sent[key], _global):
        while q and now - q[0] > 3600:
            q.popleft()
    if len(_sent[key]) >= PER_NUMBER_H:
        raise SmsError("Wysłaliśmy już 3 kody na ten numer w ciągu godziny. Spróbuj później.", 429)
    if len(_global) >= GLOBAL_H:
        raise SmsError("Chwilowo nie wysyłamy więcej SMS-ów. Spróbuj za kilkanaście minut.", 429)


def send_code(phone9, key):
    """Wysyła kod na +48 `phone9`. `key` (HMAC numeru) liczy limit bez trzymania numeru. Zwraca SID weryfikacji."""
    now = time.time()
    _within_limits(key, now)
    try:
        status, body = http.post_form(_url("Verifications"), {"To": f"+48{phone9}", "Channel": "sms"}, auth=_auth())
    except Exception as e:
        raise SmsError("Nie udało się wysłać SMS-a (brak połączenia z bramką).") from e
    if status not in (200, 201) or not (body or {}).get("sid"):
        raise SmsError(f"Bramka SMS odrzuciła numer ({(body or {}).get('code', status)}).")
    _sent[key].append(now)
    _global.append(now)
    return body["sid"]


def check_code(verification_sid, code):
    """True, gdy Twilio potwierdzi kod. 404 = weryfikacja wygasła albo wykorzystana."""
    try:
        status, body = http.post_form(_url("VerificationCheck"), {"VerificationSid": verification_sid, "Code": code},
                                      auth=_auth())
    except Exception as e:
        raise SmsError("Nie udało się sprawdzić kodu (brak połączenia z bramką).") from e
    return status == 200 and (body or {}).get("status") == "approved"
