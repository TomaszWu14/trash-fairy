"""Miejsca podrzucania odpadów — reguła w kodzie (AI tylko opisuje zdjęcia, nie decyduje).

Sygnał przy koszu w oknie 90 dni: zgłoszenie mieszkańca „Odpady obok kosza” (historia ReportHistory i zgłoszenia na żywo),
problem kierowcy „Odpady obok kosza” (StopIssue overflow) albo zdjęcie ekipy, na którym analiza widzi worki z domowymi
śmieciami. Drabinka: ≥ 2 sygnały → tablica informacyjna i edukacja, ≥ 4 → kontrola Straży Miejskiej, ≥ 6 albo ≥ 4,
z czego co najmniej połowa w jeden dzień tygodnia → „rozważ fotopułapkę (decyzja gminy)”.
Sygnał to najwyżej jeden na kosz, źródło i dzień: seria kliknięć z jednej wizyty to jeden sygnał, a dzień tygodnia
wykrywa wzorzec z kolejnych tygodni, nie serię z jednego dnia.
Zdjęcia dokumentują miejsce i czas, nie ludzi; zdjęcia mieszkańców ze zgłoszeń i zdjęcie ekipy z dnia, w którym kierowca
zgłosił już problem przy tym koszu, liczą się tylko jako dowód (zgłoszenie już jest sygnałem).
"""
from collections import Counter, defaultdict
from datetime import timedelta

from sqlalchemy import String, case, cast, func, literal_column, select, union_all

from . import db
from .dashboard import dow_of, plural, reports
from .models import PhotoAnalysis, Point, StopIssue

WINDOW_DAYS = 90
SIGN_AT = 2
PATROL_AT = 4
CAMERA_AT = 6
WEEKDAY_SHARE = 0.5  # przy ≥ PATROL_AT sygnałach: taki udział jednego dnia tygodnia → fotopułapka

LEVELS = {"fotopulapka": "Rozważ fotopułapkę (decyzja gminy)", "kontrola": "Kontrola Straży Miejskiej",
          "tablica": "Tablica informacyjna i edukacja"}
RANK = {k: i for i, k in enumerate(LEVELS)}
DAYS = ["niedziela", "poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota"]  # 0 = niedziela (dow_of)
ON_DAY = ["w niedzielę", "w poniedziałek", "we wtorek", "w środę", "w czwartek", "w piątek", "w sobotę"]
SIGNALS = ("mieszkancy", "kierowcy", "zdjecia_ekip")  # „zdjecia_zgloszen” to tylko dowód, nie osobny sygnał


def level(n, top_day):
    """Poziom drabinki z liczby sygnałów i liczby sygnałów w najczęstszym dniu tygodnia; None = poniżej progu."""
    if n >= CAMERA_AT or (n >= PATROL_AT and top_day >= WEEKDAY_SHARE * n):
        return "fotopulapka"
    if n >= PATROL_AT:
        return "kontrola"
    if n >= SIGN_AT:
        return "tablica"
    return None


def _counts(now):
    """[(point_id, źródło, dzień tygodnia, liczba dni, liczba zdarzeń)] — jedno zapytanie GROUP BY po złączonych źródłach.
    Sygnałem jest liczba dni (jeden na kosz, źródło i dzień); liczba zdarzeń służy tylko do licznika zdjęć-dowodów."""
    z = reports(now)
    lit = lambda name: literal_column(f"'{name}'")
    done = PhotoAnalysis.status == "done"
    driver_same_day = (select(StopIssue.id).where(StopIssue.point_id == PhotoAnalysis.point_id, StopIssue.kind == "overflow",
                                                  func.date(StopIssue.at) == func.date(PhotoAnalysis.at)).exists())
    signals = union_all(
        select(z.c.point_id, lit("mieszkancy").label("src"), z.c.created_at.label("at")).where(z.c.kind == "odpady_obok"),
        select(StopIssue.point_id, lit("kierowcy"), StopIssue.at).where(StopIssue.kind == "overflow"),
        select(PhotoAnalysis.point_id, case((driver_same_day, lit("zdjecia_zgloszen")), else_=lit("zdjecia_ekip")),
               PhotoAnalysis.at)
        .where(done, PhotoAnalysis.source != "resident", cast(PhotoAnalysis.misuse, String).like('%"household_bag"%')),
        select(PhotoAnalysis.point_id, lit("zdjecia_zgloszen"), PhotoAnalysis.at)
        .where(done, PhotoAnalysis.source == "resident", PhotoAnalysis.condition == "odpady_obok"),
    ).subquery("podrzucenia")
    dow = dow_of(signals.c.at)
    q = (select(signals.c.point_id, signals.c.src, dow, func.count(func.distinct(func.date(signals.c.at))), func.count())
         .where(signals.c.at > now - timedelta(days=WINDOW_DAYS), signals.c.at <= now)
         .group_by(signals.c.point_id, signals.c.src, dow))
    return db.session.execute(q).all()


def _reason(n, by_src, top, day):
    parts = [(by_src["mieszkancy"], "zgłoszenie mieszkańców", "zgłoszenia mieszkańców", "zgłoszeń mieszkańców"),
             (by_src["kierowcy"], "zgłoszenie kierowcy", "zgłoszenia kierowców", "zgłoszeń kierowców"),
             (by_src["zdjecia_ekip"], "zdjęcie z workami domowymi", "zdjęcia z workami domowymi", "zdjęć z workami domowymi")]
    what = ", ".join(f"{k} {plural(k, *forms)}" for k, *forms in parts if k)
    when = f", {top} z nich {ON_DAY[day]}" if top > 1 else ""
    return f"{n} {plural(n, 'sygnał', 'sygnały', 'sygnałów')} odpadów obok kosza w {WINDOW_DAYS} dni ({what}){when}."


def dumping_sites(now):
    """Punkty z poziomem drabinki, od najpoważniejszych: liczba sygnałów, źródła, dominujący dzień tygodnia, zdjęcia."""
    src, days = defaultdict(Counter), defaultdict(Counter)
    for pid, s, dow, n_days, n_events in _counts(now):
        n = n_days if s in SIGNALS else n_events  # sygnał = dzień ze zdarzeniem; zdjęcia-dowody liczymy sztukami
        src[pid][s] += n
        if s in SIGNALS:
            days[pid][int(dow)] += n
    found = {}
    for pid, by_src in src.items():
        n = sum(by_src[s] for s in SIGNALS)
        if not n:
            continue
        day, top = max(sorted(days[pid].items()), key=lambda kv: kv[1])  # remis: wcześniejszy dzień (od niedzieli)
        lv = level(n, top)
        if lv:
            found[pid] = (n, day, top, lv)
    points = {p.id: p for p in Point.query.filter(Point.id.in_(found))} if found else {}
    out = []
    for pid, (n, day, top, lv) in found.items():
        p, by_src = points[pid], src[pid]
        out.append({"kosz_id": pid, "kosz": p.name, "adres": p.address or "", "dzielnica": p.district, "lat": p.lat,
                    "lon": p.lon, "sygnaly": n, "zrodla": {s: by_src[s] for s in SIGNALS},
                    "zdjecia": by_src["zdjecia_ekip"] + by_src["zdjecia_zgloszen"],
                    "dzien_tygodnia": DAYS[day], "dzien_sygnaly": top, "poziom": lv, "poziom_etykieta": LEVELS[lv],
                    "uzasadnienie": _reason(n, by_src, top, day)})
    return sorted(out, key=lambda x: (RANK[x["poziom"]], -x["sygnaly"], x["kosz_id"]))
