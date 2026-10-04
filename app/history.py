"""Historia syntetyczna panelu miasta: 12 miesięcy odbiorów (Pickup) i zgłoszeń (ReportHistory) do DEMO_NOW.

DANE SYNTETYCZNE, deterministyczne dla seeda. Opowiadają jedną historię:
- sezonowość: latem więcej bio oraz metali i tworzyw, w grudniu więcej papieru i szkła;
- projekty w dzielnicach (PROJECTS) zmieniają sposób odbioru od swojego startu:
  odbiory na żądanie (Stare Miasto od 05.2026; Nowa Huta: czujniki od 07.2026) → mniej odbiorów przy
  niskim zapełnieniu i krótszy czas reakcji; optymalizacja tras (Krowodrza) → mniej km na odbiór;
  edukacja (Podgórze) → mniejszy udział zmieszanych.
- wszystkie punkty mają pełne 12 miesięcy do DEMO_NOW. 72 punkty demo (live=True): model godzinowy jak simulate()
  (opróżnienia o 6:00 i 14:00, altany co 3 dni), ale z wdrożeniami projektów; punkty miasta: model dzienny.
  Symulacja silnika (Emptying/Report ze stałym harmonogramem) to baza porównania „przed i po”, nie dane panelu —
  panel dolicza z niej tylko akcje na żywo (app/dashboard.py).

Masa i koszt odbioru: mass_kg() i cost_pln() — jedna formuła dla historii (Python) i dla Emptying (SQL, app/dashboard.py).
"""
import random
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from functools import lru_cache
from math import log

from sqlalchemy import insert, update

from . import db
from .models import Point, Pickup, Project, ReportHistory
from .simulation import (BIN_EMPTY_HOURS, BIN_HOURLY, DEMO_NOW, FALSE_ALARM_RATE, MAX_LEVEL, PRESS_ABOVE, hour_floor, hourly_multiplier,
                         is_emptying_time, is_nightlife)

HISTORY_SEED = 2026
HISTORY_DAYS = 365
HOUR = timedelta(hours=1)
HISTORY_START = hour_floor(DEMO_NOW) - timedelta(days=HISTORY_DAYS)  # początek danych panelu

# frakcja: (etykieta, gęstość kg/l w pojemniku) — gęstości przybliżone, założenie demo
FRACTIONS = {
    "papier": ("Papier", 0.08),
    "metale_tworzywa": ("Metale i tworzywa sztuczne", 0.03),
    "szklo": ("Szkło", 0.30),
    "bio": ("Bio", 0.45),
    "zmieszane": ("Zmieszane", 0.12),
}
CAPACITY_L = {"bin": 120, "shelter": 1100, "container": 1500}  # kosz i altana jak w karcie punktu (open_api.BIN_CAPACITY_L)

# --- model kosztu (ZAŁOŻENIA DEMO, nie dane MPO) ---
# koszt odbioru = wizyta + km × stawka + tona × opłata; stawki za wizytę i km z app/methodology.py (te same co /metodologia)
COST_PER_TONNE_PLN = 450  # opłata za zagospodarowanie odpadów w instalacji — założenie demo
# km przejazdu na jedną wizytę: kosz i altana z porównania 4 tygodni (stały harmonogram, 1202 km / 3360 wizyt koszy,
# 110 km / 120 wizyt altan), pojemnik do selektywnej zbiórki — założenie (punkty poza centrum, dłuższe dojazdy)
KM_PER_VISIT = {"bin": 0.36, "shelter": 0.92, "container": 1.2}
ROUTE_OPT_KM = 0.75  # optymalizacja tras: −25% km na odbiór od startu projektu


def mass_kg(fill_pct, capacity_l, density):
    """Masa odbioru. Działa na liczbach i na wyrażeniach SQL (te same działania w tej samej kolejności)."""
    return fill_pct * capacity_l * density / 100.0


