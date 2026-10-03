"""Program „Przyjaciele Wróżki” i stan urządzeń (spec: docs/superpowers/specs/2026-10-03-program-mieszkancow-design.md).

Reguły w kodzie: wiarygodność mieszkańca, potwierdzenia, punkty tylko za trafne zgłoszenia z limitem, odznaki,
rankingi. Telefon zapisujemy wyłącznie jako hash z sekretem aplikacji (RODO: minimalizacja danych).
"""
import hashlib
import hmac
import random
import re
from collections import defaultdict
from datetime import timedelta

from flask import current_app
from sqlalchemy import func

from . import db
from .models import Device, Point, PointAward, Press, Report, Resident
from .reports import reliability

START_RELIABILITY = 0.8
POINTS = {"bin": 10, "shelter": 15}  # +5 za altanę (pytanie 41)
DISTRICTS = {"Rynek": "Stare Miasto", "Kazimierz": "Kazimierz", "Grzegórzki": "Grzegórzki"}
HEARTBEAT_LOST = timedelta(hours=48)
LOW_BATTERY = 20
SELFTEST_EVERY = timedelta(hours=6)
BADGES = [  # (nazwa, opis, warunek na liście nagród)
    ("Pierwsze trafienie", "pierwsze trafne zgłoszenie", lambda aw, pts: len(aw) >= 1),
    ("Strażnik Plant", "5 trafnych zgłoszeń na Starym Mieście", lambda aw, pts: sum(pts[a.point_id].area == "Rynek" for a in aw) >= 5),
    ("Opiekun altan", "3 trafne zgłoszenia altan", lambda aw, pts: sum(a.kind == "shelter" for a in aw) >= 3),
]


class RegistrationError(Exception):
    pass


def normalize_phone(phone):
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("48") and len(digits) == 11:
        digits = digits[2:]
    if len(digits) != 9:
        raise RegistrationError("Podaj 9-cyfrowy numer telefonu.")
    return digits


def phone_hash(phone):
    key = current_app.config["SECRET_KEY"].encode()
    return hmac.new(key, normalize_phone(phone).encode(), hashlib.sha256).hexdigest()


def register(nick, phone, district, rng=random):
    nick = (nick or "").strip()
    if not 3 <= len(nick) <= 40:
        raise RegistrationError("Pseudonim: od 3 do 40 znaków.")
    if district not in DISTRICTS.values():
        raise RegistrationError("Wybierz dzielnicę.")
    h = phone_hash(phone)
    r = Resident.query.filter_by(phone_hash=h).first()
    if r and r.verified:
        raise RegistrationError("Ten numer jest już w programie (jedno konto na numer).")
    taken = Resident.query.filter_by(nick=nick).first()
    if taken and taken is not r:
        raise RegistrationError("Ten pseudonim jest zajęty.")
    if r is None:  # niepotwierdzony numer może poprosić o nowy kod (np. SMS nie doszedł) — to samo konto
        r = Resident(phone_hash=h)
        db.session.add(r)
    r.nick, r.district, r.code = nick, district, f"{rng.randrange(10**6):06d}"
    db.session.commit()
    return r


def verify(resident, code):
    """Kod demo (bez bramki SMS). Przy Twilio Verify kod sprawdza bramka, a potem wołamy mark_verified."""
    if resident.code and code == resident.code:
        mark_verified(resident)
        return True
    return False


def mark_verified(resident):
    resident.verified, resident.code = True, None
    db.session.commit()


def resident_reliability(resident_id):
    """Trafne z ostatnich 10 rozstrzygniętych zgłoszeń z naciśnięciem mieszkańca; start 80%."""
    hits = [hit for (hit,) in (db.session.query(Report.hit).join(Press, Press.report_id == Report.id)
                               .filter(Press.resident_id == resident_id, Report.hit.isnot(None))
                               .group_by(Report.id).order_by(Report.first_at.desc()).limit(10))]
    return reliability(list(reversed(hits))) if hits else START_RELIABILITY


def award(report, kind):
    """Punkty dla zarejestrowanych naciskających trafne zgłoszenie: raz na zgłoszenie, raz na punkt i dzień."""
    if not report.hit:
        return []
    awarded = []
    residents = {rid for (rid,) in db.session.query(Press.resident_id)
                 .filter(Press.report_id == report.id, Press.resident_id.isnot(None)).distinct()}
    day_start = report.first_at.replace(hour=0, minute=0, second=0, microsecond=0)
    for rid in residents:
        already = PointAward.query.filter(PointAward.resident_id == rid, PointAward.point_id == report.point_id,
                                          PointAward.at >= day_start, PointAward.at < day_start + timedelta(days=1)).first()
        if already:
            continue
        a = PointAward(resident_id=rid, point_id=report.point_id, report_id=report.id, at=report.resolved_at,
                       points=POINTS[kind], kind=kind)
        db.session.add(a)
        awarded.append(a)
    return awarded


