import io
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app import clock, db, llm, photos
from app.misuse import household_bag_links, latest_analyses, misuse_overview
from app.models import Emptying, PhotoAnalysis, Point, Report
from app.osm_import import import_points
from app.reports import record_press
from app.simulation import DEMO_NOW

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
OK_RESULT = {"fill_level": 100, "overflow_outside": True, "misuse": ["household_bag"], "damage": False,
             "confidence": 0.9, "note": "Worki domowe obok kosza."}


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=1)


@pytest.fixture
def vision(monkeypatch):
    """Atrapa Claude: ustaw wynik albo wyjątek LLMError."""
    state = {"result": OK_RESULT, "error": None}

    def fake(prompt, schema, system=None, images=(), max_tokens=0):
        if state["error"]:
            raise llm.LLMError(state["error"])
        return state["result"]
    monkeypatch.setattr(llm, "ask_json", fake)
    return state


def bin_point(area=None):
    q = Point.query.filter_by(kind="bin")
    return (q.filter_by(area=area) if area else q).order_by(Point.id).first()


# --- llm.py: brama do AI ---

def test_llm_without_key_gives_message_not_exception(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(llm.LLMError, match="brak klucza"):
        llm.ask("x")


def test_llm_refusal_and_bad_json_become_llm_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")

    def client_returning(stop_reason, text):
        response = SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)])
        return lambda **kw: SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=lambda **k: response)))

    monkeypatch.setattr(llm.anthropic, "Anthropic", client_returning("refusal", ""))
    with pytest.raises(llm.LLMError, match="odmówił"):
        llm.ask_json("x", photos.SCHEMA)
    monkeypatch.setattr(llm.anthropic, "Anthropic", client_returning("end_turn", "nie-json"))
    with pytest.raises(llm.LLMError, match="niepoprawny JSON"):
        llm.ask_json("x", photos.SCHEMA)
    monkeypatch.setattr(llm.anthropic, "Anthropic", client_returning("end_turn", '{"fill_level": 50}'))
    with pytest.raises(llm.LLMError, match="odrzucona"):  # niepełna odpowiedź nie przechodzi walidacji schematu
        llm.ask_json("x", photos.SCHEMA)
    full = '{"fill_level": 50, "overflow_outside": false, "misuse": [], "damage": false, "confidence": 0.8, "note": "ok"}'
    monkeypatch.setattr(llm.anthropic, "Anthropic", client_returning("end_turn", full))
    assert llm.ask_json("x", photos.SCHEMA)["fill_level"] == 50


def test_llm_uses_model_from_env_and_fallbacks_only_where_supported(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    seen = {}

    def create(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="ok")])
    monkeypatch.setattr(llm.anthropic, "Anthropic",
                        lambda **kw: SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create))))
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-5")
    llm.ask("x")
    assert seen["model"] == "claude-opus-5" and seen["fallbacks"] == "default"
    seen.clear()
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    llm.ask("x")
    assert seen["model"] == "claude-haiku-4-5" and "fallbacks" not in seen


def test_prompt_forbids_describing_people():
    assert "Nie opisuj osób" in photos.SYSTEM


# --- walidacja i retencja zdjęć ---

def test_validate_by_magic_bytes_and_size():
    assert photos.validate(PNG) == ("image/png", None)
    assert photos.validate(JPEG) == ("image/jpeg", None)
    assert photos.validate(b"GIF89a....")[0] is None
    assert photos.validate(b"")[0] is None
    assert "8 MB" in photos.validate(b"\xff\xd8\xff" + b"0" * photos.MAX_BYTES)[1]


def test_cleanup_removes_photo_files_after_7_days_but_keeps_analysis(demo, vision):
    p = bin_point()
    old = photos.save(p.id, DEMO_NOW, PNG, "image/png")
    new = photos.save(p.id, DEMO_NOW, PNG, "image/png")
    old.wall_at -= timedelta(days=8)
    db.session.commit()
    old_path = old.photo_path
    assert photos.cleanup() == 1
    assert old.photo_path is None and new.photo_path is not None
    assert not __import__("pathlib").Path(old_path).exists()
    assert db.session.get(PhotoAnalysis, old.id) is not None


# --- kierowca: opróżnienie (POST /api/odbiory) i zdjęcia ---

def test_crew_emptying_resolves_reports_and_resets_estimate(client, demo):
    from app.state import point_states
    p = bin_point("Rynek")
    record_press(p.id, clock.now() - timedelta(minutes=5))
    r = client.post("/api/odbiory", json={"kosz": p.id, "akcja": "oprozniono", "poziom": 100})
    assert r.status_code == 201
    assert Report.query.filter_by(point_id=p.id, hit=None).count() == 0
    assert Report.query.filter_by(point_id=p.id).order_by(Report.id.desc()).first().hit is True
    s = point_states(clock.now())[p.id]
    assert s["level"] < 30 and s["state"] == "ok"