def cost_pln(mass, km, a):
    """Koszt odbioru wg założeń `a` = methodology.money_assumptions(). Też dla wyrażeń SQL."""
    return a["cost_per_visit"] + km * a["cost_per_km"] + mass * COST_PER_TONNE_PLN / 1000.0


# mnożnik tempa zapełniania wg miesiąca (sty..gru)
SEASON = {
    "papier": [1.0, 0.95, 1.0, 1.0, 1.0, 0.95, 0.9, 0.9, 1.0, 1.05, 1.15, 1.4],
    "metale_tworzywa": [0.85, 0.85, 0.95, 1.05, 1.15, 1.3, 1.35, 1.3, 1.1, 1.0, 0.9, 1.0],
    "szklo": [0.95, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.05, 1.0, 1.0, 1.1, 1.45],
    "bio": [0.55, 0.55, 0.75, 1.0, 1.3, 1.45, 1.5, 1.45, 1.3, 1.15, 0.9, 0.6],
    "zmieszane": [0.95, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.15, 1.05, 1.0, 1.0, 1.1],
}
# punkty demo: symulacja (sierpień–październik) nie ma sezonowości, więc historię skalujemy względem tych miesięcy
LIVE_SEASON_REF = sum(SEASON["zmieszane"][7:10]) / 3

# Projekty: jedno źródło dla tabeli Project i dla efektów w generatorze (lever).
WDROZENIE = date(2026, 5, 1)  # pierwsze wdrożenie Trash Fairy (odbiory na żądanie, Stare Miasto)
PROJECTS = [
    {"slug": "odbiory-na-zadanie-stare-miasto", "name": "Odbiory na żądanie – Stare Miasto", "district": "Stare Miasto",
     "status": "w_realizacji", "start": WDROZENIE, "end": date(2027, 4, 30), "budget": 180_000, "icon": "zap",
     "lever": "on_demand", "metric": "wywozy"},
    {"slug": "pilotaz-czujnikow-nowa-huta", "name": "Pilotaż czujników zapełnienia – Nowa Huta", "district": "Nowa Huta",
     "status": "w_realizacji", "start": date(2026, 7, 1), "end": date(2026, 12, 31), "budget": 420_000, "icon": "radar",
     "lever": "on_demand", "metric": "puste_wywozy"},
    {"slug": "edukacja-segregacji-podgorze", "name": "Edukacja segregacji – Podgórze", "district": "Podgórze",
     "status": "w_realizacji", "start": date(2026, 3, 1), "end": date(2027, 2, 28), "budget": 95_000,
     "icon": "graduation-cap", "lever": "education", "metric": "udzial_zmieszanych"},
    {"slug": "optymalizacja-tras-krowodrza", "name": "Optymalizacja tras – Krowodrza", "district": "Krowodrza",
     "status": "w_realizacji", "start": date(2026, 8, 1), "end": date(2026, 12, 31), "budget": 140_000, "icon": "route",
     "lever": "route_opt", "metric": "km_na_wywoz"},
    {"slug": "przyciski-zgloszen-debniki", "name": "Przyciski zgłoszeń mieszkańców – Dębniki", "district": "Dębniki",
     "status": "planowany", "start": date(2026, 11, 1), "end": date(2027, 6, 30), "budget": 260_000, "icon": "bell-ring",
     "lever": None, "metric": "czas_reakcji"},
]

OD_PICK_LEVEL = 70  # odbiór na żądanie: kurs przy ≥70% albo gdy szacunek przekroczy 85% przed kolejnym kursem
OD_THRESHOLD = 85
REACTION_H = {False: 9.0, True: 3.0}  # średni czas reakcji na zgłoszenie (h): stały harmonogram / odbiory na żądanie
EDU_MIXED, EDU_RECYCLED, EDU_RAMP_DAYS = 0.8, 1.2, 60
ROUTE_OPT_SPREAD = 0.1  # km na odbiór po optymalizacji: ROUTE_OPT_KM ± 0,1 (różne trasy)
CITY_EVERY_DAYS = {"papier": 7, "metale_tworzywa": 7, "szklo": 14, "bio": 3}  # stały harmonogram pojemników
CITY_REPORTS = {"uszkodzony": 0.0015, "odpady_obok": 0.003, "inne": 0.001}  # na punkt i dzień


