#!/usr/bin/env python3
"""SDD progress dashboard: derives state from disk, serves it as JSON and one static page.

Costs zero agent tokens. Everything shown here is already on disk because the
skill maintains it as its source of truth (SKILL.md Step 1): the checkbox marks
in tasks.md, the frontmatter status/progress/current_milestone, each artifact's
validation: block. This reads the same files rather than asking the agent to
report anything.

The one exception is work that is in flight and therefore not on disk yet — a
judge running, a subagent dispatched. The agent appends one line per event to
.specs/.events.jsonl, which this serves alongside the derived state.

    python3 sdd_status.py --serve --repo-root .
    python3 sdd_status.py --json --repo-root .    # one-shot, no server

Serving is needed because fetch() from a file:// page is blocked by CORS.
"""
import argparse
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sdd_lint import parse_frontmatter, _parse_tasks, AGENT_TAG, FILES_TAG  # noqa: E402

HERE = Path(__file__).resolve().parent
DASHBOARD = HERE / "dashboard.html"
# Session labels are a viewing convenience, so they live with the dashboard's
# own state rather than in any repo — renaming a session must never dirty a
# working tree or show up in a diff.
NAMES_PATH = Path.home() / ".claude" / "sdd-dashboard-names.json"


def _load_names():
    try:
        return json.loads(NAMES_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_name(session, label):
    names = _load_names()
    if label:
        names[session] = label[:80]
    else:
        names.pop(session, None)
    NAMES_PATH.parent.mkdir(parents=True, exist_ok=True)
    NAMES_PATH.write_text(json.dumps(names, indent=1), encoding="utf-8")
    return names

# The lifecycle, in order. Each entry is (phase key, artifact filename).
PHASES = [
    ("discovery", "discovery.md"),
    ("spec", "spec.md"),
    ("design", "design.md"),
    ("test-catalog", "test-catalog.md"),
    ("plan", "plan.md"),
    ("tasks", "tasks.md"),
]
STATE_LABEL = {" ": "pending", "/": "in_progress", "x": "done", "!": "blocked"}


def _validation(fm):
    """Flatten the validation: list-of-single-pair-mappings into a dict."""
    out = {}
    for item in fm.get("validation", []) or []:
        if isinstance(item, dict):
            out.update(item)
    return out


def _read_artifact(path):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    fm, _ = parse_frontmatter(text)
    if fm is None:
        return None
    return text, fm


def _feature_state(feature_dir):
    """Everything the dashboard shows for one feature, read straight off disk."""
    feature = {"name": feature_dir.name, "phases": [], "tasks": [],
               "milestone": None, "progress": None, "blockers": []}

    for key, filename in PHASES:
        path = feature_dir / filename
        entry = {"phase": key, "file": filename, "exists": path.exists(),
                 "status": None, "tier1": None, "tier2_score": None,
                 "tier2_verdict": None, "judge_depth": None, "lines": None}
        if path.exists():
            read = _read_artifact(path)
            if read is not None:
                text, fm = read
                validation = _validation(fm)
                entry["status"] = fm.get("status")
                entry["tier1"] = validation.get("tier1")
                entry["tier2_score"] = validation.get("tier2_score")
                entry["tier2_verdict"] = validation.get("tier2_verdict")
                entry["judge_depth"] = validation.get("judge_depth")
                entry["lines"] = len(text.rstrip("\n").split("\n"))
        feature["phases"].append(entry)

    tasks_path = feature_dir / "tasks.md"
    read = _read_artifact(tasks_path) if tasks_path.exists() else None
    if read is not None:
        text, fm = read
        feature["milestone"] = fm.get("current_milestone")
        feature["progress"] = fm.get("progress")
        milestone = None
        for line in text.split("\n"):
            if line.startswith("## Milestone"):
                milestone = line[3:].strip()
            for task in _parse_tasks(line):
                agent = AGENT_TAG.search(task["rest"])
                files = FILES_TAG.search(task["rest"])
                feature["tasks"].append({
                    "id": task["id"],
                    "state": STATE_LABEL.get(task["state"], task["state"]),
                    "milestone": milestone,
                    "agent": agent.group(0)[len("[Agent:"):-1].strip() if agent else None,
                    "files": [f.strip() for f in files.group(1).split(",")] if files else [],
                    "deps": task["deps"],
                    "description": _strip_tags(task["rest"]),
                })
        feature["blockers"] = _blocker_log(text)
    return feature


def _strip_tags(rest):
    """Task description with the `[...]` tags removed."""
    out = []
    depth = 0
    for char in rest:
        if char == "[":
            depth += 1
        elif char == "]":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(char)
    return out and "".join(out).replace("`", "").strip() or ""


def _blocker_log(text):
    """Non-empty lines under the Execution Scratchpad heading, minus the boilerplate."""
    heading = "## Execution Scratchpad & Blocker Log"
    if heading not in text:
        return []
    body = text.split(heading, 1)[1]
    lines = []
    for line in body.split("\n"):
        if line.startswith("## "):
            break
        stripped = line.strip()
        if stripped and not stripped.startswith("*("):
            lines.append(stripped)
    return lines


def _events(repo_root, limit=40):
    """Optional in-flight pings. Absent, malformed, or empty is normal and expected.

    Liveness does not depend on these — see _last_change. They exist only for a
    session that wants to name what it is doing, and cost the agent tokens, so
    the default is to write none.
    """
    path = repo_root / ".specs" / ".events.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").split("\n")[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            out.append({"event": line})
    return out


def _last_change(repo_root):
    """Seconds since any artifact was touched — liveness, for zero agent tokens.

    A running session writes files. Nothing written for a long time means either
    finished or stuck, and either way that is what you want to see. This replaces
    the event ping as the default liveness signal, because it costs nothing.
    """
    newest = None
    for base in (repo_root / ".specs", repo_root / ".adrs"):
        if not base.is_dir():
            continue
        for path in base.rglob("*.md"):
            try:
                stamp = path.stat().st_mtime
            except OSError:
                continue
            if newest is None or stamp > newest[0]:
                newest = (stamp, str(path.relative_to(repo_root)))
    if newest is None:
        return None
    return {"seconds_ago": max(0, int(time.time() - newest[0])), "file": newest[1]}


def _tally(path, reader):
    """Fold one transcript into a totals dict, or None when it has no turns."""
    totals = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0, "turns": 0}
    try:
        handle = path.open(encoding="utf-8")
    except OSError:
        return None
    with handle:
        for line in handle:
            use = reader(line)
            if use is None:
                continue
            totals["turns"] += 1
            for key, source in (("input", "input_tokens"),
                                ("cache_write", "cache_creation_input_tokens"),
                                ("cache_read", "cache_read_input_tokens"),
                                ("output", "output_tokens")):
                totals[key] += use.get(source, 0) or 0
    if not totals["turns"]:
        return None
    totals["session"] = path.stem[:8]
    totals["at"] = int(path.stat().st_mtime)
    totals["avg_context"] = (totals["cache_read"] + totals["cache_write"]) // totals["turns"]
    return totals


