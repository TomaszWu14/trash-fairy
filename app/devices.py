"""Urządzenia na koszach: masterdane, bateria, odczyty i status. Reguły w kodzie, bez AI. DANE SYNTETYCZNE.

Dwa typy urządzeń:
- panel  — „Panel e-papier z przyciskiem” na 72 koszach demo (wiersze Device z app/residents.py: sygnał życia,
           zmierzona bateria, autotest). Odczyt = sygnał życia co PANEL interval + naciśnięcia przycisku (Press).
- czujnik — „Czujnik zapełnienia (ultradźwiękowy)” na punktach miasta w Nowej Hucie (pilotaż od 07.2026,
           app/history.py PROJECTS). Bateria liczona z wieku: 100% − wiek / żywotność × tempo zużycia.

Założenia demo (stałe na typ, nie z karty katalogowej konkretnego producenta): KINDS.
Status (jeden, wg pierwszeństwa): brak sygnału > 48 h → bateria < 15% → autotest nieudany → wymiana w 30 dni → OK.
"""
import random
from datetime import datetime, timedelta
from math import floor

from sqlalchemy import func

from . import db
from .history import CAPACITY_L
from .models import Device, DeviceInfo, Point, Press
from .residents import HEARTBEAT_LOST

KINDS = {  # założenia demo
    "panel": {"label": "Panel e-papier z przyciskiem", "model": "Panel EP-42 z przyciskiem", "prefix": "TF-EP",
              "life_days": 365, "capacity_mah": 5200, "interval_min": 60, "icon": "tablet-smartphone"},
    "czujnik": {"label": "Czujnik zapełnienia (ultradźwiękowy)", "model": "Czujnik US-1 ultradźwiękowy", "prefix": "TF-US",
                "life_days": 730, "capacity_mah": 3600, "interval_min": 15, "icon": "radio-tower"},
}
CRITICAL_BATTERY = 15  # %: poniżej bateria krytyczna
REPLACE_WITHIN_DAYS = 30  # tyle dni (lub mniej) do wymiany → „Wymiana baterii w 30 dni”
SERIES_DAYS = 7
PILOT_DISTRICT = "Nowa Huta"
PILOT_ROLLOUT = (datetime(2026, 7, 1, 8), 30)  # start montażu czujników i długość okna montażu (dni)
PANEL_ROLLOUT = (datetime(2026, 4, 20, 8), 10)  # panele zamontowane przed wdrożeniem 1.05.2026
FAULTY_DRAINS = (6.2, 6.9)  # wadliwa partia ogniw w pilotażu: jedna bateria do wymiany w 30 dni, jedna krytyczna

STATUS = {  # klucz → (etykieta, ranga pilności: 0 = najpilniejsze)
    "brak_sygnalu": ("Brak sygnału > 48 h", 0),
    "bateria_krytyczna": ("Bateria krytyczna (< 15%)", 1),
    "autotest": ("Autotest nieudany", 2),
    "wymiana_30": ("Wymiana baterii w 30 dni", 3),
    "ok": ("OK", 4),
}


def sensor_battery(installed_at, now, drain, life_days=KINDS["czujnik"]["life_days"]):
    """Bateria % czujnika z wieku: 100 − 100 × wiek / żywotność × tempo zużycia, w granicach 0–100."""
    age = max(0.0, (now - installed_at).total_seconds() / 86400)
    return max(0, min(100, round(100 - 100 * age * drain / life_days)))


def days_left(battery, life_days, drain=1.0):
    """Dni do wymiany: zostały battery% żywotności, zużywane w tempie drain. Nigdy ujemne."""
    return max(0, floor(battery / 100 * life_days / (drain or 1.0)))


def status(battery, left, online, selftest_ok):
    """Jeden status wg pierwszeństwa (STATUS). online=False = brak sygnału dłużej niż HEARTBEAT_LOST (48 h)."""
    if not online:
        return "brak_sygnalu"
    if battery < CRITICAL_BATTERY:
        return "bateria_krytyczna"
    if selftest_ok is False:
        return "autotest"
    if left <= REPLACE_WITHIN_DAYS:
        return "wymiana_30"
    return "ok"


def battery_level(battery):
    """Poziom do koloru i słowa: full (< 15%), warn (< 35%), ok."""
    return "full" if battery < CRITICAL_BATTERY else "warn" if battery < 35 else "ok"


