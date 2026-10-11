#!/usr/bin/env bash
# Testy strażnika: każdy przypadek to JSON hooka PreToolUse na stdin i oczekiwany kod wyjścia (2 = blokada, 0 = przepuść).
# Uruchom: bash .claude/hooks/test_guard.sh   (kod 1, jeśli któryś przypadek nie przeszedł)
cd "$(dirname "$0")/../.." || exit 1
fail=0
check() {  # oczekiwany_kod  json
  err=$(printf '%s' "$2" | bash .claude/hooks/run.sh guard.py 2>&1 >/dev/null); code=$?
  [ "$code" = "$1" ] && mark=OK || { mark=BŁĄD; fail=1; }
  printf '%-4s exit=%s  %s\n' "$mark" "$code" "$2"
  [ -n "$err" ] && printf '          stderr: %s\n' "$err"
}
B() { check "$1" "{\"tool_name\":\"Bash\",\"cwd\":\".\",\"scratchpad_dir\":\"/c/scratch\",\"tool_input\":{\"command\":$2}}"; }
F() { check "$1" "{\"tool_name\":\"$2\",\"tool_input\":{\"file_path\":$3,\"content\":\"x\"}}"; }

echo "== 1. rm -r poza katalogami tymczasowymi"
B 2 '"rm -rf app"'
B 2 '"rm -r ./data && echo ok"'
B 2 '"sudo rm -fr /"'
B 2 '"rm -rf /tmp/../home/user"'
B 2 '"rm -rf /tmp"'
B 0 '"rm -rf /tmp/build-123"'
B 0 '"rm -rf /c/scratch/venv"'
B 0 '"rm -r C:\\Users\\tomas\\AppData\\Local\\Temp\\x"'
B 0 '"rm plik.txt"'
check 2 '{"tool_name":"PowerShell","tool_input":{"command":"Remove-Item -Recurse -Force app"}}'
echo "== 2. git push --force / -f, git reset --hard na main, push na main"
B 2 '"git push --force origin feature"'
B 2 '"git push -f"'
B 2 '"git push --force-with-lease"'
B 2 '"git push origin +feature"'
B 2 '"git push origin main"'
B 2 '"git push origin HEAD:main"'
B 2 '"git checkout main && git reset --hard origin/main"'
B 0 '"git checkout feature && git reset --hard HEAD~1"'
B 0 '"git push -u origin chore/claude-harness"'
B 2 '"git checkout -q -- docs/0*.md"'
B 2 '"git restore app/models.py"'
B 0 '"git restore --staged app/models.py"'
B 0 '"git checkout -b fix/x origin/main"'
B 0 '"git log --oneline -5 main"'
echo "== 3. SQL"
B 2 '"psql -c \"DROP TABLE point\""'
B 2 '"sqlite3 trash_fairy.db \"truncate table press\""'
B 2 '"sqlite3 x.db \"DELETE FROM press\""'
B 2 '"sqlite3 x.db \"UPDATE point SET live=0;\""'
B 0 '"sqlite3 x.db \"DELETE FROM press WHERE id=3\""'
B 0 '"sqlite3 x.db \"UPDATE point SET note='"'"'x'"'"' WHERE id=1\""'
B 0 '"grep -rn \"DROP TABLE\" app"'
B 0 '"sqlite3 x.db \"SELECT count(*) FROM press\""'
echo "== 4. .env* i pliki z sekretami"
F 2 Write '".env"'
F 2 Edit '"C:\\repo\\.env.production"'
F 2 Write '"/home/u/.ssh/id_rsa"'
F 2 Write '"certs/server.pem"'
F 0 Write '".env.example"'
F 0 Edit '"app/models.py"'
B 2 '"echo ANTHROPIC_API_KEY=x >> .env"'
B 2 '"cp .env.example .env"'
B 2 '"sed -i s/a/b/ .env.local"'
B 0 '"cat .env.example"'
echo "== 5. produkcja: deploy i niedomowa baza"
B 2 '"DATABASE_URL=postgresql://u:p@10.0.0.5:5432/tf flask --app app seed --force"'
B 2 '"psql postgres://admin:x@db.example.com/prod"'
B 2 '"psql -h 203.0.113.10 -U tf"'
B 2 '"ssh root@203.0.113.10 docker ps"'
B 2 '"curl -X POST https://coolify.example.com/api/v1/deploy?uuid=abc"'
B 2 '"gh workflow run deploy.yml"'
B 2 '"docker push ghcr.io/x/trash-fairy"'
B 0 '"DATABASE_URL=postgresql://trashfairy:trashfairy@localhost:5432/trashfairy flask --app app run"'
B 0 '"docker compose up --build"'
B 0 '"curl -s http://localhost:8080/health"'
echo "== nieznany format wejścia"
check 0 'to nie jest json'
exit $fail
