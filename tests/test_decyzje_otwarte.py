"""Decyzje autora z 11.10.2026 dla otwartych problemów z docs/07: jedna definicja „pełny”, progi baterii w jednym
miejscu, rozbieżność poziomu i zdjęcia na liście do sprawdzenia, linki dyspozytora."""
from pathlib import Path

import pytest

from app import clock, db, devices, dyspozytor_api, epaper, residents, state
from app.api_wspolne import poziom_stan
from app.models import PhotoAnalysis, Point
from app.osm_import import import_points

UI = Path(__file__).resolve().parent.parent / "app" / "static" / "ui"


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=1)


@pytest.mark.parametrize("level, expected", [(59, "ok"), (60, "zapelnia_sie"), (85, "zapelnia_sie"), (86, "pelny")])
def test_screens_use_engine_thresholds(level, expected):
    assert poziom_stan(level) == expected
    assert dyspozytor_api.FULL_ABOVE == state.BAD_ABOVE


def test_browser_uses_the_same_thresholds():
    js = (UI / "app.js").read_text(encoding="utf-8")
    assert f"l > {state.BAD_ABOVE} ? 'full' : l >= {state.WARN_FROM} ? 'warn'" in js
    assert "poziom >= 80" not in (UI / "kierowca.js").read_text(encoding="utf-8")


@pytest.mark.parametrize("battery, level", [(14, "full"), (15, "warn"), (34, "warn"), (35, "ok")])
def test_battery_thresholds_live_in_one_place(battery, level):
    assert devices.battery_level(battery) == level
    assert epaper.FAULT_BATTERY == devices.CRITICAL_BATTERY
    assert not hasattr(residents, "LOW_BATTERY")


def test_crew_level_vs_photo_mismatch_is_listed_for_review(demo, client):
    p = Point.live_query().filter_by(kind="bin").first()
    db.session.add(PhotoAnalysis(point_id=p.id, at=clock.now(), wall_at=clock.now(), status="done", source="crew",
                                 crew_level=100, fill_level=20, confidence=0.9))
    db.session.commit()
    d = client.get("/api/dashboard/wykresy/anomalie").json
    item = next(x for x in d["zdjecia"] if x["kosz_id"] == p.id)
    assert (item["poziom_ekipa"], item["poziom_zdjecie"]) == (100, 20) and d["prog_pp"] == 25


def test_dispatcher_links_to_existing_detail_screens():
    js = (UI / "dyspozytor.js").read_text(encoding="utf-8")
    assert "/zgloszenie/${encodeURIComponent(z.numer)}" in js and "/wysypisko/${encodeURIComponent(x.numer)}" in js
    assert "/kierowca/kosz/${k.id}" in js
