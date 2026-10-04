"""Dzikie wysypiska: odpady poza koszami (worki przed ogródkami działkowymi, gabaryty pod wiatą) — reguły w kodzie.

Zgłasza mieszkaniec albo ekipa MPO. Kosza nie ma, więc położenie (GPS albo pinezka) jest treścią zgłoszenia.
AI (app/llm.py) tylko OPISUJE zdjęcie: czy widać odpady poza pojemnikiem, ile mniej więcej worków, jakie rodzaje,
czy są osoby albo tablice (wtedy zdjęcia nie pokazujemy publicznie). Status nadaje reguła (state):
„Uprzątnięte” (ekipa) > „Zweryfikowane AI” (widać odpady, pewność ≥ 0,7) > „Potwierdzone” (drugie zgłoszenie z innego
telefonu) > „Do weryfikacji”. Bez klucza API albo przy błędzie analizy → „Do weryfikacji”, nigdy 500.
Duplikat: zgłoszenie do 50 m od otwartego wysypiska z ostatnich 72 h dołącza do niego (+1 potwierdzenie z innego telefonu).
Miejsce: wysypiska do 100 m od siebie w 90 dni; drabinka jak przy podrzucaniu przy koszach (app/dumping.py: level):
≥ 2 tablica i edukacja, ≥ 4 kontrola Straży Miejskiej, ≥ 6 rozważ fotopułapkę (decyzja gminy).
"""
import hashlib
import hmac
import threading
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from flask import current_app
from sqlalchemy import or_

from . import db, llm, photos
from .geo import distance_m
from .models import DumpReport
from .residents import DUMP_DAILY_LIMIT, DUMP_POINTS

KINDS = {"bio": "Bio", "tworzywa": "Tworzywa sztuczne", "papier": "Papier", "szklo": "Szkło", "gabaryty": "Gabaryty",
         "gruz": "Gruz, odpady budowlane", "mieszane": "Zmieszane", "inne": "Inne"}
QTY_MAX = 100
KRAKOW = (49.95, 19.77, 50.14, 20.24)  # S, W, N, E: granice Krakowa z marginesem ok. 2 km
DUP_RADIUS_M, DUP_WINDOW = 50, timedelta(hours=72)
SITE_RADIUS_M, SITE_DAYS = 100, 90
CREW_PTS_PHOTO, CREW_PTS_CLEARED = 3, 2  # app/crew_points.py: podrzucenie ze zdjęciem też +3
PENDING_MAX = photos.PENDING_MAX
STATUS = {"uprzatniete": "Uprzątnięte", "zweryfikowane": "Zweryfikowane AI", "potwierdzone": "Potwierdzone",
          "w_toku": "Analiza AI w toku", "do_weryfikacji": "Do weryfikacji"}
# te dają punkty; „Potwierdzone” nie: id telefonu przysyła sam telefon, więc drugie zgłoszenie da się podrobić
VERIFIED = {"uprzatniete", "zweryfikowane"}

SCHEMA = {
    "type": "object",
    "properties": {
        "waste_outside_container": {"type": "boolean"},
        "bags": {"type": "integer", "minimum": 0, "maximum": QTY_MAX},
        "kinds": {"type": "array", "items": {"type": "string", "enum": list(KINDS)}, "maxItems": len(KINDS)},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string", "maxLength": 200},
        "people_or_plates": {"type": "boolean"},
    },
    "required": ["waste_outside_container", "bags", "kinds", "confidence", "reason", "people_or_plates"],
    "additionalProperties": False,
}
SYSTEM = (
    "Oceniasz zdjęcie dołączone do zgłoszenia dzikiego wysypiska w Krakowie (odpady porzucone poza pojemnikami). "
    "Opisujesz wyłącznie odpady: czy leżą poza pojemnikiem lub koszem (waste_outside_container), przybliżoną liczbę worków "
    "lub sztuk (bags, 0–100), rodzaje (kinds: bio, tworzywa, papier, szklo, gabaryty, gruz, mieszane, inne) i pewność "
    "oceny (confidence 0–1). Pole reason: jedno krótkie zdanie po polsku, tylko o odpadach i miejscu. "
    "people_or_plates = true, jeśli da się rozpoznać osobę (twarz, sylwetkę) albo tablicę rejestracyjną; nie opisuj ich. "
    "Nie oceniaj ludzi ani ich zachowania. Jeśli na zdjęciu nie widać odpadów, ustaw waste_outside_container = false "
    "i confidence poniżej 0.3."
)