@lru_cache(maxsize=None)
def lever_since(district, lever, d):
    """Czy w dzielnicy działa dźwignia projektu w dniu `d` (start ≤ d ≤ koniec)."""
    return any(p["district"] == district and p["lever"] == lever and p["start"] <= d <= p["end"] for p in PROJECTS)


def _education(district, d):
    for p in PROJECTS:
        if p["district"] == district and p["lever"] == "education" and p["start"] <= d <= p["end"]:
            return min(1.0, (d - p["start"]).days / EDU_RAMP_DAYS)
    return 0.0


@lru_cache(maxsize=None)
def fraction_factor(district, fraction, d):
    """Sezon × efekt edukacji (mniej zmieszanych, więcej selektywnych)."""
    edu = _education(district, d)
    shift = (EDU_MIXED if fraction == "zmieszane" else EDU_RECYCLED) - 1
    return SEASON[fraction][d.month - 1] * (1 + shift * edu)


# Odległość telefonu ekipy od kosza przy potwierdzeniu odbioru (ZAŁOŻENIE DEMO, nie dane MPO): zwykle rozrzut GPS przy
# koszu — rozkład log-normalny z medianą FAR_MEDIAN_M (σ = 0,6: ok. 95% poniżej 35 m); w FAR_ANOMALY_SHARE odbiorów
# potwierdzenie „z kabiny” albo hurtem po kursie — równomiernie FAR_ANOMALY_M od kosza. Anomalia na panelu: > 150 m
# (dashboard.ANOMALY_M). Osobny RNG (seed:far), więc pozostałe liczby historii nie zmieniają się.
FAR_MEDIAN_M, FAR_SIGMA = 12, 0.6
FAR_ANOMALY_SHARE, FAR_ANOMALY_M = 0.03, (160, 900)


def far_m(rng):
    if rng.random() < FAR_ANOMALY_SHARE:
        return rng.randint(*FAR_ANOMALY_M)
    return min(150, round(rng.lognormvariate(log(FAR_MEDIAN_M), FAR_SIGMA)))


def _reaction(rng, on_demand):
    return timedelta(hours=rng.lognormvariate(log(REACTION_H[on_demand]) - 0.125, 0.5))


class _Out:
    def __init__(self, a, far_rng):
        self.a, self.far_rng, self.pickups, self.reports = a, far_rng, [], []

    def pickup(self, p, at, fill, on_demand, rng):
        km = KM_PER_VISIT[p.kind]
        if lever_since(p.district, "route_opt", at.date()):
            km *= rng.uniform(ROUTE_OPT_KM - ROUTE_OPT_SPREAD, ROUTE_OPT_KM + ROUTE_OPT_SPREAD)
        m = mass_kg(fill, CAPACITY_L[p.kind], FRACTIONS[p.fraction][1])
        self.pickups.append({"point_id": p.id, "at": at, "fraction": p.fraction, "mass_kg": round(m, 2),
                             "cost_pln": round(cost_pln(m, km, self.a), 2), "km": round(km, 3), "fill_pct": int(fill),
                             "on_demand": on_demand, "far_m": far_m(self.far_rng)})

    def report(self, p, created, resolved, kind="przepelniony"):
        self.reports.append({"point_id": p.id, "created_at": created, "resolved_at": resolved, "kind": kind})


