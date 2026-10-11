#!/usr/bin/env bash
# Uruchamia hook Pythona interpreterem z .venv repo (tam są ruff/mypy/pytest), a bez venva – systemowym.
# Użycie w settings.json: bash "$CLAUDE_PROJECT_DIR/.claude/hooks/run.sh" guard.py
dir="$(cd "$(dirname "$0")" && pwd)"
root="${CLAUDE_PROJECT_DIR:-$dir/../..}"
[ -f "$dir/$1" ] || { echo "[hook] brak pliku $1 – pominięty" >&2; exit 0; }
for py in "$root/.venv/Scripts/python.exe" "$root/.venv/bin/python" python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c "" >/dev/null 2>&1; then
    exec "$py" "$dir/$1"
  fi
done
echo "[hook] brak interpretera Pythona – hook $1 pominięty" >&2
exit 0
