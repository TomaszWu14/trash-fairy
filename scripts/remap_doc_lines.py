"""Przelicza odwołania `plik:linia` w docs/0*.md po zmianach w app/ (stare numery → nowe, z hunków git diff -U0).

Użycie: python scripts/remap_doc_lines.py [baza=origin/main]. Linia zmieniona w diffie wskazuje początek nowego bloku;
po uruchomieniu sprawdź ręcznie 2–3 przesunięte odwołania (CLAUDE.md, „Koniec gałęzi”).
"""
import re
import subprocess
import sys
from pathlib import Path

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.M)
REF = re.compile(r"((?:app/(?:static/ui/)?)?[a-z_]+\.(?:py|js)):(\d[\d, \-–]*\d|\d)")


def hunks(diff):
    return [(int(a), int(b or 1), int(c), int(d or 1)) for a, b, c, d in HUNK.findall(diff)]


def remap(n, hs):
    """Stary numer linii → nowy według hunków (old_start, old_count, new_start, new_count)."""
    shift = 0
    for os_, oc, ns, nc in hs:
        if oc and os_ <= n < os_ + oc:
            return ns + min(n - os_, max(nc - 1, 0))
        if n >= os_ + oc if oc else n > os_:
            shift = (ns + nc) - (os_ + oc) if oc else ns + nc - 1 - os_
    return n + shift


def rewrite(text, maps):
    def fix(m):
        hs = maps.get(m.group(1).split("/")[-1])
        return m.group(1) + ":" + re.sub(r"\d+", lambda k: str(remap(int(k.group()), hs)), m.group(2)) if hs else m.group(0)
    return REF.sub(fix, text)


def main(base="origin/main"):
    git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True, encoding="utf-8").stdout  # noqa: E731
    maps = {f.split("/")[-1]: hunks(git("diff", "-U0", base, "HEAD", "--", f))
            for f in git("diff", "--name-only", base, "HEAD", "--", "app").split()}
    for doc in sorted(Path("docs").glob("0*.md")):
        old = doc.read_text(encoding="utf-8")
        new = rewrite(old, maps)
        if new != old:
            doc.write_text(new, encoding="utf-8")
            print("przeliczono", doc)


if __name__ == "__main__":
    main(*sys.argv[1:])