def _live_point(p, rng, start, end, sim_start, out):
    """Punkt demo, godzina po godzinie (jak simulate()): opróżnienia z harmonogramu; przy odbiorach na żądanie
    kurs, gdy szacunek przekroczy 85% przed kolejnym kursem, albo na zgłoszenie. Zgłoszenie: poziom > 80% (jak naciśnięcia w symulacji) i rzadkie fałszywe."""
    night = is_nightlife(p)
    # profil dnia z simulation.hourly_multiplier, policzony raz: [dzień roboczy / weekend][godzina]
    table = [[hourly_multiplier(p, base.replace(hour=h), night) for h in range(24)]
             for base in (datetime(2026, 1, 5), datetime(2026, 1, 10))]
    pt = _plain(p)
    is_bin, rate, rand = p.kind == "bin", p.base_rate, rng.random
    level, at, waiting, due = rng.uniform(0, 30), start, [], None
    while at < end:
        h, mults = at.hour, table[at.weekday() >= 5]
        on_demand = is_bin and lever_since(pt.district, "on_demand", at.date())
        season = SEASON["zmieszane"][at.month - 1] / LIVE_SEASON_REF
        slot = h in BIN_EMPTY_HOURS if is_bin else is_emptying_time(p, at, sim_start)
        if slot and on_demand:  # jak Trash Fairy: kurs, gdy szacunek przekroczy 85% przed kolejnym kursem
            gap = 8 if h == BIN_EMPTY_HOURS[0] else 16
            ahead = sum(mults[(h + k) % 24] for k in range(gap)) * rate * season
            slot = level >= OD_PICK_LEVEL or level + ahead > OD_THRESHOLD
        if slot or due is not None and at >= due:
            out.pickup(pt, at, min(100, round(level / 25) * 25), on_demand, rng)
            for created in waiting:
                out.report(pt, created, at)
            level, waiting, due = 0.0, [], None
        mult = mults[h]
        level = min(MAX_LEVEL, level + rate * mult * season * (0.6 + 0.8 * rand()))  # szum ±40% (jak gauss σ≈0,23)
        if (level > PRESS_ABOVE and rand() < min(0.8, 0.25 * mult)) or rand() < FALSE_ALARM_RATE * mult:
            created = at + timedelta(minutes=rng.randrange(60))
            if on_demand and due is None:
                due = hour_floor(created + _reaction(rng, True)) + HOUR  # kurs na zgłoszenie w kolejnej pełnej godzinie
            if created < end:
                waiting.append(created)
        at += HOUR
    for created in waiting:  # zgłoszenia jeszcze otwarte w chwili DEMO_NOW
        out.report(pt, created, None)


def _plain(p):
    """Kopia pól punktu bez ORM (gorące pętle generatora: atrybuty ORM są wolne)."""
    return SimpleNamespace(id=p.id, kind=p.kind, district=p.district, fraction=p.fraction, base_rate=p.base_rate)


def _city_point(p, rng, start, end, out):
    """Punkt miasta, dzień po dniu: odbiór rano wg harmonogramu albo (na żądanie) gdy jutro by się przepełnił."""
    p = _plain(p)
    every = 1 if p.kind == "bin" and p.district == "Stare Miasto" else 2 if p.kind == "bin" else CITY_EVERY_DAYS[p.fraction]
    offset, level, since = rng.randrange(every), rng.uniform(0, 30), 0
    day = start.date()
    hour_weights = BIN_HOURLY
    while day <= end.date():
        on_demand = lever_since(p.district, "on_demand", day)
        daily = p.base_rate * 24 * fraction_factor(p.district, p.fraction, day)
        morning = datetime.combine(day, datetime.min.time()) + timedelta(hours=6, minutes=rng.randrange(180))
        if on_demand:
            pick = level >= 85 or level + daily > 100 or since >= 3 * every
        else:
            pick = (day - start.date()).days % every == offset
        if pick and start <= morning <= end:
            out.pickup(p, morning, min(100, round(level)), on_demand, rng)
            level, since = 0.0, 0
        weekend = 1.3 if day.weekday() >= 5 and p.kind == "bin" else 1.0
        new = level + daily * weekend * max(0.0, rng.gauss(1.0, 0.25))
        if level <= 100 < new and rng.random() < 0.6:
            created = morning + timedelta(hours=1 + 14 * (100 - level) / (new - level), minutes=rng.randrange(60))
            resolved = created + _reaction(rng, on_demand)
            if created <= end:
                out.report(p, created, resolved if resolved <= end else None)
                if on_demand and resolved <= end:  # odbiór na żądanie: kurs do zgłoszenia
                    out.pickup(p, resolved, 100, True, rng)
                    new, since = 0.0, -1
        for kind, rate in CITY_REPORTS.items():
            if rng.random() < rate * (3 if kind == "odpady_obok" and new > 90 else 1):
                created = datetime.combine(day, datetime.min.time()) + timedelta(
                    hours=rng.choices(range(24), weights=hour_weights)[0], minutes=rng.randrange(60))
                resolved = created + _reaction(rng, on_demand)
                if start <= created <= end:
                    out.report(p, created, resolved if resolved <= end else None, kind)
        level, since, day = min(130.0, new), since + 1, day + timedelta(days=1)
    return min(100, round(level))


