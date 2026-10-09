"""Wspólna część API perspektyw (app/api_pl.py, app/api_kierowca.py): blueprint, jeden format błędu {"blad", "kod"},
słowniki typów zgłoszeń i opis kosza (kosz_json) dla panelu, mieszkańca, kierowcy i dyspozytora.

Wspólny słownik statusów (audit/AUDYT-UX.md, sekcja 5):
- kosz: poziom 0–100 → `ok` (< 50), `zapelnia_sie` (50–79), `pelny` (≥ 80); osobno `zgloszony` (świeże zgłoszenie mieszkańca);
- zgłoszenie: `przyjete` → `w_realizacji` (kierowca nacisnął „Jadę”) → `zrealizowane` (opróżniono).
Decyzje liczą reguły w kodzie; nic tu nie pyta AI.
"""
import os
from datetime import UTC, datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from . import clock, db, photos, residents
from .crew_points import confirmed_photo
from .models import Emptying, PhotoAnalysis, Point, PointAward, Press, Report, Resident, StopIssue
from .routes import next_runs
from .state import current_routes

bp = Blueprint("api_pl", __name__, url_prefix="/api")  # nazwa „api_pl”: endpointy api_pl.* bez zmian

TYPY = {  # typ zgłoszenia → (rodzaj w silniku, etykieta)
    "przepelniony": ("full", "Przepełniony"),
    "odpady_obok": ("overflow", "Odpady obok kosza"),
    "uszkodzony": ("damaged", "Uszkodzony"),
    "inne": ("other", "Inne"),
}
KIND_LABEL = {kind: label for kind, label in TYPY.values()} | {None: "Przycisk na koszu"}
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