def profile(resident):
    awards = PointAward.query.filter_by(resident_id=resident.id).order_by(PointAward.at.desc()).all()
    points = {p.id: p for p in Point.live_query()}
    reports = (db.session.query(Report).join(Press, Press.report_id == Report.id)
               .filter(Press.resident_id == resident.id).group_by(Report.id).order_by(Report.first_at.desc()).limit(10).all())
    return {
        "nick": resident.nick, "district": resident.district, "verified": resident.verified,
        "points": sum(a.points for a in awards), "hits": len(awards),
        "reliability": round(resident_reliability(resident.id) * 100),
        "badges": [{"name": n, "desc": d} for n, d, ok in BADGES if ok(awards, points)],
        "recent": [{"point": points[r.point_id].name, "at": f"{r.first_at:%d.%m %H:%M}",
                    "status": "trafne" if r.hit else ("fałszywe" if r.hit is False else "czeka na opróżnienie"),
                    "confirmed": r.confirmed} for r in reports],
    }


def rankings(limit=10):
    totals = dict(db.session.query(PointAward.resident_id, func.sum(PointAward.points)).group_by(PointAward.resident_id).all())
    residents = Resident.query.filter_by(verified=True).all()
    people = sorted(({"nick": r.nick, "district": r.district, "points": totals.get(r.id, 0)} for r in residents),
                     key=lambda x: -x["points"])
    districts = defaultdict(lambda: {"points": 0, "members": 0})
    for r in residents:
        districts[r.district]["points"] += totals.get(r.id, 0)
        districts[r.district]["members"] += 1
    return {"people": people[:limit], "members": len(residents),
            "districts": sorted(({"district": k, **v} for k, v in districts.items()), key=lambda x: -x["points"])}


# --- urządzenia: sygnał życia, bateria, autotest (bez wpływu na zgłoszenia) ---

def device_flags(now):
    """{point_id: powód} dla urządzeń bez sygnału od 48 h."""
    return {d.point_id: f"brak sygnału z przycisku od {d.last_heartbeat:%d.%m %H:%M}"
            for d in Device.query.filter(Device.last_heartbeat < now - HEARTBEAT_LOST)}


def devices_overview(now):
    points = {p.id: p for p in Point.live_query()}
    devs = Device.query.all()
    return {
        "total": len(devs),
        "offline": [{"point_id": d.point_id, "name": points[d.point_id].name, "since": f"{d.last_heartbeat:%d.%m %H:%M}"}
                    for d in devs if d.last_heartbeat < now - HEARTBEAT_LOST],
        "low_battery": [{"point_id": d.point_id, "name": points[d.point_id].name, "battery": d.battery}
                        for d in devs if d.battery < LOW_BATTERY],
        "selftest_due": sum(1 for d in devs if not d.last_selftest or d.last_selftest < now - SELFTEST_EVERY),
    }


def selftest(point_id, now):
    """Autotest wyświetlacza i przycisku: aktualizuje urządzenie, NIE tworzy naciśnięcia ani zgłoszenia."""
    d = db.session.get(Device, point_id)
    if d is None:
        return None
    d.last_selftest, d.selftest_ok, d.last_heartbeat = now, True, now
    db.session.commit()
    return d


DEMO_NICKS = [("Wróżkowa_Ania", "Stare Miasto"), ("Plantowicz", "Stare Miasto"), ("KazikNocą", "Kazimierz"),
              ("Grzegórz_z_bloku", "Grzegórzki"), ("ŚmieciowySzeryf", "Kazimierz"), ("Babcia_Hela", "Grzegórzki"),
              ("RowerMan", "Stare Miasto"), ("Zielona_Wstążka", "Kazimierz")]


def seed_demo(now, seed=5):
    """Urządzenia przy wszystkich punktach (2 bez sygnału, 2 ze słabą baterią) i 8 mieszkańców z historią punktów."""
    rng = random.Random(seed)
    for model in (PointAward, Device):
        db.session.query(model).delete()
    db.session.query(Press).filter(Press.resident_id.isnot(None)).update({"resident_id": None})
    db.session.query(Resident).delete()
    points = Point.live_query().order_by(Point.id).all()
    offline = {p.id for p in rng.sample(points, min(2, len(points)))}
    weak = {p.id for p in rng.sample(points, min(2, len(points)))} - offline
    for p in points:
        db.session.add(Device(point_id=p.id, battery=rng.randint(8, 18) if p.id in weak else rng.randint(45, 100),
                              last_heartbeat=now - (timedelta(hours=rng.randint(50, 70)) if p.id in offline
                                                    else timedelta(minutes=rng.randint(5, 600))),
                              last_selftest=now - timedelta(hours=rng.randint(0, 5))))
    for nick, district in DEMO_NICKS:
        r = Resident(nick=nick, phone_hash=hashlib.sha256(f"demo-{nick}".encode()).hexdigest(), district=district,
                     verified=True, source="demo")
        db.session.add(r)
        db.session.flush()
        local = [p for p in points if DISTRICTS.get(p.area) == district]
        for i in range(rng.randint(2, 12) if local else 0):
            p = rng.choice(local)
            db.session.add(PointAward(resident_id=r.id, point_id=p.id, at=now - timedelta(days=i, hours=rng.randint(1, 9)),
                                      points=POINTS[p.kind], kind=p.kind))
    db.session.commit()
