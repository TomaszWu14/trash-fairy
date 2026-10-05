"""Strażnik osi czasu lektora: napis z surowego nagrania musi trafić w to samo miejsce przyciętego filmu."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_all import on_cut  # noqa: E402


def test_on_cut():
    keep = [(1.0, 3.0), (5.0, 6.0), (10.0, 14.0)]
    assert on_cut(2.0, keep) == 1.0
    assert on_cut(4.0, keep) == 2.0  # chwila z wyciętej przerwy → początek następnego odcinka
    assert on_cut(5.5, keep) == 2.5
    assert on_cut(12.0, keep, 2.0) == 2.5  # przyspieszenie ×2
    assert on_cut(99.0, keep) == 7.0


def test_lektor_texts_stale_i_bez_duplikatow():
    from build_all import CARDS, lektor_texts
    texts = lektor_texts()  # SystemExit, gdy tekst lektora zależy od danych (f-string bez spoken=)
    assert len(texts) == len(set(texts)) and texts[0] == CARDS[0][3]
    assert all("{" not in t for t in texts)


def test_film_pelny_lektor_kompletny():
    """Każdy klucz lektora użyty w pełnym filmie ma tekst, każdy tekst jest użyty i nie zależy od danych (stały, bez liczb cyfrą)."""
    import re
    import film_pelny
    src = Path(film_pelny.__file__).read_text(encoding="utf-8")
    used = set(re.findall(r'mow\("(\w+)"', src)) | set(film_pelny.CHAPTERS) | set(re.findall(r'slides\["(s\d\d)"\]', src))
    assert used == set(film_pelny.TEKSTY)
    assert not any(re.search(r"\d", t.replace("Open311", "")) for t in film_pelny.TEKSTY.values())


def test_film_3min_ma_wszystkie_nagrania():
    """Każda kwestia filmu 3-minutowego („p:klucz” albo „k:NN”) ma plik nagrania."""
    import re
    import film_3min
    src = Path(film_3min.__file__).read_text(encoding="utf-8")
    keys = set(re.findall(r'"([pk]:\w+)"', src))
    assert keys and all((film_3min.SRC[k[0]] / f"{k[2:]}.mp3").is_file() for k in keys)