def _claude_turn(line):
    """Usage off one Claude Code transcript line, or None if the line is not a turn."""
    try:
        record = json.loads(line)
    except ValueError:
        return None
    if record.get("type") != "assistant":
        return None
    return (record.get("message") or {}).get("usage") or {}


def _generic_turn(line):
    """Usage off a line in the documented generic shape — see references/dashboard.md.

    Any agent that can emit one JSON object per turn with a `usage` object using
    Anthropic's field names is readable here without new code. This is the seam
    another tool plugs into.
    """
    try:
        record = json.loads(line)
    except ValueError:
        return None
    use = record.get("usage")
    return use if isinstance(use, dict) else None


# Where each agent keeps its per-session token accounting. Claude Code's
# location is known; anything else is configured, because guessing a path and
# silently reading nothing is worse than reporting that a source is unset.
SOURCES = [
    {"agent": "claude", "dir": lambda root: _project_dir(root),
     "glob": "*.jsonl", "reader": _claude_turn},
    {"agent": "devin", "dir": lambda root: _env_dir("SDD_DEVIN_SESSIONS"),
     "glob": "*.jsonl", "reader": _generic_turn},
]

def _env_dir(name):
    raw = os.environ.get(name)
    if not raw:
        return None
    path = Path(raw).expanduser()
    return path if path.is_dir() else None


