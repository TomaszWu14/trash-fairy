"""Symulator czujników zapełnienia: wysyła odczyty do POST /api/odczyty tak, jak robiłoby to urządzenie LoRaWAN/NB-IoT.

Użycie: python scripts/symulator_czujnikow.py [adres] [liczba_czujnikow]   (domyślnie http://127.0.0.1:5050, 5)
Tokeny liczy z SECRET_KEY środowiska (ta sama co serwera), jak przy wgrywaniu ich do urządzeń przy montażu.
"""
import json
import pathlib
import random
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from app import create_app, db  # noqa: E402
from app.devices_api import device_token  # noqa: E402
from app.models import DeviceInfo, Point  # noqa: E402

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:5050"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 5
with create_app().app_context():
    rows = [(i.serial, p.snapshot_fill or 0) for i, p in db.session.query(DeviceInfo, Point).join(Point, Point.id == DeviceInfo.point_id)
            .filter(DeviceInfo.kind == "czujnik").order_by(DeviceInfo.serial).limit(N)]
    tokens = {s: device_token(s) for s, _ in rows}
for serial, fill in rows:
    body = {"numer_seryjny": serial, "zapelnienie": min(100, fill + random.choice((0, 5, 10))), "autotest_ok": True}
    req = urllib.request.Request(f"{BASE}/api/odczyty", json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "X-Token-Urzadzenia": tokens[serial]})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(serial, r.status, json.load(r)["urzadzenie"]["status_etykieta"])
    except urllib.error.HTTPError as e:
        print(serial, e.code, json.load(e).get("blad"))
