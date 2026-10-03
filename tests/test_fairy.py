from datetime import datetime, timedelta

import pytest

from app import clock, db, fairy, llm
from app.models import Emptying, FairyReport, Point
from app.osm_import import import_points
from app.recommendations import recommend, recommendations
from app.simulation import DEMO_NOW

SECTIONS_OK = {"sections": [{"title": t, "text": "Bez uwag."} for t in fairy.SECTIONS]}


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=5)


@pytest.fixture
def model(monkeypatch):
    state = {"result": SECTIONS_OK, "error": None, "calls": []}

    def fake(prompt, schema, system=None, images=(), max_tokens=0):
        state["calls"].append(prompt)
        if state["error"]:
            raise llm.LLMError(state["error"])
        return state["result"]
    monkeypatch.setattr(llm, "ask_json", fake)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    return state


# --- rekomendacje (sekcja 6.8) ---

def stats(days=28, overflow_days=0, readings=56, half_full=0):
    return {"days": days, "overflow_days": overflow_days, "readings": readings, "half_full": half_full,
            "per_day": readings / days}


def test_compactor_when_overflowing_most_days_despite_twice_daily():
    r = recommend("bin", stats(overflow_days=15, half_full=40))
    assert r[0] == "compactor" and "−" in r[3]


def test_twice_daily_needed_for_compactor():
    assert recommend("bin", stats(overflow_days=15, readings=28, half_full=20))[0] == "bigger"


def test_bigger_bin_between_20_and_50_percent_days():
    assert recommend("bin", stats(overflow_days=6, half_full=30))[0] == "bigger"  # 21%
    assert recommend("bin", stats(overflow_days=5, half_full=30)) is None  # 18%, a ≥50% w ponad 20% opróżnień


def test_less_often_when_rarely_half_full():
    r = recommend("bin", stats(half_full=5))
    assert r[0] == "less_often" and r[3] == "−30 wizyt w miesiącu"


def test_shelter_overflowing_gets_more_frequent_pickup_not_compactor():
    assert recommend("shelter", stats(days=28, readings=10, overflow_days=20, half_full=10))[0] == "more_often"


def test_not_enough_readings_no_recommendation():
    assert recommend("bin", stats(readings=5, days=5, half_full=0)) is None


def test_recommendations_use_crew_readings_and_shelter_rule_first(demo):
    shelter = Point.query.filter_by(kind="shelter").first()
    recs = recommendations(DEMO_NOW, {shelter.id: "worki"})
    assert recs[0]["type"] == "shelter_intervention" and recs[0]["point_id"] == shelter.id
    # odczyt ekipy z 100% codziennie zmienia rekomendację punktu, który wcześniej jej nie miał
    calm = next(p for p in Point.query.filter_by(kind="bin") if p.id not in {r["point_id"] for r in recs})
    db.session.query(Emptying).filter(Emptying.point_id == calm.id).update({"level": 100})
    db.session.commit()
    assert any(r["point_id"] == calm.id and r["type"] == "compactor" for r in recommendations(DEMO_NOW))


# --- raport „Wróżka podpowiada” ---

def test_facts_are_computed_in_code(demo):
    from app.state import point_states
    facts = fairy.build_facts(DEMO_NOW)
    assert facts["punkty_do_oproznienia"] == sum(s["state"] == "bad" for s in point_states(DEMO_NOW).values())
    assert {t["flota"] for t in facts["trasy"]} == {"Kosze uliczne", "Altany osiedlowe"}
    assert len(facts["najblizsze_przekroczenia"]) <= 3 and len(facts["rekomendacje"]) <= 3


def test_prompt_forbids_new_numbers():
    assert "nie dodawaj nowych liczb" in fairy.SYSTEM


def test_unknown_numbers_are_flagged():
    facts = {"punkty": 20, "godzina": "16:11"}
    ok = [{"title": "Trasy", "text": "20 punktów, przekroczenie o 16:11."}]
    bad = [{"title": "Trasy", "text": "Oszczędność 35% i 20 punktów."}]
    assert fairy.unknown_numbers(ok, facts) == []
    assert fairy.unknown_numbers(bad, facts) == ["35"]


def test_generate_saves_report_and_latest_returns_it(demo, model):
    report = fairy.generate(DEMO_NOW)
    data = fairy.to_dict(report)
    assert fairy.is_fresh(report, DEMO_NOW)
    assert [s["title"] for s in data["sections"]] == fairy.SECTIONS
    assert FairyReport.query.count() == 1
    assert fairy.to_dict(fairy.latest(DEMO_NOW))["label"] == data["label"]


def test_api_error_raises_llm_error_and_last_report_stays(demo, model):
    fairy.generate(DEMO_NOW)
    model["error"] = "Analiza AI chwilowo niedostępna (limit zapytań). Spróbuj za minutę."
    with pytest.raises(llm.LLMError, match="limit zapytań"):
        fairy.generate(DEMO_NOW)
    assert fairy.latest(DEMO_NOW) is not None  # wywołujący pokazuje komunikat + ostatni raport, nie 500


def test_report_older_than_current_hour_is_not_fresh(demo, model):
    fairy.generate(clock.now())
    clock.advance(1)
    assert fairy.is_fresh(fairy.latest(clock.now()), clock.now()) is False


def test_reset_clears_reports(demo, model):
    fairy.generate(DEMO_NOW)
    clock.reset(weeks=1)
    assert FairyReport.query.count() == 0


# --- tryb jury i metodologia ---

def test_methodology_page_shows_assumptions_and_money(client, demo):
    html = client.get("/metodologia").get_data(as_text=True)
    assert "założenia" in html and "zł" in html and "ODbL" in html and "RODO" in html


def test_money_uses_configurable_assumptions(monkeypatch):
    from app.methodology import money
    result = {"weeks": 4, "fixed": {"total": {"km": 280, "visits": 1000}}, "fairy": {"total": {"km": 280, "visits": 720}}}
    monkeypatch.setenv("COST_PER_VISIT_PLN", "10")
    m = money(result)
    assert m["visits_month"] == 300 and m["pln_month"] == 3000 and m["km_month"] == 0


def test_city_scale_range_is_computed_from_mpo_schedule(client, demo):
    from app import comparison
    from app.methodology import MPO_SCHEDULE, city_scale
    c = city_scale(comparison.compare(clock.DEMO_NOW))
    assert sum(n for _, n, _ in MPO_SCHEDULE) == 9383 and c["full"]["bins"] == 9383
    assert 0 < c["careful"]["pln_year"] < c["full"]["pln_year"]
    assert "Skala: cały Kraków" in client.get("/metodologia").get_data(as_text=True)
