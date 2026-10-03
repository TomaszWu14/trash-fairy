import click

from .models import Point
from .osm_import import import_points, load_cache
from .simulation import simulate


@click.command("seed")
@click.option("--force", is_flag=True, help="Nadpisz istniejące punkty i historię.")
def seed_command(force):
    """Import punktów z data/*.geojson i 8 tygodni symulowanej historii."""
    if Point.query.count() and not force:
        click.echo("Baza ma już punkty — pomijam (użyj --force, żeby nadpisać).")
        return
    import_points(load_cache())
    n_levels, n_empty = simulate()
    click.echo(f"Punkty: {Point.query.filter_by(kind='bin').count()} koszy, "
               f"{Point.query.filter_by(kind='shelter').count()} altan. "
               f"Historia: {n_levels} pomiarów, {n_empty} opróżnień.")
