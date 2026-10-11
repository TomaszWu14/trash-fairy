"""Strażnik PreToolUse: blokuje groźne komendy i zapisy (exit 2 + powód na stderr).

Wejście: JSON hooka na stdin (tool_name, tool_input, cwd, scratchpad_dir). Tylko biblioteka standardowa.
Reguły: 1) rm -r poza katalogami tymczasowymi, 2) git push --force, git reset --hard na main,
3) SQL: DROP / TRUNCATE / DELETE i UPDATE bez WHERE, 4) zapis plików .env* i sekretów,
5) deploy na produkcję i połączenia z niedomową bazą.
Testy: bash .claude/hooks/test_guard.sh
"""
import json
import posixpath
import re
import subprocess
import sys

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "db", "host.docker.internal", ""}
TEMP_PREFIXES = ("/tmp/", "/var/tmp/", "/private/tmp/", "$tmpdir/", "${tmpdir}/", "$env:temp/", "%temp%/")
WRITE_OP = r"(>{1,2}|\btee\b|\bsed\s+-i|\bcp\b|\bmv\b|\bdd\b|set-content|add-content|out-file|\btouch\b)"
ENV_OK ={".env.example", ".env.sample", ".env.template"}  # wzory bez sekretów (CLAUDE.md: .env.example jako wzór)
SECRET_NAME = re.compile(
    r"^(\.env(\..+)?|.*\.(pem|key|p12|pfx|jks|keystore)|id_(rsa|ed25519|ecdsa|dsa)(\.pub)?|\.netrc|\.pgpass"
    r"|credentials(\..+)?|secrets?(\..+)?|service[-_]?account.*\.json|.*\.secret)$", re.I)


def norm(path):
    p = path.strip("\"'").replace("\\", "/").lower()
    return posixpath.normpath(p) + ("/" if p.endswith("/") else "")


def is_temp(path, scratch):
    p = norm(path)
    if "/appdata/local/temp/" in p + "/" and not p.rstrip("/").endswith("/appdata/local/temp"):
        return True
    roots = TEMP_PREFIXES + ((norm(scratch).rstrip("/") + "/",) if scratch else ())
    return any(p.startswith(r) and len(p.rstrip("/")) > len(r.rstrip("/")) for r in roots)


def is_secret_file(path):
    name = path.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1].strip("\"'")
    return bool(SECRET_NAME.match(name)) and name.lower() not in ENV_OK


def segments(cmd):
    for seg in re.split(r"\|\||&&|[;|\n]", cmd):
        toks = seg.split()
        while toks and (toks[0] in ("sudo", "env", "command", "exec") or re.match(r"^\w+=", toks[0])):
            toks.pop(0)
        if toks:
            yield [t.strip("\"'") for t in toks]


