#!/usr/bin/env bash
# Testy mutacyjne jednego modułu: bash scripts/mutate.sh forecast   (albo app/forecast.py, app.forecast)
# Raport z przeżytymi mutantami → reports/mutation-<moduł>-<data>.md. Wolne (minuty), nie jest podpięte pod hooki.
# mutmut 3 nie działa na Windows: tam skrypt uruchamia sam siebie w kontenerze python:3.12-slim (jak Dockerfile).
# Pamięć: MUTATE_JOBS równoległych procesów testów (domyślnie 4; każdy ładuje aplikację z OR-Tools), kontener max 3 GB.
set -euo pipefail
cd "$(dirname "$0")/.."
mod="${1:?Użycie: bash scripts/mutate.sh <moduł>  np. forecast}"
mod="${mod#app/}"; mod="${mod#app.}"; mod="${mod%.py}"
file="app/$mod.py"
[ -f "$file" ] || { echo "Nie ma pliku $file" >&2; exit 1; }
stamp="$(date +%Y-%m-%d)"
report="reports/mutation-$mod-$stamp.md"
mkdir -p reports

case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*)
  [ "${MUTATE_IN_DOCKER:-}" = 1 ] && { echo "Pętla: już w kontenerze" >&2; exit 1; }
  command -v docker >/dev/null || { echo "Na Windows potrzebny Docker (albo WSL): mutmut nie działa natywnie" >&2; exit 1; }
  # MSYS_NO_PATHCONV: Git Bash nie przerabia /src na ścieżkę Windows; pip cache w wolumenie przyspiesza kolejne uruchomienia
  MSYS_NO_PATHCONV=1 exec docker run --rm --memory 3g -e MUTATE_IN_DOCKER=1 -e MUTATE_JOBS="${MUTATE_JOBS:-4}" -v "$(pwd -W 2>/dev/null || pwd):/src" \
    -v trash-fairy-pip:/root/.cache/pip -w /src python:3.12-slim bash -c \
    "pip install -q --root-user-action=ignore -r requirements.txt -r requirements-dev.txt && bash scripts/mutate.sh $mod"
esac

# Kopia robocza: mutmut zapisuje mutants/ i zmienia konfigurację – repo zostaje nietknięte (poza raportem).
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
tar --exclude=./.venv --exclude=./.git --exclude=./mutants --exclude=./reports --exclude=./demo -cf - . | tar -xf - -C "$work"

# Powiązane testy – ta sama reguła co w hooku Stop (.claude/hooks/check.py); brak powiązanych → wszystkie.
tests="$(python -c "import sys; sys.path.insert(0, '.claude/hooks'); from pathlib import Path; from check import related_tests
print(' '.join(related_tests(Path('.'), ['$file']) or ['tests']))")"
python - "$work/pyproject.toml" "$file" $tests <<'EOF'
import json, sys
path, target, *tests = sys.argv[1:]
text = open(path, encoding="utf-8").read()
head = text[:text.index("[tool.mutmut]")]
open(path, "w", encoding="utf-8").write(head + "[tool.mutmut]\n" + "\n".join([
    'source_paths = ["app/"]', 'also_copy = ["data/"]',
    f"only_mutate = {json.dumps([target])}",
    f"pytest_add_cli_args_test_selection = {json.dumps(tests)}",
    'pytest_add_cli_args = ["-p", "no:cacheprovider", "-q"]']) + "\n")
EOF
echo "Moduł: $file  testy: $tests"

start=$(date +%s)
( cd "$work" && python -m mutmut run --max-children "${MUTATE_JOBS:-4}" ) > "$work/run.log" 2>&1 || true
secs=$(( $(date +%s) - start ))
( cd "$work" && python -m mutmut results --all true ) > "$work/results.txt" 2>&1 || true

{
  echo "# Testy mutacyjne: \`$file\` ($stamp)"
  echo
  echo "- Testy: \`$tests\`"
  echo "- Czas: ${secs} s · mutmut $(python -m mutmut --version 2>/dev/null | awk '{print $NF}')"
  echo
  echo "## Podsumowanie"
  echo
  echo '| status | liczba |'
  echo '|---|---|'
  grep -oE ': [a-z ]+$' "$work/results.txt" | sed 's/^: //' | sort | uniq -c | awk '{c=$1; $1=""; sub(/^ /,""); print "| " $0 " | " c " |"}'
  echo
  echo "Przeżyte mutanty (survived) = zmiana w kodzie, której żaden test nie wykrył. Dopisz test albo uznaj mutant za równoważny."
  echo
  echo "## Przeżyte mutanty"
  survivors=$(grep -E ': survived$' "$work/results.txt" | sed 's/: survived$//' | sed 's/^ *//' || true)
  if [ -z "$survivors" ]; then echo; echo "Brak."; fi
  for m in $survivors; do
    echo; echo "### \`$m\`"; echo; echo '```diff'
    ( cd "$work" && python -m mutmut show "$m" 2>&1 ) | sed -n '1,40p'
    echo '```'
  done
  echo
  echo "## Log uruchomienia (ostatnie 15 linii)"
  echo; echo '```'; tail -15 "$work/run.log" | tr '\r' '\n' | tail -15; echo '```'
} > "$report"
echo "Raport: $report"
grep -E '^\| ' "$report" || true
