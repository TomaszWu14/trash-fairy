"""Strona Metodologia: założenia czytane wprost ze stałych w kodzie + jawne przeliczenie na zł i CO₂.

Złotówki i CO₂ to wyłącznie konfigurowalne założenia (env), nie dane MPO.
"""
import os

from . import comparison, events, forecast, misuse, osm_import, photos, recommendations, reports, routes, simulation, state, traffic, weather


def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


def _pl(v):
    return f"{v:g}".replace(".", ",")


def money_assumptions():
    return {
        "cost_per_km": _env_float("COST_PER_KM_PLN", 5.0),  # paliwo + eksploatacja pojazdu
        "cost_per_visit": _env_float("COST_PER_VISIT_PLN", 4.0),  # kilka minut pracy ekipy przy punkcie
        "co2_per_km": _env_float("CO2_KG_PER_KM", 1.0),  # pojazd z silnikiem diesla
    }


def assumptions():
    """[(obszar, założenie, wartość)] — wartości wprost z kodu."""
    e = events
    return [
        ("Punkty", "Kosze uliczne (Rynek, Kazimierz, przy przeciążonych altanach)",
         f"{sum(n for _, _, n in osm_import.BIN_AREAS) + osm_import.OVERLOADED_SHELTERS * osm_import.BINS_NEAR_OVERLOADED_SHELTER}, "
         f"min. {osm_import.MIN_GAP_M} m od siebie"),
        ("Punkty", "Altany osiedlowe (Grzegórzki), w tym celowo przeciążone", f"{osm_import.SHELTERS}, {osm_import.OVERLOADED_SHELTERS}"),
        ("Symulacja", "Tempo zapełniania kosza", "1,5%/h + 0,06 za lokal lub sklep + 0,6 za przystanek w 100 m, max 8%/h"),
        ("Symulacja", "Stały harmonogram (dziś)", f"kosze o {', '.join(f'{h}:00' for h in simulation.BIN_EMPTY_HOURS)}, "
                                                  f"altany co {simulation.SHELTER_EMPTY_EVERY_DAYS} dni o {simulation.SHELTER_EMPTY_HOUR}:00"),
        ("Zgłoszenia", "Scalanie naciśnięć", f"{int(reports.MERGE_WINDOW.total_seconds() // 60)} min od pierwszego"),
        ("Zgłoszenia", "Zgłoszenie trafne", f"opróżnienie przy poziomie ≥{reports.HIT_LEVEL}%"),
        ("Zgłoszenia", "Wiarygodność przycisku", f"trafne z ostatnich {reports.RELIABILITY_WINDOW}, start {round(reports.DEFAULT_RELIABILITY * 100)}%"),
        ("Zgłoszenia", "Flaga „sprawdź przycisk”", f"<{round(reports.FLAG_BELOW * 100)}% trafnych w {reports.FLAG_DAYS} dni "
                                                  f"albo {state.OVERFLOW_HOURS} h przepełnienia bez naciśnięcia"),
        ("Stan", "Progi", f"żółty od {state.WARN_FROM}%, czerwony powyżej {state.BAD_ABOVE}% lub świeże zgłoszenie"),
        ("Prognoza", "Profil", "7 dni × 24 h na punkt: średnia i kwantyle p20/p80 z historii sprzed zegara"),
        ("Prognoza", "Wydarzenia (promień, mnożnik)", ", ".join(f"{e.SCALE_PL[k]}: {e.RADIUS_M[k]} m ×{str(e.MULTIPLIER[k]).replace('.', ',')}"
                                                               for k in e.RADIUS_M) + ", także godzinę po"),
        ("Prognoza", "Pogoda (Open-Meteo), tylko godziny przyszłe",
         f"opad ≥ {_pl(weather.RAIN_MM)} mm/h ×{_pl(weather.RAIN_FACTOR)}; weekend {weather.NICE_HOURS.start}–{weather.NICE_HOURS.stop}, "
         f"≥ {_pl(weather.WARM_C)} °C i sucho ×{_pl(weather.NICE_FACTOR)}; inaczej ×1,0. Profil, MAE i porównanie bez pogody"),
        ("Trasy", "Ruch (TomTom), tylko czas",
         f"korek = prędkość swobodna / obecna, {_pl(traffic.MIN_RATIO)}–{_pl(traffic.MAX_RATIO)}, średnia z {len(traffic.SAMPLES)} punktów; "
         f"czas jazdy = km / {traffic.CITY_KMH} km/h × korek, ETA + dojazd {traffic.APPROACH_KM} km; pomiar starszy niż "
         f"{traffic.MAX_AGE_S // 3600} h pomijany. Nie zmienia wyboru punktów ani km"),
        ("Trasy", "Wybór punktu", "pełny teraz, 85% przed kolejnym kursem albo bezpiecznik "
                                  f"(kosz {routes.FLEETS['bin']['safety'].days} dni, altana {routes.FLEETS['shelter']['safety'].days} dni)"),
        ("Trasy", "Odległości", f"linia prosta ×{str(routes.DETOUR).replace('.', ',')}, baza: {routes.DEPOT['name']}"),
        ("Zdjęcia", "Rozbieżność zdjęcie ↔ ekipa", f">{photos.DISCREPANCY_PP} p.p."),
        ("Nadużycia", "Powiązanie altana → kosz", f"worki domowe w {misuse.LINK_RADIUS_M} m od altany przepełnionej w ostatnich "
                                                  f"{int(misuse.SHELTER_WINDOW.total_seconds() // 3600)} h"),
        ("Rekomendacje", "Kompaktor", f"przepełniony w >{round(recommendations.OVERFLOW_COMPACTOR * 100)}% dni mimo 2× dziennie "
                                      f"(pojemność ×{recommendations.COMPACTOR_FACTOR} — założenie)"),
        ("Rekomendacje", "Większy kosz", f"przepełniony w {round(recommendations.OVERFLOW_BIGGER_BIN * 100)}–"
                                         f"{round(recommendations.OVERFLOW_COMPACTOR * 100)}% dni"),
        ("Rekomendacje", "Rzadziej", f"<{round(recommendations.RARELY_HALF_FULL * 100)}% opróżnień przy poziomie ≥50%"),
    ]


def money(result):
    """Przeliczenie wyniku porównania (4 tygodnie) na miesiąc, zł i CO₂ — wg jawnych założeń."""
    a = money_assumptions()
    scale = 30 / (result["weeks"] * 7)
    fixed, fairy = result["fixed"]["total"], result["fairy"]["total"]
    d_km = (fixed["km"] - fairy["km"]) * scale
    d_visits = (fixed["visits"] - fairy["visits"]) * scale
    return {
        "assumptions": a,
        "km_month": round(d_km), "visits_month": round(d_visits),
        "pln_month": round(d_km * a["cost_per_km"] + d_visits * a["cost_per_visit"]),
        "co2_kg_month": round(d_km * a["co2_per_km"]),
        "forecast": forecast.QUALITY_DAYS,
    }


def page_context(now):
    result = comparison.compare(simulation.DEMO_NOW)
    return {"assumptions": assumptions(), "money": money(result), "result": result,
            "quality": forecast.forecast_quality(simulation.hour_floor(now))}
