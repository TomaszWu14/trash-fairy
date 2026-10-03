"""Strony pomocnicze (PNG e-papieru, dokumentacja API, dostępność, prywatność, zdrowie) i przekierowania starych adresów.

Ekrany perspektyw są w app/ui.py. Stare adresy (QR na naklejkach, slajdy, zakładki jury) prowadzą do nowych ekranów 301,
więc żaden stary link nie kończy się ślepym zaułkiem (audit/AUDYT-UX.md, sekcja 4)."""
import io
import json
from pathlib import Path

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, send_file, url_for
from sqlalchemy import text

from . import clock, db
from .models import Point
from .ui import DEMO_BIN_ID

bp = Blueprint("main", __name__)


@bp.get("/api/docs")
def api_docs():
    """Dokumentacja otwartego API /api/v1 (własna strona, kontrakt w static/openapi.json)."""
    spec = json.loads(Path(current_app.static_folder, "openapi.json").read_text(encoding="utf-8"))
    return render_template("api_docs.html", spec=spec)


@bp.get("/epapier/<int:point_id>.png")
def epaper_png(point_id):
    """Obraz 1-bitowy aktualnego stanu ekranu e-papierowego; ?part=1 = tylko okno odświeżania częściowego."""
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
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["ETag"] = etag
    resp.headers["X-Epaper-State"] = state
    return resp


@bp.get("/dostepnosc")
def accessibility():
    """Deklaracja dostępności (decyzja 31): uczciwie „częściowo zgodna”."""
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


# ---------- stare adresy → nowe perspektywy ----------
REDIRECTS = {
    "/telefony": "ui.start", "/dyspozytor": "ui.dashboard", "/program": "ui.start", "/program/regulamin": "ui.start",
    "/przyjaciele": "ui.start", "/zdjecia": "ui.dashboard", "/logowanie": "ui.start", "/ekipa": "ui.driver",
}


def _old(endpoint):
    return lambda: redirect(url_for(endpoint), 301)


for _path, _endpoint in REDIRECTS.items():
    bp.add_url_rule(_path, f"old{_path.replace('/', '_')}", _old(_endpoint))


@bp.get("/jury")
def jury():
    from .api_pl import qr_token
    return redirect(url_for("ui.report", point_id=DEMO_BIN_ID, qr=qr_token(DEMO_BIN_ID)), 301)


@bp.get("/epapier/<int:point_id>")
def epaper_page(point_id):
    return redirect(url_for("ui.kiosk", point_id=point_id), 301)


@bp.get("/przycisk/<int:point_id>")
def button(point_id):
    return redirect(url_for("ui.kiosk", point_id=point_id), 301)


@bp.get("/kosz/<int:point_id>/zglos")
def qr_report(point_id):
    """Adres z kodu QR na ekranie e-papieru: zgłoszenie z potwierdzonym skanem (token kosza)."""
    from .api_pl import qr_token
    return redirect(url_for("ui.report", point_id=point_id, qr=qr_token(point_id)))


@bp.get("/kosz/<int:point_id>/status")
def qr_status(point_id):
    return redirect(url_for("ui.kiosk", point_id=point_id))
