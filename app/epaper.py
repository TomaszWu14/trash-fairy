"""Stan wyświetlacza e-papierowego na koszu (docs/epapier/HANDOFF.md): wyzwalacze, priorytety, dane do renderera.

Priorytet przy konflikcie: fault > overflow > confirm > enroute > emptied > night > calm. Reguły w kodzie, bez AI.
Pas stanu (head/big/sub) zawiera tylko treści stałe dla stanu → zmiana = pełne odświeżenie (mignięcie).
Wszystko, co zmienia się w trakcie stanu (zapełnienie, czasy, liczba osób) → pola fill/b/c okna częściowego.
"""
import hashlib
from datetime import timedelta

from . import db
from .events import AFTER, RADIUS_M
from .geo import distance_m
from .models import Device, Emptying, Event, Point, Report
from .reports import MERGE_WINDOW
from .residents import HEARTBEAT_LOST
from .routes import next_runs
from .state import current_routes, point_states

EMPTIED_HOLD = timedelta(minutes=60)   # „Opróżniono” znika po godzinie
ENROUTE_BEFORE = timedelta(minutes=45)  # ekipa „wyjechała”: tyle przed godziną kursu, gdy punkt jest na trasie
FAULT_BATTERY = 15                      # % — poniżej przycisk może nie działać
NIGHT = (22, 6)
STOP_MINUTES = 3                        # szacunek: tyle minut na przystanek (tylko do „Przyjazd ok. X min”)


def plural_people(n):
    return f"{n} {'osoba' if n == 1 else 'osoby' if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else 'osób'}"


def _when(run_at, now):
    return f"{'jutro ' if run_at.date() > now.date() else 'ok. '}{run_at:%H:%M}"


def device_info(point):
    """Dane urządzenia do renderera; `qr` = dzienny token kosza (kod „zgłoś” na ekranie zmienia się raz na dobę)."""
    from .api_pl import qr_token  # import lokalny: api_pl ładuje silnik stanu, jak ten moduł
    return {"name": point.name, "device_no": str(point.id), "address": point.osm_tags.get("addr:street") or point.area,
            "qr": qr_token(point.id)}


def display_state(point, now, states=None, routes=None):
    """(state, data) dla renderera. `states`/`routes` można podać z zewnątrz, żeby nie liczyć ich wiele razy."""
    states = states or point_states(now)
    s = states[point.id]
    device = db.session.get(Device, point.id)
    report = (Report.query.filter(Report.point_id == point.id, Report.hit.is_(None), Report.first_at <= now)
              .order_by(Report.first_at.desc()).first())
    last_empty = (Emptying.query.filter(Emptying.point_id == point.id, Emptying.at <= now)
                  .order_by(Emptying.at.desc()).first())
    run_at, following = next_runs(point.kind, now)
    battery = device.battery if device else 78
    heartbeat = device.last_heartbeat if device else now
    fill = s["level"]
    data = {"device": device_info(point), "fill": fill,
            "foot": f"Bateria {battery} % · ostatni sygnał {heartbeat:%H:%M}"}
    people = plural_people(report.presses) if report else None

    # fault: brak sygnału ≥ 48 h albo bateria < 15 %
    if device and (device.last_heartbeat < now - HEARTBEAT_LOST or device.battery < FAULT_BATTERY):
        lost = device.last_heartbeat < now - HEARTBEAT_LOST
        data.update(sub=(f"Brak sygnału od {int((now - device.last_heartbeat).total_seconds() // 3600)} h, " if lost else "")
                    + f"bateria {battery} %. Zgłoszenie przez QR działa.",
                    fill=None, b=("Serwis", "za 2 dni rob."), c=("Bateria", f"{battery} %"),
                    foot=f"Bateria {battery} % · ostatni sygnał {heartbeat:%d.%m, %H:%M}")
        return "fault", data
    # overflow: szacunek z prognozy ≥ 100 % przy otwartym zgłoszeniu (nie „value”, które samo zgłoszenie podbija)
    if report and s["level"] >= 100:
        in_event = any(distance_m(point.lat, point.lon, e.lat, e.lon) <= RADIUS_M[e.scale]
                       for e in Event.query.filter(Event.start <= now, Event.end + AFTER > now))
        data.update(big=f"Zgłoszenie przyjęte {report.first_at:%H:%M}", fill=min(100, fill),
                    sub="Trwa wydarzenie, kosz zapełnia się szybciej. Czas odbioru może się wydłużyć." if in_event
                    else "Kosz zapełnił się przed planowym odbiorem. Zgłoszenie podniosło jego priorytet.",
                    b=("Odbiór planowo", _when(run_at, now)), c=("Zgłosiły", people))
        return "overflow", data
    # confirm: świeże zgłoszenie (okno scalania) albo zgłoszenie bez przystanku na trasie
    stop = None
    if report:
        fresh = now - report.last_at <= MERGE_WINDOW
        if not fresh:
            routes = routes if routes is not None else current_routes(now)
            for f in routes:
                for st in f["stops"]:
                    if st["id"] == point.id:
                        stop = (st["order"], len(f["stops"]), f)
        if fresh or stop is None or now < run_at - ENROUTE_BEFORE:
            data.update(big=f"Zgłoszenie przyjęte o {report.first_at:%H:%M}", b=("Ekipa", _when(run_at, now)), c=("Zgłosiły", people))
            return "confirm", data
        order, total, f = stop
        minutes = max(1, int((run_at - now).total_seconds() // 60) + order * STOP_MINUTES)
        data.update(b=("Przyjazd", f"ok. {minutes} min"), c=("Przystanek", f"{order} z {total}"))
        return "enroute", data
    # emptied: opróżnienie z ostatniej godziny
    if last_empty and now - last_empty.at <= EMPTIED_HOLD:
        data.update(big=f"{last_empty.at:%H:%M} · dziękujemy", sub=f"Następny odbiór {_when(run_at, now)}. Zarejestrowani dostają +10 pkt.",
                    fill=min(fill, 10), b=("Następny odbiór", _when(run_at, now)), c=("Zgłoszenia", "zamknięte"))
        return "emptied", data
    # night: 22–06 przy spokoju
    if now.hour >= NIGHT[0] or now.hour < NIGHT[1]:
        data.update(big=f"Odbiór {_when(run_at, now)}", foot="Tryb oszczędny · odświeżanie co godzinę")
        return "night", data
    data.update(b=("Następny odbiór", _when(run_at, now)), c=("Zgłoszenia", "brak"))
    return "calm", data


def keys(state, data):
    """state_key zmienia się tylko przy pełnym odświeżeniu, values_key przy zmianie okna częściowego."""
    full = (state, data.get("head"), data.get("big"), data.get("sub"), data["device"]["device_no"], data["device"].get("qr"))
    partial = (data.get("fill"), data.get("b"), data.get("c"))
    # hashlib, nie hash(): hash() napisów jest losowany per proces, a 2 workery dawałyby różne klucze (fałszywe mignięcia)
    digest = lambda t: hashlib.sha1(repr(t).encode()).hexdigest()[:12]
    return digest(full), digest(partial)
