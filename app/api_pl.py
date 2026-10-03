"""API perspektyw (panel na koszu, mieszkaniec, kierowca, demo). JSON wszędzie, jeden format błędu {"blad", "kod"}.

Wspólny słownik statusów (audit/AUDYT-UX.md, sekcja 5):
- kosz: poziom 0–100 → `ok` (< 50), `zapelnia_sie` (50–79), `pelny` (≥ 80); osobno `zgloszony` (świeże zgłoszenie mieszkańca);
- zgłoszenie: `przyjete` → `w_realizacji` (kierowca nacisnął „Jadę”) → `zrealizowane` (opróżniono).
Decyzje liczą reguły w kodzie; nic tu nie pyta AI.
"""
import hashlib
import hmac
from datetime import UTC, datetime

from flask import Blueprint, current_app, jsonify, request

from . import clock, db, osrm, photos, rate, traffic
from .geo import distance_m
from .models import Emptying, PhotoAnalysis, Point, Press, Report, StopIssue
from .reports import resolve_reports, record_press
from .routes import DEPOT, next_runs
from .state import current_routes, data_version, point_states

bp = Blueprint("api_pl", __name__, url_prefix="/api")

GEO_RADIUS_M = 150          # zgłoszenie tylko z telefonu najwyżej 150 m od kosza (jak dotąd, decyzja 28)
MAX_ACCURACY_M = 150        # słaby GPS w kamienicy nie blokuje zgłoszenia przy koszu, ale „5 km dokładności” nie wyłącza kontroli
REPORT_GAP_S = 60           # ten sam telefon i ten sam kosz: nie częściej niż raz na minutę
REPORTS_PER_IP_HOUR = 30    # wszystkie kosze z jednego adresu IP (obok limitu per telefon i kosz)
LEVELS = (0, 25, 50, 75, 100)
TYPY = {  # typ zgłoszenia → (rodzaj w silniku, etykieta)
    "przepelniony": ("full", "Przepełniony"),
    "odpady_obok": ("overflow", "Odpady obok kosza"),
    "uszkodzony": ("damaged", "Uszkodzony"),
    "inne": ("other", "Inne"),
}
KIND_LABEL = {kind: label for kind, label in TYPY.values()} | {None: "Przycisk na koszu"}
PROBLEMY = {"no_access": "Nie da się podjechać", "damaged": "Kosz uszkodzony", "blocked": "Zablokowany dojazd",
            "overflow": "Odpady obok kosza"}
FRAKCJE = {"papier": "Papier", "metale_tworzywa": "Metale i tworzywa", "szklo": "Szkło", "bio": "Bio", "zmieszane": "Zmieszane"}


def blad(message, kod, status=400):
    return jsonify(blad=message, kod=kod), status


def meta():
    return {"zegar": clock.now().isoformat(), "syntetyczne": True}


def poziom_stan(level):
    return "pelny" if level >= 80 else "zapelnia_sie" if level >= 50 else "ok"


def qr_token(point_id):
    """Token z kodu QR na panelu kosza: bez niego nie ma zgłoszenia (wymaganie: skan QR + bycie przy koszu)."""
    key = current_app.config["SECRET_KEY"].encode()
    return hmac.new(key, f"kosz:{point_id}".encode(), hashlib.sha256).hexdigest()[:12]


def numer(report_id):
    return f"TF-{report_id:05d}"


def _report_from_nr(nr):
    try:
        return db.session.get(Report, int(str(nr).upper().removeprefix("TF-")))
    except (TypeError, ValueError):
        return None


def _point(value):
    try:
        p = db.session.get(Point, int(value))
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


def _report_texts(reports):
    """Treść zgłoszeń dla kierowcy i panelu: rodzaj, komentarz mieszkańca i analiza zdjęcia (bez danych osobowych)."""
    ids = [r.id for r in reports]
    if not ids:
        return []
    return [{"typ": KIND_LABEL.get(p.kind, "Zgłoszenie"), "komentarz": p.note, "o": p.at.isoformat(), "ai": _ai(p)}
            for p in Press.query.filter(Press.report_id.in_(ids)).order_by(Press.at.desc()).limit(10)]


