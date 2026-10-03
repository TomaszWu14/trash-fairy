"""Agregacje panelu miasta — wyłącznie zapytania GROUP BY w bazie.

Odbiory = Pickup (historia syntetyczna, wszystkie punkty, 12 miesięcy) UNION ALL Emptying z source="crew" (kierowca
na żywo; masa i koszt tą samą formułą z app/history.py). Zgłoszenia = ReportHistory UNION ALL Report z naciśnięciem
na żywo (Press.wall_at IS NOT NULL). Symulowane Emptying/Report (stały harmonogram — baza porównania silnika) się NIE
liczą; akcje z demo od razu zmieniają liczniki panelu.
"""
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta

from sqlalchemy import Integer, case, cast, extract, func, literal, select, union_all

from . import db
from .history import CAPACITY_L, FRACTIONS, KM_PER_VISIT, WDROZENIE, cost_pln, mass_kg
from .methodology import money_assumptions
from .models import Emptying, Pickup, Point, Press, Report, ReportHistory

EMPTY_BELOW = 50  # odbiór przy zapełnieniu poniżej 50% = „pusty wywóz” (jak EMPTY_VISIT_BELOW w porównaniu)
BASELINE = (date(2025, 11, 1), WDROZENIE)  # plan = średnia dzienna z miesięcy przed pierwszym wdrożeniem


@dataclass(frozen=True)
class Filters:
    od: datetime
    do: datetime  # wyłącznie (pół-otwarty przedział)
    district: str | None = None
    fraction: str | None = None

    def previous(self):
        span = self.do - self.od
        return replace(self, od=self.od - span, do=self.od)

    @property
    def days(self):
        return (self.do - self.od).total_seconds() / 86400


# --- SQL zależny od dialektu (SQLite lokalnie i w testach, PostgreSQL na produkcji) ---

def _pg():
    return db.engine.dialect.name == "postgresql"


def month_of(col):
    return func.to_char(col, "YYYY-MM") if _pg() else func.strftime("%Y-%m", col)


def hours_between(a, b):
    return extract("epoch", b - a) / 3600.0 if _pg() else (func.julianday(b) - func.julianday(a)) * 24.0


def dow_of(col):
    """0 = niedziela (oba dialekty)."""
    return cast(extract("dow", col), Integer) if _pg() else cast(func.strftime("%w", col), Integer)


def hour_of(col):
    return cast(extract("hour", col), Integer) if _pg() else cast(func.strftime("%H", col), Integer)


def _by(mapping, col):
    return case(*[(col == k, literal(float(v))) for k, v in mapping.items()], else_=literal(0.0))


# --- źródła danych ---

def pickups(now):
    """Wszystkie odbiory do `now`: kolumny point_id, district, fraction, at, mass_kg, cost_pln, km, fill_pct, on_demand."""
    a = money_assumptions()
    km = _by(KM_PER_VISIT, Point.kind)
    mass = mass_kg(Emptying.level, _by(CAPACITY_L, Point.kind), _by({k: v[1] for k, v in FRACTIONS.items()}, Point.fraction))
    live = (select(Emptying.point_id, Point.district, Point.fraction, Emptying.at, mass.label("mass_kg"),
                   cost_pln(mass, km, a).label("cost_pln"), km.label("km"), Emptying.level.label("fill_pct"),
                   literal(1).label("on_demand"))
            .join(Point, Point.id == Emptying.point_id).where(Emptying.source == "crew", Emptying.at <= now))
    hist = (select(Pickup.point_id, Point.district, Pickup.fraction, Pickup.at, Pickup.mass_kg, Pickup.cost_pln, Pickup.km,
                   Pickup.fill_pct, case((Pickup.on_demand, 1), else_=0).label("on_demand"))
            .join(Point, Point.id == Pickup.point_id).where(Pickup.at <= now))
    return union_all(hist, live).subquery("odbiory")


def reports(now):
    """Wszystkie zgłoszenia do `now`: point_id, district, fraction, created_at, resolved_at (None = otwarte), kind."""
    hist = (select(ReportHistory.point_id, Point.district, Point.fraction, ReportHistory.created_at,
                   case((ReportHistory.resolved_at <= now, ReportHistory.resolved_at)).label("resolved_at"), ReportHistory.kind)
            .join(Point, Point.id == ReportHistory.point_id).where(ReportHistory.created_at <= now))
    live = (select(Report.point_id, Point.district, Point.fraction, Report.first_at.label("created_at"),
                   case((Report.resolved_at <= now, Report.resolved_at)).label("resolved_at"), literal("przepelniony").label("kind"))
            .join(Point, Point.id == Report.point_id)
            .where(Report.first_at <= now, Report.id.in_(select(Press.report_id).where(Press.wall_at.isnot(None)))))
    return union_all(hist, live).subquery("zgloszenia")