def _ticks(a, b, interval_min, loss):
    """Liczba odczytów co interval_min w przedziale [a, b), pomniejszona o straty transmisji."""
    if b <= a:
        return 0
    return round(floor((b - a).total_seconds() / 60 / interval_min) * (1 - loss))


def seed_demo(now, seed=7):
    """Masterdane dla wszystkich urządzeń (deterministycznie). Wymaga Device (residents.seed_demo) i punktów miasta."""
    db.session.query(DeviceInfo).delete()
    for d in Device.query.order_by(Device.point_id):
        rng = random.Random(f"{seed}:panel:{d.point_id}")
        start, window = PANEL_ROLLOUT
        db.session.add(DeviceInfo(point_id=d.point_id, kind="panel", model=KINDS["panel"]["model"],
                                  serial=f"{KINDS['panel']['prefix']}-{d.point_id:06d}",
                                  installed_at=start + timedelta(days=rng.randrange(window), minutes=rng.randrange(480)),
                                  firmware=rng.choice(["2.3.1", "2.4.0", "2.4.0"]), drain=1.0, loss=rng.uniform(0, .03)))
    pilot = Point.query.filter(Point.district == PILOT_DISTRICT, Point.live.is_(False)).order_by(Point.osm_id).all()
    rng = random.Random(f"{seed}:pilot")
    picks = rng.sample(range(len(pilot)), min(4, len(pilot)))
    faulty = dict(zip(picks[:2], FAULTY_DRAINS))
    offline = picks[2] if len(picks) > 2 else None
    failed = picks[3] if len(picks) > 3 else None
    start, window = PILOT_ROLLOUT
    for i, p in enumerate(pilot):
        r = random.Random(f"{seed}:czujnik:{p.osm_id}")
        installed = start if i in faulty else start + timedelta(days=r.randrange(window), minutes=r.randrange(480))
        seen = now - (timedelta(hours=r.randint(55, 80)) if i == offline else timedelta(minutes=r.randint(1, 14)))
        db.session.add(DeviceInfo(point_id=p.id, kind="czujnik", model=KINDS["czujnik"]["model"],
                                  serial=f"{KINDS['czujnik']['prefix']}-{p.id:06d}", installed_at=installed,
                                  firmware=r.choice(["1.8.2", "1.9.0", "1.9.0"]), drain=faulty.get(i, r.uniform(.9, 1.2)),
                                  loss=r.uniform(0, .04), last_seen=seen, selftest_ok=i != failed))
    db.session.commit()


def _presses(now):
    """Naciśnięcia z ostatnich 7 dni: {(point_id, 'RRRR-MM-DD'): n} i {point_id: n z ostatniej doby} — GROUP BY w bazie."""
    since = datetime.combine(now.date() - timedelta(days=SERIES_DAYS - 1), datetime.min.time())
    day = func.date(Press.at)
    by_day = {(pid, str(d)): n for pid, d, n in db.session.query(Press.point_id, day, func.count())
              .filter(Press.at >= since, Press.at <= now).group_by(Press.point_id, day)}
    last24 = dict(db.session.query(Press.point_id, func.count()).filter(Press.at > now - timedelta(hours=24), Press.at <= now)
                  .group_by(Press.point_id).all())
    last = dict(db.session.query(Press.point_id, func.max(Press.at)).filter(Press.at <= now).group_by(Press.point_id).all())
    return by_day, last24, last


