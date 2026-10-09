"""API panelu miasta (/api/dashboard/*, /api/projekty). Wszystkie liczby z bazy (app/dashboard.py, GROUP BY).

Dane są SYNTETYCZNE (app/history.py) + zdarzenia demo na żywo — każda odpowiedź ma meta.syntetyczne = true.
Błędy: {"blad": "<komunikat po polsku>", "kod": "<kod>"} z kodem HTTP 400 (zły filtr) albo 404.
"""
import csv
import io
from dataclasses import replace
from datetime import date, datetime, timedelta
from functools import wraps

from flask import Blueprint, Response, jsonify, request
from sqlalchemy import func, select

from . import clock, db, dumping
from . import crew_points as cp
from .dashboard import (ANOMALY_M, BASELINE, REPAIR_SLA, SLA_H, Filters, PROJECT_METRICS, accuracy, anomaly_pct,
                        baseline_label, by_district, control_districts, cost_explanation, dow_of, effect_label, hour_of, last_months,
                        latest_anomalies, metric_value, month_days, monthly, monthly_plan, pickups, pl_num, pl_range, plan, plural,
                        project_windows, repair_queue, reports, savings, sla_pct, totals, _baseline, _where)
from .history import FRACTIONS, HISTORY_START, WDROZENIE
from .methodology import money_assumptions, visit_cost_parts
from .misuse import misuse_overview
from .models import Point, Project
from .recommendations import WINDOW, recommendations
from .state import _cached, current_routes, point_states

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
        d = date.fromisoformat(raw)
        if not date(2020, 1, 1) <= d <= date(2100, 12, 31):  # 0001-01-01 / 9999-12-31 przepełniały timedelta (500)
            raise ValueError
        return d
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
    zl, _, km = savings(t, p, a)
    return {"koszt": _num(t["koszt"]), "wywozy": int(t["wywozy"]), "zapelnienie": _num(t["zapelnienie"], 1),
            "zgloszenia": int(t["zgloszenia"]), "czas_reakcji": _num(t["czas_reakcji"], 1),
            "oszczednosci": _num(zl), "co2": _num(km * a["co2_per_km"], 1),
            "sla_2h": _num(sla_pct(t), 1), "anomalie": int(t["anomalie"]), "anomalie_pct": _num(anomaly_pct(t), 1)}


# Odbiór = opróżnienie kosza (odbiory mniej to pominięte kosze), kurs = przejazd śmieciarki. Id KPI bez zmian (front, testy).
# Kolejność = układ kafli: rząd 1 efekty (oszczędności na 2 kolumny, CO₂, odbiory, anomalie), rząd 2 obsługa.
KPI = [("oszczednosci", "Oszczędności wobec planu", "zł", "wiecej"), ("co2", "CO₂ mniej niż w planie", "kg", "wiecej"),
       ("wywozy", "Odbiory", "szt.", "mniej"), ("anomalie", "Anomalie ekipy", "szt.", "mniej"),
       ("koszt", "Koszt odbiorów", "zł", "mniej"), ("zapelnienie", "Zapełnienie przy odbiorze", "%", "wiecej"),
       ("zgloszenia", "Zgłoszenia", "szt.", "mniej"), ("czas_reakcji", "Średni czas reakcji", "h", "mniej"),
       ("sla_2h", f"Obsłużone w ≤ {SLA_H} h", "%", "wiecej")]
KPI_OPIS = {"zapelnienie": "Średnie zapełnienie kosza w chwili odbioru: im wyższe, tym mniej pustych przejazdów.",
            "sla_2h": f"Norma MPO dla interwencji: {SLA_H} h od zgłoszenia. Liczone ze zgłoszeń zamkniętych albo otwartych "
                      f"dłużej niż {SLA_H} h.",
            "anomalie": f"Odbiory potwierdzone w aplikacji kierowcy dalej niż {ANOMALY_M} m od kosza."}
