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
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sdd_lint import parse_frontmatter, _parse_tasks, AGENT_TAG, FILES_TAG  # noqa: E402

HERE = Path(__file__).resolve().parent
DASHBOARD = HERE / "dashboard.html"

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


def _usage(project_dir, limit_sessions=8):
    """Real token usage, read from the transcripts the harness already writes.

    Costs zero agent tokens: these files exist whether or not anything reads
    them. Cache reads are billed at a fraction of fresh input, so they are
    reported separately rather than summed into one misleading total.
    """
    if project_dir is None or not project_dir.is_dir():
        return None
    sessions = []
    for path in sorted(project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime,
                       reverse=True)[:limit_sessions]:
        totals = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0, "turns": 0}
        try:
            handle = path.open(encoding="utf-8")
        except OSError:
            continue
        with handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if record.get("type") != "assistant":
                    continue
                use = (record.get("message") or {}).get("usage") or {}
                totals["turns"] += 1
                totals["input"] += use.get("input_tokens", 0)
                totals["cache_write"] += use.get("cache_creation_input_tokens", 0)
                totals["cache_read"] += use.get("cache_read_input_tokens", 0)
                totals["output"] += use.get("output_tokens", 0)
        if not totals["turns"]:
            continue
        totals["session"] = path.stem[:8]
        totals["at"] = int(path.stat().st_mtime)
        totals["avg_context"] = (totals["cache_read"] + totals["cache_write"]) // totals["turns"]
        sessions.append(totals)
    return sessions or None


def _project_dir(repo_root):
    """Claude Code's transcript directory for this repo, or None if not found."""
    encoded = str(repo_root).replace("/", "-")
    candidate = Path.home() / ".claude" / "projects" / encoded
    return candidate if candidate.is_dir() else None


def collect(repo_root):
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
    return {"repo": repo_root.name, "features": features, "adrs": adrs,
            "events": _events(repo_root),
            "last_change": _last_change(repo_root),
            "usage": _usage(_project_dir(repo_root))}


class Handler(BaseHTTPRequestHandler):
    repo_root = Path(".")

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler's interface
        if self.path.startswith("/status.json"):
            payload = json.dumps(collect(self.repo_root)).encode("utf-8")
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="SDD progress dashboard")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--port", type=int, default=4517)
    args = parser.parse_args(argv)

    if args.as_json or not args.serve:
        print(json.dumps(collect(args.repo_root), indent=2))
        return 0

    Handler.repo_root = Path(args.repo_root).resolve()
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print("SDD dashboard: http://127.0.0.1:%d  (ctrl-c to stop)" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
