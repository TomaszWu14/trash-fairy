from unittest.mock import patch

from app import osrm

A, B = [50.06, 19.94], [50.07, 20.00]


def test_no_network_falls_back_to_straight_line(app):
    app.config["OSRM_URL"] = "http://osrm.invalid"
    with patch.object(osrm, "_cache", {}), patch.object(osrm, "_fetch", side_effect=OSError("offline")):
        path, approx = osrm.street_path([A, B])
    assert approx and path == [A, B]


def test_street_path_cached_after_first_fetch(app, tmp_path):
    app.config["OSRM_URL"] = "http://osrm.test"
    street = [A, [50.065, 19.97], B]
    with patch.object(osrm, "_cache", {}), patch.object(osrm, "CACHE_FILE", tmp_path / "c.json"), \
            patch.object(osrm, "_fetch", return_value=street) as fetch:
        assert osrm.street_path([A, B]) == (street, False)
        assert osrm.street_path([A, B]) == (street, False)
    assert fetch.call_count == 1
    assert (tmp_path / "c.json").exists()


def test_route_api_has_street_line(client):
    assert isinstance(client.get("/api/trasa").json["linia"], list)
