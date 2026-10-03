"""API panelu miasta (/api/dashboard/*, /api/projekty). Wszystkie liczby z bazy (app/dashboard.py, GROUP BY).

Dane są SYNTETYCZNE (app/history.py) + zdarzenia demo na żywo — każda odpowiedź ma meta.syntetyczne = true.
Błędy: {"blad": "<komunikat po polsku>", "kod": "<kod>"} z kodem HTTP 400 (zły filtr) albo 404.
"""
from dataclasses import replace
from datetime import date, datetime, timedelta
from functools import wraps

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select

from . import clock, db
from .dashboard import (Filters, PROJECT_METRICS, dow_of, hour_of, last_months, metric_value, month_days, monthly,
                        monthly_plan, pickups, plan, project_windows, reports, savings, totals, _where)
from .history import FRACTIONS, HISTORY_START, WDROZENIE
from .methodology import money_assumptions
from .models import Point, Project
from .state import _cached, point_states

bp = Blueprint("dashboard_api", __name__, url_prefix="/api")

OKRESY = {"miesiac": (30, "Ostatnie 30 dni"), "kwartal": (90, "Ostatnie 90 dni"), "rok": (365, "Ostatnie 12 miesięcy")}
DISTRICT_ORDER = ["Stare Miasto", "Grzegórzki", "Krowodrza", "Podgórze", "Nowa Huta", "Dębniki"]
DNI = ["Pn", "Wt", "Śr", "Cz", "Pt", "Sb", "Nd"]
HOT_DAYS = 90
STATUS_PL = {"planowany": "Planowany", "w_realizacji": "W realizacji", "zakonczony": "Zakończony"}


class ApiError(Exception):
    def __init__(self, status, kod, blad):
        super().__init__(blad)
        self.status, self.kod, self.blad = status, kod, blad


@bp.errorhandler(ApiError)
def _api_error(e):
    return jsonify(blad=e.blad, kod=e.kod), e.status


