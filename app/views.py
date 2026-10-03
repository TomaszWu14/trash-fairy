import os
from pathlib import Path
import random

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, send_file, send_from_directory, url_for
from sqlalchemy import text

from . import auth, clock, db
from .geo import distance_m
from .methodology import page_context
from .models import Point
from .osm_import import RYNEK

JURY_POOL = 6  # tyle koszy najbliżej Rynku losujemy dla jury — punkty dobrze widoczne na mapie

JURY_POINT_ID = 18  # ten sam kosz w ramkach /telefony, w QR jury i na slajdach (decyzja 13)
bp = Blueprint("main", __name__)


@bp.get("/")
def show():
    """Widok C „Pokaz dla jury”: historia w 4 krokach na jednej mapie."""
    clock.maybe_auto_reset()  # kolejny widz po 30 min bezczynności zaczyna od 13:30
    return render_template("pokaz.html", public_url=os.environ.get("PUBLIC_URL", ""))


@bp.get("/telefony")
def phones():
    """Dla jury: cykl jednego kosza w trzech ramkach (e-papier, mieszkaniec, kierowca w podglądzie) — decyzje 11–13."""
    clock.maybe_auto_reset()
    return render_template("telefony.html", point=db.get_or_404(Point, JURY_POINT_ID), public_url=os.environ.get("PUBLIC_URL", ""))


@bp.get("/dyspozytor")
def panel():
    return render_template("panel.html", public_url=os.environ.get("PUBLIC_URL", ""))


def jury_pool():
    bins = Point.query.filter_by(kind="bin").all()
    return sorted(bins, key=lambda p: distance_m(p.lat, p.lon, *RYNEK))[:JURY_POOL]


@bp.get("/jury")
def jury():
    """Kod QR w panelu prowadzi tutaj: losowy kosz przy Rynku, żeby jury naciskało różne przyciski."""
    pool = jury_pool()
    if not pool:
        return redirect(url_for("main.panel"))
    return redirect(url_for("main.report", point_id=random.choice(pool).id, jury=1))


@bp.get("/zglos/<int:point_id>")
def report(point_id):
    """Publiczny ekran „Zgłoś kosz” (PWA): mieszkaniec trafia tu z kodu QR na koszu."""
    from .api import WEEKDAYS_SHORT
    now = clock.now()
    return render_template("zglos.html", point=db.get_or_404(Point, point_id),
                           clock_label=f"{WEEKDAYS_SHORT[now.weekday()]} {now:%d.%m, %H:%M}")


@bp.get("/zglos")
def report_pick():
    """start_url PWA bez kosza: wybór kosza (najbliższe wg GPS w JS, zapas: pula przy Rynku)."""
    return render_template("zglos_wybor.html", points=jury_pool())


@bp.get("/zglos/sw.js")
def sw():
    """Service worker PWA zgłoszeń. Nagłówek pozwala na zakres /zglos (bez ukośnika), czyli także start_url."""
    resp = send_from_directory(os.path.join(current_app.static_folder, "zglos"), "sw.js", mimetype="application/javascript")
    resp.headers["Service-Worker-Allowed"] = "/zglos"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@bp.get("/api/docs")
def api_docs():
    """Dokumentacja otwartego API /api/v1 (własna strona, kontrakt w static/openapi.json)."""
    import json
    spec = json.loads(Path(current_app.static_folder, "openapi.json").read_text(encoding="utf-8"))
    return render_template("api_docs.html", spec=spec)


@bp.get("/kierowca")
def driver():
    """PWA kierowcy MPO: start zmiany → trasa → przystanek → podsumowanie (offline z kolejką).
    ?podglad=1: dla jury (ramka na /telefony), bez logowania, prawdziwa trasa floty koszy, zapisy wyłączone (decyzja 11)."""
    preview = request.args.get("podglad") == "1"
    if not preview and auth.role() != "driver":
        return redirect(url_for("main.login", next="/kierowca"))
    return render_template("kierowca.html", preview=preview)


@bp.get("/kierowca/sw.js")
def driver_sw():
    """Service worker PWA kierowcy, zakres /kierowca (jak /zglos/sw.js)."""
    resp = send_from_directory(os.path.join(current_app.static_folder, "kierowca"), "sw.js", mimetype="application/javascript")
    resp.headers["Service-Worker-Allowed"] = "/kierowca"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@bp.get("/epapier/<int:point_id>")
