"""Rekomendacje inwestycyjne (koncepcja, sekcja 6.8) — reguły na odczytach z ostatnich 4 tygodni.

Źródło: poziom zastany przy opróżnieniu (Emptying.level), czyli dane, które MPO naprawdę ma od ekip.
Poziom 100% przy opróżnieniu = przepełniony tego dnia. Ukrytej „prawdy” z symulatora tu nie czytamy.
"""
from collections import defaultdict
from datetime import timedelta

from .models import Emptying, Point

WINDOW = timedelta(weeks=4)
DAYS_PER_MONTH = 30
COMPACTOR_FACTOR = 5  # kompaktor zgniata odpady ok. 5× (Mr Fill deklaruje do 7×) — założenie, patrz Metodologia
OVERFLOW_COMPACTOR = 0.5  # przepełniony w >50% dni …
MIN_PER_DAY_COMPACTOR = 2  # … mimo opróżniania 2× dziennie → kompaktor
OVERFLOW_BIGGER_BIN = 0.2  # przepełniony w 20–50% dni → większy kosz
RARELY_HALF_FULL = 0.2  # <20% opróżnień przy poziomie ≥50% → można rzadziej
MIN_READINGS = 10


def point_stats(now):
    """{point_id: {"days", "overflow_days", "readings", "half_full", "per_day"}} z okna 4 tygodni."""
    rows = defaultdict(list)
    for pid, at, level in (Emptying.query.with_entities(Emptying.point_id, Emptying.at, Emptying.level)
                           .filter(Emptying.at <= now, Emptying.at > now - WINDOW)):
        rows[pid].append((at, level))
    out = {}
    for pid, readings in rows.items():
        days = {at.date() for at, _ in readings}
        out[pid] = {
            "days": len(days),
            "overflow_days": len({at.date() for at, level in readings if level >= 100}),
            "readings": len(readings),
            "half_full": sum(level >= 50 for _, level in readings),
            "per_day": len(readings) / len(days),
        }
    return out


def recommend(kind, s):
    """(typ, etykieta, uzasadnienie, efekt) albo None — reguły z tabeli w sekcji 6.8."""
    if s["readings"] < MIN_READINGS:
        return None
    share = s["overflow_days"] / s["days"]
    visits_month = round(s["per_day"] * DAYS_PER_MONTH)
    why_overflow = f"przepełniony w {s['overflow_days']} z {s['days']} dni"
    if kind == "bin" and share > OVERFLOW_COMPACTOR and round(s["per_day"]) >= MIN_PER_DAY_COMPACTOR:  # brzegi okna to niepełne dni
        saved = visits_month - round(visits_month / COMPACTOR_FACTOR)
        return ("compactor", "kompaktor", f"{why_overflow}, mimo opróżniania {s['per_day']:.0f}× dziennie",
                f"−{saved} wizyt w miesiącu i mniej przepełnień (pojemność ×{COMPACTOR_FACTOR})")
    if share > OVERFLOW_COMPACTOR and kind == "shelter":
        return ("more_often", "częstszy odbiór altany", why_overflow, "mniej worków w koszach ulicznych obok")
    if share >= OVERFLOW_BIGGER_BIN:
        return ("bigger", "większy kosz" if kind == "bin" else "większy pojemnik w altanie", why_overflow,
                "mniej dni z przepełnieniem przy tych samych kursach")
    if s["half_full"] / s["readings"] < RARELY_HALF_FULL:
        saved = visits_month - round(visits_month / 2)
        return ("less_often", "można opróżniać rzadziej",
                f"{s['half_full'] or 'żadne'} z {s['readings']} opróżnień przy poziomie ≥50%", f"−{saved} wizyt w miesiącu")
    return None


ORDER = {"shelter_intervention": 0, "compactor": 1, "more_often": 2, "bigger": 3, "less_often": 4}


def recommendations(now, shelter_interventions=None):
    """Lista rekomendacji, od najważniejszych. `shelter_interventions`: {shelter_id: tekst} z reguły altana → kosz."""
    stats = point_stats(now)
    out = []
    for p in Point.query.order_by(Point.id):
        if shelter_interventions and p.id in shelter_interventions:
            out.append({"point_id": p.id, "name": p.name, "kind": p.kind, "type": "shelter_intervention",
                        "label": "interwencja przy altanie", "reason": "worki domowe w koszach ulicznych obok",
                        "impact": "mniej przepełnionych koszy ulicznych w promieniu 200 m"})
            continue
        r = recommend(p.kind, stats[p.id]) if p.id in stats else None
        if r:
            out.append({"point_id": p.id, "name": p.name, "kind": p.kind, "type": r[0], "label": r[1],
                        "reason": r[2], "impact": r[3]})
    return sorted(out, key=lambda r: ORDER[r["type"]])
