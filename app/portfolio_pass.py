"""Przepustka z portfolio (https://portfolio.twapp.pl): gość, który przedstawił się tam raz, nie widzi formularza bramki.

Portfolio ustawia ciasteczko `gosc` (domena nadrzędna .twapp.pl, więc trafia też do tego dema). Backend pyta portfolio
(`GET {PORTFOLIO_URL}/api/gosc`, nagłówek `Cookie: gosc=<token>`, timeout 2 s, bez przekierowań); liczy się wyłącznie kod
200. Błąd sieci, timeout i każdy inny kod = jak bez przepustki (formularz bramki), nigdy 500. Do portfolio idzie tylko
ciasteczko `gosc`; jego wartość nie trafia do logów. Wynik pozytywny jest w pamięci procesu ~10 min (po hashu tokenu),
a bramka i tak zapamiętuje go w sesji dema na 30 dni.

Ustawienia: `PORTFOLIO_URL` (domyślnie https://portfolio.twapp.pl; musi zaczynać się od https://, poza testami),
`PORTFOLIO_PASS` (domyślnie włączone; `0` wyłącza sprawdzanie przepustki)."""
import hashlib
import logging
import re
import time
import urllib.error
import urllib.request

from flask import current_app

from . import http

COOKIE = "gosc"
MAX_TOKEN = 200
TOKEN_RE = re.compile(r"[A-Za-z0-9._~+/=-]+")  # bez spacji, średników i znaków sterujących (wstrzyknięcie nagłówka)
DEFAULT_URL = "https://portfolio.twapp.pl"
TIMEOUT_S = 2
CACHE_TTL_S = 600
CACHE_MAX = 1000
GUEST_NAME = "Gość z portfolio"  # rekord DemoVisitor bez danych osobowych (potrzebny do liczenia aktywności)
_FALSE = {"0", "false", "off", "no", "nie"}
_cache: dict[str, float] = {}  # sha256(token) -> moment wygaśnięcia (monotonic)
log = logging.getLogger(__name__)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # 3xx wraca jako HTTPError → traktowane jak odmowa


opener = urllib.request.build_opener(_NoRedirect)


def enabled():
    return str(http.config("PORTFOLIO_PASS", "1")).strip().lower() not in _FALSE


def _base_url():
    url = (http.config("PORTFOLIO_URL") or DEFAULT_URL).strip().rstrip("/")
    if url.lower().startswith("https://") or (current_app.testing and url.lower().startswith("http://")):
        return url
    log.warning("przepustka: PORTFOLIO_URL musi zaczynać się od https:// – sprawdzanie przepustki wyłączone")
    return None


def clear_cache():
    _cache.clear()


def valid(token):
    """Czy token z ciasteczka `gosc` jest uznany przez portfolio. Bez ciasteczka/pustego/zbyt długiego: bez wywołania sieci."""
    if not token or len(token) > MAX_TOKEN or not TOKEN_RE.fullmatch(token) or not enabled():
        return False
    key = hashlib.sha256(token.encode()).hexdigest()
    now = time.monotonic()
    if _cache.get(key, 0) > now:
        return True
    base = _base_url()
    if base is None:
        return False
    req = urllib.request.Request(f"{base}/api/gosc", headers={"Cookie": f"{COOKIE}={token}", "User-Agent": http.USER_AGENT})
    try:
        with opener.open(req, timeout=TIMEOUT_S) as r:  # nosec B310 – schemat sprawdza _base_url()
            ok = r.status == 200
    except Exception as e:  # noqa: BLE001 – przepustka nigdy nie psuje odpowiedzi; treść błędu bez tokenu
        log.info("przepustka: portfolio niedostępne lub odmowa (%s)", type(e).__name__)
        return False
    if ok:
        if len(_cache) >= CACHE_MAX:
            _cache.clear()
        _cache[key] = now + CACHE_TTL_S
    return ok
