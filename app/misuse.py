"""Nadużycia i powiązanie altana → kosz (koncepcja, sekcja 6.5) — reguły w kodzie.

AI tylko rozpoznaje na zdjęciu „worek z domowymi śmieciami”. Powiązanie tworzy reguła: worki domowe w koszu
ulicznym w promieniu 200 m od altany, którą szacunek pokazywał jako przepełnioną (>100%) w ostatnich 48 h.
Bez automatycznych zgłoszeń do Straży Miejskiej.
"""
from datetime import timedelta

from .forecast import EST, point_series
from .geo import distance_m
from .models import PhotoAnalysis, Point
from .photos import MISUSE_LABELS, discrepancy

LINK_RADIUS_M = 200
SHELTER_WINDOW = timedelta(hours=48)
ANALYSIS_WINDOW = timedelta(hours=48)
OVERFLOW_LEVEL = 100


def latest_analyses(now):
    """{point_id: (ostatnia analiza dowolna, ostatnia udana)} z okna 48 h przed `now`."""
    out = {}
    for pa in (PhotoAnalysis.query.filter(PhotoAnalysis.at <= now, PhotoAnalysis.at > now - ANALYSIS_WINDOW)
               .order_by(PhotoAnalysis.at, PhotoAnalysis.id)):
        last, last_ok = out.get(pa.point_id, (None, None))
        out[pa.point_id] = (pa, pa if pa.status == "done" else last_ok)
    return out


def overflowing_shelters(now, shelters):
    """{shelter_id: najwyższy szacunek} dla altan przepełnionych wg prognozy w ostatnich 48 h."""
    hours = int(SHELTER_WINDOW.total_seconds() // 3600)
    out = {}
    for s in shelters:
        peak = max((row[EST] or 0 for row in point_series(s, now, hours_back=hours) if row[0] <= now), default=0)
        if peak > OVERFLOW_LEVEL:
            out[s.id] = peak
    return out


def household_bag_links(bins_with_bags, shelters, overflowing):
    """[(bin, shelter)] dla worków domowych w promieniu 200 m od przepełnionej altany."""
    return [(b, s) for b in bins_with_bags for s in shelters
            if s.id in overflowing and distance_m(b.lat, b.lon, s.lat, s.lon) <= LINK_RADIUS_M]


def misuse_overview(now):
    """Wszystko, czego potrzebuje panel: plakietki nadużyć, flagi rozbieżności, linie i rekomendacje."""
    points = {p.id: p for p in Point.live_query()}
    analyses = latest_analyses(now)
    per_point = {}
    bins_with_bags = []
    for pid, (last, last_ok) in analyses.items():
        info = {"photo_error": last.error if last.status == "error" else None,
                "photo_pending": last.status == "pending"}
        if last_ok:
            info.update(misuse=[MISUSE_LABELS[m] for m in last_ok.misuse or []], photo_note=last_ok.note,
                        photo_level=last_ok.fill_level, photo_at=last_ok.at.isoformat(),
                        photo_flag=discrepancy(last_ok))
            if "household_bag" in (last_ok.misuse or []) and points[pid].kind == "bin":
                bins_with_bags.append(points[pid])
        per_point[pid] = info

    shelters = [p for p in points.values() if p.kind == "shelter"]
    overflowing = overflowing_shelters(now, shelters) if bins_with_bags else {}
    links = household_bag_links(bins_with_bags, shelters, overflowing)
    recommendations = {}
    for b, s in links:
        recommendations[s.id] = (f"Zwiększ częstotliwość odbioru: altana była przepełniona w ostatnich 48 h "
                                 f"(szacunek do {round(overflowing[s.id])}%), a w koszach obok są worki z domowymi śmieciami.")
    return {
        "points": per_point,
        "links": [{"bin_id": b.id, "shelter_id": s.id, "bin": [b.lat, b.lon], "shelter": [s.lat, s.lon],
                   "label": f"{b.name} ← {s.name}: worki domowe 200 m od przepełnionej altany"} for b, s in links],
        "recommendations": recommendations,
    }