BEFORE_KPI = ("zapelnienie", "sla_2h", "czas_reakcji")  # kafle z wartością „przed wdrożeniem” (_before_rollout)


def _period(f):
    """Okres filtra jako daty: {od, do (włącznie), dni}."""
    od = f.od.date()
    return {"od": od.isoformat(), "do": max(od, (f.do - timedelta(seconds=1)).date()).isoformat(), "dni": round(f.days, 2)}


def _savings_detail(f, now, t, pl, a):
    """Kafel oszczędności: skąd liczba (plan vs rzeczywistość, stawki) i przeliczenie liniowe na dzień, miesiąc, rok."""
    zl, visits, km = savings(t, pl, a)
    period, mniej = _period(f), round(visits)
    stop_min = a.get("stop_min", 3)
    hours = mniej * stop_min / 60
    daily = zl / f.days if f.days else 0.0
    q = Point.query
    if f.district:
        q = q.filter(Point.district == f.district)
    if f.fraction:
        q = q.filter(Point.fraction == f.fraction)
    visit, per_km = a["cost_per_visit"], a["cost_per_km"]
    vc = visit_cost_parts()
    parts = ({"osoby": vc["crew_size"], "zl_osoba_h": vc["crew_pln_h"], "pojazd_zl_h": vc["vehicle_pln_h"], "zl_h": vc["per_hour"]}
             if visit == vc["cost"] else None)  # None = stawka nadpisana w konfiguracji (COST_PER_VISIT_PLN)
    crew = f"{vc['crew_size']} {plural(vc['crew_size'], 'osoba', 'osoby', 'osób')}"
    how = (f"założenie: ok. {pl_num(vc['stop_min'])} min postoju × ({crew} × {pl_num(vc['crew_pln_h'])} zł/h "
           f"+ pojazd {pl_num(vc['vehicle_pln_h'])} zł/h) = {pl_num(visit, 2)} zł, szczegóły: /metodologia#koszt-odbioru"
           if parts else "stawka z konfiguracji")
    word = plural(mniej, "odbiór", "odbiory", "odbiorów")
    more = f"{pl_num(abs(mniej))} {word} {'mniej' if mniej >= 0 else 'więcej'}"
    span = pl_range(date.fromisoformat(period["od"]), date.fromisoformat(period["do"]))
    return {
        "okres": period, "dziennie": _num(daily), "miesiac": _num(daily * 30), "rok": _num(daily * 365),
        "odbiory_mniej": mniej, "km_mniej": _num(km, 1), "godziny_ekip": _num(hours, 2),
        "plan": {"odbiory": round(pl["wywozy"]), "km": _num(pl["km"], 1)},
        "faktycznie": {"odbiory": int(t["wywozy"]), "km": _num(t["km"], 1)},
        "skladniki": {"odbiory_zl": _num(visits * visit), "km_zl": _num(km * per_km)},
        "stawki": {"odbior_zl": visit, "km_zl": per_km, "postoj_min": stop_min, "odbior_rozpisanie": parts},
        "kosze": q.count(), "baza": baseline_label(),
        "plan_opis": (f"Plan to liczba odbiorów i km, jaka byłaby bez Trash Fairy: średnia dzienna z okresu {baseline_label()} "
                      "(przed pierwszym wdrożeniem, te same filtry), poprawiona o zmianę w dzielnicach bez projektów "
                      "(grupa kontrolna) i pomnożona przez liczbę dni okresu. Oszczędność to odbiory mniej × "
                      f"{pl_num(visit, 2)} zł ({how}) plus km mniej × {pl_num(per_km, 2)} zł (założenie); opłata za tony "
                      "odpadów jest w planie i w rzeczywistości taka sama, więc jej nie liczymy."),
        "podpis": f"{more} · {pl_num(hours, 1)} h pracy ekip · {span}",
    }


