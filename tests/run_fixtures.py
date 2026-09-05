#!/usr/bin/env python3
"""Run every fixture through both linter runners and assert identical, expected output.

Then assert the shipped templates and the golden worked example lint clean —
they are what the skill tells an agent to copy, so a template that no longer
passes its own linter teaches the wrong shape.
"""
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

    failures.extend(_check_clean(available))
    failures.extend(_check_status())
    failures.extend(_check_extract())

    print("ran %d fixture(s) against runners: %s" % (len(cases), ", ".join(sorted(available))))
    if failures:
        print("\nFAILURES:\n" + "\n".join(failures))
        return 1
    print("all fixtures pass")
    return 0


CLEAN_TARGETS = [
    ("templates", ROOT / "skills/sdd/templates", ROOT / "skills/sdd/templates"),
    ("golden spec", ROOT / "tests/golden/payment-split/.specs/features/payment-split",
     ROOT / "tests/golden/payment-split"),
    ("golden adrs", ROOT / "tests/golden/payment-split/.adrs",
     ROOT / "tests/golden/payment-split"),
]


def _check_clean(available):
    """Templates and the golden example must carry zero blockers, in both runners."""
    problems = []
    for label, directory, repo_root in CLEAN_TARGETS:
        for artifact in sorted(directory.glob("*.md")):
            for name, cmd in available.items():
                proc = subprocess.run(
                    cmd + [str(artifact), "--json", "--repo-root", str(repo_root)],
                    capture_output=True, text=True,
                )
                blockers = [f for f in json.loads(proc.stdout or "[]")
                            if f["severity"] == "blocker"]
                if blockers:
                    problems.append("%s: %s [%s] must lint clean but has %d blocker(s):\n  %s"
                                    % (label, artifact.name, name, len(blockers),
                                       json.dumps(blockers)))
    return problems


def _check_status():
    """sdd_status.py must derive the golden example's real state off disk.

    It shares the linter's parsers, so a change to frontmatter or task-line
    parsing breaks both. This asserts the numbers, not just that it runs.
    """
    script = ROOT / "skills/sdd/scripts/sdd_status.py"
    golden = ROOT / "tests/golden/payment-split"
    if not script.exists():
        return ["sdd_status.py is missing"]
    proc = subprocess.run(
        [sys.executable, str(script), "--json", "--repo-root", str(golden)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return ["sdd_status.py exited %d:\n%s" % (proc.returncode, proc.stderr)]
    try:
        data = json.loads(proc.stdout)
    except ValueError as exc:
        return ["sdd_status.py did not emit valid JSON: %s" % exc]

    problems = []
    if len(data["features"]) != 1:
        problems.append("status: expected 1 feature, got %d" % len(data["features"]))
        return problems
    feature = data["features"][0]
    if len(feature["tasks"]) != 16:
        problems.append("status: expected 16 tasks, got %d" % len(feature["tasks"]))
    if feature["milestone"] != "M1":
        problems.append("status: expected milestone M1, got %r" % feature["milestone"])
    spec = next(p for p in feature["phases"] if p["phase"] == "spec")
    if spec["tier2_verdict"] != "PASS":
        problems.append("status: spec verdict should come off the validation block, got %r"
                        % spec["tier2_verdict"])
    first = feature["tasks"][0]
    if not first["files"]:
        problems.append("status: task files should be parsed from the [files:] tag")
    if not first["description"] or "[" in first["description"]:
        problems.append("status: task description should have its tags stripped, got %r"
                        % first["description"])
    if not data["adrs"]:
        problems.append("status: the golden ADR should be listed")
    return problems


def _check_extract():
    """sdd_extract.py must return a real slice, and fail loudly on a miss.

    A silent empty result is the dangerous failure here: it reads to an agent
    like "that section is empty" rather than "you asked for the wrong thing."
    """
    script = ROOT / "skills/sdd/scripts/sdd_extract.py"
    design = ROOT / "tests/golden/payment-split/.specs/features/payment-split/design.md"
    spec = ROOT / "tests/golden/payment-split/.specs/features/payment-split/spec.md"
    if not script.exists():
        return ["sdd_extract.py is missing"]

    def run(target, *flags):
        return subprocess.run([sys.executable, str(script), str(target)] + list(flags),
                              capture_output=True, text=True)

    problems = []
    whole = len(design.read_text())

    got = run(design, "--section", "3.1")
    if got.returncode != 0:
        problems.append("extract: --section 3.1 failed: %s" % got.stderr.strip())
    elif "3.1 API Contracts" not in got.stdout:
        problems.append("extract: --section 3.1 did not return that section")
    elif len(got.stdout) > whole // 4:
        problems.append("extract: --section 3.1 returned %d of %d chars; it is not slicing"
                        % (len(got.stdout), whole))

    got = run(design, "--section", "3")
    if got.returncode != 0 or got.stdout.count("### ") < 4:
        problems.append("extract: --section 3 must include its subsections")

    got = run(spec, "--ids", "BR-01,EC-02")
    if got.returncode != 0:
        problems.append("extract: --ids failed: %s" % got.stderr.strip())
    else:
        if "BR-01" not in got.stdout or "EC-02" not in got.stdout:
            problems.append("extract: --ids did not return both rows")
        if got.stdout.count("|---") < 2:
            problems.append("extract: --ids must carry each table's header row")
        if "BR-02" in got.stdout:
            problems.append("extract: --ids returned a row that was not asked for")

    got = run(design, "--outline")
    if got.returncode != 0 or "9 File Map" not in got.stdout:
        problems.append("extract: --outline did not list the headings")

    # A miss must fail loudly, never return an empty string with exit 0.
    for flags in (("--section", "99"), ("--ids", "BR-99")):
        got = run(design, *flags)
        if got.returncode == 0:
            problems.append("extract: %s should exit non-zero on a miss" % (flags,))
    return problems


def _has_node():
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(main())
