"""Strony dokumentów po poprawkach jury: koszt odbioru z jawnych składników, decyzja 1 (bez położenia), progi podrzucania."""
import pytest

from app import clock, comparison, crew_points, dumping, methodology
from app.osm_import import import_points


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def test_visit_cost_is_built_from_stated_components(monkeypatch):
    monkeypatch.delenv("COST_PER_VISIT_PLN", raising=False)
    a = methodology.money_assumptions()
    assert a["cost_per_visit"] == 12.0 and a["stop_min"] == 3  # (3 × 45 + 105) zł/h × 3/60 h
    monkeypatch.setenv("COST_PER_VISIT_PLN", "7")
    assert methodology.money_assumptions()["cost_per_visit"] == 7.0


def test_money_counts_saved_crew_hours():
    result = {"weeks": 4, "fixed": {"total": {"km": 100, "visits": 1000}}, "fairy": {"total": {"km": 100, "visits": 720}}}
    assert methodology.money(result)["crew_hours_month"] == 15  # 300 odbiorów mniej × 3 min


def test_methodology_page_numbers_match_engine(client, demo):
    html = client.get("/metodologia").get_data(as_text=True)
    r = comparison.compare(clock.DEMO_NOW)
    city = methodology.city_scale(r)
    careful, full = (f"{v['pln_year'] / 1e6:.1f}".replace(".", ",") for v in (city["careful"], city["full"]))
    assert f"{careful}–{full} mln zł" in html  # kafelek = tabela skali Krakowa = strona startowa
    assert f"{r['fixed']['bin']['empty_share']}% → {r['fairy']['bin']['empty_share']}%" in html
    assert "Skąd 12 zł za odbiór" in html and "240 zł/h" in html and "do ustalenia w pilotażu" in html
    assert "Wróżka" not in html and "wizyt" not in html and "p.p." not in html
    for anchor in ("wyniki", "porownanie", "krakow", "pilotaz", "rekomendacje"):
        assert f'id="{anchor}"' in html and f'href="#{anchor}"' in html


def test_methodology_dumping_thresholds_come_from_rule(client, demo):
    html = client.get("/metodologia").get_data(as_text=True)
    assert f"w oknie {dumping.WINDOW_DAYS} dni" in html and "rozważ fotopułapkę (decyzja gminy)" in html
    assert all(f"co najmniej {n}" in html for n in (dumping.SIGN_AT, dumping.PATROL_AT, dumping.CAMERA_AT))
    assert "Punkty zaangażowania ekipy" in html and "regulamin MPO" in html and "Tu przydałby się kosz" in html
    assert all(f"+{r['punkty']}</td>" in html for r in crew_points.RULES)


@pytest.mark.parametrize("path", ["/metodologia", "/prywatnosc", "/dostepnosc", "/api/docs"])
def test_documents_follow_decision_1(client, demo, path):
    html = client.get(path).get_data(as_text=True)
    assert "150 m" not in html and "w pobliżu" not in html and "geoloc" not in html


def test_privacy_matches_code(client):
    html = client.get("/prywatnosc").get_data(as_text=True)
    assert "<b>7 dni</b>" in html and "EXIF" in html and "nie pobieramy" in html and "codziennie" in html
    assert "Kodeksem pracy" in html and "decyduje gmina" in html and 'class="stack"' in html
    assert "Nie zbieramy" not in html and "nie zbieramy danych osobowych" not in html  # IP i zdjęcie to dane osobowe
    assert "Nie fotografujemy celowo ludzi" in html and "regulamin MPO" in html


def test_api_docs_open311_on_top_and_post_badge(client):
    html = client.get("/api/docs").get_data(as_text=True)
    assert "<h1>Otwarte API</h1>" in html and "Open311 GeoReport v2</a>" in html
    assert 'class="c-doc-post">POST' in html and "<pre>" not in html
    assert html.count("Otwarte API v1</h2>") == 1 and html.count('"blad": "…"') == 1  # grupy po tagu, format błędu raz


@pytest.mark.parametrize("path", ["/metodologia", "/prywatnosc", "/dostepnosc", "/api/docs"])
def test_documents_styles_only_in_doc_css(client, demo, path):
    assert "<style" not in client.get(path).get_data(as_text=True)  # wszystko w doc.css, tylko tokeny


def test_methodology_details_collapsed(client, demo):
    html = client.get("/metodologia").get_data(as_text=True)
    assert '<details id="reguly">' in html and '<details id="dla-deweloperow">' in html and "<details open" not in html
    assert html.index("COST_PER_KM_PLN") > html.index('<details id="dla-deweloperow">')  # nazwy zmiennych tylko w zwiniętej sekcji


def test_privacy_dumps_and_proof_of_service(client):
    html = client.get("/prywatnosc").get_data(as_text=True)
    assert "Dzikie wysypisko" in html and "współrzędne miejsca z odpadami, a nie telefonu" in html
    assert "tylko zdjęcie zweryfikowane" in html and "bez osób oraz tablic rejestracyjnych" in html
    assert "Zdjęcie kosza od ekipy (w demo opcjonalne)" in html and html.count("<b>7 dni</b>") >= 3


def test_methodology_comparison_grouped_by_fleet(client, demo):
    html = client.get("/metodologia").get_data(as_text=True)
    assert ">Flota</th>" not in html  # floty jako grupy wierszy: 3 kolumny mieszczą się w 320 px (WCAG 1.4.10)
    assert html.count('scope="rowgroup"') == 2 and 'scope="rowgroup">Kosze uliczne' in html


def test_api_docs_group_nav_and_v1_limits_next_to_group(client):
    html = client.get("/api/docs").get_data(as_text=True)
    assert 'aria-label="Grupy endpointów"' in html and 'href="#grupa-1"' in html
    v1 = html.index("Otwarte API v1</h2>")
    assert v1 < html.index("Czego otwarte API v1 nie zwraca") < html.index("<h2", v1 + 1)  # zaraz pod swoją grupą


def test_privacy_dump_ip_row_matches_limit(client):
    from app import wysypiska_api
    html = client.get("/prywatnosc").get_data(as_text=True)
    dumps = html[html.index("Dzikie wysypisko"):html.index("Dowód wykonania usługi")]
    assert "Adres IP zgłoszenia" in dumps and f"najwyżej {wysypiska_api.PER_IP_HOUR} zgłoszeń wysypisk" in dumps


def test_accessibility_covers_new_screens(client):
    html = client.get("/dostepnosc").get_data(as_text=True)
    assert "Panel kosza" in html and "ciemny (domyślny) i jasny" in html and "Podpowiedzi" in html
    assert "16 ekranów" in html and "200%" in html and "w pobliżu" not in html