def test_crew_emptying_validates_level(client, demo):
    p = bin_point()
    assert client.post("/api/odbiory", json={"kosz": p.id, "akcja": "oprozniono", "poziom": 60}).status_code == 400
    assert client.post("/api/odbiory", json={"kosz": 99999, "akcja": "oprozniono", "poziom": 50}).status_code == 404
    assert Emptying.query.filter_by(point_id=p.id, at=clock.now()).count() == 0


def test_crew_photo_is_analysed_and_flags_discrepancy(demo, vision):
    p = bin_point("Rynek")
    pa = photos.save(p.id, clock.now(), PNG, "image/png", crew_level=25)
    photos.analyze_in_background(pa.id)
    pa = db.session.get(PhotoAnalysis, pa.id)
    assert pa.status == "done" and pa.fill_level == 100 and pa.misuse == ["household_bag"]
    assert photos.discrepancy(pa)  # ekipa 25%, zdjęcie 100%


def test_bad_photo_in_report_is_rejected(client, demo):
    from app.api_pl import qr_token
    p = bin_point()
    r = client.post("/api/zgloszenia", data={"kosz": p.id, "typ": "przepelniony", "qr": qr_token(p.id), "lat": p.lat,
                                             "lon": p.lon, "zdjecie": (io.BytesIO(b"not an image"), "x.png")},
                    content_type="multipart/form-data")
    assert r.status_code == 400 and r.json["kod"] == "zle_zdjecie" and "JPEG" in r.json["blad"]
    assert Report.query.filter(Report.point_id == p.id, Report.first_at == clock.now()).count() == 0


# --- test 9 z sekcji 11: błąd API → komunikat i ostatni wynik, nie 500 ---

def test_api_error_shows_message_and_last_result(demo, vision):
    p = bin_point("Rynek")
    photos.analyze_in_background(photos.save(p.id, clock.now(), PNG, "image/png").id)
    vision["error"] = "Analiza AI chwilowo niedostępna (limit zapytań). Spróbuj za minutę."
    photos.analyze_in_background(photos.save(p.id, clock.now(), PNG, "image/png").id)
    d = misuse_overview(clock.now())["points"][p.id]
    assert "limit zapytań" in d["photo_error"]
    assert d["photo_note"] == OK_RESULT["note"]  # ostatni udany wynik


# --- test 8 z sekcji 11: reguła altana → kosz (200 m, 48 h) ---

def test_household_bag_link_within_200_m_of_overflowing_shelter():
    shelter = SimpleNamespace(id=1, lat=50.0590, lon=19.9600)
    near = SimpleNamespace(id=2, lat=50.0590 + 0.0017, lon=19.9600)  # ok. 189 m
    far = SimpleNamespace(id=3, lat=50.0590 + 0.0020, lon=19.9600)  # ok. 222 m
    assert household_bag_links([near, far], [shelter], {1: 110}) == [(near, shelter)]
    assert household_bag_links([near], [shelter], {}) == []  # altana nieprzepełniona → brak powiązania


def test_demo_starts_with_links_and_recommendations(demo):
    mo = misuse_overview(DEMO_NOW)
    shelters = {s.id for s in Point.query.filter_by(kind="shelter", overloaded=True)}
    assert mo["links"] and {l["shelter_id"] for l in mo["links"]} <= shelters
    assert set(mo["recommendations"]) == {l["shelter_id"] for l in mo["links"]}


def test_old_analyses_and_other_misuse_do_not_link(demo):
    db.session.query(PhotoAnalysis).delete()
    b = bin_point("Grzegórzki")
    db.session.add(PhotoAnalysis(point_id=b.id, at=DEMO_NOW - timedelta(hours=49), wall_at=datetime.now(UTC).replace(tzinfo=None),
                                 status="done", misuse=["household_bag"], fill_level=100))
    db.session.add(PhotoAnalysis(point_id=b.id, at=DEMO_NOW - timedelta(hours=1), wall_at=datetime.now(UTC).replace(tzinfo=None),
                                 status="done", misuse=["clothes"], fill_level=75))
    db.session.commit()
    assert latest_analyses(DEMO_NOW)[b.id][1].misuse == ["clothes"]
    mo = misuse_overview(DEMO_NOW)
    assert mo["links"] == [] and mo["points"][b.id]["misuse"] == ["ubrania lub buty"]


def test_old_crew_page_redirects_to_driver_pwa(client, demo):
    r = client.get("/ekipa")
    assert r.status_code == 301 and r.headers["Location"].endswith("/kierowca")