def _wall():
    return datetime.now(UTC).replace(tzinfo=None)


def numer(rid):
    return f"WD-{rid:05d}"


def from_nr(nr):
    try:
        rid = int(str(nr).upper().removeprefix("WD-"))
        return db.session.get(DumpReport, rid) if 0 < rid < 2**31 else None
    except (TypeError, ValueError):
        return None


def client_hash(raw):
    """Identyfikator telefonu jako HMAC: niezależność potwierdzeń bez trzymania surowego id."""
    key = current_app.config["SECRET_KEY"].encode()
    return hmac.new(key, f"wd:{raw}".encode(), hashlib.sha256).hexdigest()[:32]


def in_krakow(lat, lon):
    s, w, n, e = KRAKOW
    return s <= lat <= n and w <= lon <= e


# ---------- reguły statusu ----------
def ai_status(ai):
    """Reguła (nie AI): widać odpady poza pojemnikiem i pewność ≥ progu weryfikacji zdjęć (0,7)."""
    ok = ai.get("status") == "done" and ai["widac_odpady"] and ai["pewnosc"] >= photos.VERIFY_MIN_CONFIDENCE
    return "zweryfikowane" if ok else "do_weryfikacji"


def state(g, rows):
    """Status wysypiska `g` (wiersz bez parent_id) z jego zgłoszeń `rows` (z nim samym)."""
    if g.cleared_at:
        return "uprzatniete"
    if any(r.status == "zweryfikowane" for r in rows):
        return "zweryfikowane"
    if g.confirmations >= 2:
        return "potwierdzone"
    if any(r.status == "w_toku" and _wall() - r.wall_at <= PENDING_MAX for r in rows):
        return "w_toku"  # dłużej „w toku” = wątek analizy padł (restart workera): „Do weryfikacji”
    return "do_weryfikacji"


def reason(st, rows):
    if st == "uprzatniete":
        return "Ekipa MPO oznaczyła miejsce jako uprzątnięte."
    if st == "zweryfikowane":
        conf = max(r.ai["pewnosc"] for r in rows if r.status == "zweryfikowane")
        return (f"AI widzi na zdjęciu odpady poza pojemnikiem (pewność {round(conf * 100)}%). Status nadała reguła: "
                f"widać odpady i pewność od {round(photos.VERIFY_MIN_CONFIDENCE * 100)}%.")
    if st == "potwierdzone":
        return f"Drugie zgłoszenie z innego telefonu w promieniu {DUP_RADIUS_M} m w ciągu {DUP_WINDOW.days * 24} h."
    if st == "w_toku":
        return "Sprawdzamy zdjęcie, to potrwa kilka sekund."
    if not any(r.media_type for r in rows):
        return "Zgłoszenie bez zdjęcia: miejsce sprawdzi ekipa MPO."
    if any((r.ai or {}).get("status") == "error" or r.status == "w_toku" for r in rows):
        return "Analiza AI niedostępna. Zdjęcie sprawdzi dyspozytor."
    return f"AI nie potwierdziła odpadów na zdjęciu z pewnością od {round(photos.VERIFY_MIN_CONFIDENCE * 100)}%. Sprawdzi dyspozytor."


def public_photo(r):
    """Zdjęcie pokazujemy tylko, gdy reguła je zweryfikowała (widać odpady, pewność ≥ 0,7) i AI nie widzi osób ani
    tablic. Zdjęcie bez odpadów (napis, mem, zrzut ekranu) i każde bez klucza API zostaje niepubliczne."""
    return bool(r.photo_path and r.status == "zweryfikowane" and not r.ai["osoby"])


# ---------- zapis i łączenie ----------
def find_open(lat, lon, now):
    """Najbliższe otwarte wysypisko do DUP_RADIUS_M z ostatnich DUP_WINDOW albo None."""
    near = [(distance_m(lat, lon, r.lat, r.lon), r.id, r)
            for r in DumpReport.query.filter(DumpReport.parent_id.is_(None), DumpReport.cleared_at.is_(None),
                                             DumpReport.at > now - DUP_WINDOW, DumpReport.at <= now)]
    near = [x for x in near if x[0] <= DUP_RADIUS_M]
    return min(near)[2] if near else None