def _before_rollout(f, now, slug):
    """(wartości 3 KPI „przed wdrożeniem”, okno Filters) albo (None, None). Całe miasto: okres bazowy planu. Dzielnica
    z projektem (albo filtr projektu): okno „przed” tego projektu (project_windows). Dzielnica bez projektu (grupa
    kontrolna): brak — porównanie zimy z wrześniem pokazałoby sezonowość, nie efekt. Bez korekty sezonu."""
    if not f.district:
        w = _baseline(f)
    else:
        if f.district in control_districts(now):
            return None, None
        pr = (Project.query.filter_by(slug=slug).first() if slug else
              Project.query.filter(Project.district == f.district, Project.start <= now.date()).order_by(Project.start).first())
        windows = pr and project_windows(pr, now)
        if not windows:
            return None, None
        w = replace(f, od=windows[0].od, do=windows[0].do)
    t = totals(w, now)
    return {"zapelnienie": _num(t["zapelnienie"], 1), "sla_2h": _num(sla_pct(t), 1),
            "czas_reakcji": _num(t["czas_reakcji"], 1)}, w


@bp.get("/dashboard/kpi")
@_cached_json
def kpi():
    now = clock.now()
    f, meta = parse_filters(now)
    a = money_assumptions()
    t, pl = totals(f, now), plan(f, now)
    cur = _kpi_values(t, pl, a)
    prev_f = f.previous()
    # poprzedni okres sprzed początku historii nie ma pełnych danych → zmiana_pct = null
    prev = _kpi_values(totals(prev_f, now), plan(prev_f, now), a) if prev_f.od >= HISTORY_START else None
    before, bw = _before_rollout(f, now, meta["filtry"]["projekt"])
    months = last_months(now)
    series, plans = monthly(f, now, months), monthly_plan(f, now, months)
    trends = {m: _kpi_values(series[m], plans[m], a) for m in months}
    out = []
    for kid, label, unit, better in KPI:
        item = {"id": kid, "etykieta": label, "wartosc": cur[kid], "jednostka": unit,
                "zmiana_pct": _change(cur[kid], prev[kid]) if prev else None, "lepiej_gdy": better,
                "trend": [trends[m][kid] for m in months]}
        if kid == "oszczednosci":
            item.update(_savings_detail(f, now, t, pl, a))
        if kid in KPI_OPIS:
            item["opis"] = KPI_OPIS[kid]
        if kid == "co2":
            item["opis"] = (f"Z tych samych km mniej co w oszczędnościach × {pl_num(a['co2_per_km'], 2)} kg CO₂/km "
                            "(założenie: diesel).")
        if kid in BEFORE_KPI:
            item["przed_wdrozeniem"] = before[kid] if before else None
        if kid == "anomalie" and cur["anomalie_pct"] is not None:
            item["podpis"] = f"{cur['anomalie_pct']:g}".replace(".", ",") + f"% odbiorów · próg {ANOMALY_M} m"
        out.append(item)
    baza = {"od": BASELINE[0].isoformat(), "do": (BASELINE[1] - timedelta(days=1)).isoformat(), "etykieta": baseline_label()}
    # okno wartości „przed wdrożeniem” (null = dzielnica bez projektu); surowe średnie, bez korekty sezonu — do podpisu
    przed = bw and {"od": bw.od.date().isoformat(), "do": (bw.do - timedelta(days=1)).date().isoformat(),
                    "etykieta": f"{pl_range(bw.od.date(), (bw.do - timedelta(days=1)).date())}, bez korekty sezonu"}
    return {"meta": {**meta, "miesiace": months, "wdrozenie": f"{WDROZENIE:%Y-%m}", "baza": baza, "przed_wdrozeniem": przed},
            "kpi": out}


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


def _pct(a, b, nd=1):
    return round(100 * a / b, nd) if b else None


