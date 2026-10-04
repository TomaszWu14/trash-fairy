"""API i ekran „Zgłoś dzikie wysypisko” oraz „Twoje punkty” mieszkańca demo. Reguły: app/wysypiska.py."""
import math
import re
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request, send_file

from . import clock, db, photos, rate, residents
from . import wysypiska as wd
from .api_pl import _json_body, blad, meta

bp = Blueprint("wysypiska", __name__)

GAP_S = 120         # jeden telefon: jedno zgłoszenie wysypiska na 2 minuty
PER_IP_HOUR = 20    # jedna sieć: 20 zgłoszeń wysypisk na godzinę


@bp.get("/wysypisko")
def page():
    """Formularz: mapa z pinezką, rodzaj, liczba worków, zdjęcie. ?ekipa=1 = zgłoszenie kierowcy MPO."""
    ekipa = request.args.get("ekipa") == "1"
    return render_template("ui/wysypisko.html", kinds=wd.KINDS, ekipa=ekipa, nr=None, krakow=wd.KRAKOW,
                           perspective="kierowca" if ekipa else "mieszkaniec")


@bp.get("/wysypisko/<nr>")
def status_page(nr):
    """Status zgłoszenia; ?ekipa=1 dokłada przycisk „Uprzątnięte” dla ekipy MPO."""
    ekipa = request.args.get("ekipa") == "1"
    return render_template("ui/wysypisko.html", kinds=wd.KINDS, ekipa=ekipa, nr=nr.upper(), krakow=wd.KRAKOW,
                           perspective="kierowca" if ekipa else "mieszkaniec")


def _coord(value):
    try:
        v = float(value)
    except (TypeError, ValueError, OverflowError):  # OverflowError: ogromna liczba całkowita z JSON
        return None
    return v if math.isfinite(v) else None


@bp.post("/api/wysypiska")
def create():
    """Pola (multipart albo JSON): lat, lon, rodzaj (wiele), ilosc (1–100, brak = „nie wiem”), komentarz?, zdjecie?,
    klient (id telefonu), zrodlo ("ekipa" dla kierowcy), konto ("demo" = mieszkanka demo z perspektywy mieszkańca)."""
    form = bool(request.files or request.form)
    data = request.form if form else _json_body()
    lat, lon = _coord(data.get("lat")), _coord(data.get("lon"))
    if lat is None or lon is None:
        return blad("Zaznacz miejsce na mapie albo użyj swojego położenia.", "brak_polozenia")
    if not wd.in_krakow(lat, lon):
        return blad("To miejsce jest poza Krakowem. Zgłaszamy tylko wysypiska w granicach miasta.", "poza_krakowem")
    kinds = data.getlist("rodzaj") if form else data.get("rodzaj")
    kinds = [kinds] if isinstance(kinds, str) else kinds
    if not isinstance(kinds, list) or not kinds or not all(isinstance(k, str) and k in wd.KINDS for k in kinds):
        return blad("Wybierz, co leży: co najmniej jeden rodzaj odpadów z listy.", "zly_rodzaj")
    qty = data.get("ilosc")
    if qty in (None, "", "nie_wiem"):
        qty = None
    else:  # tylko cyfry: odrzuca 7.9, true, Infinity i 1e999 z JSON zamiast obcinać albo rzucać OverflowError
        qty = int(s) if re.fullmatch(r"\d{1,3}", s := str(qty)) else 0
        if not 1 <= qty <= wd.QTY_MAX:
            return blad(f"Liczba worków lub sztuk: od 1 do {wd.QTY_MAX} albo „nie wiem”.", "zla_ilosc")
    raw, mt, error = photos.read_upload(request.files.get("zdjecie"))  # przed limitami: zły plik nie zużywa limitu
    if error:
        return blad(error, "zle_zdjecie")
    client = wd.client_hash(str(data.get("klient") or request.remote_addr)[:64])
    if not rate.hit(f"wd:{client}", 1, GAP_S):
        return blad("Twoje zgłoszenie już dotarło. Kolejne z tego telefonu możesz wysłać za 2 minuty.", "za_czesto", 429)
    if not rate.hit(f"wd-ip:{request.remote_addr}", PER_IP_HOUR, 3600):
        return blad(f"Z tej sieci wysłano już {PER_IP_HOUR} zgłoszeń wysypisk w ciągu godziny. Spróbuj później.",
                    "za_duzo_zgloszen", 429)
    crew = data.get("zrodlo") == "ekipa"
    resident_id = residents.demo_resident().id if not crew and data.get("konto") == "demo" else None
    note = str(data.get("komentarz") or "").strip()[:280] or None
    r, g = wd.create(clock.now(), lat, lon, list(dict.fromkeys(kinds)), qty, note, raw, mt,
                     "crew" if crew else "resident", client, resident_id)
    clock.touch()
    if raw:  # AI tylko opisuje zdjęcie; status nadaje reguła (wysypiska.ai_status)
        wd.analyze_in_background(r.id)
        db.session.refresh(r)
    rows = wd.group_rows(g)
    st = wd.state(g, rows)
    return jsonify(numer=wd.numer(g.id), dolaczone=g.id != r.id, status=st, etykieta=wd.STATUS[st],
                   uzasadnienie=wd.reason(st, rows), zdjecie=bool(raw), meta=meta()), 201


