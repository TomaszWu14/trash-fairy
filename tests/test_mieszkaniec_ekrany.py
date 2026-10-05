"""Ekrany mieszkańca po uwagach jury (J-32, J-55, decyzja a): treści i kolejność, które muszą zostać w HTML."""
import pytest

from app import clock
from app.osm_import import import_points


@pytest.fixture
def demo(cache):
    import_points(cache)
    clock.reset(weeks=2)


def test_start_order_empty_state_and_no_map(client, demo):
    html = client.get("/zglos").get_data(as_text=True)
    order = [html.index(s) for s in ('data-scan', 'href="/wysypisko"', 'id="m-mine"', 'id="m-points"')]
    assert order == sorted(order)  # skan QR → dzikie wysypisko → Twoje zgłoszenia → Twoje punkty
    assert "Nie masz jeszcze zgłoszeń. Zgłoś problem przy koszu: zeskanuj kod QR na jego panelu." in html
    assert "wysypisko.js" not in html and "leaflet" not in html


def test_report_form_says_what_we_do_not_collect(client, demo):
    html = client.get("/zglos/18").get_data(as_text=True)
    assert "Do zgłoszenia nie potrzeba imienia, numeru telefonu ani położenia" in html and "Konto służy tylko do punktów" in html
    assert "Nie pytamy" not in html and "(EXIF)" in html and "adres IP kasujemy po 24 h" in html


def test_status_title_is_status_number_in_eyebrow(client, demo):
    html = client.get("/zgloszenie/tf-00001").get_data(as_text=True)
    assert 'id="st-title"' in html and 'Zgłoszenie <span class="num">TF-00001</span>' in html
    assert "Twoje zgłoszenia" in html and "Zgłoś inny kosz" not in html and 'id="st-badge"' not in html


def test_points_card_data_rules_and_rewards(client, demo):
    p = client.get("/api/mieszkaniec/punkty").json
    assert {z["punkty"] for z in p["zasady"]} == {10, 15, 20}
    assert p["nagrody"] and all({"prog", "nazwa", "brakuje"} <= set(n) for n in p["nagrody"])
    # karta punktów: jedna najbliższa nagroda z paskiem, cały katalog zwinięty (nie dominuje ekranu przy 0 pkt)
    html = client.get("/zglos").get_data(as_text=True)
    assert 'id="m-pts-next"' in html and '<details class="m-more m-rewards-all">' in html
    assert html.index('id="m-pts-next"') < html.index('id="m-pts-rewards"')


def test_status_live_region_only_on_title(client, demo):
    # TF.watch odświeża co zmianę w demo: czytnik ma ogłaszać tylko zmianę statusu, nie całą głowę karty
    html = client.get("/zgloszenie/tf-00001").get_data(as_text=True)
    head = html.split('<div class="m-st-head"', 1)[1].split(">", 1)[0]  # atrybuty otwierającego znacznika (np. data-help)
    assert 'id="st-title" aria-live="polite"' in html and "aria-live" not in head


def test_simulated_scan_offers_bins_with_panel_and_todays_token(client, demo):
    # HANDOFF 2e: symulowany skan losuje kosz z panelem; dzisiejszy token z tej samej funkcji co panel, bez nowego endpointu
    import json
    import re
    from app import db
    from app.api_pl import qr_token, qr_valid
    from app.models import DeviceInfo
    html = client.get("/zglos").get_data(as_text=True)
    bins = json.loads(re.search(r'<script type="application/json" id="scan-bins">(.*?)</script>', html, re.S).group(1))
    panels = {pid for (pid,) in db.session.query(DeviceInfo.point_id).filter(DeviceInfo.kind == "panel")}
    assert len(bins) > 1 and any(b["losuj"] for b in bins)
    assert all(b["id"] in panels and b["qr"] == qr_token(b["id"]) and qr_valid(b["id"], b["qr"]) for b in bins)
    assert "Losuj inny" in html and 'id="scan-sim"' in html and "/zglos/18?qr=" in html  # bez JS: kosz demo
    # nazwa kosza (jak na panelu), nie id; zmiana losowania ogłaszana czytnikowi ekranu
    name18 = next(b["nazwa"] for b in bins if b["id"] == 18)
    assert f'aria-live="polite">Wylosowany kosz: <b id="scan-sim-n">{name18}</b>' in html


def test_success_screens_thank_and_lead_back(client, demo):
    # HANDOFF 2: „Dziękujemy!” + powrót (do panelu tego kosza po skanie QR, inaczej na stronę mieszkańca) + cichy link na start
    from app.api_pl import qr_token
    scanned = client.get(f"/zglos/18?qr={qr_token(18)}").get_data(as_text=True)
    assert "Dziękujemy!" in scanned and 'href="/panel/18"' in scanned and "Wróć do panelu kosza" in scanned
    assert "Strona główna" in scanned and 'id="m-nr"' in scanned and 'id="m-status-link"' in scanned
    assert "Wróć na stronę mieszkańca" in client.get("/zglos/18").get_data(as_text=True)
    dump = client.get("/wysypisko").get_data(as_text=True)
    assert "Dziękujemy!" in dump and "Wróć na stronę mieszkańca" in dump and 'id="wd-nr"' in dump


def test_dump_status_title_is_status_like_bin_report(client, demo):
    # spójnie z /zgloszenie (J-32): numer w nadtytule, H1 = status z dużą ikoną
    html = client.get("/wysypisko/WD-00001").get_data(as_text=True)
    assert 'Dzikie wysypisko <span class="num">WD-00001</span>' in html and 'id="wd-st-ico"' in html
    assert 'id="wd-st-h" aria-live="polite"' in html and 'id="wd-st-badge"' not in html
