import random

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app, db
from app.osm_import import GRZEGORZKI, KAZIMIERZ, RYNEK


class BufferedClient(FlaskClient):
    """Odpowiedź czytana od razu i zamykana – pliki statyczne i zdjęcia nie wiszą otwarte do gc (ResourceWarning)."""

    def open(self, *args, buffered=True, **kwargs):
        return super().open(*args, buffered=buffered, **kwargs)


Flask.test_client_class = BufferedClient


@pytest.fixture(autouse=True)
def app():
    from app import comparison, forecast, state
    forecast.clear_cache()
    comparison.clear_cache()
    state.clear_cache()
    # wszystkie integracje wyłączone: testy nie wychodzą do sieci (test_weather/traffic/sms włączają je z FakeOpener)
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True, "OSRM_URL": "",
                      "WEATHER_URL": "", "TOMTOM_API_KEY": "", "TWILIO_ACCOUNT_SID": "", "TWILIO_AUTH_TOKEN": "",
                      "TWILIO_VERIFY_SID": "", "SMS_DEMO_FALLBACK": "1"})
    with app.app_context():
        yield app
        db.session.remove()
        db.engine.dispose()  # zamyka połączenia SQLite :memory: (inaczej ResourceWarning przy gc)


@pytest.fixture
def client(app):
    return app.test_client()


def _scatter(rng, centre, n, spread=0.006, prefix="node"):
    return [{"osm_id": f"{prefix}/{rng.randrange(10**9)}", "tags": {},
             "lat": centre[0] + rng.uniform(-spread, spread), "lon": centre[1] + rng.uniform(-spread, spread)}
            for _ in range(n)]


@pytest.fixture
def cache():
    """Mały, sztuczny odpowiednik data/*.geojson (bez sieci)."""
    rng = random.Random(1)
    return {
        "bins": _scatter(rng, RYNEK, 150) + _scatter(rng, KAZIMIERZ, 120) + _scatter(rng, GRZEGORZKI, 60, spread=0.01),
        "shelters": _scatter(rng, GRZEGORZKI, 30, spread=0.01),
        "pois": _scatter(rng, RYNEK, 200, spread=0.002),
        "stops": _scatter(rng, RYNEK, 5, spread=0.002),
    }
