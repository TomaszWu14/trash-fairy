"""scripts/remap_doc_lines.py: odwołania plik:linia w docs przesuwają się razem z kodem."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("remap", Path(__file__).resolve().parent.parent / "scripts" / "remap_doc_lines.py")
remap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remap)

# 3 linie wstawione po linii 9 (przed dawną 10), dawne linie 20–21 zamienione na jedną
DIFF = "@@ -9,0 +10,3 @@\n+a\n+b\n+c\n@@ -20,2 +23 @@\n-x\n-y\n+z\n"


def test_lines_after_insert_shift_and_before_stay():
    hs = remap.hunks(DIFF)
    assert [remap.remap(n, hs) for n in (5, 10, 12, 20, 21, 30)] == [5, 13, 15, 23, 23, 32]


def test_rewrite_touches_only_changed_files():
    maps = {"state.py": remap.hunks(DIFF)}
    text = "`app/state.py:12, 30` i `app/routes.py:12`"
    assert remap.rewrite(text, maps) == "`app/state.py:15, 32` i `app/routes.py:12`"