def epaper_page(point_id):
    """Symulator ekranu e-papierowego z fizycznym przyciskiem (docs/epapier/HANDOFF.md, etap 1)."""
    return render_template("epapier.html", point=db.get_or_404(Point, point_id))


@bp.get("/epapier/<int:point_id>.png")
def epaper_png(point_id):
    """Obraz 1-bitowy aktualnego stanu; ?part=1 = tylko okno odświeżania częściowego."""
    import io
    from . import epaper, epaper_render
    point = db.get_or_404(Point, point_id)
    state, data = epaper.display_state(point, clock.now())
    part = bool(request.args.get("part"))
    state_key, values_key = epaper.keys(state, data)
    etag = f'"{point_id}-{int(part)}-{state_key}-{values_key}"'  # ten sam ekran = 304 bez renderowania PNG (decyzja 35)
    if request.headers.get("If-None-Match") == etag:
        return "", 304, {"ETag": etag, "Cache-Control": "no-cache", "X-Epaper-State": state}
    img = epaper_render.render_partial(state, data) if part else epaper_render.render(state, data)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    resp = send_file(buf, mimetype="image/png")
    resp.headers["Cache-Control"] = "no-cache"  # przeglądarka pyta za każdym razem, ale dostaje 304, gdy ekran się nie zmienił
    resp.headers["ETag"] = etag
    resp.headers["X-Epaper-State"] = state
    return resp


# adresy z kodów QR na ekranie (renderer: /kosz/<nr>/zglos, /kosz/<nr>/status, /przyjaciele)
@bp.get("/kosz/<int:point_id>/zglos")
def qr_report(point_id):
    return redirect(url_for("main.report", point_id=point_id))


@bp.get("/kosz/<int:point_id>/status")
def qr_status(point_id):
    return redirect(url_for("main.report", point_id=point_id, status=1))


@bp.get("/przyjaciele")
def qr_program():
    return redirect(url_for("main.program"))


@bp.get("/zdjecia")
@auth.require("dispatcher")
def photos_upload():
    """Wgrywanie zdjęć z miasta paczką: kosz dobiera się z GPS w EXIF."""
    return render_template("zdjecia.html")


@bp.get("/metodologia")
def methodology():
    return render_template("metodologia.html", **page_context(clock.now()))


@bp.get("/przycisk/<int:point_id>")
def button(point_id):
    """Stara makieta słupka: zastąpiona symulatorem e-papieru z tym samym przyciskiem."""
    return redirect(url_for("main.epaper_page", point_id=point_id), 301)


@bp.get("/ekipa")
def crew():
    """Stary widok ekipy: zastąpiony PWA kierowcy (z uprawnieniami floty)."""
    return redirect(url_for("main.driver"), 301)


@bp.route("/logowanie", methods=["GET", "POST"])
def login():
    nxt = request.values.get("next") or ""
    safe_next = nxt if nxt.startswith("/") and not nxt.startswith("//") else ""  # tylko ścieżki w tej aplikacji
    error = None
    if request.method == "POST":
        error = auth.login(request.form.get("login"), request.form.get("password"), request.remote_addr)
        if error is None:
            return redirect(safe_next or auth.home_for_role())
    return render_template("logowanie.html", error=error, next=safe_next), 400 if error else 200


@bp.post("/wyloguj")
def logout():
    auth.logout()
    return redirect(url_for("main.show"))


@bp.get("/dostepnosc")
def accessibility():
    """Deklaracja dostępności (ustawa o dostępności cyfrowej, decyzja 31): uczciwie „częściowo zgodna”."""
    return render_template("dostepnosc.html")


@bp.get("/prywatnosc")
def privacy_page():
    """Jak używamy danych (decyzja 32)."""
    return render_template("prywatnosc.html")


@bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        return jsonify(status="error", db="down"), 503
    return jsonify(status="ok", db="ok")


@bp.get("/program")
def program():
    from .residents import DISTRICTS
    return render_template("program.html", districts=sorted(set(DISTRICTS.values())))


@bp.get("/program/regulamin")
def program_rules():
    from .residents import HEARTBEAT_LOST, POINTS
    return render_template("regulamin.html", points=POINTS, heartbeat_h=int(HEARTBEAT_LOST.total_seconds() // 3600))