def generate_history(seed=HISTORY_SEED, now=DEMO_NOW, sim_start=None):
    """Zastępuje historię panelu miasta i projekty. Bez punktów miasta (np. testy silnika demo) nic nie generuje."""
    from .methodology import money_assumptions  # import lokalny: methodology importuje cały silnik
    for model in (Pickup, ReportHistory, Project):
        db.session.query(model).delete()
    city = Point.query.filter(Point.live.is_(False)).order_by(Point.osm_id).all()
    if not city:
        db.session.commit()
        return {"pickups": 0, "reports": 0, "projects": 0}
    end = hour_floor(now)
    start = end - timedelta(days=HISTORY_DAYS)
    sim_start = sim_start or end  # tylko wyrównanie cyklu altan (co 3 dni) z symulacją
    out = _Out(money_assumptions(), random.Random(f"{seed}:far"))
    for p in Point.live_query().order_by(Point.osm_id):
        _live_point(p, random.Random(f"{seed}:{p.osm_id}"), start, now, sim_start, out)
    snapshot = [{"id": p.id, "snapshot_fill": _city_point(p, random.Random(f"{seed}:{p.osm_id}"), start, now, out)}
                for p in city]
    for model, rows in ((Pickup, out.pickups), (ReportHistory, out.reports)):
        if rows:
            db.session.execute(insert(model.__table__), rows)  # Core executemany: szybciej niż ORM bulk
    db.session.execute(update(Point), snapshot)
    db.session.commit()
    from .dashboard import project_effect  # efekty liczone z właśnie zapisanej historii (SQL)
    for spec in PROJECTS:
        db.session.add(Project(**project_row(spec, now)))
    db.session.flush()
    for pr in Project.query:
        pr.effect_value, pr.effect_label = project_effect(pr, now)
    db.session.commit()
    return {"pickups": len(out.pickups), "reports": len(out.reports), "projects": len(PROJECTS)}


def project_row(spec, now):
    """Postęp i wydatki z kalendarza projektu (deterministycznie); efekt dopisuje generate_history."""
    if spec["status"] == "zakonczony":
        progress, spent_share = 100, 0.93  # zamknięty poniżej budżetu
    elif spec["status"] == "planowany":
        progress, spent_share = 0, 0.0
    else:
        total = (spec["end"] - spec["start"]).days
        progress = max(1, min(99, round(100 * (now.date() - spec["start"]).days / total)))
        spent_share = progress / 100 * 0.97
    return {"slug": spec["slug"], "name": spec["name"], "district": spec["district"], "status": spec["status"],
            "progress_pct": progress, "budget_pln": float(spec["budget"]),
            "spent_pln": float(round(spec["budget"] * spent_share, -2)), "start": spec["start"], "end": spec["end"],
            "metric": spec["metric"], "icon": spec["icon"], "effect_label": "", "effect_value": None}
