"""Wejście Gunicorna (Dockerfile, --preload): aplikacja i ciężkie wyliczenia raz w procesie głównym, przed forkiem workerów.

Porównanie 4 tygodni (2–5 s) i stan punktów liczymy tu, więc karta „Efekt” i pierwsze wejście jury nie czekają (decyzja 25)."""
from . import create_app

app = create_app()

with app.app_context():
    try:
        from .comparison import compare
        from .simulation import DEMO_NOW
        compare(DEMO_NOW)
    except Exception:  # pusta baza przed seed: policzy się przy pierwszym zapytaniu
        pass