def _jakosc(f, now):
    """Jakość obsługi według dzielnic: norma 2 h, anomalie ekipy (> 150 m), trafność zgłoszeń (symulacja obszaru demo)."""
    names = [f.district] if f.district else districts()
    rows, acc = by_district(f, now), accuracy(f, now)
    out = []
    for d in names:
        r = rows.get(d, {})
        hit, n = acc.get(d, (0, 0))
        out.append({"dzielnica": d, "sla_2h_pct": _pct(r.get("sla_ok", 0), r.get("sla_ocenione", 0)),
                    "sla_ocenione": int(r.get("sla_ocenione", 0)), "wywozy": int(r.get("wywozy", 0)),
                    "anomalie": int(r.get("anomalie", 0)), "anomalie_pct": _pct(r.get("anomalie", 0), r.get("wywozy", 0), 2),
                    "trafnosc_pct": _pct(hit, n), "trafnosc_rozstrzygniete": n})
    return {"dzielnice": out, "norma_h": SLA_H, "prog_m": ANOMALY_M, "trafnosc_etykieta": "Trafność przycisków (symulacja)",
            "trafnosc_zrodlo": "Symulacja obszaru demo (72 punkty, Stare Miasto i Grzegórzki), nie pomiar z miasta: "
                               "zgłoszenie trafne, gdy przy odbiorze kosz był zapełniony co najmniej w 75%."}


def _anomalie(f, now):
    rows = latest_anomalies(f, now)
    names = {p.id: (p.name, p.address) for p in Point.query.filter(Point.id.in_({r.point_id for r in rows}))} if rows else {}
    return {"prog_m": ANOMALY_M, "lista": [
        {"kosz_id": r.point_id, "kosz": names.get(r.point_id, ("", ""))[0], "adres": names.get(r.point_id, ("", ""))[1],
         "dzielnica": r.district, "data": r.at.isoformat(), "odleglosc_m": int(r.far_m)} for r in rows]}


CHARTS = {"frakcje": _frakcje, "dzielnice": _dzielnice, "koszty": _koszty, "zgloszenia": _zgloszenia,
          "heatmapa": _heatmapa, "mapa": _mapa, "jakosc": _jakosc, "anomalie": _anomalie}


@bp.get("/dashboard/wykresy/<nazwa>")
@_cached_json
def chart(nazwa):
    if nazwa not in CHARTS:
        raise ApiError(404, "nieznany_wykres", f"Nieznany wykres. Dostępne: {', '.join(CHARTS)}.")
    now = clock.now()
    f, meta = parse_filters(now)
    return {"meta": meta, **CHARTS[nazwa](f, now)}


