#!/usr/bin/env python3
"""Run every fixture through both linter runners and assert identical, expected output."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
RUNNERS = {
    "python": [sys.executable, str(ROOT / "skills/sdd/scripts/sdd_lint.py")],
    "node": ["node", str(ROOT / "skills/sdd/scripts/sdd_lint.mjs")],
}


def run(runner_cmd, target):
    proc = subprocess.run(
        runner_cmd + [str(target), "--json", "--repo-root", str(target.parent)],
        capture_output=True, text=True,
    )
    if proc.returncode not in (0, 1):
        raise SystemExit("runner crashed on %s:\n%s" % (target, proc.stderr))
    return json.loads(proc.stdout or "[]")


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    available = {
        name: cmd for name, cmd in RUNNERS.items()
        if Path(cmd[1]).exists() and (name != "node" or _has_node())
    }
    if not available:
        raise SystemExit("no runner available")

    failures = []
    cases = sorted(p for p in FIXTURES.iterdir() if p.is_dir())
    for case in cases:
        if only and only != case.name:
            continue
        expected = json.loads((case / "expected.json").read_text())
        artifacts = sorted(p for p in case.glob("*.md"))
        results = {}
        for name, cmd in available.items():
            found = []
            for artifact in artifacts:
                found.extend(run(cmd, artifact))
            found.sort(key=lambda f: (f["file"], f["rule_id"], f["line"]))
            results[name] = found
            if found != expected:
                failures.append("%s [%s]\n  expected: %s\n  actual:   %s"
                                % (case.name, name, json.dumps(expected), json.dumps(found)))
        values = list(results.values())
        if len(values) > 1 and any(v != values[0] for v in values):
            failures.append("%s: RUNNER DRIFT — python and node disagree" % case.name)

    print("ran %d fixture(s) against runners: %s" % (len(cases), ", ".join(sorted(available))))
    if failures:
        print("\nFAILURES:\n" + "\n".join(failures))
        return 1
    print("all fixtures pass")
    return 0


def _has_node():
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(main())