def _where(q, sub, f, time_col):
    q = q.where(time_col >= f.od, time_col < f.do)
    if isinstance(f.district, tuple):  # grupa dzielnic (grupa kontrolna planu)
        q = q.where(sub.c.district.in_(f.district))
    elif f.district:
        q = q.where(sub.c.district == f.district)
    if f.fraction:
        q = q.where(sub.c.fraction == f.fraction)
    return q


def _pickup_cols(o):
    return (func.count().label("wywozy"), func.coalesce(func.sum(o.c.cost_pln), 0).label("koszt"),
            func.coalesce(func.sum(o.c.mass_kg), 0).label("masa"), func.coalesce(func.sum(o.c.km), 0).label("km"),
            func.avg(o.c.fill_pct).label("zapelnienie"),
            func.coalesce(func.sum(case((o.c.fill_pct < EMPTY_BELOW, 1), else_=0)), 0).label("puste"),
            func.coalesce(func.sum(case((o.c.fraction == "zmieszane", o.c.mass_kg), else_=0)), 0).label("masa_zmieszane"))


def _report_cols(z):
    return (func.count().label("zgloszenia"), func.avg(hours_between(z.c.created_at, z.c.resolved_at)).label("czas_reakcji"))


def pickup_totals(f, now):
    o = pickups(now)
    return dict(db.session.execute(_where(select(*_pickup_cols(o)), o, f, o.c.at)).mappings().one())


def totals(f, now):
    """Sumy odbiorów i zgłoszeń w przedziale filtrów."""
    z = reports(now)
    r = db.session.execute(_where(select(*_report_cols(z)), z, f, z.c.created_at)).mappings().one()
    return {**pickup_totals(f, now), **r}


def monthly(f, now, months, with_reports=True):
    """{miesiąc 'YYYY-MM': sumy} dla miesięcy `months` (filtr dzielnicy/frakcji z `f`, czas z listy miesięcy)."""
    first = datetime.strptime(months[0], "%Y-%m")
    mf = replace(f, od=first, do=now + timedelta(seconds=1))
    o, z = pickups(now), reports(now)
    om, zm = month_of(o.c.at), month_of(z.c.created_at)
    out = {m: {"wywozy": 0, "koszt": 0, "masa": 0, "km": 0, "zapelnienie": None, "puste": 0, "masa_zmieszane": 0,
               "zgloszenia": 0, "czas_reakcji": None} for m in months}
    for row in db.session.execute(_where(select(om.label("m"), *_pickup_cols(o)), o, mf, o.c.at).group_by(om)).mappings():
        if row["m"] in out:
            out[row["m"]].update({k: v for k, v in row.items() if k != "m"})
    if with_reports:
        for row in db.session.execute(_where(select(zm.label("m"), *_report_cols(z)), z, mf, z.c.created_at)
                                      .group_by(zm)).mappings():
            if row["m"] in out:
                out[row["m"]].update({k: v for k, v in row.items() if k != "m"})
    return out


# --- plan ---
# Plan = dzienna średnia z miesięcy przed pierwszym wdrożeniem (BASELINE) dla tych samych filtrów × sezonowość grupy
# kontrolnej (dzielnice, w których żaden projekt jeszcze nie działał): plan(okres) = baza/dzień × dni × indeks, gdzie
# indeks = (kontrola/dzień w okresie) / (kontrola/dzień w BASELINE). Planujemy kursy i km; oszczędności = kursy × stawka
# + km × stawka (jak methodology.money), a koszt wg planu = koszt rzeczywisty + oszczędności — masy odpadów system
# nie zmniejsza, więc opłata za tony jest w obu taka sama.
PLAN_KEYS = ("wywozy", "km")


def control_districts(now):
    from .history import PROJECTS
    active = {p["district"] for p in PROJECTS if p["lever"] and p["start"] <= now.date()}
    present = {d for (d,) in db.session.query(Point.district).distinct() if d}
    return tuple(sorted(present - active))


def _per_day(t, days):
    return {k: float(t[k] or 0) / days if days else 0.0 for k in PLAN_KEYS}


def _baseline(f):
    return replace(f, od=datetime.combine(BASELINE[0], datetime.min.time()),
                   do=datetime.combine(BASELINE[1], datetime.min.time()))


