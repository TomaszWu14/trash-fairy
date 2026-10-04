"""Nowe UI „Przegląd jury”: cztery perspektywy jednej historii (audit/AUDYT-UX.md, sekcja 4). Bez logowania."""
import os

from flask import Blueprint, abort, render_template, request

from . import clock, db
from .comparison import compare
from .methodology import city_scale, page_context
from .models import DeviceInfo, Point
from .simulation import DEMO_NOW
from .state import point_states

# „Co tu wrzucać” na panelu kosza: polski system 5 frakcji, po 2–3 najczęstsze przykłady (czytelne z daleka)
SORTOWANIE = {
    "papier": ("gazety, kartony, zeszyty", "paragony, tłusty papier, kartony po mleku"),
    "metale_tworzywa": ("butelki plastikowe, puszki, kartony po mleku", "baterie, elektrośmieci, styropian budowlany"),
    "szklo": ("butelki i słoiki", "ceramika, szyby i lustra, żarówki"),
    "bio": ("obierki, resztki owoców i warzyw, fusy", "mięso i kości, olej, odchody zwierząt"),
    "zmieszane": ("zabrudzone opakowania, zużyte chusteczki", "baterie, leki, elektrośmieci"),
}
DEMO_BIN_ID = 18  # ten sam kosz w scenariuszu demo, QR na slajdach i w nagraniu (decyzja 13)

bp = Blueprint("ui", __name__)


@bp.app_context_processor
def ui_context():
    from .api_pl import qr_token
    return {"demo_bin_id": DEMO_BIN_ID, "demo_qr": qr_token(DEMO_BIN_ID)}


def headline():
    """Trzy liczby z porównania 4 tygodni i skali Krakowa: te same co na /metodologia i slajdach."""
    result = compare(DEMO_NOW)
    city = city_scale(result)
    return {"empty_from": result["fixed"]["bin"]["empty_share"], "empty_to": result["fairy"]["bin"]["empty_share"],
            "shelter_from": result["fixed"]["shelter"]["overflow_hours"], "shelter_to": result["fairy"]["shelter"]["overflow_hours"],
            "pln_min": city["careful"]["pln_year"] / 1e6, "pln_max": city["full"]["pln_year"] / 1e6}


@bp.get("/")
def start():
    clock.maybe_auto_reset()  # kolejny widz po 30 min bezczynności zaczyna od stanu początkowego
    now = clock.now()
    bin18 = db.get_or_404(Point, DEMO_BIN_ID)
    st = point_states(now).get(DEMO_BIN_ID, {})
    return render_template("ui/start.html", perspective="start", bin=bin18, bin_level=round(st.get("value") or 0),
                           head=headline(), public_url=os.environ.get("PUBLIC_URL", ""))


@bp.get("/metodologia")
def methodology():
    return render_template("metodologia.html", **page_context(clock.now()))


@bp.get("/panel/<int:point_id>")
def kiosk(point_id):
    """Panel kosza (kiosk 1280×800): kod QR z dziennym tokenem tego kosza i przyciski „Zgłoś na miejscu”.
    Token urządzenia panelu jest w HTML tylko dlatego, że w demo panel to strona WWW (prawdziwy panel liczy go sam)."""
    from .api_pl import FRAKCJE, _point, kosz_json, qr_seconds_left, qr_token
    from .devices_api import device_token
    p = _point(point_id)
    if p is None:
        abort(404)
    now = clock.now()
    base = (os.environ.get("PUBLIC_URL") or request.url_root).rstrip("/")
    k = kosz_json(p, point_states(now), now)
    info = db.session.get(DeviceInfo, p.id)
    return render_template("ui/kiosk.html", bin=k, frakcje=FRAKCJE, sortowanie=SORTOWANIE.get(k["frakcja"], SORTOWANIE["zmieszane"]),
                           qr_url=f"{base}/zglos/{p.id}?qr={qr_token(p.id)}", qr_left_s=qr_seconds_left(),
                           panel_token=device_token(info.serial) if info and info.kind == "panel" else None)


@bp.get("/zglos")
def report_pick():
    """Mieszkaniec: skan kodu QR z panelu i „Twoje zgłoszenia”. Bez mapy i listy cudzych koszy (mieszkaniec to nie kierowca)."""
    return render_template("ui/zglos_wybor.html")


@bp.get("/zglos/<int:point_id>")
def report(point_id):
    """Zgłoszenie na jednym ekranie: problem → Wyślij. ?qr=<token> z kodu na panelu potwierdza skan (dzienny token kosza)."""
    from .api_pl import FRAKCJE, _point, kosz_json, qr_valid
    p = _point(point_id)
    if p is None:
        abort(404)
    now = clock.now()
    qr = request.args.get("qr", "")
    return render_template("ui/zglos.html", bin=kosz_json(p, point_states(now), now), frakcje=FRAKCJE, qr=qr,
                           qr_state="ok" if qr_valid(p.id, qr) else "nieaktualny" if qr else "brak")


@bp.get("/zgloszenie/<nr>")
def report_status(nr):
    """Status zgłoszenia jako oś czasu (dane z /api/zgloszenia/<nr>, odświeżane co kilka sekund)."""
    return render_template("ui/zgloszenie.html", nr=nr.upper())


@bp.get("/kierowca")
def driver():
    """Kierowca: mapa trasy i kosze po priorytecie (dane z /api/trasa, odświeżane przy każdej zmianie)."""
    return render_template("ui/kierowca.html")


@bp.get("/kierowca/kosz/<int:point_id>")
def driver_bin(point_id):
    """Karta kosza: zgłoszenia, „Jadę” z nawigacją w aplikacji, „Opróżniono”, „Problem”."""
    from .api_pl import _point, kosz_json
    p = _point(point_id)
    if p is None:
        abort(404)
    now = clock.now()
    return render_template("ui/kierowca_kosz.html", bin=kosz_json(p, point_states(now), now))


@bp.get("/dashboard")
def dashboard():
    """Dashboard miasta: KPI, wykresy, mapa, projekty. Dane z /api/dashboard/* (agregacje GROUP BY w bazie)."""
    from .api_pl import FRAKCJE
    return render_template("ui/dashboard.html", frakcje=FRAKCJE)


@bp.get("/dashboard/urzadzenia")
def devices_page():
    """Urządzenia na koszach: bateria, odczyty, masterdane (dane z /api/urzadzenia)."""
    return render_template("ui/urzadzenia.html")


@bp.get("/dashboard/projekty/<slug>")
def project(slug):
    """Szczegóły projektu z wykresami przed i po (dane z /api/projekty/<slug>)."""
    return render_template("ui/projekt.html", slug=slug)
