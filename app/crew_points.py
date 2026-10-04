"""Punkty zaangażowania ekipy — reguła w kodzie za potwierdzone sygnały, nie za liczbę kliknięć.

+1 za odbiór ze zdjęciem potwierdzonym regułą, +3 za zgłoszenie podrzucenia odpadów ze zdjęciem, które je pokazuje,
+5 za sugestię „Tu przydałby się kosz” (StopIssue need_bin) zgodną z danymi, a za dzikie wysypiska reguły z app/wysypiska.py
(crew_dump_points: +3 zgłoszenie ze zdjęciem zweryfikowane lub uprzątnięte, +2 uprzątnięcie). AI tylko opisuje zdjęcia; czy sygnał jest
potwierdzony, decyduje reguła. Dowód dotyczy kosza, nie osoby. O premii decyduje regulamin MPO — system daje dowód.
"""
from datetime import timedelta

from sqlalchemy import func, select

from . import db
from .dashboard import pl_num, plural, reports
from .geo import distance_m
from .models import PhotoAnalysis, Point, StopIssue
from .photos import VERIFY_MIN_CONFIDENCE, discrepancy
from .wysypiska import CREW_PTS_CLEARED, CREW_PTS_PHOTO, crew_dump_points

ROUTE = "K-07"  # ponytail: w demo jedna trasa, wszystkie akcje ekipy idą na nią; przy wielu trasach przypisanie z planu tras
WINDOW_DAYS = 30
PTS_PHOTO, PTS_DUMPING, PTS_NEED_BIN = 1, 3, 5
PHOTO_MATCH = timedelta(minutes=30)  # zdjęcie ekipy należy do jej zgłoszenia przy tym samym koszu w tym oknie
NEED_BIN_RADIUS_M = 100
NEED_BIN_REPORTS = 2  # … albo tyle zgłoszeń mieszkańców w WINDOW_DAYS przy koszu w tym promieniu
NEED_BIN_RECS = {"compactor", "bigger", "more_often"}  # rekomendacje z danych, które mówią „za mała pojemność”
RULES = [
    {"punkty": PTS_PHOTO, "za": f"Odbiór ze zdjęciem potwierdzonym regułą (pewność analizy co najmniej "
                               f"{pl_num(VERIFY_MIN_CONFIDENCE, 2)}, poziom zgodny z tym, co wybrała ekipa)"},
    {"punkty": PTS_DUMPING, "za": "Zgłoszenie odpadów obok kosza ze zdjęciem, które je pokazuje"},
    {"punkty": PTS_NEED_BIN, "za": f"Sugestia „Tu przydałby się kosz” zgodna z danymi: w promieniu {NEED_BIN_RADIUS_M} m kosz "
                                   f"z rekomendacją większej pojemności albo z co najmniej {NEED_BIN_REPORTS} zgłoszeniami "
                                   f"mieszkańców w {WINDOW_DAYS} dni"},
    {"punkty": CREW_PTS_PHOTO, "za": "Zgłoszenie dzikiego wysypiska ze zdjęciem, gdy wysypisko jest zweryfikowane albo uprzątnięte"},
    {"punkty": CREW_PTS_CLEARED, "za": "Dzikie wysypisko uprzątnięte"},
]


def confirmed_photo(pa):
    """Zdjęcie potwierdza odbiór: analiza gotowa, pewność ≥ progu weryfikacji zdjęć, poziom zgodny z kliknięciem ekipy."""
    return pa.status == "done" and (pa.confidence or 0) >= VERIFY_MIN_CONFIDENCE and not discrepancy(pa)


def shows_dumping(pa):
    return pa.status == "done" and bool(pa.overflow_outside or "household_bag" in (pa.misuse or []))


