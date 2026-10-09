"""API kierowcy: trasa na najbliższy kurs z priorytetem przystanków, dojazd po ulicach, odbiory („Jadę”, „Opróżniono”
ze zdjęciem kosza, problem) i publiczne zdjęcie odbioru. Rejestruje trasy na blueprincie „api_pl” z app/api_wspolne.py."""
import math

from flask import jsonify, request, send_file

from . import clock, db, osrm, photos, traffic
from .api_wspolne import (_json_body, _jade_at, _open_reports, _point, blad, bp, crew_photo_required, crew_photo_status,
                          kosz_json, meta, public_crew_photo)
from .geo import distance_m
from .models import Emptying, PhotoAnalysis, Point, Press, StopIssue
from .reports import resolve_reports
from .routes import DEPOT
from .state import current_routes, point_states

LEVELS = (0, 25, 50, 75, 100)
PROBLEMY = {"no_access": "Nie da się podjechać", "damaged": "Kosz uszkodzony", "blocked": "Zablokowany dojazd",
            "overflow": "Odpady obok kosza", "need_bin": "Tu przydałby się kosz"}
AI_DEPRIORITIZE_CONFIDENCE = 0.8  # zdjęcie „W porządku” z tą pewnością obniża priorytet zgłoszenia; nigdy go nie odrzuca
SKIPPED_LIMIT = 30          # ile pominiętych koszy pokazujemy kierowcy (najpełniejsze)


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
