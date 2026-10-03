import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app import forecast, http, weather
from tests.fakes import FakeOpener

REAL = json.loads((Path(__file__).parent / "fixtures" / "open_meteo.json").read_text(encoding="utf-8"))
SAT, MON = datetime(2026, 10, 3, 13), datetime(2026, 10, 5, 13)  # sobota / poniedziałek


@pytest.fixture
def live(app, monkeypatch, tmp_path):
    """Włącza Open-Meteo z fałszywym openerem i pustym cache w katalogu tymczasowym."""
    app.config["WEATHER_URL"] = weather.DEFAULT_URL
    monkeypatch.setattr(weather, "CACHE_FILE", tmp_path / "weather.json")
    monkeypatch.setattr(weather, "_state", {"data": None, "next_try": 0.0})

    def use(routes):
        fake = FakeOpener(routes)
        monkeypatch.setattr(http, "opener", fake)
        return fake
    return use


def test_rule():
    assert weather.factor({"temp": 12, "rain": 1.4, "code": 61}, SAT) == 0.8
    assert weather.factor({"temp": 22, "rain": 0.0, "code": 0}, SAT) == 1.25
    assert weather.factor({"temp": 22, "rain": 0.0, "code": 0}, MON) == 1.0       # nie weekend
    assert weather.factor({"temp": 22, "rain": 0.0, "code": 0}, SAT.replace(hour=23)) == 1.0  # poza 10–22
    assert weather.factor({"temp": 22, "rain": 0.3, "code": 51}, SAT) == 1.0     # mżawka: nie sucho, ale < 1 mm
    assert weather.factor(None, SAT) == 1.0


def test_parses_real_open_meteo_response(live):
    fake = live({"open-meteo": (200, REAL)})
    c = weather.conditions(datetime(2026, 10, 3, 12, 30))
    assert c["available"] and c["temp_c"] == REAL["hourly"]["temperature_2m"][2] and c["source"] == "Open-Meteo"
    assert "hourly=temperature_2m%2Cprecipitation%2Cweather_code" in fake.requests[0].full_url
    weather.conditions(SAT)
    assert len(fake.requests) == 1  # druga odpowiedź z pamięci, nie z sieci


def test_error_keeps_last_result_and_backs_off(live):
    live({"open-meteo": (200, REAL)})
    weather.data()
    weather._state["data"]["fetched_at"] -= weather.TTL_S + 1  # przeterminowane
    fake = live({"open-meteo": OSError("sieć")})
    assert weather.data()["hours"]                  # błąd = ostatni wynik
    weather.data()
    assert len(fake.requests) == 1                  # kolejna próba najwcześniej za 10 min


def test_disabled_and_no_cache_means_neutral(app):
    assert weather.data() is None and weather.conditions(SAT) == {"available": False}
    assert weather.factor_at()(SAT) == 1.0


def test_weather_changes_only_future_hours():
    now = datetime(2026, 10, 3, 12)
    args = (None, [], {now - timedelta(hours=3)}, now - timedelta(hours=3), now + timedelta(hours=3), now)
    plain = forecast.trajectory(*args)
    rainy = forecast.trajectory(*args, weather_at=lambda at: 0.5)
    for (at, est, *_), (_, est_rain, *_) in zip(plain, rainy):
        assert (est_rain == est) if at <= now else (est_rain < est)
