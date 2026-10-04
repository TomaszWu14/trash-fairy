"""Agregacje panelu miasta — wyłącznie zapytania GROUP BY w bazie.

Odbiory = Pickup (historia syntetyczna, wszystkie punkty, 12 miesięcy) UNION ALL Emptying z source="crew" (kierowca
na żywo). Koszt obu liczony w zapytaniu formułą history.cost_pln z bieżących założeń (methodology.money_assumptions),
nie z kolumny Pickup.cost_pln: zmiana stawki działa bez ponownego seedowania i zgadza się z oszczędnościami.
Zgłoszenia = ReportHistory UNION ALL Report z naciśnięciem na żywo (Press.wall_at IS NOT NULL). Symulowane
Emptying/Report (stały harmonogram — baza porównania silnika) się NIE liczą; akcje z demo od razu zmieniają liczniki panelu.
"""
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta

from sqlalchemy import Integer, and_, case, cast, extract, func, literal, or_, select, union_all

from . import db
from .history import CAPACITY_L, COST_PER_TONNE_PLN, FRACTIONS, HISTORY_START, KM_PER_VISIT, WDROZENIE, cost_pln, mass_kg
from .methodology import money_assumptions
from .models import Emptying, Pickup, Point, Press, Report, ReportHistory

EMPTY_BELOW = 50  # odbiór przy zapełnieniu poniżej 50% = „pusty wywóz” (jak EMPTY_VISIT_BELOW w porównaniu)
BASELINE = (date(2025, 11, 1), WDROZENIE)  # plan = średnia dzienna z miesięcy przed pierwszym wdrożeniem
SLA_H = 2  # norma MPO: interwencja na zgłoszenie w ≤ 2 h
SLA_EPS_H = 1 / 3600  # 1 s tolerancji: julianday w SQLite liczy różnicę z błędem zaokrąglenia
ANOMALY_M = 150  # „anomalia ekipy”: odbiór potwierdzony dalej niż 150 m od kosza (ten sam promień co zgłoszenia, api_pl)


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
    """Wszystkie odbiory do `now`: kolumny point_id, district, fraction, at, mass_kg, cost_pln, km, fill_pct, on_demand, far_m."""
    a = money_assumptions()
    km = _by(KM_PER_VISIT, Point.kind)
    mass = mass_kg(Emptying.level, _by(CAPACITY_L, Point.kind), _by({k: v[1] for k, v in FRACTIONS.items()}, Point.fraction))
    live = (select(Emptying.point_id, Point.district, Point.fraction, Emptying.at, mass.label("mass_kg"),
                   cost_pln(mass, km, a).label("cost_pln"), km.label("km"), Emptying.level.label("fill_pct"),
                   literal(1).label("on_demand"), Emptying.far_m)
            .join(Point, Point.id == Emptying.point_id).where(Emptying.source == "crew", Emptying.at <= now))
    hist = (select(Pickup.point_id, Point.district, Pickup.fraction, Pickup.at, Pickup.mass_kg,
                   cost_pln(Pickup.mass_kg, Pickup.km, a).label("cost_pln"), Pickup.km,
                   Pickup.fill_pct, case((Pickup.on_demand, 1), else_=0).label("on_demand"), Pickup.far_m)
            .join(Point, Point.id == Pickup.point_id).where(Pickup.at <= now))
    return union_all(hist, live).subquery("odbiory")


def reports(now):
    """Wszystkie zgłoszenia do `now`: point_id, district, fraction, created_at, resolved_at (None = otwarte), kind."""
    hist = (select(ReportHistory.point_id, Point.district, Point.fraction, ReportHistory.created_at,
                   case((ReportHistory.resolved_at <= now, ReportHistory.resolved_at)).label("resolved_at"), ReportHistory.kind)
            .join(Point, Point.id == ReportHistory.point_id).where(ReportHistory.created_at <= now))
    first_kind = (select(Press.kind).where(Press.report_id == Report.id).order_by(Press.at, Press.id).limit(1)
                  .correlate(Report).scalar_subquery())
    kind = case((first_kind == "overflow", "odpady_obok"), (first_kind == "damaged", "uszkodzony"), (first_kind == "other", "inne"),
                else_="przepelniony")  # Press.kind → słownik historii (ReportHistory.kind); przycisk = przepełniony
    live = (select(Report.point_id, Point.district, Point.fraction, Report.first_at.label("created_at"),
                   case((Report.resolved_at <= now, Report.resolved_at)).label("resolved_at"), kind.label("kind"))
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
            func.coalesce(func.sum(case((o.c.fraction == "zmieszane", o.c.mass_kg), else_=0)), 0).label("masa_zmieszane"),
            _anomaly_col(o))