def group_rows(g):
    return [g, *DumpReport.query.filter_by(parent_id=g.id).order_by(DumpReport.id)]


def create(now, lat, lon, kinds, qty, note, raw, mt, source, client, resident_id):
    """Zapisuje zgłoszenie; duplikat dołącza do otwartego wysypiska. Zwraca (zgłoszenie, wysypisko)."""
    parent = find_open(lat, lon, now)
    r = DumpReport(at=now, wall_at=_wall(), lat=lat, lon=lon, kinds=kinds, qty=qty, note=note, source=source,
                   client=client, resident_id=resident_id, parent_id=parent.id if parent else None)
    if raw:
        path = photos.photo_dir() / f"wd-{uuid.uuid4().hex}.{mt.split('/')[1].replace('jpeg', 'jpg')}"
        path.write_bytes(raw)
        r.photo_path, r.media_type, r.ai, r.status = str(path), mt, {"status": "pending"}, "w_toku"
    rows = group_rows(parent) if parent else []
    if parent and client not in {x.client for x in rows} and not (resident_id and resident_id in {x.resident_id for x in rows}):
        parent.confirmations += 1  # ten sam telefon albo to samo konto drugi raz nie jest niezależnym potwierdzeniem
    db.session.add(r)
    db.session.commit()
    return r, parent or r


def analyze(rid):
    """Opis zdjęcia od AI + status z reguły. Każdy błąd (brak klucza, sieć, zły JSON) → „Do weryfikacji”, bez wyjątku."""
    r = db.session.get(DumpReport, rid)
    try:
        result = llm.ask_json("Opisz to zdjęcie według schematu.", SCHEMA, system=SYSTEM,
                              images=[llm.image_block(Path(r.photo_path).read_bytes(), r.media_type)], max_tokens=1500)
        r.ai = {"status": "done", "widac_odpady": result["waste_outside_container"], "worki": result["bags"],
                "rodzaje": [k for k in result["kinds"] if k in KINDS], "pewnosc": float(result["confidence"]),
                "opis": result["reason"][:200], "osoby": result["people_or_plates"]}
    except Exception as e:  # LLMError, OSError i każdy inny: analiza nie może zostać „w toku” na zawsze
        r.ai = {"status": "error", "blad": str(e)[:255] or type(e).__name__}
    r.status = ai_status(r.ai)
    db.session.commit()
    return r


def analyze_in_background(rid):
    """Jak photos.analyze_in_background: telefon nie czeka na AI; w testach (TESTING) od razu, deterministycznie."""
    app = current_app._get_current_object()
    if app.config.get("TESTING"):
        return analyze(rid)

    def run():
        with app.app_context():
            analyze(rid)

    threading.Thread(target=run, daemon=True).start()


# ---------- odczyt: lista, miejsca, status ----------
def _groups(rows):
    """{id wysypiska: (wysypisko, [jego zgłoszenia])} — tylko grupy, których wysypisko jest w `rows`."""
    by = defaultdict(list)
    for r in rows:
        by[r.parent_id or r.id].append(r)
    return {gid: (g, rs) for gid, rs in by.items() for g in rs if g.id == gid}


def sites(parents):
    """Miejsca: wysypiska do SITE_RADIUS_M od pierwszego wysypiska miejsca (od najstarszego).
    ponytail: zachłanne kotwiczenie O(n·miejsca); przy tysiącach zgłoszeń indeks przestrzenny."""
    from .dumping import LEVELS, level  # import lokalny: dumping ciągnie cały dashboard
    out = []
    for g in sorted(parents, key=lambda g: (g.at, g.id)):
        s = next((s for s in out if distance_m(g.lat, g.lon, s["lat"], s["lon"]) <= SITE_RADIUS_M), None)
        if s is None:
            s = {"id": len(out) + 1, "lat": g.lat, "lon": g.lon, "wysypiska": []}
            out.append(s)
        s["wysypiska"].append(numer(g.id))
    for s in out:
        n = len(s["wysypiska"])
        s["poziom"] = level(n, 0)  # bez reguły dnia tygodnia: dzikie wysypiska to rzadkie zdarzenia
        s["etykieta"] = LEVELS.get(s["poziom"])
        s["powod"] = f"{n} {_plural(n, 'wysypisko', 'wysypiska', 'wysypisk')} w promieniu {SITE_RADIUS_M} m w {SITE_DAYS} dni."
    return out


