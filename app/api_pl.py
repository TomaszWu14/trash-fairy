"""API panelu kosza, mieszkańca i demo: kosze, przycisk na panelu, zgłoszenia z kodem QR, oś czasu zgłoszenia.
Trasy kierowcy: app/api_kierowca.py; wspólne helpery i blueprint: app/api_wspolne.py (ten sam blueprint „api_pl”).
Nazwy importowane z app.api_pl przez inne moduły i testy zostają dostępne tutaj (re-eksport niżej)."""
import hashlib
import hmac
import math
import time
from datetime import UTC, datetime, timedelta, timezone
from datetime import time as dt_time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app, jsonify, request

from . import clock, db, photos, rate, residents
from .api_wspolne import (FRAKCJE, KIND_LABEL, TYPY, _address, _ai, _dowod, _jade_at, _json_body, _point,  # noqa: F401
                          _punkty, _report_from_nr, blad, bp, kosz_json, meta, numer, poziom_stan)
from .devices_api import device_token
from .geo import distance_m
from .models import DeviceInfo, Point, Press
from .reports import record_press
from .routes import next_runs
from .state import data_version, point_states

try:
    WARSAW = ZoneInfo("Europe/Warsaw")  # doba kodu QR kosza = doba kalendarzowa w Krakowie
except ZoneInfoNotFoundError:  # obraz bez tzdata: doba w UTC+1, kod zmienia się najwyżej godzinę „za wcześnie” latem
    WARSAW = timezone(timedelta(hours=1))
QR_GRACE_S = 3600           # wczorajszy kod działa jeszcze godzinę po północy: skan tuż przed północą nie przepada
BUTTON_PRESSES_PER_MIN = 3  # przycisk na panelu: najwyżej 3 zgłoszenia na minutę z jednego kosza
REPORT_GAP_S = 60           # ten sam telefon i ten sam kosz: nie częściej niż raz na minutę
REPORTS_PER_IP_HOUR = 200   # wszystkie kosze z jednego IP: wysoko, bo sala HackYeah i jury wychodzą przez jeden NAT
RESET_GAP_S = 20            # ręczny reset demo najwyżej raz na 20 s (wszystkie workery)


def _local(at=None):
    """Zegar ŚCIENNY w Krakowie, nie zegar demo: kod QR to zabezpieczenie, nie może stać razem ze scenariuszem."""
    return datetime.fromtimestamp(time.time() if at is None else at, WARSAW)


def qr_token(point_id, at=None):
    """Token z kodu QR na panelu kosza, inny każdego dnia (doba w Krakowie): bez niego nie ma zgłoszenia mieszkańca.
    Zdjęcie kodu nie pozwala zgłaszać jutro ani z innego kosza; położenia telefonu nie sprawdzamy (decyzja w DECYZJE.md)."""
    key = current_app.config["SECRET_KEY"].encode()
    return hmac.new(key, f"kosz:{point_id}:{_local(at).date().isoformat()}".encode(), hashlib.sha256).hexdigest()[:12]


def qr_valid(point_id, token):
    """Kod z dziś albo, przez pierwszą godzinę po północy, z wczoraj. Porównanie bajtów: znaki spoza ASCII nie dają 500."""
    now, token = time.time(), str(token or "").encode()
    return any(hmac.compare_digest(token, qr_token(point_id, now - back).encode()) for back in (0, QR_GRACE_S))


def qr_seconds_left(at=None):
    """Sekundy do najbliższej północy w Krakowie (panel przeładowuje się wtedy z nowym kodem). Przez timestamp: zmiana czasu
    w marcu i październiku nie przesuwa wyniku o godzinę."""
    now = _local(at)
    midnight = datetime.combine(now.date() + timedelta(days=1), dt_time.min, WARSAW)
    return max(1, round(midnight.timestamp() - now.timestamp()))


@bp.get("/zmiany")
def zmiany():
    """Wersja danych do pollingu wszystkich perspektyw (co 3 s): zmienia się po zgłoszeniu, odbiorze i resecie."""
    return jsonify(wersja=data_version(), meta=meta())


@bp.post("/demo/reset")
def demo_reset():
    """Przywraca dane demo do stanu początkowego (jedna rola „Przegląd jury”, bez logowania).
    Reset trwa kilka–kilkanaście sekund: limit wspólny dla workerów i blokada w procesie, żeby dwa kliknięcia
    (albo kliknięcie w trakcie auto-resetu) nie kasowały i nie wstawiały symulacji równolegle."""
    if not rate.hit("demo-reset", 1, RESET_GAP_S) or not clock.reset_exclusive():
        return blad("Reset danych demo już trwa albo był przed chwilą. Spróbuj za kilkanaście sekund.", "reset_trwa", 429)
    return jsonify(ok=True, meta=meta())