def _anomaly_col(o):
    return func.coalesce(func.sum(case((o.c.far_m > ANOMALY_M, 1), else_=0)), 0).label("anomalie")


def _sla_cols(z, now):
    """Norma 2 h. sla_ocenione = zgłoszenia z rozstrzygniętą normą: zamknięte albo otwarte dłużej niż 2 h (otwarte od
    30 min jeszcze mogą zdążyć — nie liczą się ani na plus, ani na minus)."""
    in_time = and_(z.c.resolved_at.isnot(None), hours_between(z.c.created_at, z.c.resolved_at) <= SLA_H + SLA_EPS_H)
    judged = or_(z.c.resolved_at.isnot(None), z.c.created_at <= now - timedelta(hours=SLA_H))
    return (func.coalesce(func.sum(case((in_time, 1), else_=0)), 0).label("sla_ok"),
            func.coalesce(func.sum(case((judged, 1), else_=0)), 0).label("sla_ocenione"))


def _report_cols(z, now):
    return (func.count().label("zgloszenia"), func.avg(hours_between(z.c.created_at, z.c.resolved_at)).label("czas_reakcji"),
            *_sla_cols(z, now))


def sla_pct(t):
    """Udział zgłoszeń obsłużonych w ≤ 2 h (%), None = brak ocenionych zgłoszeń."""
    return 100 * t["sla_ok"] / t["sla_ocenione"] if t["sla_ocenione"] else None


def anomaly_pct(t):
    return 100 * t["anomalie"] / t["wywozy"] if t["wywozy"] else None


def pickup_totals(f, now):
    o = pickups(now)
    return dict(db.session.execute(_where(select(*_pickup_cols(o)), o, f, o.c.at)).mappings().one())


def totals(f, now):
    """Sumy odbiorów i zgłoszeń w przedziale filtrów."""
    z = reports(now)
    r = db.session.execute(_where(select(*_report_cols(z, now)), z, f, z.c.created_at)).mappings().one()
    return {**pickup_totals(f, now), **r}


def monthly(f, now, months, with_reports=True):
    """{miesiąc 'YYYY-MM': sumy} dla miesięcy `months` (filtr dzielnicy/frakcji z `f`, czas z listy miesięcy)."""
    first = datetime.strptime(months[0], "%Y-%m")
    mf = replace(f, od=first, do=now + timedelta(seconds=1))
    o, z = pickups(now), reports(now)
    om, zm = month_of(o.c.at), month_of(z.c.created_at)
    out = {m: {"wywozy": 0, "koszt": 0, "masa": 0, "km": 0, "zapelnienie": None, "puste": 0, "masa_zmieszane": 0,
               "anomalie": 0, "zgloszenia": 0, "czas_reakcji": None, "sla_ok": 0, "sla_ocenione": 0} for m in months}
    for row in db.session.execute(_where(select(om.label("m"), *_pickup_cols(o)), o, mf, o.c.at).group_by(om)).mappings():
        if row["m"] in out:
            out[row["m"]].update({k: v for k, v in row.items() if k != "m"})
    if with_reports:
        for row in db.session.execute(_where(select(zm.label("m"), *_report_cols(z, now)), z, mf, z.c.created_at)
                                      .group_by(zm)).mappings():
            if row["m"] in out:
                out[row["m"]].update({k: v for k, v in row.items() if k != "m"})
    return out


# --- jakość obsługi: norma 2 h, anomalie ekipy, trafność zgłoszeń, kolejka napraw ---
REPAIR_SLA = timedelta(hours=24)  # „Uszkodzony”: naprawa w 24 h od zgłoszenia, niezależnie od trasy odbioru


def by_district(f, now):
    """{dzielnica: {wywozy, anomalie, sla_ok, sla_ocenione}} w przedziale filtrów."""
    o, z = pickups(now), reports(now)
    out = {}
    for row in db.session.execute(_where(select(o.c.district, func.count().label("wywozy"), _anomaly_col(o)), o, f, o.c.at)
                                  .group_by(o.c.district)).mappings():
        out.setdefault(row["district"], {}).update(wywozy=row["wywozy"], anomalie=row["anomalie"])
    for row in db.session.execute(_where(select(z.c.district, *_sla_cols(z, now)), z, f, z.c.created_at)
                                  .group_by(z.c.district)).mappings():
        out.setdefault(row["district"], {}).update(sla_ok=row["sla_ok"], sla_ocenione=row["sla_ocenione"])
    return out


def latest_anomalies(f, now, limit=50):
    """Najnowsze odbiory potwierdzone > 150 m od kosza: [(at, point_id, district, far_m)]."""
    o = pickups(now)
    q = _where(select(o.c.at, o.c.point_id, o.c.district, o.c.far_m).where(o.c.far_m > ANOMALY_M), o, f, o.c.at)
    return db.session.execute(q.order_by(o.c.at.desc()).limit(limit)).all()


