import random

import pytest

from app import create_app
from app.osm_import import GRZEGORZKI, KAZIMIERZ, RYNEK


@pytest.fixture(autouse=True)
def app():
    from app import comparison, forecast
    forecast.clear_cache()
    comparison.clear_cache()
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})
    with app.app_context():
        yield app


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
        "bins": _scatter(rng, RYNEK, 150) + _scatter(rng, KAZIMIERZ, 120),
        "shelters": _scatter(rng, GRZEGORZKI, 30, spread=0.01),
        "pois": _scatter(rng, RYNEK, 200, spread=0.002),
        "stops": _scatter(rng, RYNEK, 5, spread=0.002),
    }