def _index(ctrl_now, ctrl_base):
    return {k: ctrl_now[k] / ctrl_base[k] if ctrl_now[k] and ctrl_base[k] else 1.0 for k in PLAN_KEYS}


def plan(f, now):
    """{wywozy, km} wg planu w przedziale `f`."""
    b = _baseline(f)
    base = _per_day(pickup_totals(b, now), b.days)
    ctrl = replace(f, district=control_districts(now))
    idx = _index(_per_day(pickup_totals(ctrl, now), f.days), _per_day(pickup_totals(_baseline(ctrl), now), b.days))
    return {k: base[k] * idx[k] * f.days for k in PLAN_KEYS}


def monthly_plan(f, now, months):
    """{miesiąc: {wywozy, km}} wg planu (indeks grupy kontrolnej liczony miesiąc po miesiącu)."""
    b = _baseline(f)
    base = _per_day(pickup_totals(b, now), b.days)
    ctrl = replace(f, district=control_districts(now))
    ctrl_base = _per_day(pickup_totals(_baseline(ctrl), now), b.days)
    out = {}
    for m, t in monthly(ctrl, now, months, with_reports=False).items():
        days = month_days(m, now)
        idx = _index(_per_day(t, days), ctrl_base)
        out[m] = {k: base[k] * idx[k] * days for k in PLAN_KEYS}
    return out


def savings(actual, planned, a):
    """(zł, kursy, km) zaoszczędzone wobec planu — wizyty × stawka + km × stawka (methodology.money_assumptions)."""
    visits = planned["wywozy"] - (actual["wywozy"] or 0)
    km = planned["km"] - float(actual["km"] or 0)
    return visits * a["cost_per_visit"] + km * a["cost_per_km"], visits, km


def last_months(now, n=12):
    y, m = now.year, now.month
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return out[::-1]


def month_days(month, now):
    """Dni miesiąca w danych (bieżący miesiąc: do `now`)."""
    start = datetime.strptime(month, "%Y-%m")
    nxt = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return (min(nxt, now) - start).total_seconds() / 86400


# --- efekty projektów ---

def metric_value(metric, t, days):
    """Miara efektu projektu z sum `t` (totals/monthly). None = brak danych."""
    if metric == "wywozy":
        return t["wywozy"] / days if days and t["wywozy"] else None
    if metric == "puste_wywozy":
        return 100 * t["puste"] / t["wywozy"] if t["wywozy"] else None
    if metric == "udzial_zmieszanych":
        return 100 * t["masa_zmieszane"] / t["masa"] if t["masa"] else None
    if metric == "km_na_wywoz":
        return t["km"] / t["wywozy"] if t["wywozy"] else None
    if metric == "koszt_wywozu":
        return t["koszt"] / t["wywozy"] if t["wywozy"] else None
    if metric == "czas_reakcji":
        return t["czas_reakcji"]
    raise ValueError(metric)


# (jednostka zmiany, dopełniacz do etykiety)
PROJECT_METRICS = {"wywozy": ("%", "wywozów"), "puste_wywozy": ("p.p.", "pustych wywozów"),
                   "udzial_zmieszanych": ("p.p.", "udziału zmieszanych"), "koszt_wywozu": ("%", "kosztu wywozu"),
                   "km_na_wywoz": ("%", "km na wywóz"),
                   "czas_reakcji": ("%", "czasu reakcji")}


def project_windows(project, now):
    """(przed, po): „po” = od startu do końca (najdalej do teraz), „przed” = tyle samo dni tuż przed startem."""
    start = datetime.combine(project.start, datetime.min.time())
    end = min(datetime.combine(project.end + timedelta(days=1), datetime.min.time()), now)
    if end <= start:
        return None
    after = Filters(od=start, do=end, district=project.district)
    return after.previous(), after


def project_effect(project, now):
    """(wartość zmiany, etykieta) z historii dzielnicy przed i po starcie projektu."""
    unit, noun = PROJECT_METRICS[project.metric]
    windows = project_windows(project, now)
    if windows is None:
        return None, f"Start {project.start:%m.%Y} — efekt po wdrożeniu"
    before, after = (metric_value(project.metric, totals(w, now), w.days) for w in windows)
    if before is None or after is None:
        return None, "Za mało danych do oceny efektu"
    value = round(after - before, 1) if unit == "p.p." else round(100 * (after - before) / before, 1)
    sign = "−" if value < 0 else "+"
    number = f"{abs(value):g}".replace(".", ",")
    return value, f"{sign}{number}{'%' if unit == '%' else ' p.p.'} {noun}"
