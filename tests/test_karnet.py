import io
import json
from datetime import date, datetime
from pathlib import Path

import pytest

from app import karnet, llm
from app.models import Event

SAMPLE = (Path(__file__).parent / "fixtures" / "karnet_sample.html").read_text(encoding="utf-8")
SAT, SUN = date(2026, 10, 3), date(2026, 10, 4)


@pytest.fixture
def no_ai(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_parse_list_reads_coordinates_dates_and_text():
    items = karnet.parse_list(SAMPLE)
    assert [i["id"] for i in items] == ["101", "102", "103"]  # wpis bez daty pominięty
    jazz = items[0]
    assert jazz["name"] == "Jazz na Rynku & przyjaciele"
    assert (jazz["lat"], jazz["lon"]) == (50.0617, 19.9373)
    assert (jazz["start"], jazz["end"]) == ("2026-10-03", "2026-10-04")
    assert jazz["type"] == "Koncerty" and "19:00" in jazz["text"]
    assert jazz["url"].endswith("/101-krakow-jazz-na-rynku")


def test_demo_filter_by_bbox_and_day():
    items = karnet.parse_list(SAMPLE)
    assert [i["id"] for i in items if karnet.in_demo(i, SAT)] == ["101", "103"]
    assert not karnet.in_demo(items[0], date(2026, 10, 5))


def test_default_rules_without_ai(no_ai):
    jazz, _, exhibition = karnet.parse_list(SAMPLE)
    assert karnet.details(jazz) == ({"start_hour": 18, "end_hour": 22, "scale": "medium"}, "rules")
    assert karnet.details(exhibition)[0]["scale"] == "small"  # długa wystawa nie ściąga tłumu jednego dnia


def test_ai_details_used_when_valid_and_rejected_when_absurd(monkeypatch):
    jazz = karnet.parse_list(SAMPLE)[0]
    monkeypatch.setattr(llm, "ask_json", lambda *a, **k: {"start_hour": 19, "end_hour": 23, "scale": "large"})
    assert karnet.details(jazz) == ({"start_hour": 19, "end_hour": 23, "scale": "large"}, "ai")
    monkeypatch.setattr(llm, "ask_json", lambda *a, **k: {"start_hour": 22, "end_hour": 3, "scale": "large"})
    assert karnet.details(jazz)[1] == "rules"


def test_import_replaces_only_karnet_events_and_calls_ai_once_per_event(monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "ask_json", lambda *a, **k: calls.append(1) or {"start_hour": 19, "end_hour": 22, "scale": "medium"})
    from app import db
    db.session.add(Event(name="Ręczne", venue="Rynek", lat=50.06, lon=19.93, start=datetime(2026, 10, 3, 10),
                         end=datetime(2026, 10, 3, 20), scale="large", source="manual"))
    db.session.commit()
    items = karnet.parse_list(SAMPLE)
    assert karnet.import_events([SAT, SUN], items) == 4  # 2 wydarzenia × 2 dni
    assert karnet.import_events([SAT, SUN], items) == 4  # ponowny import nie duplikuje
    assert Event.query.filter_by(source="karnet").count() == 4
    assert Event.query.filter_by(source="manual").count() == 1
    assert len(calls) == 4  # 2 importy × 2 wydarzenia, nie × dni
    jazz_sat = Event.query.filter_by(source="karnet", start=datetime(2026, 10, 3, 19)).first()
    assert jazz_sat.end == datetime(2026, 10, 3, 22) and jazz_sat.scale == "medium"


def test_fetch_is_polite_and_writes_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(karnet, "CACHE", tmp_path / "karnet.json")
    monkeypatch.setattr(karnet, "DELAY_S", 0)
    requests = []

    class FakeResponse(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def opener(req, timeout):
        requests.append((req.full_url, req.get_header("User-agent")))
        return FakeResponse(SAMPLE.encode("utf-8"))

    assert karnet.fetch(pages_per_list=2, opener=opener) == 3  # te same wydarzenia na każdej stronie → bez duplikatów
    assert len(requests) == len(karnet.LISTS) * 2
    assert all("Item_page=" in url and "trash-fairy" in ua for url, ua in requests)
    assert len(json.loads((tmp_path / "karnet.json").read_text(encoding="utf-8"))) == 3


def test_import_without_cache_is_noop(monkeypatch, tmp_path):
    monkeypatch.setattr(karnet, "CACHE", tmp_path / "missing.json")
    assert karnet.import_events([SAT]) == 0