def accuracy(f, now):
    """{dzielnica: (trafne, rozstrzygnięte)} z tabeli Report (72 punkty demo: symulacja + naciśnięcia na żywo).
    Bez zgłoszeń z naciśnięciem „uszkodzony”/„inne”: nie mówią, czy kosz był pełny. Wykluczamy, a nie wybieramy
    naciśnięcia o zapełnieniu, bo naciśnięcia z symulacji nie mają report_id."""
    other = select(Press.report_id).where(Press.kind.in_(("damaged", "other")), Press.report_id.isnot(None))
    r = (select(Point.district, Point.fraction, Report.first_at, Report.hit).join(Point, Point.id == Report.point_id)
         .where(Report.hit.isnot(None), Report.resolved_at <= now, Report.id.notin_(other))).subquery("trafnosc")
    q = _where(select(r.c.district, func.coalesce(func.sum(case((r.c.hit, 1), else_=0)), 0), func.count()), r, f, r.c.first_at)
    return {d: (int(hit), int(n)) for d, hit, n in db.session.execute(q.group_by(r.c.district))}


def repair_queue(now, district=None):
    """Otwarte zgłoszenia „Uszkodzony” (Press.kind = damaged, zgłoszenie nierozstrzygnięte w chwili `now`), od
    najpilniejszego. Termin = pierwsze zgłoszenie uszkodzenia + REPAIR_SLA; po terminie, gdy now > termin."""
    q = (db.session.query(Press, Point).join(Report, Report.id == Press.report_id).join(Point, Point.id == Press.point_id)
         .filter(Press.kind == "damaged", Press.at <= now, or_(Report.resolved_at.is_(None), Report.resolved_at > now)))
    if district:
        q = q.filter(Point.district == district)
    items = {}
    for press, point in q.order_by(Press.at, Press.id):
        it = items.setdefault(press.report_id, {"point": point, "at": press.at, "note": None, "presses": 0})
        it["presses"] += 1
        it["note"] = it["note"] or press.note
    out = []
    for it in items.values():
        due = it["at"] + REPAIR_SLA
        out.append({**it, "due": due, "late": now > due})
    return sorted(out, key=lambda x: x["due"])


# --- plan ---
# Plan = dzienna średnia z miesięcy przed pierwszym wdrożeniem (BASELINE) dla tych samych filtrów × sezonowość grupy
# kontrolnej (dzielnice, w których żaden projekt jeszcze nie działał): plan(okres) = baza/dzień × dni × indeks, gdzie
# indeks = (kontrola/dzień w okresie) / (kontrola/dzień w BASELINE). Planujemy odbiory i km; oszczędności = odbiory × stawka
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
    """(zł, odbiory mniej, km mniej) wobec planu — odbiory × stawka + km × stawka (methodology.money_assumptions)."""
    visits = planned["wywozy"] - (actual["wywozy"] or 0)
    km = planned["km"] - float(actual["km"] or 0)
    return visits * a["cost_per_visit"] + km * a["cost_per_km"], visits, km


def cost_parts(t, a):
    """Koszt odbiorów z sum `t` rozbity na składniki history.cost_pln: wizyty przy koszach, km, opłata za tony."""
    return {"odbiory_zl": int(t["wywozy"] or 0) * a["cost_per_visit"], "km_zl": float(t["km"] or 0) * a["cost_per_km"],
            "tony_zl": float(t["masa"] or 0) * COST_PER_TONNE_PLN / 1000.0}


def _pct_change(after, before):
    return 100 * (after - before) / before if before else None


def _signed_pct(v):
    return f"{'−' if v < 0 else '+'}{pl_num(abs(v), 1)}%"


