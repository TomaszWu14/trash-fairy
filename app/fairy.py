"""Raport „Wróżka podpowiada” (koncepcja, sekcja 8): fakty liczy kod, Claude tylko je opisuje.

Każdy raport jest zapisywany (FairyReport). Przy błędzie API pokazujemy komunikat i ostatni raport.
Liczby w tekście, których nie ma w faktach, oznaczamy — model nie ma prawa niczego dopowiadać.
"""
import json
import re

from . import db, llm
from .misuse import misuse_overview
from .models import FairyReport, Point
from .recommendations import recommendations
from .routes import plan_routes
from .simulation import hour_floor
from .state import point_states

SECTIONS = ["Najważniejsze dziś", "Trasy", "Nadużycia i powiązania", "Przyciski do sprawdzenia", "Rekomendacja inwestycyjna"]

SCHEMA = {
    "type": "object",
    "properties": {"sections": {"type": "array", "items": {
        "type": "object",
        "properties": {"title": {"type": "string", "enum": SECTIONS}, "text": {"type": "string"}},
        "required": ["title", "text"], "additionalProperties": False}}},
    "required": ["sections"],
    "additionalProperties": False,
}

SYSTEM = (
    "Jesteś asystentem dyspozytora MPO Kraków w systemie Trash Fairy. Dostajesz fakty w JSON policzone przez system. "
    "Napisz krótki raport po polsku, łącznie około 150 słów, w pięciu sekcjach: " + ", ".join(SECTIONS) + ". "
    "Każda sekcja to 1–2 zdania w tonie rzeczowym, bez wstępów. "
    "Używaj wyłącznie liczb, godzin i nazw, które są w JSON — niczego nie licz, nie szacuj i nie dodawaj nowych liczb. "
    "Nie podejmujesz decyzji: przekazujesz to, co ustaliły reguły systemu. Jeśli sekcja nie ma danych, napisz „Bez uwag.”."
)


def build_facts(now):
    """Wszystkie liczby do raportu — liczone w kodzie, nie przez model."""
    states = point_states(now)
    mo = misuse_overview(now)
    fleets = plan_routes(now, states)
    recs = recommendations(now, mo["recommendations"])
    points = {p.id: p for p in Point.query}
    upcoming = sorted(((pid, s) for pid, s in states.items() if s["crossing"] and s["crossing"] > now.isoformat()),
                      key=lambda item: item[1]["crossing"])
    soon = [{"punkt": points[pid].name, "przekroczenie_85": s["crossing_label"], "stan": s["label"]}
            for pid, s in upcoming[:3]]
    return {
        "zegar": f"{now:%d.%m.%Y %H:%M}",
        "punkty_do_oproznienia": sum(s["state"] == "bad" for s in states.values()),
        "punkty_zapelniajace_sie": sum(s["state"] == "warn" for s in states.values()),
        "najblizsze_przekroczenia": soon,
        "trasy": [{"flota": f["label"], "kurs": f["run_label"], "punktow": len(f["stops"]), "km": f["km"]} for f in fleets],
        "naduzycia": [{"punkt": points[pid].name, "co": info["misuse"]}
                      for pid, info in mo["points"].items() if info.get("misuse")],
        "powiazania_altana_kosz": [link["label"] for link in mo["links"]],
        "przyciski_do_sprawdzenia": [{"punkt": points[pid].name, "powod": s["check_reason"]}
                                     for pid, s in states.items() if s["check_button"]],
        "rekomendacje": [{"punkt": r["name"], "co": r["label"], "dlaczego": r["reason"], "efekt": r["impact"]} for r in recs[:3]],
    }


def unknown_numbers(sections, facts):
    """Liczby z tekstu raportu, których nie ma w faktach (np. 16:11 → „16” i „11” muszą wystąpić w JSON)."""
    known = set(re.findall(r"\d+", json.dumps(facts, ensure_ascii=False)))
    found = {n for s in sections for n in re.findall(r"\d+", s["text"])}
    return sorted(found - known, key=int)


def generate(now):
    """Nowy raport albo LLMError (wtedy wywołujący pokazuje ostatni zapisany)."""
    facts = build_facts(now)
    result = llm.ask_json("Fakty z systemu (JSON):\n" + json.dumps(facts, ensure_ascii=False, indent=1),
                          SCHEMA, system=SYSTEM, max_tokens=4000)
    order = {t: i for i, t in enumerate(SECTIONS)}
    sections = sorted(result["sections"], key=lambda s: order[s["title"]])
    report = FairyReport(at=now, facts=facts, sections=sections, model=llm.model(),
                         unknown_numbers=unknown_numbers(sections, facts))
    db.session.add(report)
    db.session.commit()
    return report


def latest(now=None):
    q = FairyReport.query
    if now is not None:
        q = q.filter(FairyReport.at <= now)
    return q.order_by(FairyReport.at.desc(), FairyReport.id.desc()).first()


def is_fresh(report, now):
    return report is not None and hour_floor(report.at) == hour_floor(now)


def to_dict(report):
    if report is None:
        return None
    return {"at": report.at.isoformat(), "label": f"{report.at:%d.%m %H:%M}", "sections": report.sections,
            "model": report.model, "unknown_numbers": report.unknown_numbers}