def _plural(n, one, few, many):
    return one if n == 1 else few if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else many


def _kinds(rows):
    chosen = {k for r in rows for k in r.kinds or []}
    return [label for k, label in KINDS.items() if k in chosen]


def item(g, rows):
    """Wysypisko dla dashboardu i statusu: bez komentarza (może mieć dane osobowe) i bez zdjęć z osobami."""
    st = state(g, rows)
    photo = next((r for r in rows if public_photo(r)), None)
    described = next((r for r in rows if r.status == "zweryfikowane"), None) or next(
        (r for r in reversed(rows) if (r.ai or {}).get("status") == "done"), None)
    qty = [r.qty for r in rows if r.qty]
    return {"numer": numer(g.id), "lat": round(g.lat, 5), "lon": round(g.lon, 5), "rodzaje": _kinds(rows),
            "ilosc": max(qty) if qty else None, "status": st, "etykieta": STATUS[st], "uzasadnienie": reason(st, rows),
            "zrodlo": "ekipa" if g.source == "crew" else "mieszkaniec", "zgloszono": g.at.isoformat(),
            "uprzatnieto": g.cleared_at.isoformat() if g.cleared_at else None, "potwierdzenia": g.confirmations,
            "zgloszen": len(rows), "zdjecie": f"/api/wysypiska/{numer(photo.id)}/zdjecie" if photo else None,
            "ai": None if described is None else {
                "widac_odpady": described.ai["widac_odpady"], "worki": described.ai["worki"],
                "rodzaje": [KINDS[k] for k in described.ai["rodzaje"]], "pewnosc": round(described.ai["pewnosc"], 2),
                "opis": described.ai["opis"], "zdjecie_publiczne": not described.ai["osoby"]}}


def overview(now):
    """Otwarte i uprzątnięte wysypiska z SITE_DAYS dni oraz miejsca z poziomem drabinki (od najpoważniejszych)."""
    rows = (DumpReport.query.filter(DumpReport.at > now - timedelta(days=SITE_DAYS), DumpReport.at <= now)
            .order_by(DumpReport.at, DumpReport.id).all())
    groups = _groups(rows)
    site_list = sites([g for g, _ in groups.values()])
    site_of = {nr: s["id"] for s in site_list for nr in s["wysypiska"]}
    items = [item(g, rs) | {"miejsce": site_of[numer(g.id)]} for g, rs in groups.values()]
    items.sort(key=lambda x: x["zgloszono"], reverse=True)
    items.sort(key=lambda x: x["status"] == "uprzatniete")  # otwarte najpierw, w każdej grupie najnowsze na górze
    from .dumping import RANK
    site_list.sort(key=lambda s: (RANK.get(s["poziom"], len(RANK)), -len(s["wysypiska"])))
    return {"wysypiska": items, "miejsca": site_list,
            "otwarte": sum(x["status"] != "uprzatniete" for x in items), "okres_dni": SITE_DAYS}


def detail(r, now):
    """Status dla zgłaszającego (numer własnego zgłoszenia albo wysypiska, do którego dołączyło)."""
    g = db.session.get(DumpReport, r.parent_id) if r.parent_id else r
    site = next((s for s in overview(now)["miejsca"] if numer(g.id) in s["wysypiska"]), None)
    return item(g, group_rows(g)) | {"komentarz": g.note, "miejsce": site}