def prognoza(s, now):
    """Prognoza przekroczenia 85% z silnika (state.crossing) jako krótki tekst dla panelu i kierowcy."""
    if not s.get("crossing"):
        return "Bez przepełnienia w ciągu 24 h"
    if datetime.fromisoformat(s["crossing"]) <= now:
        return f"Powyżej 85% od ok. {s['crossing_label']}"
    return f"Przewidywane 85% ok. {s['crossing_label']}"


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
        out.update(nastepny_odbior=run_at.isoformat(), zgloszenia=_report_texts(reports),
                   zgloszenia_liczba=sum(r.presses for r in reports),
                   oprozniono=last.at.isoformat() if last else None, kierowca_w_drodze=jade is not None,
                   pojemnosc_l=120 if p.kind == "bin" else 1100)
    return out


@bp.get("/zmiany")
def zmiany():
    """Wersja danych do pollingu wszystkich perspektyw (co 3 s): zmienia się po zgłoszeniu, odbiorze i resecie."""
    return jsonify(wersja=data_version(), meta=meta())


@bp.post("/demo/reset")
def demo_reset():
    """Przywraca dane demo do stanu początkowego (jedna rola „Przegląd jury”, bez logowania)."""
    clock.reset()
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


def _accuracy(data):
    try:
        return min(max(float(data.get("dokladnosc") or 0), 0.0), MAX_ACCURACY_M)
    except (TypeError, ValueError):
        return 0.0


@bp.post("/zgloszenia")
def zglos():
    """Zgłoszenie mieszkańca: tylko z tokenem z kodu QR kosza i z położeniem do 150 m od kosza.
    Pola: kosz, typ, qr, lat, lon, dokladnosc, komentarz?, symulacja?, zdjecie? (multipart)."""
    data = request.form if request.files or request.form else (request.get_json(silent=True) or {})
    p = _point(data.get("kosz"))
    if p is None:
        return blad("Nie ma takiego kosza.", "kosz_nie_istnieje", 404)
    if data.get("typ") not in TYPY:
        return blad("Wybierz, co jest nie tak z koszem.", "zly_typ")
    if not hmac.compare_digest(str(data.get("qr") or ""), qr_token(p.id)):
        return blad("Zeskanuj kod QR na koszu, żeby zgłosić problem.", "brak_skanu_qr", 403)
    try:
        lat, lon = float(data.get("lat")), float(data.get("lon"))
    except (TypeError, ValueError):
        return blad("Włącz udostępnianie lokalizacji: zgłoszenie przyjmujemy tylko przy koszu.", "brak_lokalizacji", 403)
    dist = distance_m(lat, lon, p.lat, p.lon)
    if dist - _accuracy(data) > GEO_RADIUS_M:
        return blad(f"Jesteś {round(dist)} m od kosza. Podejdź bliżej (do {GEO_RADIUS_M} m), żeby zgłosić.", "za_daleko", 403)
    raw = mt = None
    upload = request.files.get("zdjecie")
    if upload and upload.filename:  # zdjęcie sprawdzamy przed limitami: zły plik nie zużywa limitu
        raw = upload.read(photos.MAX_BYTES + 1)
        mt, error = photos.validate(raw)
        if not error:
            try:
                raw = photos.strip_metadata(raw, mt)  # bez GPS i danych aparatu, zanim cokolwiek trafi na dysk
            except Exception:  # sygnatura się zgadza, ale obrazu nie da się odczytać
                error = "Nie udało się odczytać zdjęcia. Spróbuj innego pliku."
        if error:
            return blad(error, "zle_zdjecie")
    client = str(data.get("klient") or request.remote_addr)[:64]
    if not rate.hit(f"zgl:{client}:{p.id}", 1, REPORT_GAP_S):
        return blad("To zgłoszenie już dotarło. Kolejne z tego telefonu możesz wysłać za minutę.", "za_czesto", 429)
    if not rate.hit(f"zgl-ip:{request.remote_addr}", REPORTS_PER_IP_HOUR, 3600):
        return blad(f"Z tej sieci wysłano już {REPORTS_PER_IP_HOUR} zgłoszeń w ciągu godziny. Spróbuj później.",
                    "za_duzo_zgloszen", 429)
    note = (data.get("komentarz") or "").strip()[:280] or None
    photo_id = photos.save(p.id, clock.now(), raw, mt, source="resident").id if raw else None
    now = clock.now()
    kind = TYPY[data["typ"]][0]
    report = record_press(p.id, now, ip=request.remote_addr, wall_at=datetime.now(UTC).replace(tzinfo=None),
                          source="qr", kind=kind)
    press = Press.query.filter_by(report_id=report.id).order_by(Press.id.desc()).first()
    press.note, press.photo_id = note, photo_id
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
    if r.resolved_at is None:  # opróżnienie z PWA kierowcy rozstrzyga zgłoszenie od razu (resolve_reports)
        e = Emptying.query.filter(Emptying.point_id == p.id, Emptying.at >= r.first_at, Emptying.at <= now).first()
        done_at = e.at if e else None
    else:
        done_at = r.resolved_at
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
                   kosz=kosz_json(p, point_states(now), now), meta=meta())


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
    if n:
        return f"{n} {_plural(n, 'zgłoszenie', 'zgłoszenia', 'zgłoszeń')} · {k['poziom']}%"
    if k["poziom"] >= 80:
        return f"Pełny {k['poziom']}%"
    if k["prognoza"].startswith("Przewidywane"):
        return k["prognoza"].replace("Przewidywane", "Prognoza")
    return f"Według planu kursu · {k['poziom']}%"