@bp.get("/kosze")
def kosze():
    """Kosze operacyjne z poziomem; ?blisko=lat,lon sortuje po odległości i dodaje `odleglosc_m`."""
    now = clock.now()
    states = point_states(now)
    pts = [p for p in Point.query.order_by(Point.id) if p.id in states and getattr(p, "live", True)]
    out = [kosz_json(p, states, now) for p in pts]
    if request.args.get("blisko"):
        try:
            lat, lon = (float(x) for x in request.args["blisko"].split(","))
            if not (math.isfinite(lat) and math.isfinite(lon)):
                raise ValueError
        except ValueError:
            return blad("Parametr „blisko” to szerokość i długość geograficzna, np. 50.06,19.94.", "zly_parametr")
        for k in out:
            k["odleglosc_m"] = round(distance_m(lat, lon, k["lat"], k["lon"]))
        out.sort(key=lambda k: k["odleglosc_m"])
    return jsonify(kosze=out, meta=meta())


@bp.get("/kosze/<int:point_id>")
def kosz(point_id):
    p = _point(point_id)
    if p is None:
        return blad("Nie ma takiego kosza.", "kosz_nie_istnieje", 404)
    now = clock.now()
    return jsonify(kosz=kosz_json(p, point_states(now), now, detail=True), meta=meta())


@bp.post("/kosze/<int:point_id>/przycisk")
def przycisk(point_id):
    """Przycisk na panelu kosza: naciśnięcie fizycznego przycisku = obecność przy koszu, więc bez kodu QR.
    Body JSON: {"typ": klucz TYPY, "token": token urządzenia panelu} (ten sam HMAC co nagłówek w POST /api/odczyty).
    W demo panel to strona WWW i ma token w HTML; prawdziwy panel liczy go sam z sekretu wgranego przy montażu."""
    p = _point(point_id)
    if p is None:
        return blad("Nie ma takiego kosza.", "kosz_nie_istnieje", 404)
    data = _json_body()
    info = db.session.get(DeviceInfo, p.id)
    token = str(data.get("token") or "").encode()
    if info is None or info.kind != "panel" or not hmac.compare_digest(token, device_token(info.serial).encode()):
        return blad("Ten panel nie jest zarejestrowany przy tym koszu. Zgłoś problem kodem QR z ekranu.", "zly_token_panelu", 403)
    if not isinstance(data.get("typ"), str) or data["typ"] not in TYPY:
        return blad("Wybierz, co jest nie tak z koszem.", "zly_typ")
    if not rate.hit(f"btn:{p.id}", BUTTON_PRESSES_PER_MIN, 60):
        return blad("Zgłoszenia z tego kosza już dotarły. Kolejne możesz wysłać za minutę.", "za_czesto", 429)
    record_press(p.id, clock.now(), ip=request.remote_addr, wall_at=datetime.now(UTC).replace(tzinfo=None),
                 source="button", kind=TYPY[data["typ"]][0])  # record_press zapisuje (commit)
    clock.touch()
    return jsonify(komunikat="Dziękujemy, zgłoszenie przyjęte.", meta=meta()), 201