def need_bin_suggestions(now, recs):
    """Sugestie kierowców „Tu przydałby się kosz” z ostatnich WINDOW_DAYS, każda z oceną reguły i powodem.
    `recs` = recommendations.recommendations(now)."""
    since = now - timedelta(days=WINDOW_DAYS)
    issues = (StopIssue.query.filter(StopIssue.kind == "need_bin", StopIssue.at > since, StopIssue.at <= now)
              .order_by(StopIssue.at, StopIssue.id).all())  # od najstarszej: punkty tylko za pierwszą przy danym koszu
    if not issues:
        return []
    z = reports(now)
    busy = dict(db.session.execute(select(z.c.point_id, func.count()).where(z.c.created_at > since)
                                   .group_by(z.c.point_id).having(func.count() >= NEED_BIN_REPORTS)).all())
    rec = {r["point_id"]: r["label"] for r in recs if r["type"] in NEED_BIN_RECS}
    pts = {p.id: p for p in Point.query.filter(Point.id.in_(set(busy) | set(rec) | {i.point_id for i in issues}))}
    # rekomendacje przed zgłoszeniami: mocniejszy dowód
    evidence = ([(pid, f"{label} przy „{pts[pid].name}” (rekomendacja z danych)") for pid, label in rec.items()]
                + [(pid, f"{n} {plural(n, 'zgłoszenie', 'zgłoszenia', 'zgłoszeń')} mieszkańców w {WINDOW_DAYS} dni "
                         f"przy „{pts[pid].name}”") for pid, n in busy.items()])
    out, scored = [], set()
    for i in issues:
        p = pts[i.point_id]
        why = next((text for pid, text in evidence
                    if distance_m(p.lat, p.lon, pts[pid].lat, pts[pid].lon) <= NEED_BIN_RADIUS_M), None)
        repeat = why is not None and p.id in scored
        if why:
            scored.add(p.id)
        out.append({"kosz_id": p.id, "kosz": p.name, "adres": p.address or "", "dzielnica": p.district,
                    "data": i.at.isoformat(), "notatka": i.note or "", "potwierdzona": why is not None,
                    "punkty": PTS_NEED_BIN if why and not repeat else 0,
                    "powod": (f"W promieniu {NEED_BIN_RADIUS_M} m: {why}."
                              + (" Punkty przyznane już za wcześniejszą sugestię przy tym koszu." if repeat else "")) if why else
                             f"Brak potwierdzenia w danych: w promieniu {NEED_BIN_RADIUS_M} m nie ma rekomendacji większej "
                             f"pojemności ani {NEED_BIN_REPORTS} zgłoszeń mieszkańców w {WINDOW_DAYS} dni."})
    return out[::-1]  # najnowsze pierwsze


def crew_points(now, suggestions):
    """Punkty ekipy trasy ROUTE z ostatnich WINDOW_DAYS: suma i pozycje (każda z dowodem). `suggestions` z need_bin_suggestions.
    Najwyżej jedna pozycja na kosz, rodzaj i dzień (sugestia kosza: jedna na kosz w oknie), a jedno zdjęcie potwierdza
    najwyżej jedno zgłoszenie — powtórzone kliknięcia nie dają punktów."""
    since = now - timedelta(days=WINDOW_DAYS)
    photos = PhotoAnalysis.query.filter(PhotoAnalysis.source == "crew", PhotoAnalysis.at > since - PHOTO_MATCH,
                                        PhotoAnalysis.at <= now).order_by(PhotoAnalysis.at, PhotoAnalysis.id).all()
    dumps = (StopIssue.query.filter(StopIssue.kind == "overflow", StopIssue.at > since, StopIssue.at <= now)
             .order_by(StopIssue.at, StopIssue.id).all())
    items = {}  # (kosz, rodzaj, dzień) → pierwsza pozycja
    for pa in photos:
        if pa.at > since and pa.crew_level is not None and confirmed_photo(pa):
            items.setdefault((pa.point_id, "odbior_ze_zdjeciem", pa.at.date()),
                             (pa.point_id, pa.at, "odbior_ze_zdjeciem", PTS_PHOTO, "Odbiór potwierdzony zdjęciem"))
    used = set()
    for d in dumps:
        key = (d.point_id, "podrzucenie_ze_zdjeciem", d.at.date())
        pa = None if key in items else next((pa for pa in photos if pa.id not in used and pa.point_id == d.point_id
                                             and abs(pa.at - d.at) <= PHOTO_MATCH and shows_dumping(pa)), None)
        if pa:
            used.add(pa.id)
            items[key] = (d.point_id, d.at, "podrzucenie_ze_zdjeciem", PTS_DUMPING, "Odpady obok kosza, zdjęcie to pokazuje")
    names = {p.id: p.name for p in Point.query.filter(Point.id.in_({k[0] for k in items}))} if items else {}
    out = [{"kosz_id": pid, "kosz": names.get(pid, ""), "data": at.isoformat(), "rodzaj": kind, "punkty": pts, "opis": text}
           for pid, at, kind, pts, text in items.values()]
    out += [{"kosz_id": s["kosz_id"], "kosz": s["kosz"], "data": s["data"], "rodzaj": "sugestia_kosza",
             "punkty": s["punkty"], "opis": s["powod"]} for s in suggestions if s["punkty"]]
    out += crew_dump_points(now, WINDOW_DAYS)
    out.sort(key=lambda x: x["data"], reverse=True)
    return {"trasa": ROUTE, "okres_dni": WINDOW_DAYS, "suma": sum(x["punkty"] for x in out), "pozycje": out, "zasady": RULES,
            "uwaga": "Punkty za potwierdzone sygnały, nie za liczbę kliknięć. Dowód dotyczy kosza, nie osoby; "
                     "o premii decyduje regulamin MPO."}
