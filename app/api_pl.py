"""API perspektyw (panel kosza, mieszkaniec, kierowca, demo). JSON wszędzie, jeden format błędu {"blad", "kod"}.

Wspólny słownik statusów (audit/AUDYT-UX.md, sekcja 5):
- kosz: poziom 0–100 → `ok` (< 50), `zapelnia_sie` (50–79), `pelny` (≥ 80); osobno `zgloszony` (świeże zgłoszenie mieszkańca);
- zgłoszenie: `przyjete` → `w_realizacji` (kierowca nacisnął „Jadę”) → `zrealizowane` (opróżniono).
Decyzje liczą reguły w kodzie; nic tu nie pyta AI.
"""
import hashlib
import hmac
import math
import os
import time
from datetime import UTC, datetime, timedelta, timezone
from datetime import time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import Blueprint, current_app, jsonify, request, send_file

from . import clock, db, osrm, photos, rate, residents, traffic
from .crew_points import confirmed_photo
from .devices_api import device_token
from .geo import distance_m
from .models import DeviceInfo, Emptying, PhotoAnalysis, Point, PointAward, Press, Report, Resident, StopIssue
from .reports import resolve_reports, record_press
from .routes import DEPOT, next_runs
from .state import current_routes, data_version, point_states

bp = Blueprint("api_pl", __name__, url_prefix="/api")

try:
    WARSAW = ZoneInfo("Europe/Warsaw")  # doba kodu QR kosza = doba kalendarzowa w Krakowie
except ZoneInfoNotFoundError:  # obraz bez tzdata: doba w UTC+1, kod zmienia się najwyżej godzinę „za wcześnie” latem
    WARSAW = timezone(timedelta(hours=1))
QR_GRACE_S = 3600           # wczorajszy kod działa jeszcze godzinę po północy: skan tuż przed północą nie przepada
BUTTON_PRESSES_PER_MIN = 3  # przycisk na panelu: najwyżej 3 zgłoszenia na minutę z jednego kosza
REPORT_GAP_S = 60           # ten sam telefon i ten sam kosz: nie częściej niż raz na minutę
REPORTS_PER_IP_HOUR = 200   # wszystkie kosze z jednego IP: wysoko, bo sala HackYeah i jury wychodzą przez jeden NAT
RESET_GAP_S = 20            # ręczny reset demo najwyżej raz na 20 s (wszystkie workery)
LEVELS = (0, 25, 50, 75, 100)
TYPY = {  # typ zgłoszenia → (rodzaj w silniku, etykieta)
    "przepelniony": ("full", "Przepełniony"),
    "odpady_obok": ("overflow", "Odpady obok kosza"),
    "uszkodzony": ("damaged", "Uszkodzony"),
    "inne": ("other", "Inne"),
}
KIND_LABEL = {kind: label for kind, label in TYPY.values()} | {None: "Przycisk na koszu"}
PROBLEMY = {"no_access": "Nie da się podjechać", "damaged": "Kosz uszkodzony", "blocked": "Zablokowany dojazd",
            "overflow": "Odpady obok kosza", "need_bin": "Tu przydałby się kosz"}
AI_DEPRIORITIZE_CONFIDENCE = 0.8  # zdjęcie „W porządku” z tą pewnością obniża priorytet zgłoszenia; nigdy go nie odrzuca
SKIPPED_LIMIT = 30          # ile pominiętych koszy pokazujemy kierowcy (najpełniejsze)
FRAKCJE = {"papier": "Papier", "metale_tworzywa": "Metale i tworzywa", "szklo": "Szkło", "bio": "Bio", "zmieszane": "Zmieszane"}


