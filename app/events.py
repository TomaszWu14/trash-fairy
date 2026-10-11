"""Wydarzenia i mnożnik tłumu (koncepcja, sekcje 6.3–6.4).

Etap 3: ręczna lista zapasowa z data/events.json (dane demonstracyjne). Pobieranie z Karnetu: etap 6.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

from . import db
from .geo import distance_m
from .models import Event

EVENTS_FILE = Path(__file__).resolve().parent.parent / "data" / "events.json"
RADIUS_M = {"small": 200, "medium": 400, "large": 800}
MULTIPLIER = {"small": 1.3, "medium": 1.6, "large": 2.0}
SCALE_PL = {"small": "mały tłum", "medium": "średni tłum", "large": "duży tłum"}
AFTER = timedelta(hours=1)  # ludzie rozchodzą się jeszcze godzinę po wydarzeniu


def import_events(path=EVENTS_FILE):
    db.session.query(Event).filter_by(source="manual").delete()
    for e in json.loads(path.read_text(encoding="utf-8")):
        try:
            ev = Event(name=e["name"], venue=e["venue"], lat=float(e["lat"]), lon=float(e["lon"]), scale=e["scale"],
                       start=datetime.fromisoformat(e["start"]), end=datetime.fromisoformat(e["end"]))
        except (KeyError, TypeError, ValueError):
            continue
        if ev.scale in RADIUS_M and ev.end > ev.start:  # nieznana skala dałaby KeyError w events_near przy każdym przeliczeniu
            db.session.add(ev)
    db.session.commit()


def events_near(lat, lon, events):
    return [e for e in events if distance_m(lat, lon, e.lat, e.lon) <= RADIUS_M[e.scale]]


def multiplier(at, near_events):
    """Mnożnik najsilniejszego wydarzenia w promieniu, aktywnego w godzinie `at` albo godzinę po nim."""
    return max((MULTIPLIER[e.scale] for e in near_events if e.start <= at < e.end + AFTER), default=1.0)