def _cached_json(view):
    """Odpowiedź z cache silnika (state._cached): klucz = adres z parametrami, zegar demo i wersja danych, więc
    opróżnienie albo zgłoszenie na żywo od razu daje świeże liczby. Reset demo czyści cache (state.clear_cache).
    ponytail: jeden wpis na adres; przy wielu różnych zakresach od/do cache rośnie — wtedy LRU."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        return jsonify(_cached(f"dashboard:{request.full_path}", clock.now(), lambda: view(*args, **kwargs)))
    return wrapper


def districts():
    present = {d for (d,) in db.session.query(Point.district).distinct() if d}
    return [d for d in DISTRICT_ORDER if d in present] + sorted(present - set(DISTRICT_ORDER))


def _date(name):
    raw = request.args.get(name)
    if raw is None or raw == "":
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise ApiError(400, "nieprawidlowa_data", f"Parametr „{name}” musi być datą w formacie RRRR-MM-DD.") from None


def parse_filters(now):
    """(Filters, meta) z parametrów zapytania; nieznane wartości → ApiError 400."""
    a = request.args
    okres = a.get("okres") or "miesiac"
    if okres not in OKRESY:
        raise ApiError(400, "nieznany_okres", "Nieznany okres. Dozwolone: miesiac, kwartal, rok.")
    district, fraction, slug = a.get("dzielnica") or None, a.get("frakcja") or None, a.get("projekt") or None
    if district and district not in districts():
        raise ApiError(400, "nieznana_dzielnica", f"Nieznana dzielnica: {district}.")
    if fraction and fraction not in FRACTIONS:
        raise ApiError(400, "nieznana_frakcja", f"Nieznana frakcja. Dozwolone: {', '.join(FRACTIONS)}.")
    project = None
    if slug:
        project = Project.query.filter_by(slug=slug).first()
        if project is None:
            raise ApiError(400, "nieznany_projekt", f"Nieznany projekt: {slug}.")
        if district and district != project.district:
            raise ApiError(400, "sprzeczne_filtry", "Projekt dotyczy innej dzielnicy niż wybrana.")
        district = project.district

    days, label = OKRESY[okres]
    end = now + timedelta(seconds=1)  # przedziały są pół-otwarte, a opróżnienie zapisane „teraz” ma się liczyć
    do, od = end, now - timedelta(days=days)
    if project:
        od = datetime.combine(project.start, datetime.min.time())
        do = min(datetime.combine(project.end + timedelta(days=1), datetime.min.time()), end)
        label = f"Projekt: {project.name}"
    d_od, d_do = _date("od"), _date("do")
    if d_od or d_do:
        do = min(datetime.combine(d_do + timedelta(days=1), datetime.min.time()), end) if d_do else end
        od = datetime.combine(d_od, datetime.min.time()) if d_od else do - timedelta(days=30)
        if d_od and d_do and d_od > d_do:
            raise ApiError(400, "nieprawidlowy_zakres", "Data „od” jest późniejsza niż „do”.")
        label = f"{od:%d.%m.%Y} – {(do - timedelta(seconds=1)):%d.%m.%Y}"
    if do <= od:  # np. przedział w przyszłości zegara demo: pusty wynik, nie błąd
        do = od
    f = Filters(od=od, do=do, district=district, fraction=fraction)
    meta = {"syntetyczne": True,
            "zrodlo": "Dane syntetyczne (generator app/history.py) i zdarzenia demo na żywo; adresy i położenie z OSM.",
            "od": od.isoformat(), "do": min(do, now).isoformat(), "etykieta": label, "teraz": now.isoformat(),
            "filtry": {"okres": okres, "dzielnica": district, "frakcja": fraction, "projekt": slug}}
    return f, meta


def _num(v, nd=2):
    return round(float(v), nd) if v is not None else None


MAX_CHANGE_PCT = 999  # powyżej tego zmiana procentowa to szum (np. oszczędności z ~0 zł)


def _change(cur, prev):
    if cur is None or not prev or (cur < 0) != (prev < 0):
        return None
    pct = round(100 * (cur - prev) / abs(prev), 1)
    return pct if abs(pct) <= MAX_CHANGE_PCT else None


def _kpi_values(t, p, a):
    zl, visits, km = savings(t, p, a)
    return {"koszt": _num(t["koszt"]), "wywozy": int(t["wywozy"]), "zapelnienie": _num(t["zapelnienie"], 1),
            "zgloszenia": int(t["zgloszenia"]), "czas_reakcji": _num(t["czas_reakcji"], 1),
            "oszczednosci": _num(zl), "co2": _num(km * a["co2_per_km"], 1), "kursy": round(visits)}


KPI = [("koszt", "Koszt wywozów", "zł", "mniej"), ("wywozy", "Wywozy", "szt.", "mniej"),
       ("zapelnienie", "Średnie zapełnienie przy odbiorze", "%", "wiecej"), ("zgloszenia", "Zgłoszenia", "szt.", "mniej"),
       ("czas_reakcji", "Średni czas reakcji", "h", "mniej"), ("oszczednosci", "Oszczędności wobec planu", "zł", "wiecej"),
       ("co2", "Redukcja CO₂", "kg", "wiecej")]


@bp.get("/dashboard/kpi")
@_cached_json
def kpi():
    now = clock.now()
    f, meta = parse_filters(now)
    a = money_assumptions()
    cur = _kpi_values(totals(f, now), plan(f, now), a)
    prev_f = f.previous()
    # poprzedni okres sprzed początku historii nie ma pełnych danych → zmiana_pct = null
    prev = _kpi_values(totals(prev_f, now), plan(prev_f, now), a) if prev_f.od >= HISTORY_START else None
    months = last_months(now)
    series, plans = monthly(f, now, months), monthly_plan(f, now, months)
    trends = {m: _kpi_values(series[m], plans[m], a) for m in months}
    out = []
    for kid, label, unit, better in KPI:
        item = {"id": kid, "etykieta": label, "wartosc": cur[kid], "jednostka": unit,
                "zmiana_pct": _change(cur[kid], prev[kid]) if prev else None, "lepiej_gdy": better,
                "trend": [trends[m][kid] for m in months]}
        if kid == "oszczednosci":
            item["kursy"] = cur["kursy"]
        out.append(item)
    return {"meta": {**meta, "miesiace": months}, "kpi": out}


def _frakcje(f, now):
    o = pickups(now)
    rows = dict(db.session.execute(_where(select(o.c.fraction, func.sum(o.c.mass_kg)), o, f, o.c.at)
                                   .group_by(o.c.fraction)).all())
    codes = [f.fraction] if f.fraction else list(FRACTIONS)
    return {"frakcje": [{"frakcja": c, "etykieta": FRACTIONS[c][0], "masa_t": round(float(rows.get(c) or 0) / 1000, 3)}
                        for c in codes]}


def _dzielnice(f, now):
    o = pickups(now)
    names = [f.district] if f.district else districts()
    cells = {(d, fr): (c, n) for d, fr, c, n in db.session.execute(
        _where(select(o.c.district, o.c.fraction, func.sum(o.c.cost_pln), func.count()), o, f, o.c.at)
        .group_by(o.c.district, o.c.fraction)).all()}
    codes = [f.fraction] if f.fraction else list(FRACTIONS)
    return {"dzielnice": names, "serie": [
        {"frakcja": c, "etykieta": FRACTIONS[c][0],
         "koszt": [_num(cells.get((d, c), (0, 0))[0]) for d in names],
         "wywozy": [int(cells.get((d, c), (0, 0))[1]) for d in names]} for c in codes]}


def _koszty(f, now):
    months = last_months(now)
    series, plans, a = monthly(f, now, months, with_reports=False), monthly_plan(f, now, months), money_assumptions()
    return {"miesiace": months, "rzeczywiste": [_num(series[m]["koszt"]) for m in months],
            "plan": [_num(float(series[m]["koszt"]) + savings(series[m], plans[m], a)[0]) for m in months],
            "wdrozenie": f"{WDROZENIE:%Y-%m}"}


def _zgloszenia(f, now):
    months = last_months(now)
    series = monthly(f, now, months)
    return {"miesiace": months, "liczba": [int(series[m]["zgloszenia"]) for m in months],
            "czas_reakcji_h": [_num(series[m]["czas_reakcji"], 1) for m in months]}


def _heatmapa(f, now):
    z = reports(now)
    dow, hour = dow_of(z.c.created_at), hour_of(z.c.created_at)
    counts = {((d + 6) % 7, h): n for d, h, n in db.session.execute(
        _where(select(dow, hour, func.count()), z, f, z.c.created_at).group_by(dow, hour)).all()}
    return {"dni": DNI, "dane": [[d, h, counts.get((d, h), 0)] for d in range(7) for h in range(24)]}


def _mapa(f, now):
    q = Point.query
    if f.district:
        q = q.filter(Point.district == f.district)
    if f.fraction:
        q = q.filter(Point.fraction == f.fraction)
    points = q.order_by(Point.id).all()
    states = {}
    if any(p.live for p in points):
        states = point_states(now)
    kosze = [{"id": p.id, "nazwa": p.name, "adres": p.address, "dzielnica": p.district, "frakcja": p.fraction,
              "rodzaj": p.kind, "lat": p.lat, "lon": p.lon, "live": p.live,
              "zapelnienie": min(100, states[p.id]["level"]) if p.live and p.id in states else p.snapshot_fill}
             for p in points]
    z = reports(now)
    hot = replace(f, od=now - timedelta(days=HOT_DAYS), do=now + timedelta(seconds=1))
    q = select(Point.lat, Point.lon, func.count()).select_from(z).join(Point, Point.id == z.c.point_id)
    rows = db.session.execute(_where(q, z, hot, z.c.created_at).group_by(Point.id, Point.lat, Point.lon)).all()
    return {"kosze": kosze, "goraco": [[lat, lon, n] for lat, lon, n in rows], "goraco_dni": HOT_DAYS}


CHARTS = {"frakcje": _frakcje, "dzielnice": _dzielnice, "koszty": _koszty, "zgloszenia": _zgloszenia,
          "heatmapa": _heatmapa, "mapa": _mapa}


@bp.get("/dashboard/wykresy/<nazwa>")
@_cached_json
def chart(nazwa):
    if nazwa not in CHARTS:
        raise ApiError(404, "nieznany_wykres", f"Nieznany wykres. Dostępne: {', '.join(CHARTS)}.")
    now = clock.now()
    f, meta = parse_filters(now)
    return {"meta": meta, **CHARTS[nazwa](f, now)}


def _project_trend(pr, now, months):
    series = monthly(Filters(od=now, do=now, district=pr.district), now, months)
    return [_num(metric_value(pr.metric, series[m], month_days(m, now)), 2) for m in months]


def _project(pr, now, months):
    unit, noun = PROJECT_METRICS[pr.metric]
    return {"id": pr.id, "slug": pr.slug, "nazwa": pr.name, "dzielnica": pr.district, "status": pr.status,
            "status_etykieta": STATUS_PL[pr.status], "postep_pct": pr.progress_pct, "budzet": pr.budget_pln,
            "wykorzystano": pr.spent_pln, "start": pr.start.isoformat(), "koniec": pr.end.isoformat(),
            "efekt_etykieta": pr.effect_label, "efekt_wartosc": pr.effect_value, "efekt_jednostka": unit,
            "miara": pr.metric, "ikona": pr.icon, "trend": _project_trend(pr, now, months)}


@bp.get("/projekty")
@_cached_json
def projects():
    now = clock.now()
    f, meta = parse_filters(now)
    months = last_months(now)
    q = Project.query.order_by(Project.start)
    if f.district:
        q = q.filter(Project.district == f.district)
    return {"meta": {**meta, "miesiace": months}, "projekty": [_project(pr, now, months) for pr in q]}


@bp.get("/projekty/<slug>")
@_cached_json
def project(slug):
    now = clock.now()
    pr = Project.query.filter_by(slug=slug).first()
    if pr is None:
        raise ApiError(404, "nieznany_projekt", f"Nie ma projektu „{slug}”.")
    _, meta = parse_filters(now)
    months = last_months(now)
    series = monthly(Filters(od=now, do=now, district=pr.district), now, months)
    windows = project_windows(pr, now)
    summary = None
    if windows:
        summary = {name: {k: _num(metric_value(k, totals(w, now), w.days), 2) for k in PROJECT_METRICS} | {
            "od": w.od.isoformat(), "do": w.do.isoformat()} for name, w in zip(("przed", "po"), windows)}
    przed_po = {"start": f"{pr.start:%Y-%m}", "koniec": f"{pr.end:%Y-%m}", "miesiace": months,
                "koszt": [_num(series[m]["koszt"]) for m in months],
                "wywozy": [int(series[m]["wywozy"]) for m in months],
                "zapelnienie": [_num(series[m]["zapelnienie"], 1) for m in months],
                "czas_reakcji": [_num(series[m]["czas_reakcji"], 1) for m in months],
                "podsumowanie": summary}
    return {"meta": {**meta, "miesiace": months}, "projekt": {**_project(pr, now, months), "przed_po": przed_po}}