def _priority(k):
    """Kolejność na liście kierowcy: najpierw zgłoszone przez mieszkańców, potem najpełniejsze. Reguła, nie AI."""
    return (not k["zgloszony"], -k["poziom"], k["kolejnosc"])


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
                 w_drodze=bool(reports and _jade_at(p.id, reports[0].first_at)), zrobione=p.id in done)
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
    return jsonify(kurs=fleet["run_at"], etykieta=fleet["run_label"], pojazd=fleet["vehicle"], km=fleet["km"],
                   baza=DEPOT, przystanki=todo + [s for s in stops if s["zrobione"]],
                   postep={"zrobione": len(stops) - len(todo), "wszystkie": len(stops), "pozostalo_min": left_min},
                   linia=out, meta=meta())


@bp.get("/trasa/dojazd")
def dojazd():
    """Przebieg po ulicach z punktu (od=lat,lon) do kosza (do=id): nawigacja prowadzona w aplikacji, bez map zewnętrznych."""
    p = _point(request.args.get("do"))
    if p is None:
        return blad("Nie ma takiego kosza.", "kosz_nie_istnieje", 404)
    try:
        lat, lon = (float(x) for x in request.args.get("od", "").split(","))
    except ValueError:
        lat, lon = DEPOT["lat"], DEPOT["lon"]
    path, approx = osrm.street_path([(lat, lon), (p.lat, p.lon)])
    return jsonify(sciezka=path, przyblizona=approx, meta=meta())


@bp.post("/odbiory")
def odbior():
    """Akcje kierowcy jednym dotknięciem: `jade`, `oprozniono` (z poziomem zastanym), `problem` (z rodzajem)."""
    data = request.form if request.form else (request.get_json(silent=True) or {})
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
        far = None
        try:
            far = max(0, round(distance_m(float(data["lat"]), float(data["lon"]), p.lat, p.lon)))
        except (KeyError, TypeError, ValueError):
            pass
        e = Emptying(point_id=p.id, at=now, level=level, source="crew", far_m=far)
        db.session.add(e)
        resolve_reports(e)
        msg = f"Opróżniono: {p.name}."
    elif akcja == "problem":
        if data.get("problem") not in PROBLEMY:
            return blad("Wybierz, jaki to problem.", "zly_problem")
        db.session.add(StopIssue(point_id=p.id, at=now, kind=data["problem"], note=(data.get("notatka") or "").strip()[:200] or None))
        msg = f"Zgłoszono problem: {PROBLEMY[data['problem']]}."
    else:
        return blad("Nieznana akcja. Dozwolone: jade, oprozniono, problem.", "zla_akcja")
    db.session.commit()
    clock.touch()
    return jsonify(ok=True, komunikat=msg, meta=meta()), 201
