"""Wydarzenia z Karnet Kraków (koncepcja, sekcja 6.4). Publicznego API brak — czytamy listę wydarzeń.

Lista Karnetu ma już współrzędne (data-latitude/longitude), więc geokodowanie nie jest potrzebne.
Brakuje godzin i skali tłumu: uzupełnia je Claude z opisu (llm.ask_json), a bez klucza — jawne reguły domyślne.
Wynik pobrania trafia do data/karnet.json, żeby demo nie zależało od sieci.
"""
import html
import json
import re
import time
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

from . import db, llm
from .models import Event

BASE = "https://karnet.krakowculture.pl"
LISTS = ["/wydarzenia", "/wydarzenia/festiwale,30", "/wydarzenia/koncerty,21"]
CACHE = Path(__file__).resolve().parent.parent / "data" / "karnet.json"
USER_AGENT = "trash-fairy-hackyeah/0.1 (HackYeah 2026, demo projektu Smart City)"
DELAY_S = 1.0  # grzecznie: jedno zapytanie na sekundę
BBOX = (50.045, 19.925, 50.070, 19.975)  # Stare Miasto + Kazimierz + Grzegórzki (S, W, N, E)
LONG_RUNNING_DAYS = 7  # wystawy trwające tygodniami nie ściągają tłumów jednego dnia
MAX_ENRICH = 15

SCHEMA = {
    "type": "object",
    "properties": {
        "start_hour": {"type": "integer", "minimum": 0, "maximum": 24},
        "end_hour": {"type": "integer", "minimum": 0, "maximum": 24},
        "scale": {"type": "string", "enum": ["small", "medium", "large"]},
    },
    "required": ["start_hour", "end_hour", "scale"],
    "additionalProperties": False,
}
SYSTEM = (
    "Dostajesz opis wydarzenia z Karnet Kraków. Oszacuj godziny trwania danego dnia (pełne godziny 0–23) "
    "i skalę tłumu w okolicy miejsca: small (do ok. 200 osób), medium (do ok. 2000), large (więcej, np. plenerowy festiwal). "
    "Jeśli w tekście nie ma godzin, przyjmij typowe dla tego rodzaju wydarzenia."
)


def _text(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def _first(pattern, chunk):
    m = re.search(pattern, chunk, re.S)
    return _text(m.group(1)) if m else ""


def parse_list(page):
    """[{id, name, lat, lon, type, location, start, end, text, url}] z HTML listy wydarzeń."""
    items = []
    for chunk in re.split(r"<div class='event-item'", page)[1:]:
        head = re.match(r'\s*data-id="(\d+)"\s+data-name="([^"]*)"\s+data-latitude="([-\d.]+)"\s+data-longitude="([-\d.]+)"',
                        chunk)
        if not head:
            continue
        link = re.search(r'href="(/\d+[^"]*)"', chunk)
        dates = re.findall(r"(\d{2})\.(\d{2})\.(\d{4})", _first(r"class='event-date'>(.*?)</a>", chunk))
        if not dates:
            continue
        days = [date(int(y), int(m), int(d)) for d, m, y in dates]
        items.append({
            "id": head.group(1), "name": html.unescape(head.group(2)),
            "lat": float(head.group(3)), "lon": float(head.group(4)),
            "type": _first(r'class="event-type">(.*?)</span>', chunk),
            "location": _first(r"class='event-location'>(.*?)</p>", chunk),
            "start": days[0].isoformat(), "end": days[-1].isoformat(),
            "text": _first(r"class='event-text'>(.*?)</p>", chunk),
            "url": BASE + link.group(1) if link else BASE,
        })
    return items


def in_demo(item, day):
    s, w, n, e = BBOX
    return (s <= item["lat"] <= n and w <= item["lon"] <= e
            and date.fromisoformat(item["start"]) <= day <= date.fromisoformat(item["end"]))


def default_details(item):
    """Jawne reguły, gdy AI niedostępne: festiwale/koncerty średni tłum, wystawy i długie cykle mały."""
    long_running = (date.fromisoformat(item["end"]) - date.fromisoformat(item["start"])).days > LONG_RUNNING_DAYS
    kind = item["type"].lower()
    if long_running or "wystaw" in kind:
        return {"start_hour": 10, "end_hour": 18, "scale": "small"}
    if "koncert" in kind or "festiwal" in kind:
        return {"start_hour": 18, "end_hour": 22, "scale": "medium"}
    return {"start_hour": 17, "end_hour": 21, "scale": "small"}


def details(item):
    """(szczegóły, źródło): z Claude albo z reguł domyślnych (przy braku klucza lub błędzie API)."""
    try:
        d = llm.ask_json("Opis wydarzenia ze strony Karnetu:\n" + llm.fence(
            f"Nazwa: {item['name']}\nTyp: {item['type']}\nMiejsce: {item['location']}\n"
            f"Daty: {item['start']} – {item['end']}\nOpis: {item['text']}"), SCHEMA, system=SYSTEM, max_tokens=1000)
        if 0 <= d["start_hour"] < d["end_hour"] <= 24:
            return d, "ai"
    except llm.LLMError:
        pass
    return default_details(item), "rules"


def fetch(pages_per_list=5, opener=urllib.request.urlopen):
    """Pobiera listy wydarzeń (grzecznie, z opóźnieniem) i zapisuje do cache. Zwraca liczbę wydarzeń."""
    seen = {}
    for path in LISTS:
        for page in range(1, pages_per_list + 1):
            req = urllib.request.Request(f"{BASE}{path}?Item_page={page}", headers={"User-Agent": USER_AGENT})
            with opener(req, timeout=30) as r:
                for item in parse_list(r.read().decode("utf-8", errors="replace")):
                    seen[item["id"]] = item
            time.sleep(DELAY_S)
    CACHE.write_text(json.dumps(list(seen.values()), ensure_ascii=False, indent=0), encoding="utf-8")
    return len(seen)


def import_events(days, items=None):
    """Zastępuje wydarzenia z Karnetu (source='karnet') wydarzeniami z obszaru demo w podanych dniach."""
    if items is None:
        if not CACHE.exists():
            return 0
        items = json.loads(CACHE.read_text(encoding="utf-8"))
    db.session.query(Event).filter_by(source="karnet").delete()
    added, cache = 0, {}
    for day in days:
        for item in [i for i in items if in_demo(i, day)][:MAX_ENRICH]:
            if item["id"] not in cache:  # jedno wywołanie AI na wydarzenie, nie na dzień
                cache[item["id"]] = details(item)[0]
            d = cache[item["id"]]
            start = datetime.combine(day, datetime.min.time()) + timedelta(hours=d["start_hour"])
            end = datetime.combine(day, datetime.min.time()) + timedelta(hours=d["end_hour"])
            db.session.add(Event(name=item["name"][:200], venue=(item["location"] or "Kraków")[:200], lat=item["lat"],
                                 lon=item["lon"], start=start, end=end, scale=d["scale"], source="karnet"))
            added += 1
    db.session.commit()
    return added