# ---------- punkty ----------
def resident_dump_items(resident_id):
    """Pozycje punktów mieszkańca za wysypiska (reguła): +DUMP_POINTS raz na wysypisko, tylko za zgłoszenie ze zdjęciem,
    najwyżej DUMP_DAILY_LIMIT na dobę (zegar demo). Zgłoszenie dołączone do wcześniejszego: tylko gdy jego WŁASNE zdjęcie
    przeszło regułę AI. Pierwsze zgłoszenie: gdy dowolne zdjęcie wysypiska przeszło regułę AI albo wysypisko oznaczył
    „Uprzątnięte” inny telefon niż telefony tego mieszkańca. „Potwierdzone” (drugie zgłoszenie) punktów nie daje.
    Liczone przy odczycie, bez tabeli nagród: status tylko rośnie, więc suma się nie cofa.
    ponytail: id telefonu przysyła telefon; docelowo „Uprzątnięte” tylko z tokenem ekipy (jak devices_api)."""
    mine = DumpReport.query.filter_by(resident_id=resident_id).order_by(DumpReport.at, DumpReport.id).all()
    if not mine:
        return []
    phones = {r.client for r in mine}
    gids = {r.parent_id or r.id for r in mine}
    groups = _groups(DumpReport.query.filter(or_(DumpReport.id.in_(gids), DumpReport.parent_id.in_(gids))).all())
    awarded, per_day, out = set(), Counter(), []
    for r in mine:
        gid = r.parent_id or r.id
        if gid in awarded or gid not in groups:
            continue
        g, rows = groups[gid]
        by_ai = r.status == "zweryfikowane" if r.parent_id else any(x.status == "zweryfikowane" for x in rows)
        by_crew = not r.parent_id and g.cleared_at is not None and g.cleared_by not in phones
        pts = 0
        if not r.media_type:
            why = "Bez zdjęcia: punkty są tylko za zgłoszenia ze zdjęciem"
        elif not (by_ai or by_crew):
            why = ("Dołączone do wcześniejszego zgłoszenia: punkty, gdy AI potwierdzi Twoje zdjęcie" if r.parent_id
                   else "Uprzątnięte z telefonu, z którego przyszło zgłoszenie: bez punktów" if g.cleared_at
                   else "Czeka na weryfikację")
        elif per_day[r.at.date()] >= DUMP_DAILY_LIMIT:
            why = f"Limit {DUMP_DAILY_LIMIT} nagrodzonych wysypisk na dobę"
        else:
            pts, why = DUMP_POINTS, f"Dzikie wysypisko: {'zweryfikowane AI' if by_ai else 'uprzątnięte przez ekipę'}"
            per_day[r.at.date()] += 1
            awarded.add(gid)
        out.append({"numer": numer(gid), "o": r.at.isoformat(), "punkty": pts, "powod": why})
    return out


def crew_dump_points(now, days=30):
    """Pozycje punktów ekipy za wysypiska z `days` dni, w formacie crew_points.crew_points()["pozycje"]:
    +3 za zgłoszenie ekipy ze zdjęciem, gdy wysypisko jest „Zweryfikowane AI” albo „Uprzątnięte” (raz na wysypisko),
    +2 za „Uprzątnięte”."""
    since = now - timedelta(days=days)
    rows = DumpReport.query.filter(DumpReport.at > since - DUP_WINDOW, DumpReport.at <= now).all()
    out = []
    for g, rs in _groups(rows).values():
        nr, st = numer(g.id), state(g, rs)
        crew = next((r for r in rs if r.source == "crew" and r.media_type and r.at > since), None)
        if crew and st in VERIFIED:
            out.append({"kosz_id": None, "kosz": f"Dzikie wysypisko {nr}", "data": crew.at.isoformat(),
                        "rodzaj": "wysypisko_ze_zdjeciem", "punkty": CREW_PTS_PHOTO,
                        "opis": f"Zgłoszenie dzikiego wysypiska ze zdjęciem, status: {STATUS[st].lower()}"})
        if g.cleared_at and since < g.cleared_at <= now:
            out.append({"kosz_id": None, "kosz": f"Dzikie wysypisko {nr}", "data": g.cleared_at.isoformat(),
                        "rodzaj": "wysypisko_uprzatniete", "punkty": CREW_PTS_CLEARED, "opis": "Wysypisko uprzątnięte"})
    return sorted(out, key=lambda x: x["data"], reverse=True)


# ---------- retencja i reset demo ----------
def cleanup(now_wall=None):
    """Zdjęcia starsze niż 7 dni (jak photos.cleanup): plik usuwamy, opis AI i media_type zostają."""
    now_wall = now_wall or _wall()
    rows = DumpReport.query.filter(DumpReport.photo_path.isnot(None), DumpReport.wall_at < now_wall - photos.RETENTION).all()
    for r in rows:
        Path(r.photo_path).unlink(missing_ok=True)
        r.photo_path = None
    db.session.commit()
    return len(rows)


def reset_demo():
    """Reset scenariusza: wysypiska z poprzedniego pokazu znikają razem z plikami zdjęć."""
    for r in DumpReport.query.filter(DumpReport.photo_path.isnot(None)):
        Path(r.photo_path).unlink(missing_ok=True)
    db.session.query(DumpReport).delete()
    db.session.commit()
