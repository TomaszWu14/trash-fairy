"""Kontrakt adresów API perspektyw (#24): podział api_pl na moduły nie zmienia adresów, metod ani nazw endpointów."""

API_PL = {
    ("/api/demo/reset", "api_pl.demo_reset", "POST"),
    ("/api/kosze", "api_pl.kosze", "GET"),
    ("/api/kosze/<int:point_id>", "api_pl.kosz", "GET"),
    ("/api/kosze/<int:point_id>/przycisk", "api_pl.przycisk", "POST"),
    ("/api/odbiory", "api_pl.odbior", "POST"),
    ("/api/odbiory/zdjecie/<int:photo_id>", "api_pl.zdjecie_odbioru", "GET"),
    ("/api/trasa", "api_pl.trasa", "GET"),
    ("/api/trasa/dojazd", "api_pl.dojazd", "GET"),
    ("/api/zgloszenia", "api_pl.zglos", "POST"),
    ("/api/zgloszenia/<nr>", "api_pl.zgloszenie", "GET"),
    ("/api/zmiany", "api_pl.zmiany", "GET"),
}


def test_api_pl_routes_unchanged(app):
    rules = {(r.rule, r.endpoint, ",".join(sorted(r.methods - {"HEAD", "OPTIONS"})))
             for r in app.url_map.iter_rules() if r.endpoint.startswith("api_pl.")}
    assert rules == API_PL
