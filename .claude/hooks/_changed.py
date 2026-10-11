"""Pliki .py zmienione względem main: commity na gałęzi + niezacommitowane + nowe nieśledzone.

Baza to origin/main (lokalny main bywa nieaktualny), a gdy jej nie ma – main.
Tylko biblioteka standardowa. Uruchomienie: python .claude/hooks/_changed.py
"""
import subprocess
from pathlib import Path


def _git(root, *args):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8")
    return r.stdout.splitlines() if r.returncode == 0 else []


def base_ref(root):
    for ref in ("origin/main", "main"):
        if _git(root, "rev-parse", "--verify", "--quiet", ref):
            return ref
    return None


def changed_files(root, suffix=".py"):
    root = Path(root)
    names = set(_git(root, "diff", "--name-only", "HEAD"))  # staged + unstaged
    names |= set(_git(root, "ls-files", "--others", "--exclude-standard"))
    base = base_ref(root)
    if base:
        names |= set(_git(root, "diff", "--name-only", f"{base}...HEAD"))
    return sorted(n for n in names if n.endswith(suffix) and (root / n).is_file())


if __name__ == "__main__":
    print("\n".join(changed_files(Path(__file__).resolve().parents[2])))
