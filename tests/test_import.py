from app.geo import distance_m
from app.models import Point
from app.osm_import import MIN_GAP_M, bin_rate, import_points, select_spaced


def test_import_selects_60_bins_and_12_shelters(cache):
    import_points(cache)
    assert Point.query.filter_by(kind="bin").count() == 60
    assert Point.query.filter_by(kind="shelter").count() == 12
    assert Point.query.filter_by(kind="shelter", overloaded=True).count() == 2
    assert {p.area for p in Point.query.filter_by(kind="bin")} == {"Rynek", "Kazimierz", "Grzegórzki"}


def test_overloaded_shelters_have_street_bins_nearby(cache):
    import_points(cache)
    bins = Point.query.filter_by(kind="bin").all()
    for s in Point.query.filter_by(kind="shelter", overloaded=True):
        assert any(distance_m(s.lat, s.lon, b.lat, b.lon) <= 200 for b in bins)


def test_imported_bins_keep_minimum_gap(cache):
    import_points(cache)
    bins = Point.query.filter_by(kind="bin").all()
    for i, a in enumerate(bins):
        for b in bins[i + 1:]:
            assert distance_m(a.lat, a.lon, b.lat, b.lon) >= MIN_GAP_M


def test_import_is_idempotent(cache):
    import_points(cache)
    import_points(cache)
    assert Point.query.count() == 72


def test_select_spaced_respects_already_taken():
    centre = (50.0617, 19.9373)
    cands = [{"lat": 50.0617 + i * 1e-4, "lon": 19.9373} for i in range(50)]  # co ~11 m
    out = select_spaced(cands, centre, 3, 80, taken=[cands[0]])
    assert len(out) == 3
    assert cands[0] not in out


def test_bin_rate_grows_with_nearby_pois_and_is_capped():
    b = {"lat": 50.0617, "lon": 19.9373}
    far = {"lat": 50.07, "lon": 19.95}
    assert bin_rate(b, [far], []) == 1.5
    assert bin_rate(b, [b] * 10, [b]) == 1.5 + 0.6 + 0.6
    assert bin_rate(b, [b] * 1000, []) == 8.0
