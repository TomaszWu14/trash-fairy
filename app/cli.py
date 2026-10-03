import click

from datetime import timedelta

from . import clock, karnet, photos
from .events import import_events
from .models import Event, Point
from .osm_import import import_points, load_cache
from .simulation import DEMO_NOW

DEMO_DAYS = [DEMO_NOW.date(), DEMO_NOW.date() + timedelta(days=1)]


@click.command("seed")
@click.option("--force", is_flag=True, help="Nadpisz istniejące punkty i historię.")
def seed_command(force):
    """Import punktów z data/*.geojson i wydarzeń z data/events.json, symulacja historii i zegar demo na start scenariusza."""
    if Point.query.count() and not force:
        click.echo("Baza ma już punkty — pomijam (użyj --force, żeby nadpisać).")
        return
    import_points(load_cache())
    import_events()
    n_karnet = karnet.import_events(DEMO_DAYS)  # z cache data/karnet.json, bez sieci
    stats = clock.reset()
    click.echo(f"Punkty: {Point.query.filter_by(kind='bin').count()} koszy, "
               f"{Point.query.filter_by(kind='shelter').count()} altan, {Event.query.count()} wydarzeń "
               f"(w tym {n_karnet} z Karnetu). Symulacja: {stats}")


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
