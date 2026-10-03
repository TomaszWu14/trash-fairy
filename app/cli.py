import time

import click
from sqlalchemy import func

from datetime import timedelta

from . import clock, db, history, karnet, photos
from .events import import_events
from .models import Emptying, Event, Point
from .osm_import import import_city_points, import_points, load_cache
from .simulation import DEMO_NOW

DEMO_DAYS = [DEMO_NOW.date(), DEMO_NOW.date() + timedelta(days=1)]


@click.command("seed")
@click.option("--force", is_flag=True, help="Nadpisz istniejące punkty i historię.")
def seed_command(force):
    """Import punktów z data/*.geojson i wydarzeń z data/events.json, symulacja historii i zegar demo na start scenariusza."""
    if Point.query.count() and not force:
        if Point.query.filter(Point.live.is_(False)).count() == 0:  # baza sprzed panelu miasta: dokładamy tylko jego dane
            n_city = import_city_points()
            click.echo(f"Dodano {n_city} punktów miasta. Historia: {history.generate_history(sim_start=_sim_start())}")
            return
        click.echo("Baza ma już punkty — pomijam (użyj --force, żeby nadpisać).")
        return
    t0 = time.perf_counter()
    # PostgreSQL pilnuje kluczy obcych (SQLite nie): najpierw tabele zależne od punktów, w kolejności zależności
    from .models import (Device, DeviceInfo, Emptying, Forecast, PhotoAnalysis, Pickup, PointAward, Press, Report,
                         ReportHistory, StopIssue)
    for model in (PointAward, Press, Report, Emptying, Forecast, StopIssue, PhotoAnalysis, Pickup, ReportHistory, DeviceInfo, Device):
        db.session.query(model).delete()
    db.session.commit()
    import_points(load_cache())
    n_city = import_city_points()
    import_events()
    n_karnet = karnet.import_events(DEMO_DAYS)  # z cache data/karnet.json, bez sieci
    stats = clock.reset()
    click.echo(f"Punkty demo: {Point.live_query().filter_by(kind='bin').count()} koszy, "
               f"{Point.live_query().filter_by(kind='shelter').count()} altan; punkty miasta: {n_city}; "
               f"{Event.query.count()} wydarzeń (w tym {n_karnet} z Karnetu). Symulacja: {stats}. "
               f"Czas: {time.perf_counter() - t0:.1f} s")


def _sim_start():
    """Początek okna symulacji w istniejącej bazie (historia punktów demo kończy się tuż przed nim)."""
    return db.session.query(func.min(Emptying.at)).scalar() or DEMO_NOW


@click.command("cleanup-photos")
def cleanup_photos_command():
    """Usuwa pliki zdjęć starszych niż 7 dni (wyniki analiz zostają w bazie). Do crona."""
    click.echo(f"Usunięto {photos.cleanup()} zdjęć.")


@click.command("karnet")
@click.option("--pages", default=5, help="Ile stron każdej listy pobrać (12 wydarzeń na stronę).")
def karnet_command(pages):
    """Pobiera wydarzenia z Karnet Kraków do data/karnet.json, importuje je i odtwarza symulację."""
    click.echo(f"Pobrano {karnet.fetch(pages)} wydarzeń.")
    click.echo(f"W obszarze demo w weekend demo: {karnet.import_events(DEMO_DAYS)}.")
    clock.reset()
    click.echo("Symulacja odtworzona z nowymi wydarzeniami.")