@bp.get("/api/wysypiska")
def overview():
    """Dashboard: otwarte i uprzątnięte wysypiska z 90 dni (bez komentarzy i bez zdjęć z osobami) i miejsca z drabinką."""
    return jsonify(**wd.overview(clock.now()), meta=meta())


def _get(nr):
    r = wd.from_nr(nr)
    return r, (None if r else blad("Nie znaleźliśmy zgłoszenia o tym numerze.", "wysypisko_nie_istnieje", 404))


@bp.get("/api/wysypiska/<nr>")
def detail(nr):
    r, err = _get(nr)
    return err or jsonify(wysypisko=wd.detail(r, clock.now()), meta=meta())


@bp.get("/api/wysypiska/<nr>/zdjecie")
def photo(nr):
    """Zdjęcie tylko po analizie AI bez osób i tablic; inaczej 404 (jak brak zdjęcia)."""
    r, err = _get(nr)
    if err or not wd.public_photo(r) or not Path(r.photo_path).exists():
        return blad("Nie ma publicznego zdjęcia tego zgłoszenia.", "brak_zdjecia", 404)
    return send_file(r.photo_path, mimetype=r.media_type, max_age=3600)


@bp.post("/api/wysypiska/<nr>/uprzatnieto")
def cleared(nr):
    """Ekipa MPO: wysypisko uprzątnięte (status końcowy z czasem zegara demo). Bez logowania, jak akcje kierowcy;
    zapisujemy telefon (klient), żeby uprzątnięcie z telefonu zgłaszającego nie dawało mu punktów."""
    r, err = _get(nr)
    if err:
        return err
    g = db.session.get(type(r), r.parent_id) if r.parent_id else r
    if g.cleared_at:
        return blad("To wysypisko jest już oznaczone jako uprzątnięte.", "juz_uprzatniete", 409)
    g.cleared_at, g.cleared_by = clock.now(), wd.client_hash(str(_json_body().get("klient") or request.remote_addr)[:64])
    db.session.commit()
    clock.touch()
    return jsonify(ok=True, komunikat=f"Uprzątnięte: {wd.numer(g.id)}.", uprzatnieto=g.cleared_at.isoformat(), meta=meta())


@bp.get("/api/mieszkaniec/punkty")
def resident_points():
    """Punkty konta demo „Anna K.”: tylko za potwierdzone zgłoszenia; katalog nagród to propozycja dla miasta."""
    return jsonify(**residents.points_summary(residents.demo_resident()), meta=meta())