def _json_body():
    """Ciało JSON jako słownik; tablica, liczba albo zły JSON → {} (walidacja pól zwróci 400 zamiast 500)."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def blad(message, kod, status=400):
    return jsonify(blad=message, kod=kod), status


def meta():
    return {"zegar": clock.now().isoformat(), "syntetyczne": True}


def poziom_stan(level):
    return "pelny" if level >= 80 else "zapelnia_sie" if level >= 50 else "ok"


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


def numer(report_id):
    return f"TF-{report_id:05d}"


def _report_from_nr(nr):
    try:
        rid = int(str(nr).upper().removeprefix("TF-"))
        return db.session.get(Report, rid) if 0 < rid < 2**31 else None
    except (TypeError, ValueError):
        return None


def _point(value):
    try:
        pid = int(value)
        p = db.session.get(Point, pid) if 0 < pid < 2**31 else None
    except (TypeError, ValueError):
        return None
    return p if p is not None and getattr(p, "live", True) else None


def _address(p):
    tags = p.osm_tags or {}
    if getattr(p, "address", None):
        return p.address
    if tags.get("addr:street"):
        return f"{tags['addr:street']} {tags.get('addr:housenumber', '')}".strip()
    return {"Rynek": "Rynek Główny i okolice", "Kazimierz": "Kazimierz", "Grzegórzki": "Grzegórzki"}.get(p.area, p.area)


def _last_emptying(point_id, now):
    return (Emptying.query.filter(Emptying.point_id == point_id, Emptying.at <= now)
            .order_by(Emptying.at.desc(), Emptying.id.desc()).first())


def _open_reports(point_id, now):
    last = _last_emptying(point_id, now)
    q = Report.query.filter(Report.point_id == point_id, Report.hit.is_(None), Report.first_at <= now)
    if last:
        q = q.filter(Report.first_at >= last.at)
    return q.order_by(Report.first_at).all()


def _jade_at(point_id, since):
    i = (StopIssue.query.filter(StopIssue.point_id == point_id, StopIssue.kind == "jade", StopIssue.at >= since)
         .order_by(StopIssue.at).first())
    return i.at if i else None


def _ai(press):
    """Analiza AI zdjęcia dołączonego do zgłoszenia jako status weryfikacji (reguła: photos.verification); None bez zdjęcia."""
    if press is None or press.photo_id is None:
        return None
    return photos.verification(db.session.get(PhotoAnalysis, press.photo_id), press.kind)


def _ai_ok(reports):
    """Pewność AI (0–1), że na najnowszym zdjęciu ze zgłoszeń kosz jest w porządku, gdy ≥ AI_DEPRIORITIZE_CONFIDENCE;
    inaczej None. Reguła w kodzie: wynik tylko przesuwa kosz niżej na liście kierowcy, zgłoszenie zostaje otwarte."""
    if not reports:
        return None
    press = (Press.query.filter(Press.report_id.in_([r.id for r in reports]), Press.photo_id.isnot(None))
             .order_by(Press.at.desc(), Press.id.desc()).first())
    pa = db.session.get(PhotoAnalysis, press.photo_id) if press else None
    if (pa is None or pa.status != "done" or not pa.bin_visible or pa.condition != "w_porzadku"
            or (pa.confidence or 0) < AI_DEPRIORITIZE_CONFIDENCE):
        return None
    return round(pa.confidence, 2)


def crew_photo_required():
    """Pilotaż: odbiór tylko ze zdjęciem kosza (env REQUIRE_CREW_PHOTO=1; domyślnie zdjęcie opcjonalne)."""
    flag = current_app.config.get("REQUIRE_CREW_PHOTO", os.environ.get("REQUIRE_CREW_PHOTO", ""))
    return str(flag).strip().lower() in ("1", "true", "tak", "yes")


def _crew_photo(point_id, at):
    """Zdjęcie kosza od ekipy zrobione przy odbiorze o czasie `at` (zapisane z tym samym czasem zegara demo)."""
    return (PhotoAnalysis.query.filter_by(point_id=point_id, source="crew", at=at)
            .order_by(PhotoAnalysis.id.desc()).first())


def crew_photo_status(pa):
    """Dowód odbioru dla kierowcy: reguła crew_points.confirmed_photo, AI tylko opisuje zdjęcie. None = bez zdjęcia."""
    if pa is None:
        return None
    if pa.status == "pending" and datetime.now(UTC).replace(tzinfo=None) - pa.wall_at <= photos.PENDING_MAX:
        return {"status": "w_toku", "etykieta": "Sprawdzamy zdjęcie", "id": pa.id}
    if confirmed_photo(pa):
        return {"status": "potwierdzone", "etykieta": "Potwierdzone zdjęciem", "id": pa.id}
    return {"status": "do_weryfikacji", "etykieta": "Do weryfikacji", "id": pa.id}


def public_crew_photo(pa):
    """Zdjęcie ekipy pokazujemy mieszkańcowi tylko potwierdzone regułą i gdy analiza wprost nie wykryła osób ani tablic."""
    return (pa is not None and pa.source == "crew" and confirmed_photo(pa) and pa.people is False
            and bool(pa.photo_path) and Path(pa.photo_path).exists())


def _dowod(r, done_at):
    """Dowód wykonania usługi przy zgłoszeniu: zdjęcie kosza od ekipy przy odbiorze, które rozstrzygnęło zgłoszenie."""
    if done_at is None:
        return None
    pa = _crew_photo(r.point_id, done_at)
    if pa is None:
        return {"etykieta": "Zrealizowane, bez zdjęcia ekipy", "potwierdzone": False, "zdjecie": None}
    if not confirmed_photo(pa):
        return {"etykieta": "Zdjęcie ekipy w weryfikacji", "potwierdzone": False, "zdjecie": None}
    return {"etykieta": "Zrealizowane, potwierdzone zdjęciem ekipy", "potwierdzone": True,
            "zdjecie": f"/api/odbiory/zdjecie/{pa.id}" if public_crew_photo(pa) else None}


def _punkty(r, p):
    """Punkty programu mieszkańców za trafne zgłoszenie (residents.POINTS) i czy konto demo już je dostało."""
    awarded = (db.session.query(PointAward.id).join(Resident, Resident.id == PointAward.resident_id)
               .filter(PointAward.report_id == r.id, Resident.nick == residents.DEMO_RESIDENT[0]).first())
    return {"za_trafne": residents.POINTS.get(p.kind, residents.POINTS["bin"]), "przyznane": awarded is not None}


def _route_status(p, now):
    """Czy kosz jedzie na najbliższy kurs swojej floty i dlaczego (tak albo nie). Reguły z app/routes.py."""
    fleet = next(f for f in current_routes(now) if f["kind"] == p.kind)
    stop = next((s for r in [fleet, *fleet["extra_routes"]] for s in r["stops"] if s["id"] == p.id), None)
    skip = next((s for s in fleet["skipped"] if s["id"] == p.id), None)
    return {"na_trasie": stop is not None, "powod": stop["reason"] if stop else skip["reason"] if skip else None}


def _report_texts(reports):
    """Treść zgłoszeń dla kierowcy i panelu: rodzaj, komentarz mieszkańca i analiza zdjęcia (bez danych osobowych)."""
    ids = [r.id for r in reports]
    if not ids:
        return []
    out = [{"typ": KIND_LABEL.get(p.kind, "Zgłoszenie"), "komentarz": p.note, "o": p.at.isoformat(), "ai": _ai(p)}
           for p in Press.query.filter(Press.report_id.in_(ids)).order_by(Press.at.desc()).limit(10)]
    # zgłoszenia bez wierszy Press (seed, symulacja): wpis zastępczy, żeby lista nie przeczyła zgloszenia_liczba
    with_press = {rid for (rid,) in db.session.query(Press.report_id).filter(Press.report_id.in_(ids)).distinct()}
    out += [{"typ": KIND_LABEL[None], "komentarz": None, "o": r.first_at.isoformat(), "ai": None, "osob": r.presses}
            for r in reports if r.id not in with_press]
    return sorted(out, key=lambda z: z["o"], reverse=True)[:10]


def prognoza(s, now):
    """Prognoza przekroczenia 85% z silnika (state.crossing) jako krótki tekst dla panelu i kierowcy (J-30): przechodzień
    pyta „kiedy trzeba opróżnić”, a próg 85% zostaje w regułach, nie na ekranie."""
    if not s.get("crossing"):
        return "Bez przepełnienia w ciągu 24 h"
    if datetime.fromisoformat(s["crossing"]) <= now:
        return f"Do opróżnienia od ok. {s['crossing_label']}"
    return f"Do opróżnienia ok. {s['crossing_label']}"


def kosz_json(p, states, now, detail=False):
    s = states.get(p.id, {})
    level = round(s.get("value") or 0)
    out = {"id": p.id, "nazwa": p.name, "adres": _address(p), "dzielnica": getattr(p, "district", None) or "Stare Miasto",
           "frakcja": getattr(p, "fraction", None) or "zmieszane", "rodzaj": "kosz uliczny" if p.kind == "bin" else "altana",
           "lat": p.lat, "lon": p.lon, "poziom": level, "stan": poziom_stan(level), "zgloszony": bool(s.get("fresh")),
           "prognoza": prognoza(s, now), "prognoza_o": s.get("crossing")}
    if detail:
        run_at, _ = next_runs(p.kind, now)
        reports = _open_reports(p.id, now)
        last = _last_emptying(p.id, now)
        jade = _jade_at(p.id, reports[0].first_at) if reports else None
        route = _route_status(p, now)
        # J-08: termin odbioru tylko, gdy ten kosz jedzie na najbliższy kurs; inaczej None (panel: „gdy będzie potrzebny”)
        out.update(nastepny_odbior=run_at.isoformat() if route["na_trasie"] else None, zgloszenia=_report_texts(reports),
                   zgloszenia_liczba=sum(r.presses for r in reports),
                   oprozniono=last.at.isoformat() if last else None, kierowca_w_drodze=jade is not None,
                   pojemnosc_l=120 if p.kind == "bin" else 1100, trasa=route,
                   wymaga_zdjecia=crew_photo_required(),
                   zdjecie_odbioru=crew_photo_status(_crew_photo(p.id, last.at) if last and last.source == "crew" else None))
    return out


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


# ---------- kierowca ----------
def _done_ids(kind):
    """Kosze opróżnione przez kierowcę od resetu demo (postęp trasy)."""
    return {pid for (pid,) in db.session.query(Emptying.point_id).join(Point, Point.id == Emptying.point_id)
            .filter(Emptying.source == "crew", Point.kind == kind).distinct()}


def _plural(n, one, few, many):
    return one if n == 1 else few if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else many


def powod(k):
    """Krótkie „dlaczego tu” przy przystanku kierowcy; ta sama kolejność co _priority. Reguła, nie AI."""
    n = k["zgloszenia_liczba"]
    if k.get("ai_w_porzadku"):
        conf = f"{k['ai_w_porzadku']:.2f}".replace(".", ",")
        return f"Zdjęcie: kosz w porządku (AI {conf}) · sprawdź przy okazji"
    if n:
        return f"{n} {_plural(n, 'zgłoszenie', 'zgłoszenia', 'zgłoszeń')}"  # procent stoi obok w wierszu
    if k["poziom"] >= 80:
        return "Pełny"
    if k["prognoza"].startswith("Do opróżnienia"):
        return k["prognoza"]
    return "Według planu kursu"


def _priority(k):
    """Kolejność na liście kierowcy: najpierw zgłoszone przez mieszkańców (te ze zdjęciem „w porządku” wg AI na końcu
    zgłoszonych), potem najpełniejsze. Reguła, nie AI: analiza zdjęcia tylko obniża priorytet, nigdy nie odrzuca."""
    return (not k["zgloszony"], bool(k.get("ai_w_porzadku")), -k["poziom"], k["kolejnosc"])


@bp.get("/trasa")
def trasa():
    """Trasa floty koszy na najbliższy kurs: przystanki po priorytecie, postęp i szacowany czas do końca."""
    now = clock.now()
    states = point_states(now)
    fleet = next(f for f in current_routes(now) if f["kind"] == "bin")
    done = _done_ids("bin")
    stops = []
    for n, s in enumerate(fleet["stops"], 1):
        p = db.session.get(Point, s["id"])
        k = kosz_json(p, states, now)
        reports = _open_reports(p.id, now)
        k.update(kolejnosc=n, zgloszenia_liczba=sum(r.presses for r in reports),
                 w_drodze=bool(reports and _jade_at(p.id, reports[0].first_at)), zrobione=p.id in done,
                 ai_w_porzadku=_ai_ok(reports))
        k["powod"] = powod(k)
        stops.append(k)
    for pid in done - {s["id"] for s in stops}:  # opróżnione wypadają z planu: zostają na liście jako zrobione
        p = db.session.get(Point, pid)
        stops.append({**kosz_json(p, states, now), "kolejnosc": len(stops) + 1, "zgloszenia_liczba": 0, "w_drodze": False, "zrobione": True})
    todo = [s for s in stops if not s["zrobione"]]
    todo.sort(key=_priority)
    service_min = 3  # min na przystanek: podjazd, opróżnienie, odjazd (założenie demo)
    drive_min = traffic.drive_min(fleet["km"], traffic.city_ratio())
    left_min = round(drive_min * (len(todo) / max(1, len(stops))) + service_min * len(todo))
    out, _ = osrm.street_path(fleet["path"][:-1])
    skipped = [{"id": s["id"], "nazwa": s["name"], "poziom": s["level"], "powod": s["reason"]}
               for s in fleet["skipped"] if s["id"] not in done]  # już posortowane: najpełniejsze pierwsze
    return jsonify(kurs=fleet["run_at"], etykieta=fleet["run_label"], pojazd=fleet["vehicle"], km=fleet["km"],
                   baza=DEPOT, przystanki=todo + [s for s in stops if s["zrobione"]],
                   postep={"zrobione": len(stops) - len(todo), "wszystkie": len(stops), "pozostalo_min": left_min},
                   pojazdy=fleet["vehicles"], pominiete=skipped[:SKIPPED_LIMIT], pominiete_liczba=len(skipped),
                   linia=out, meta=meta())


@bp.get("/trasa/dojazd")
def dojazd():
    """Przebieg po ulicach z punktu (od=lat,lon) do kosza (do=id): nawigacja prowadzona w aplikacji, bez map zewnętrznych."""
    p = _point(request.args.get("do"))
    if p is None:
        return blad("Nie ma takiego kosza.", "kosz_nie_istnieje", 404)
    try:
        lat, lon = (round(float(x), 4) for x in request.args.get("od", "").split(","))  # ~10 m: cache OSRM nie rośnie od szumu GPS
        if not (math.isfinite(lat) and math.isfinite(lon)):
            raise ValueError
    except ValueError:
        lat, lon = DEPOT["lat"], DEPOT["lon"]
    path, approx = osrm.street_path([(lat, lon), (p.lat, p.lon)])
    return jsonify(sciezka=path, przyblizona=approx, meta=meta())


@bp.post("/odbiory")
def odbior():
    """Akcje kierowcy jednym dotknięciem: `jade`, `oprozniono` (z poziomem zastanym, opcjonalnie zdjęcie kosza w multipart
    jako dowód odbioru; w pilotażu REQUIRE_CREW_PHOTO obowiązkowe), `problem` (z rodzajem, także `need_bin`)."""
    data = request.form if request.form or request.files else _json_body()
    p = _point(data.get("kosz"))
    if p is None:
        return blad("Nie ma takiego kosza.", "kosz_nie_istnieje", 404)
    akcja, now = data.get("akcja"), clock.now()
    if akcja == "jade":
        db.session.add(StopIssue(point_id=p.id, at=now, kind="jade"))
        msg = f"Jedziesz do: {p.name}."
    elif akcja == "oprozniono":
        try:
            level = int(data.get("poziom"))
        except (TypeError, ValueError):
            level = None
        if level not in LEVELS:
            return blad("Wybierz, ile było w koszu: 0, 25, 50, 75 albo 100%.", "zly_poziom")
        raw, mt, error = photos.read_upload(request.files.get("zdjecie"))  # walidacja i usunięcie EXIF przed zapisem
        if error:
            return blad(error, "zle_zdjecie")
        if raw is None and crew_photo_required():
            return blad("W pilotażu odbiór wymaga zdjęcia kosza.", "brak_zdjecia")
        far = None
        try:
            far = max(0, round(distance_m(float(data["lat"]), float(data["lon"]), p.lat, p.lon)))
        except (KeyError, TypeError, ValueError):
            pass
        e = Emptying(point_id=p.id, at=now, level=level, source="crew", far_m=far)
        db.session.add(e)
        # „Jadę” zrealizowane: bez tego kolejne zgłoszenie z tą samą minutą zegara demo od razu było „w realizacji”
        StopIssue.query.filter(StopIssue.point_id == p.id, StopIssue.kind == "jade").delete(synchronize_session=False)
        resolve_reports(e)
        msg = f"Opróżniono: {p.name}."
        if raw:  # dowód dotyczy kosza; AI tylko opisuje zdjęcie, potwierdzenie liczy reguła (crew_points.confirmed_photo)
            db.session.commit()
            pa = photos.save(p.id, now, raw, mt, crew_level=level, source="crew")
            photos.analyze_in_background(pa.id)
            clock.touch()
            return jsonify(ok=True, komunikat=msg + " Zdjęcie kosza zapisane.", zdjecie=crew_photo_status(pa), meta=meta()), 201
    elif akcja == "problem":
        if not isinstance(data.get("problem"), str) or data["problem"] not in PROBLEMY:
            return blad("Wybierz, jaki to problem.", "zly_problem")
        db.session.add(StopIssue(point_id=p.id, at=now, kind=data["problem"], note=str(data.get("notatka") or "").strip()[:200] or None))
        msg = ("Zapisano sugestię: tu przydałby się kosz. Sprawdzimy ją w danych." if data["problem"] == "need_bin"
               else f"Zgłoszono problem: {PROBLEMY[data['problem']]}.")
    else:
        return blad("Nieznana akcja. Dozwolone: jade, oprozniono, problem.", "zla_akcja")
    db.session.commit()
    clock.touch()
    return jsonify(ok=True, komunikat=msg, meta=meta()), 201


@bp.get("/odbiory/zdjecie/<int:photo_id>")
def zdjecie_odbioru(photo_id):
    """Zdjęcie kosza od ekipy (dowód odbioru) dla mieszkańca: tylko potwierdzone regułą i bez osób i tablic; inaczej 404."""
    pa = db.session.get(PhotoAnalysis, photo_id) if 0 < photo_id < 2**31 else None
    if not public_crew_photo(pa):
        return blad("Nie ma publicznego zdjęcia tego odbioru.", "brak_zdjecia", 404)
    return send_file(pa.photo_path, mimetype=pa.media_type, max_age=3600)