def _item(info, p, dev, now, presses, full=False):
    k = KINDS[info.kind]
    if info.kind == "panel":
        seen, battery, selftest_ok, selftest_at = dev.last_heartbeat, dev.battery, dev.selftest_ok, dev.last_selftest
    else:
        seen, selftest_ok = info.last_seen, info.selftest_ok
        battery = sensor_battery(info.installed_at, now, info.drain, k["life_days"])
        selftest_at = datetime.combine(min(seen, now).date(), datetime.min.time()) + timedelta(hours=3)  # codziennie o 3:00
        if selftest_at > seen:
            selftest_at -= timedelta(days=1)
    by_day, last24, last_press = presses
    online = seen >= now - HEARTBEAT_LOST
    left = days_left(battery, k["life_days"], info.drain)
    st = status(battery, left, online, selftest_ok)
    end = min(seen, now)
    days = [now.date() - timedelta(days=i) for i in range(SERIES_DAYS - 1, -1, -1)]
    series = []
    for d in days:
        d0 = datetime.combine(d, datetime.min.time())
        loss = random.Random(f"{info.serial}:{d}").uniform(0, 2 * info.loss)  # straty różne dzień do dnia, średnio info.loss
        series.append(_ticks(max(d0, info.installed_at), min(d0 + timedelta(days=1), end), k["interval_min"], loss)
                      + by_day.get((p.id, d.isoformat()), 0))
    n24 = _ticks(max(now - timedelta(hours=24), info.installed_at), end, k["interval_min"], info.loss) + last24.get(p.id, 0)
    if info.kind == "panel":
        pressed = last_press.get(p.id)
        if pressed and pressed >= seen:
            reading = {"czas": pressed.isoformat(), "wartosc": None, "opis": "Naciśnięcie przycisku"}
        else:
            reading = {"czas": seen.isoformat(), "wartosc": None, "opis": "Sygnał życia"}
    else:
        reading = {"czas": seen.isoformat(), "wartosc": p.snapshot_fill, "opis": f"Zapełnienie {p.snapshot_fill or 0}%"}
    out = {"id": p.id, "typ": info.kind, "typ_etykieta": k["label"], "ikona": k["icon"], "numer_seryjny": info.serial,
           "kosz": {"id": p.id, "nazwa": p.name, "adres": p.address, "dzielnica": p.district, "frakcja": p.fraction},
           "bateria_pct": battery, "bateria_poziom": battery_level(battery), "dni_do_wymiany": left,
           "wymiana_data": (now.date() + timedelta(days=left)).isoformat(), "online": online,
           "status": st, "status_etykieta": STATUS[st][0], "ostatni_odczyt": reading,
           "odczyty_24h": n24, "odczyty_7d": sum(series), "odczyty_dni": series}
    if full:
        out["kosz"] |= {"rodzaj": p.kind, "pojemnosc_l": CAPACITY_L.get(p.kind)}
        out["urzadzenie"] = {"typ": k["label"], "model": info.model, "numer_seryjny": info.serial, "firmware": info.firmware,
                             "zainstalowano": info.installed_at.isoformat(), "zywotnosc_baterii_dni": k["life_days"],
                             "pojemnosc_baterii_mah": k["capacity_mah"], "interwal_odczytow_min": k["interval_min"],
                             "przewidywana_wymiana": out["wymiana_data"], "ostatni_sygnal": seen.isoformat(),
                             "ostatni_autotest": selftest_at.isoformat() if selftest_at else None, "autotest_ok": selftest_ok}
        out["seria"] = {"dni": [d.isoformat() for d in days], "odczyty": series}
    return out


def _query():
    return (db.session.query(DeviceInfo, Point, Device).join(Point, Point.id == DeviceInfo.point_id)
            .outerjoin(Device, Device.point_id == DeviceInfo.point_id))


def overview(now, kind=None, district=None):
    """Lista urządzeń (filtr typu i dzielnicy) posortowana wg pilności: status, potem dni do wymiany."""
    q = _query()
    if kind:
        q = q.filter(DeviceInfo.kind == kind)
    if district:
        q = q.filter(Point.district == district)
    presses = _presses(now)
    items = [_item(i, p, d, now, presses) for i, p, d in q]
    return sorted(items, key=lambda x: (STATUS[x["status"]][1], x["dni_do_wymiany"], x["id"]))


def detail(point_id, now):
    row = _query().filter(DeviceInfo.point_id == point_id).first()
    return _item(*row, now, _presses(now), full=True) if row else None


def counts_by_kind(kind=None, district=None):
    """Liczba urządzeń wg typu (GROUP BY), z tymi samymi filtrami co lista."""
    q = db.session.query(DeviceInfo.kind, func.count()).join(Point, Point.id == DeviceInfo.point_id)
    if kind:
        q = q.filter(DeviceInfo.kind == kind)
    if district:
        q = q.filter(Point.district == district)
    return dict(q.group_by(DeviceInfo.kind).all())


def districts():
    return sorted(d for (d,) in db.session.query(Point.district).join(DeviceInfo, DeviceInfo.point_id == Point.id).distinct() if d)