def current_branch(cwd, git_dir_arg):
    where = git_dir_arg or cwd or "."
    r = subprocess.run(["git", "-C", where, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip()


def check_command(cmd, cwd, scratch):
    # 1) rekurencyjne kasowanie poza katalogami tymczasowymi
    for toks in segments(cmd):
        head = toks[0].lower()
        if head == "rm" or head.endswith("/rm"):
            flags = [t for t in toks[1:] if t.startswith("-")]
            if any(f == "--recursive" or re.match(r"^-[a-zA-Z]*[rR]", f) for f in flags):
                targets = [t for t in toks[1:] if not t.startswith("-")]
                bad = [t for t in targets if not is_temp(t, scratch)] or (["(brak celu)"] if not targets else [])
                if bad:
                    return f"rm -r poza katalogiem tymczasowym: {' '.join(bad)}. Kasuj tylko w /tmp lub scratchpadzie."
        if head in ("remove-item", "ri", "rd", "rmdir") and any(t.lower().startswith("-r") for t in toks[1:]):
            targets = [t for t in toks[1:] if not t.startswith("-")]
            if not targets or any(not is_temp(t, scratch) for t in targets):
                return f"{toks[0]} -Recurse poza katalogiem tymczasowym: {' '.join(targets) or '(brak celu)'}."

    # 2) git: wymuszony push, push na main, reset --hard na main
    branch_switch = None
    for toks in segments(cmd):
        if toks[0] != "git":
            continue
        rest, git_dir = toks[1:], None
        while rest and rest[0] in ("-C", "-c"):
            git_dir = rest[1] if rest[0] == "-C" and len(rest) > 1 else git_dir
            rest = rest[2:]
        if not rest:
            continue
        sub, args = rest[0], rest[1:]
        if sub in ("checkout", "switch") and args:
            branch_switch = args[-1]
        if sub == "push":
            if any(a.startswith("--force") or re.match(r"^-[a-zA-Z]*f[a-zA-Z]*$", a) or a.startswith("+")
                   for a in args):
                return "git push --force/-f jest zablokowany: przepisuje historię zdalną. Zrób zwykły push nowego commita."
            if any(a in ("main", "master") or re.search(r":(refs/heads/)?(main|master)$", a) for a in args):
                return "Push bezpośrednio na main jest zablokowany (main = produkcja). Pushuj gałąź i otwórz PR."
        if sub == "reset" and "--hard" in args:
            br = branch_switch or current_branch(cwd, git_dir)
            if br in ("main", "master"):
                return f"git reset --hard na gałęzi {br} jest zablokowany: traci commity i zmiany. Użyj git revert albo nowej gałęzi."

    # 3) niszczący SQL (pomijamy wyszukiwanie tekstu, np. grep "DROP TABLE")
    first = cmd.split(maxsplit=1)[0].lower() if cmd.strip() else ""
    if first not in ("grep", "rg", "ag", "findstr", "select-string"):
        if m := re.search(r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|COLUMN|USER|ROLE|OWNED)\b", cmd, re.I):
            return f"SQL {m.group(0).upper()} jest zablokowany: nieodwracalna utrata danych/schematu."
        if m := re.search(r"\bTRUNCATE\s+(TABLE\s+)?[\w.]+", cmd, re.I):
            return f"SQL TRUNCATE jest zablokowany ({m.group(0)}): czyści całą tabelę."
        for stmt in cmd.split(";"):
            if re.search(r"\bDELETE\s+FROM\b", stmt, re.I) and not re.search(r"\bWHERE\b", stmt, re.I):
                return "SQL DELETE bez WHERE jest zablokowany: usunąłby wszystkie wiersze."
            if re.search(r"\bUPDATE\s+[\w.\"]+\s+SET\b", stmt, re.I) and not re.search(r"\bWHERE\b", stmt, re.I):
                return "SQL UPDATE bez WHERE jest zablokowany: zmieniłby wszystkie wiersze."

    # 4) zapis do .env* / plików z sekretami przez powłokę
    for tok in re.findall(r"[^\s\"'<>|;&]+", cmd):
        if is_secret_file(tok) and re.search(WRITE_OP + r"[^;&|\n]*" + re.escape(tok), cmd, re.I):
            return f"Zapis do pliku z sekretami ({tok}) jest zablokowany. Sekrety zmienia człowiek ręcznie."

    # 5) produkcja: niedomowa baza, deploy
    for host in re.findall(r"postgres(?:ql)?(?:\+\w+)?://[^@\s\"']*@\[?([^:/\s\"'\]]+)", cmd, re.I):
        if host.lower() not in LOCAL_HOSTS:
            return f"Połączenie z niedomową bazą ({host}) jest zablokowane: to może być produkcja. Pracuj na SQLite/compose."
    for toks in segments(cmd):
        head = toks[0].lower()
        if head in ("psql", "pg_dump", "pg_restore", "pgcli", "pg_dumpall"):
            for i, t in enumerate(toks):
                host = toks[i + 1] if t in ("-h", "--host") and i + 1 < len(toks) else (t.split("=", 1)[1] if t.startswith("--host=") else None)
                if host is not None and host.lower() not in LOCAL_HOSTS:
                    return f"{head} do hosta {host} jest zablokowany: to może być baza produkcyjna."
        if head in ("ssh", "scp", "rsync", "sftp"):
            return f"{head} na serwer jest zablokowany: zmiany na produkcji robi człowiek (Coolify)."
        if head == "coolify" or (head == "docker" and len(toks) > 1 and toks[1] == "push"):
            return f"Komenda deployu ({' '.join(toks[:2])}) jest zablokowana: deploy robi człowiek."
        if head == "gh" and toks[1:3] == ["workflow", "run"]:
            return "gh workflow run jest zablokowany: może uruchomić deploy. Poproś człowieka."
    if re.search(r"\b(curl|wget|invoke-webrequest|invoke-restmethod|iwr|irm)\b", cmd, re.I) and \
            re.search(r"coolify|/api/v1/deploy|/deploy\b|webhook", cmd, re.I):
        return "Wywołanie API/webhooka deployu jest zablokowane: deploy na produkcję robi człowiek."
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0  # nie nasz format – nie blokujemy pracy przez błąd strażnika
    tool, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    reason = None
    if tool in ("Bash", "PowerShell"):
        reason = check_command(inp.get("command", ""), data.get("cwd"), data.get("scratchpad_dir"))
    elif tool in ("Write", "Edit") and is_secret_file(inp.get("file_path", "")):
        reason = f"Zapis/edycja {inp.get('file_path')} jest zablokowana: plik z sekretami. Zmienia go człowiek ręcznie."
    if reason:
        print(f"[guard] {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