def _usage(repo_root, limit_sessions=8):
    """Real token usage per session, across every configured agent.

    Costs zero agent tokens: these files are written by the tools themselves
    whether or not anything reads them. Cache reads are billed at a fraction of
    fresh input, so they stay a separate column rather than being summed into
    one misleading total.
    """
    sessions = []
    for source in SOURCES:
        directory = source["dir"](repo_root)
        if directory is None:
            continue
        paths = sorted(directory.glob(source["glob"]),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        for path in paths[:limit_sessions]:
            totals = _tally(path, source["reader"])
            if totals is None:
                continue
            totals["agent"] = source["agent"]
            sessions.append(totals)
    sessions.sort(key=lambda s: s["at"], reverse=True)
    return sessions[:limit_sessions]


def _sources_status():
    """Which usage sources are wired up, so an empty panel is explainable."""
    out = []
    for source in SOURCES:
        directory = source["dir"](Path.cwd())
        out.append({"agent": source["agent"], "configured": directory is not None,
                    "error": None})
    return out


def _project_dir(repo_root):
    """Claude Code's transcript directory for this repo, or None if not found."""
    encoded = str(repo_root).replace("/", "-")
    candidate = Path.home() / ".claude" / "projects" / encoded
    return candidate if candidate.is_dir() else None


def collect_one(repo_root):
    repo_root = Path(repo_root).resolve()
    features_dir = repo_root / ".specs" / "features"
    features = []
    if features_dir.is_dir():
        for entry in sorted(p for p in features_dir.iterdir() if p.is_dir()):
            features.append(_feature_state(entry))
    adrs = []
    adr_dir = repo_root / ".adrs"
    if adr_dir.is_dir():
        for path in sorted(adr_dir.glob("*.md")):
            read = _read_artifact(path)
            if read is None:
                continue
            adrs.append({"file": path.name, "id": read[1].get("id"),
                         "status": read[1].get("status")})
    return {"repo": repo_root.name, "path": str(repo_root),
            "features": features, "adrs": adrs,
            "events": _events(repo_root),
            "last_change": _last_change(repo_root),
            "usage": _usage(repo_root),
            "sources": _sources_status()}


def collect(repo_roots):
    """One payload covering every watched repo.

    Working on several features across several projects at once is the normal
    case, not the exception, so the dashboard is multi-repo by construction
    rather than something you run N copies of.
    """
    if isinstance(repo_roots, (str, Path)):
        repo_roots = [repo_roots]
    projects = [collect_one(r) for r in repo_roots]
    names = _load_names()
    for project in projects:
        for session in project["usage"]:
            session["label"] = names.get(session["session"], "")
    return {"projects": projects, "generated_at": int(time.time())}


class Handler(BaseHTTPRequestHandler):
    repo_roots = [Path(".")]
    lang = "en"

    def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler's interface
        """Rename a session. Labels are local to this machine and never touch a repo."""
        if not self.path.startswith("/rename"):
            self._send(404, "text/plain", b"not found")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
            session = str(body.get("session", ""))[:64]
            if not session:
                raise ValueError("no session given")
            _save_name(session, str(body.get("label", "")))
        except (ValueError, OSError) as exc:
            self._send(400, "application/json",
                       json.dumps({"error": str(exc)}).encode("utf-8"))
            return
        self._send(200, "application/json", b'{"ok":true}')

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler's interface
        if self.path.startswith("/status.json"):
            state = collect(self.repo_roots)
            state["lang"] = self.lang
            payload = json.dumps(state).encode("utf-8")
            self._send(200, "application/json", payload)
        elif self.path in ("/", "/index.html", "/dashboard.html"):
            if not DASHBOARD.exists():
                self._send(500, "text/plain", b"dashboard.html is missing")
                return
            self._send(200, "text/html; charset=utf-8", DASHBOARD.read_bytes())
        else:
            self._send(404, "text/plain", b"not found")

    def _send(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # a poll every second would drown the terminal it was started from


def _print_context(repo_root):
    """What the current session's context costs, and what dropping it would save.

    The agent has no way to read its own context size, so this reads the live
    transcript instead and turns it into the number a /clear offer should carry.
    A recommendation with an estimate attached is actionable; one without is
    noise the human learns to skip.
    """
    sessions = _usage(Path(repo_root).resolve(), limit_sessions=1)
    if not sessions:
        print("no transcript for this project yet - nothing to estimate")
        return 0
    current = sessions[0]
    context = current["avg_context"]
    turns = current["turns"]
    last = context
    # A rebuild after /clear: the gated artifact, its authoring reference, and
    # its template. Measured against this skill's own artifacts.
    rebuild = 6000
    print("session %s - %d turns, context now ~%s tokens/turn"
          % (current["session"], turns, f"{last:,}"))
    print()
    for horizon in (50, 100, 200):
        saved = max(0, last - rebuild) * horizon
        print("  over the next %3d turns, a /clear here saves ~%s tokens"
              % (horizon, f"{saved:,}"))
    print()
    print("  (rebuild after the reset costs ~%s: the gated artifact, its" % f"{rebuild:,}")
    print("   authoring reference, and its template. Everything else is on disk.)")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="SDD progress dashboard")
    parser.add_argument("--repo-root", action="append", default=None,
                        help="repeatable; watch several projects at once")
    parser.add_argument("--lang", choices=("en", "pt-BR"), default="en",
                        help="dashboard language; the page also has a toggle")
    parser.add_argument("--context", action="store_true",
                        help="print this project's current context size and what a reset saves")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--port", type=int, default=4517)
    args = parser.parse_args(argv)
    roots = args.repo_root or ["."]

    if args.context:
        return _print_context(roots[0])

    if args.as_json or not args.serve:
        print(json.dumps(collect(roots), indent=2))
        return 0

    Handler.repo_roots = [Path(r).resolve() for r in roots]
    Handler.lang = args.lang
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print("SDD dashboard: http://127.0.0.1:%d  (ctrl-c to stop)" % args.port)
    for root in Handler.repo_roots:
        print("  watching %s" % root)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