def cost_explanation(before, after, a, days):
    """Czemu koszt nie spada razem z liczbą odbiorów (sumy `totals` przed i po starcie projektu, `days` = (dni przed,
    dni po)): składniki history.cost_pln i zdanie z liczbami. Okna mogą mieć różną długość (project_windows), więc
    porównujemy średnie dzienne, a zmianę w zł podajemy na 30 dni. None, gdy brak danych w którymś oknie."""
    d_b, d_a = days
    if not (before["wywozy"] and after["wywozy"] and before["koszt"] and before["masa"] and d_b and d_a):
        return None
    pb, pa = cost_parts(before, a), cost_parts(after, a)
    rate = lambda t, k, d: float(t[k]) / d
    service = 30 * ((pa["odbiory_zl"] + pa["km_zl"]) / d_a - (pb["odbiory_zl"] + pb["km_zl"]) / d_b)
    visits = _pct_change(rate(after, "wywozy", d_a), rate(before, "wywozy", d_b))
    cost = _pct_change(rate(after, "koszt", d_a), rate(before, "koszt", d_b))
    mass = _pct_change(rate(after, "masa", d_a), rate(before, "masa", d_b))
    share = 100 * pa["tony_zl"] / float(after["koszt"])
    text = (f"Odbiorów {'mniej' if visits < 0 else 'więcej'} o {pl_num(abs(visits), 1)}% (średnio na dzień), a dzienny "
            f"koszt zmienił się o {_signed_pct(cost)}: {pl_num(share)}% kosztu to opłata za tony odpadów, na którą liczba "
            f"odbiorów nie wpływa (masa odpadów na dzień {_signed_pct(mass)}), a koszt wizyt przy koszach i przejazdów "
            f"zmienił się o {'−' if service < 0 else '+'}{pl_num(abs(service))} zł miesięcznie (na 30 dni).")
    rnd = lambda p: {k: round(v, 2) for k, v in p.items()}
    return {"zdanie": text, "przed": rnd(pb), "po": rnd(pa), "dni": {"przed": round(d_b, 2), "po": round(d_a, 2)},
            "odbiory_pct": round(visits, 1), "koszt_pct": round(cost, 1), "masa_pct": round(mass, 1),
            "udzial_ton_pct": round(share, 1), "wizyty_i_km_zl_30_dni": round(service, 2)}


def plural(n, one, few, many):
    """Odmiana po liczbie: 1 odbiór, 2–4 odbiory, 5+ odbiorów (12–14 też „many”)."""
    n = abs(int(n))
    return one if n == 1 else few if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else many


def pl_num(v, nd=0):
    """Liczba po polsku: twarda spacja tysięcy, przecinek dziesiętny, bez końcowych zer."""
    s = f"{v:,.{nd}f}".replace(",", "\u00a0").replace(".", ",")
    return s.rstrip("0").rstrip(",") if "," in s else s


def pl_range(od, do):
    """Zakres dat po polsku: 1–30.09.2026, 3.09–2.10.2026, 3.12.2025–2.01.2026."""
    if (od.year, od.month) == (do.year, do.month):
        return f"{od.day}–{do.day}.{do:%m.%Y}"
    if od.year == do.year:
        return f"{od.day}.{od:%m}–{do.day}.{do:%m.%Y}"
    return f"{od.day}.{od:%m.%Y}–{do.day}.{do:%m.%Y}"


def baseline_label():
    return pl_range(BASELINE[0], BASELINE[1] - timedelta(days=1))


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


# (jednostka zmiany, dopełniacz do etykiety). Odbiór = opróżnienie kosza; klucze miar bez zmian (zgodność danych).
PROJECT_METRICS = {"wywozy": ("%", "odbiorów"), "puste_wywozy": ("p.p.", "pustych odbiorów"),
                   "udzial_zmieszanych": ("p.p.", "udziału zmieszanych"), "koszt_wywozu": ("%", "kosztu odbioru"),
                   "km_na_wywoz": ("%", "km na odbiór"),
                   "czas_reakcji": ("%", "czasu reakcji")}


def effect_label(metric, value):
    """Etykieta efektu projektu, np. „−13,2% odbiorów”. Panel liczy ją z wartości przy każdym zapytaniu, więc zmiana
    słownictwa nie wymaga ponownego generowania historii."""
    unit, noun = PROJECT_METRICS[metric]
    sign = "−" if value < 0 else "+"
    return f"{sign}{abs(value):g}".replace(".", ",") + f"{'%' if unit == '%' else ' p.p.'} {noun}"


def project_windows(project, now):
    """(przed, po): „po” = od startu do końca (najdalej do teraz), „przed” = tyle samo dni tuż przed startem, przycięte
    do początku historii (dni bez danych zaniżałyby „przed”); okna mogą więc mieć różną długość — porównuj średnie dzienne."""
    start = datetime.combine(project.start, datetime.min.time())
    end = min(datetime.combine(project.end + timedelta(days=1), datetime.min.time()), now)
    if end <= start:
        return None
    n = max(min(end - start, start - HISTORY_START), timedelta(0))
    return Filters(od=start - n, do=start, district=project.district), Filters(od=start, do=end, district=project.district)


def project_effect(project, now):
    """(wartość zmiany, etykieta) z historii dzielnicy przed i po starcie projektu."""
    unit = PROJECT_METRICS[project.metric][0]
    windows = project_windows(project, now)
    if windows is None:
        return None, f"Start {project.start:%m.%Y} — efekt po wdrożeniu"
    before, after = (metric_value(project.metric, totals(w, now), w.days) for w in windows)
    if before is None or after is None:
        return None, "Za mało danych do oceny efektu"
    value = round(after - before, 1) if unit == "p.p." else round(100 * (after - before) / before, 1)
    return value, effect_label(project.metric, value)
