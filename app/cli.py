import click

from . import clock
from .events import import_events
from .models import Event, Point
from .osm_import import import_points, load_cache


@click.command("seed")
@click.option("--force", is_flag=True, help="Nadpisz istniejące punkty i historię.")
def seed_command(force):
    """Import punktów z data/*.geojson i wydarzeń z data/events.json, symulacja historii i zegar demo na start scenariusza."""
    if Point.query.count() and not force:
        click.echo("Baza ma już punkty — pomijam (użyj --force, żeby nadpisać).")
        return
    import_points(load_cache())
    import_events()
    stats = clock.reset()
    click.echo(f"Punkty: {Point.query.filter_by(kind='bin').count()} koszy, "
               f"{Point.query.filter_by(kind='shelter').count()} altan, {Event.query.count()} wydarzenia. Symulacja: {stats}")