@bp.post("/zgloszenia")
def zglos():
    """Zgłoszenie mieszkańca: tylko z dziennym tokenem z kodu QR tego kosza (qr_valid). Położenia nie sprawdzamy:
    jury testuje zdalnie, a GPS w kamienicach bywa zawodny. Pola: kosz, typ, qr, komentarz?, zdjecie? (multipart);
    lat/lon z dawnych klientów są ignorowane."""
    data = request.form if request.files or request.form else _json_body()
    p = _point(data.get("kosz"))
    if p is None:
        return blad("Nie ma takiego kosza.", "kosz_nie_istnieje", 404)
    if not isinstance(data.get("typ"), str) or data["typ"] not in TYPY:
        return blad("Wybierz, co jest nie tak z koszem.", "zly_typ")
    if not qr_valid(p.id, data.get("qr")):
        return blad("Kod QR jest nieaktualny albo z innego kosza. Zeskanuj kod z panelu tego kosza." if data.get("qr")
                    else "Zeskanuj kod QR z panelu kosza, żeby zgłosić problem.", "brak_skanu_qr", 403)
    raw, mt, error = photos.read_upload(request.files.get("zdjecie"))  # przed limitami: zły plik nie zużywa limitu
    if error:
        return blad(error, "zle_zdjecie")
    client = str(data.get("klient") or request.remote_addr)[:64]
    if not rate.hit(f"zgl:{client}:{p.id}", 1, REPORT_GAP_S):
        return blad("To zgłoszenie już dotarło. Kolejne z tego telefonu możesz wysłać za minutę.", "za_czesto", 429)
    if not rate.hit(f"zgl-ip:{request.remote_addr}", REPORTS_PER_IP_HOUR, 3600):
        return blad(f"Z tej sieci wysłano już {REPORTS_PER_IP_HOUR} zgłoszeń w ciągu godziny. Spróbuj później.",
                    "za_duzo_zgloszen", 429)
    note = str(data.get("komentarz") or "").strip()[:280] or None
    photo_id = photos.save(p.id, clock.now(), raw, mt, source="resident").id if raw else None
    now = clock.now()
    kind = TYPY[data["typ"]][0]
    # konto demo „Anna K.” z nagłówka perspektywy mieszkańca: TYLKO punkty za trafne zgłoszenie (residents.award czyta
    # Press.resident_id po opróżnieniu). Nie przez record_press: wspólne konto jury podniosłoby wagę i „potwierdziło” zgłoszenie
    resident_id = residents.demo_resident().id if data.get("konto") == "demo" else None
    report = record_press(p.id, now, ip=request.remote_addr, wall_at=datetime.now(UTC).replace(tzinfo=None),
                          source="qr", kind=kind)
    press = Press.query.filter_by(report_id=report.id).order_by(Press.id.desc()).first()
    press.note, press.photo_id, press.resident_id = note, photo_id, resident_id
    db.session.commit()
    clock.touch()
    if photo_id:  # AI tylko opisuje zdjęcie; status weryfikacji liczy reguła (photos.verification)
        photos.analyze_in_background(photo_id)
    return jsonify(numer=numer(report.id), dolaczone=report.presses > 1, meta=meta()), 201


@bp.get("/zgloszenia/<nr>")
def zgloszenie(nr):
    """Oś czasu zgłoszenia: przyjęte → w realizacji („Jadę”) → zrealizowane (opróżniono)."""
    r = _report_from_nr(nr)
    if r is None:
        return blad("Nie znaleźliśmy zgłoszenia o tym numerze.", "zgloszenie_nie_istnieje", 404)
    p = db.session.get(Point, r.point_id)
    now = clock.now()
    jade = _jade_at(p.id, r.first_at)
    # opróżnienie z aplikacji kierowcy rozstrzyga zgłoszenie od razu (resolve_reports); szukanie Emptying „po first_at”
    # łapało wcześniejsze opróżnienie z tą samą minutą zegara demo i nowe zgłoszenie było od razu „zrealizowane”
    done_at = r.resolved_at if r.resolved_at and r.resolved_at <= now else None
    jade = jade or done_at  # „Jadę” kasujemy przy opróżnieniu (patrz odbior): krok „W realizacji” kończy się najpóźniej z odbiorem
    status = "zrealizowane" if done_at else "w_realizacji" if jade else "przyjete"
    run_at, _ = next_runs(p.kind, now)
    first = Press.query.filter_by(report_id=r.id).order_by(Press.at).first()
    with_photo = (Press.query.filter(Press.report_id == r.id, Press.photo_id.isnot(None))
                  .order_by(Press.at.desc(), Press.id.desc()).first())
    return jsonify(numer=numer(r.id), status=status, typ=KIND_LABEL.get(first.kind if first else None, "Zgłoszenie"),
                   komentarz=first.note if first else None, osob=r.presses, ai=_ai(with_photo), kurs=run_at.isoformat(),
                   kroki=[{"id": "przyjete", "etykieta": "Przyjęte", "o": r.first_at.isoformat()},
                          {"id": "w_realizacji", "etykieta": "W realizacji", "o": jade.isoformat() if jade else None},
                          {"id": "zrealizowane", "etykieta": "Zrealizowane", "o": done_at.isoformat() if done_at else None}],
                   kosz=kosz_json(p, point_states(now), now), dowod=_dowod(r, done_at), punkty=_punkty(r, p), meta=meta())

# trasy kierowcy rejestrują się na tym samym blueprincie przy imporcie; nazwy dla dotychczasowych importów z app.api_pl
from .api_kierowca import AI_DEPRIORITIZE_CONFIDENCE, _done_ids, powod  # noqa: E402,F401