@bp.get("/naprawy")
@_cached_json
def repairs():
    """Kolejka napraw: otwarte zgłoszenia „Uszkodzony” z terminem 24 h (dashboard.REPAIR_SLA). Okres filtrów nie ma
    znaczenia (to stan na teraz); filtr dzielnicy działa."""
    now = clock.now()
    f, meta = parse_filters(now)
    items = repair_queue(now, f.district)
    return {"meta": {**meta, "sla_h": int(REPAIR_SLA.total_seconds() // 3600)}, "naprawy": [
        {"kosz_id": it["point"].id, "kosz": it["point"].name, "adres": it["point"].address or "",
         "dzielnica": it["point"].district, "zgloszono": it["at"].isoformat(), "termin": it["due"].isoformat(),
         "status": "po terminie" if it["late"] else "w terminie", "po_terminie": it["late"],
         "zgloszen": it["presses"], "komentarz": it["note"] or ""} for it in items]}


@bp.get("/dashboard/rekomendacje")
@_cached_json
def recommendations_view():
    """Rekomendacje z danych (reguły): pojemność i częstotliwość (app/recommendations.py), miejsca podrzucania odpadów
    (app/dumping.py), sugestie ekip „Tu przydałby się kosz” i punkty zaangażowania ekipy (app/crew_points.py).
    Okna czasu są stałe (reguły), okres filtra nie ma znaczenia; filtr dzielnicy działa na listy koszy."""
    now = clock.now()
    f, meta = parse_filters(now)
    recs = recommendations(now, misuse_overview(now)["recommendations"])
    suggestions = cp.need_bin_suggestions(now, recs)
    points = cp.crew_points(now, suggestions)
    sites = dumping.dumping_sites(now)
    where = {p.id: (p.district, p.address or "") for p in Point.query.filter(Point.id.in_({r["point_id"] for r in recs}))} \
        if recs else {}
    rekomendacje = [{"kosz_id": r["point_id"], "kosz": r["name"], "adres": where[r["point_id"]][1],
                     "dzielnica": where[r["point_id"]][0], "rodzaj": r["type"], "etykieta": r["label"][:1].upper() + r["label"][1:],
                     "powod": r["reason"], "efekt": r["impact"]} for r in recs]
    if f.district:
        rekomendacje, sites, suggestions = ([x for x in xs if x["dzielnica"] == f.district]
                                            for xs in (rekomendacje, sites, suggestions))
    return {"meta": {**meta,
                     "okna_dni": {"rekomendacje": WINDOW.days, "podrzucanie": dumping.WINDOW_DAYS, "ekipy": cp.WINDOW_DAYS},
                     "progi_podrzucania": {"tablica": dumping.SIGN_AT, "kontrola": dumping.PATROL_AT,
                                           "fotopulapka": dumping.CAMERA_AT, "jeden_dzien_udzial": dumping.WEEKDAY_SHARE},
                     "poziomy_podrzucania": {k: sum(s["poziom"] == k for s in sites) for k in dumping.LEVELS},
                     "zasada": "Decyzje to reguły w kodzie; AI tylko opisuje zdjęcia. Zdjęcia dokumentują miejsce i czas, "
                               "nie ludzi. Fotopułapkę i kontrolę zleca gmina, nie system."},
            "rekomendacje": rekomendacje, "podrzucanie": sites, "sugestie_ekip": suggestions, "punkty_ekip": points}


def _project_trend(pr, now, months):
    series = monthly(Filters(od=now, do=now, district=pr.district), now, months)
    return [_num(metric_value(pr.metric, series[m], month_days(m, now)), 2) for m in months]


def _project(pr, now, months):
    unit, noun = PROJECT_METRICS[pr.metric]
    return {"id": pr.id, "slug": pr.slug, "nazwa": pr.name, "dzielnica": pr.district, "status": pr.status,
            "status_etykieta": STATUS_PL[pr.status], "postep_pct": pr.progress_pct, "budzet": pr.budget_pln,
            "wykorzystano": pr.spent_pln, "start": pr.start.isoformat(), "koniec": pr.end.isoformat(),
            "efekt_etykieta": pr.effect_label if pr.effect_value is None else effect_label(pr.metric, pr.effect_value),
            "efekt_wartosc": pr.effect_value, "efekt_jednostka": unit,
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
    summary = why = None
    if windows:
        tw = [totals(w, now) for w in windows]
        summary = {name: {k: _num(metric_value(k, t, w.days), 2) for k in PROJECT_METRICS} | {
            "od": w.od.isoformat(), "do": w.do.isoformat()} for name, w, t in zip(("przed", "po"), windows, tw)}
        why = cost_explanation(*tw, money_assumptions(), [w.days for w in windows])
    przed_po = {"start": f"{pr.start:%Y-%m}", "koniec": f"{pr.end:%Y-%m}", "miesiace": months,
                "koszt": [_num(series[m]["koszt"]) for m in months],
                "wywozy": [int(series[m]["wywozy"]) for m in months],
                "zapelnienie": [_num(series[m]["zapelnienie"], 1) for m in months],
                "czas_reakcji": [_num(series[m]["czas_reakcji"], 1) for m in months],
                "podsumowanie": summary, "koszt_wyjasnienie": why}
    return {"meta": {**meta, "miesiace": months}, "projekt": {**_project(pr, now, months), "przed_po": przed_po}}



EXPORTS = {  # nazwa pliku → (źródło, kolumna czasu, nagłówki CSV)
    "odbiory": (pickups, "at", ["data", "kosz_id", "dzielnica", "frakcja", "masa_kg", "koszt_zl", "km", "zapelnienie_pct",
                                "na_zadanie"]),
    "zgloszenia": (reports, "created_at", ["data", "kosz_id", "dzielnica", "frakcja", "rodzaj", "zamkniete"]),
}


ROUTES_HEADER = ["flota", "pojazd", "kolejnosc", "kosz_id", "kosz", "dzielnica", "frakcja", "lat", "lon", "planowany_kurs",
                 "km_trasy"]


def _dec(v, nd):
    return str(round(float(v), nd)).replace(".", ",")


def _route_rows(now, f):
    """Plan najbliższego kursu obu flot, wszystkie pojazdy (jak /api/trasa). Okres nie dotyczy planu – filtrują dzielnica/frakcja."""
    for fleet in current_routes(now):
        run_at = datetime.fromisoformat(fleet["run_at"]).strftime("%Y-%m-%d %H:%M")
        for route in [fleet] + fleet["extra_routes"]:
            stops = route["stops"]
            points = {p.id: p for p in Point.query.filter(Point.id.in_([s["id"] for s in stops]))}
            for s in stops:
                p = points[s["id"]]
                if (f.district and p.district != f.district) or (f.fraction and p.fraction != f.fraction):
                    continue
                name = p.name or ""
                name = "'" + name if name[:1] in ("=", "+", "-", "@") else name  # nazwa z OSM: bez formuł w Excelu
                yield [fleet["label"], s["vehicle"], s["order"], p.id, name, p.district, p.fraction,
                       _dec(s["lat"], 6), _dec(s["lon"], 6), run_at, _dec(route["km"], 1)]


@bp.get("/eksport/<nazwa>.csv")
def export_csv(nazwa):
    """CSV z tymi samymi filtrami co dashboard (okres, od/do, dzielnica, frakcja, projekt); separator „;” pod polski Excel."""
    if nazwa not in EXPORTS and nazwa != "trasy":
        raise ApiError(404, "nieznany_eksport", f"Nieznany eksport. Dostępne: {', '.join([*EXPORTS, 'trasy'])}.")
    now = clock.now()
    f, meta = parse_filters(now)
    if nazwa == "trasy":
        return _csv_response(nazwa, f, meta, ROUTES_HEADER, _route_rows(now, f))
    source, col, header = EXPORTS[nazwa]
    sub = source(now)
    c = sub.c
    cols = ([c.at, c.point_id, c.district, c.fraction, c.mass_kg, c.cost_pln, c.km, c.fill_pct, c.on_demand] if nazwa == "odbiory"
            else [c.created_at, c.point_id, c.district, c.fraction, c.kind, c.resolved_at])
    rows = db.session.execute(_where(select(*cols), sub, f, getattr(c, col)).order_by(getattr(c, col)))
    out = []
    for r in rows:
        r = list(r)
        r[0] = r[0].strftime("%Y-%m-%d %H:%M")
        if nazwa == "odbiory":
            r[4:7] = [_dec(v, 2) for v in r[4:7]]
            r[8] = "tak" if r[8] else "nie"
        else:
            r[5] = r[5].strftime("%Y-%m-%d %H:%M") if r[5] else ""
        out.append(r)
    return _csv_response(nazwa, f, meta, header, out)


def _csv_response(nazwa, f, meta, header, rows):
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")
    w.writerow([f"# {meta['zrodlo']} Okres: {meta['etykieta']}."])
    w.writerow(header)
    w.writerows(rows)
    name = f"trash-fairy-{nazwa}-{f.od:%Y%m%d}-{(f.do - timedelta(seconds=1)):%Y%m%d}.csv"
    return Response("﻿" + out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})
