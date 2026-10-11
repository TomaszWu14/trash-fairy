#!/usr/bin/env bash
# Skan bezpieczeństwa: pip-audit (zależności z requirements.txt), bandit (app/, poziom medium+),
# trivy na obrazie Dockera (binarka w PATH albo obraz aquasec/trivy; bez nich – pominięty).
# Wynik: reports/security-<data>.md. Kod wyjścia 1, gdy którekolwiek narzędzie coś znalazło.
#   bash scripts/security_scan.sh            SKIP_TRIVY=1 bash scripts/security_scan.sh
set -uo pipefail
cd "$(dirname "$0")/.."
py=python; for p in .venv/Scripts/python.exe .venv/bin/python; do [ -x "$p" ] && py="$p" && break; done
mkdir -p reports
report="reports/security-$(date +%Y-%m-%d).md"
found=0

section() {  # tytuł  kod_wyjścia  plik_z_wynikiem
  echo "## $1"; echo
  if [ "$2" = 0 ]; then echo "Wynik: **brak zgłoszeń**."; else echo "Wynik: **są zgłoszenia** (kod wyjścia $2)."; fi
  echo; echo '```'; cat "$3"; echo '```'; echo
}
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

echo "pip-audit..."
"$py" -m pip_audit -r requirements.txt --progress-spinner off > "$tmp/pip" 2>&1; pip_rc=$?
echo "bandit..."
"$py" -m bandit -c pyproject.toml -r app -ll -q > "$tmp/bandit" 2>&1; bandit_rc=$?

trivy_rc=skip
if [ -z "${SKIP_TRIVY:-}" ] && command -v docker >/dev/null && docker info >/dev/null 2>&1; then
  if command -v trivy >/dev/null; then trivy_cmd=(trivy)
  elif docker image inspect aquasec/trivy >/dev/null 2>&1 || docker pull -q aquasec/trivy >/dev/null 2>&1; then
    trivy_cmd=(docker run --rm -v //var/run/docker.sock:/var/run/docker.sock -v trash-fairy-trivy:/root/.cache aquasec/trivy)
  fi
  if [ -n "${trivy_cmd+x}" ]; then
    echo "docker build + trivy..."
    if docker build -q -t trash-fairy:security-scan . > "$tmp/build" 2>&1; then
      MSYS_NO_PATHCONV=1 "${trivy_cmd[@]}" image --quiet --scanners vuln --severity HIGH,CRITICAL --table-mode detailed --exit-code 1 \
        trash-fairy:security-scan > "$tmp/trivy" 2>&1; trivy_rc=$?
    else
      cp "$tmp/build" "$tmp/trivy"; trivy_rc=build-failed
    fi
  fi
fi

{
  echo "# Skan bezpieczeństwa $(date '+%Y-%m-%d %H:%M')"
  echo
  echo "Gałąź \`$(git rev-parse --abbrev-ref HEAD)\` @ \`$(git rev-parse --short HEAD)\`"
  echo
  echo "| narzędzie | zakres | wynik |"
  echo "|---|---|---|"
  echo "| pip-audit | requirements.txt (zależności produkcyjne) | $([ $pip_rc = 0 ] && echo 'czysto' || echo "zgłoszenia ($pip_rc)") |"
  echo "| bandit | app/, poziom medium+ (-ll) | $([ $bandit_rc = 0 ] && echo 'czysto' || echo "zgłoszenia ($bandit_rc)") |"
  case "$trivy_rc" in
    skip) echo "| trivy | obraz Dockera | pominięty (brak trivy/Dockera lub SKIP_TRIVY) |" ;;
    0) echo "| trivy | obraz Dockera, HIGH+CRITICAL | czysto |" ;;
    *) echo "| trivy | obraz Dockera, HIGH+CRITICAL | zgłoszenia / błąd ($trivy_rc) |" ;;
  esac
  echo
  section "pip-audit" "$pip_rc" "$tmp/pip"
  section "bandit (medium+)" "$bandit_rc" "$tmp/bandit"
  [ "$trivy_rc" != skip ] && section "trivy (HIGH, CRITICAL)" "$trivy_rc" "$tmp/trivy"
} > "$report"

for rc in "$pip_rc" "$bandit_rc" "$trivy_rc"; do [ "$rc" = 0 ] || [ "$rc" = skip ] || found=1; done
echo "Raport: $report"
sed -n '/^| narzędzie/,/^$/p' "$report"
exit $found
