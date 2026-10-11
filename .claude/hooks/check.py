"""Hook Stop: ruff + mypy na zmienionych plikach .py, potem pytest -x -q na powiązanych testach.

Błąd → exit 2 i ostatnie ~60 linii wyniku na stderr (Claude dostaje je i poprawia przed zakończeniem).
stop_hook_active = true → exit 0 (ochrona przed pętlą). Bez zmienionych .py nic nie uruchamia.
Pełne pytest -n auto trwa ~184 s (pomiar 11.10.2026) > 60 s, więc tylko testy powiązane ze zmianą.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _changed import changed_files  # noqa: E402

TAIL = 60


def related_tests(root, files):
    """tests/test_<moduł>.py + pliki testów importujące zmieniony moduł app.<moduł>; zmienione testy wprost."""
    if {"app/__init__.py", "tests/conftest.py", "tests/fakes.py"} & set(files):
        return ["tests"]  # fabryka aplikacji / wspólne fixtury – dotyczą wszystkich testów (~3 min z -n auto)
    tests = {f for f in files if re.match(r"^(tests|demo)/test_.*\.py$", f)}
    for f in files:
        m = re.match(r"^app/(\w+)\.py$", f)
        if not m:
            continue
        mod = m.group(1)
        pat = re.compile(rf"^\s*(import app\.{mod}\b|from app\.{mod}\b|from app import .*\b{mod}\b)", re.M)
        for t in (root / "tests").glob("test_*.py"):
            if t.name == f"test_{mod}.py" or pat.search(t.read_text(encoding="utf-8")):
                tests.add(t.relative_to(root).as_posix())
    return sorted(tests)


def run(root, *args):
    r = subprocess.run([sys.executable, "-m", *args], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=420)
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    if data.get("stop_hook_active"):
        return 0
    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or "."
    top = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode:
        return 0
    root = Path(top.stdout.strip())
    files = changed_files(root)
    if not files:
        return 0

    steps = [("ruff", ["ruff", "check", *files]),
             ("mypy", ["mypy", "--follow-imports=silent", "--no-error-summary", *files])]
    tests = related_tests(root, files)
    if tests:
        # -n 4 dla kilku plików: 94 s vs 181 s z -n auto (12 workerów dławi się ciężkimi fixturami); pomiar 11.10.2026
        workers = ["-n", "auto"] if tests == ["tests"] else ["-n", "4"] if len(tests) > 1 else []
        steps.append(("pytest", ["pytest", "-x", "-q", "-p", "no:cacheprovider", *workers, *tests]))
    for name, args in steps:
        if importlib.util.find_spec(args[0]) is None:
            continue  # brak narzędzia w tym interpreterze – nie blokujemy (pip install -r requirements-dev.txt)
        code, out = run(root, *args)
        if code:
            tail = "\n".join(out.splitlines()[-TAIL:])
            print(f"[check] {name} nie przechodzi na zmienionych plikach ({len(files)} plików .py).\n"
                  f"Popraw przed zakończeniem:\n{tail}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
