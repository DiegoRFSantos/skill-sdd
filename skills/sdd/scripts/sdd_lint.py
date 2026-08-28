#!/usr/bin/env python3
"""SDD Tier 1 deterministic linter. Rules come from rules.json; this file only executes them."""
import argparse
import json
import re
import sys
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent / "rules.json"
NOT_APPLICABLE = re.compile(r"^\s*_Not applicable:.+_\s*$", re.ASCII)


def load_rules():
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def parse_frontmatter(text):
    """Minimal YAML subset: flat scalars, lists of scalars, lists of single-pair mappings.

    Returns (data, body_offset) where body_offset is the 1-based line number the body starts on.
    Returns (None, 1) when no frontmatter block is present.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, 1
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, 1

    data = {}
    current_list_key = None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        stripped = raw.strip()
        if stripped.startswith("- "):
            item = stripped[2:].strip()
            if current_list_key is None:
                continue
            if ":" in item:
                k, v = item.split(":", 1)
                data[current_list_key].append({k.strip(): _scalar(v)})
            else:
                data[current_list_key].append(_scalar(item))
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        value_no_comment = "" if value.startswith("#") else value.split(" #")[0].strip()
        if value_no_comment == "":
            data[key] = []
            current_list_key = key
        else:
            data[key] = _scalar(value)
            current_list_key = None
    return data, end + 2


def _scalar(value):
    value = value.split(" #")[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def finding(file_name, rule_id, message, line=1, severity="blocker"):
    return {"file": file_name, "rule_id": rule_id, "severity": severity,
            "line": line, "message": message}


def parse_md_table(text, heading):
    """Rows of the first pipe table under an exact-text heading line.

    Returns a list of dicts: {"cells": [str, ...], "line": int} (1-based line
    number of that data row). Skips the header row and the `---` separator
    row. Stops at the first blank line, non-`|`-prefixed line, or the next
    heading after the table starts.
    """
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i
            break
    if start is None:
        return []
    # find header row (first "|"-prefixed line after heading), then separator,
    # then data rows
    i = start + 1
    while i < len(lines) and not lines[i].strip().startswith("|"):
        if lines[i].strip().startswith("#"):
            return []  # hit next heading before any table
        i += 1
    if i >= len(lines):
        return []
    i += 1  # skip header row
    if i < len(lines) and lines[i].strip().startswith("|"):
        i += 1  # skip separator row
    rows = []
    while i < len(lines) and lines[i].strip().startswith("|"):
        raw = lines[i].strip()
        cells = [c.strip() for c in raw.strip("|").split("|")]
        rows.append({"cells": cells, "line": i + 1})
        i += 1
    return rows


def check_frontmatter_required(path, fm, spec, findings):
    for key in spec["frontmatter"]["required"]:
        if key not in fm or fm[key] in ("", [], None):
            findings.append(finding(path.name, "FM_MISSING_KEY",
                                    "frontmatter missing required key: %s" % key))


def check_frontmatter_enums(path, fm, spec, findings):
    for key, allowed in sorted(spec["frontmatter"]["enums"].items()):
        value = fm.get(key)
        if value is not None and value not in allowed:
            findings.append(finding(path.name, "FM_BAD_ENUM",
                                    "frontmatter key '%s' has value '%s'; allowed: %s"
                                    % (key, value, ", ".join(allowed))))


def check_frontmatter_patterns(path, fm, spec, findings):
    for key, pattern in sorted(spec["frontmatter"]["patterns"].items()):
        value = fm.get(key)
        if isinstance(value, str) and value and not re.match(pattern, value, re.ASCII):
            findings.append(finding(path.name, "FM_BAD_PATTERN",
                                    "frontmatter key '%s' value '%s' does not match %s"
                                    % (key, value, pattern)))


def check_frontmatter_refs(path, fm, spec, findings, repo_root):
    """Every declared ref must resolve to an existing artifact carrying that id."""
    for key, target_type in sorted(spec["frontmatter"].get("refs", {}).items()):
        value = fm.get(key)
        if not value:
            continue
        values = value if isinstance(value, list) else [value]
        for wanted in values:
            if isinstance(wanted, dict):
                wanted = next(iter(wanted.values()), "")
            if not isinstance(wanted, str) or not wanted or wanted == "null":
                continue
            if not _id_exists(repo_root, wanted, target_type):
                findings.append(finding(path.name, "REF_UNRESOLVED",
                                        "%s '%s' does not resolve to an existing %s artifact"
                                        % (key, wanted, target_type)))


def _find_artifact_text(repo_root, wanted_id, target_type):
    """Walk repo_root for the *.md file whose frontmatter id/type match; return its raw text."""
    for candidate in sorted(repo_root.rglob("*.md")):
        try:
            text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fm, _ = parse_frontmatter(text)
        if fm and fm.get("id") == wanted_id and fm.get("type") == target_type:
            return text
    return None


def _id_exists(repo_root, wanted_id, target_type):
    return _find_artifact_text(repo_root, wanted_id, target_type) is not None


def check_sections(path, text, spec, findings):
    for heading in spec["sections"]:
        if heading not in text:
            findings.append(finding(path.name, "SECTION_MISSING",
                                    "missing required section: %s" % heading))


def check_body_patterns(path, text, spec, rules, findings):
    """Forbidden per-artifact patterns plus the global placeholder patterns.

    Fenced code blocks are skipped: a design.md legitimately quotes SQL and routes.
    HTML comment blocks are also skipped: illustrative syntax explained to a future
    reader (e.g. `<!-- - [ ] **Task <id>** ... -->`) is documentation, not artifact
    prose, the same way fenced code isn't.
    """
    patterns = list(spec.get("forbidden", [])) + list(rules["placeholder_patterns"])
    in_fence = False
    in_comment = False
    for index, line in enumerate(text.split("\n"), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if "<!--" in line:
            in_comment = True
            if "-->" in line:
                in_comment = False
            continue
        if in_fence or NOT_APPLICABLE.search(line):
            continue
        for rule in patterns:
            if re.search(rule["regex"], line, re.ASCII):
                findings.append(finding(path.name, rule["id"], rule["message"], line=index))


CHECKS = [check_frontmatter_required, check_frontmatter_enums, check_frontmatter_patterns]
ROOT_AWARE_CHECKS = [check_frontmatter_refs]

TASK_LINE = re.compile(r"^- \[( |x|/|!)\] \*\*(Task [\w.]+)\*\*(.*)$", re.ASCII)
AGENT_TAG = re.compile(r"\[Agent:\s*[^\]]+\]", re.ASCII)
CRITICALITY_TAG = re.compile(r"\[(REQUIRED|OPTIONAL)\]", re.ASCII)
DEPENDS_TAG = re.compile(r"\[depends_on:\s*([^\]]+)\]", re.ASCII)


def _parse_tasks(text):
    """Returns a list of dicts: id, state, deps, line."""
    parsed = []
    for index, line in enumerate(text.split("\n"), start=1):
        match = TASK_LINE.match(line)
        if not match:
            continue
        state, task_id, rest = match.group(1), match.group(2), match.group(3)
        deps_match = DEPENDS_TAG.search(rest)
        deps = []
        if deps_match:
            raw = deps_match.group(1).strip()
            if raw.lower() != "none":
                deps = [d.strip() for d in raw.split(",") if d.strip()]
        parsed.append({"id": task_id, "state": state, "deps": deps,
                       "line": index, "rest": rest})
    return parsed


def check_tasks_tags(path, text, fm, findings, repo_root):
    for task in _parse_tasks(text):
        if not AGENT_TAG.search(task["rest"]):
            findings.append(finding(path.name, "TASKS_MISSING_AGENT",
                                    "%s is missing an [Agent: ...] tag" % task["id"],
                                    line=task["line"]))
        if not CRITICALITY_TAG.search(task["rest"]):
            findings.append(finding(path.name, "TASKS_MISSING_CRITICALITY",
                                    "%s is missing a [REQUIRED] or [OPTIONAL] tag" % task["id"],
                                    line=task["line"]))


def check_tasks_progress(path, text, fm, findings, repo_root):
    tasks = _parse_tasks(text)
    done = sum(1 for t in tasks if t["state"] == "x")
    declared = fm.get("progress", "")
    if not re.match(r"^\d+/\d+$", str(declared), re.ASCII):
        return
    d_done, d_total = (int(part) for part in declared.split("/"))
    if d_done != done or d_total != len(tasks):
        findings.append(finding(path.name, "TASKS_PROGRESS_MISMATCH",
                                "progress says %s but the checklist has %d completed of %d tasks"
                                % (declared, done, len(tasks))))


def check_tasks_depends_on(path, text, fm, findings, repo_root):
    tasks = _parse_tasks(text)
    known = {t["id"] for t in tasks}
    for task in tasks:
        for dep in task["deps"]:
            if dep not in known:
                findings.append(finding(path.name, "TASKS_UNKNOWN_DEP",
                                        "%s depends_on '%s' which does not exist" % (task["id"], dep),
                                        line=task["line"]))


def check_tasks_cycles(path, text, fm, findings, repo_root):
    graph = {t["id"]: [d for d in t["deps"]] for t in _parse_tasks(text)}
    state = {}

    def visit(node, trail):
        if state.get(node) == "done":
            return None
        if state.get(node) == "open":
            return trail[trail.index(node):] + [node]
        state[node] = "open"
        for dep in graph.get(node, []):
            if dep not in graph:
                continue
            cycle = visit(dep, trail + [node])
            if cycle:
                return cycle
        state[node] = "done"
        return None

    for node in sorted(graph):
        cycle = visit(node, [])
        if cycle:
            findings.append(finding(path.name, "TASKS_CYCLE",
                                    "dependency cycle detected: %s" % " -> ".join(cycle)))
            return


def check_discovery_ledger(path, text, fm, findings, repo_root):
    if fm.get("status") != "resolved":
        return
    for row in parse_md_table(text, "## 5. Open-Question Ledger"):
        cells = row["cells"]
        if len(cells) > 2 and cells[2] == "open":
            row_id = cells[0]
            findings.append(finding(path.name, "DISC_LEDGER_OPEN",
                                    "open-question ledger row %s is still 'open' while discovery status is 'resolved'"
                                    % row_id, line=row["line"]))


SPEC_ID_HEADING = re.compile(r"^### ((?:BR|AC|EC)-\d+)", re.MULTILINE | re.ASCII)


def check_catalog_non_empty(path, text, fm, findings, repo_root):
    rows = parse_md_table(text, "## 2. Test Cases")
    if not rows:
        findings.append(finding(path.name, "CATALOG_EMPTY",
                                "test catalog has no test cases in section 2"))


def check_catalog_ids_resolve(path, text, fm, findings, repo_root):
    spec_ref = fm.get("spec_ref")
    if not spec_ref:
        return
    spec_text = _find_artifact_text(repo_root, spec_ref, "spec")
    if spec_text is None:
        return
    valid_ids = set(SPEC_ID_HEADING.findall(spec_text))
    for row in parse_md_table(text, "## 2. Test Cases"):
        cells = row["cells"]
        if len(cells) < 2:
            continue
        covers = [c.strip() for c in cells[1].split(",") if c.strip()]
        for spec_id in covers:
            if spec_id not in valid_ids:
                findings.append(finding(path.name, "CATALOG_UNKNOWN_ID",
                                        "test case covers spec id '%s' which does not exist in %s"
                                        % (spec_id, spec_ref), line=row["line"]))


def check_catalog_coverage_prompt(path, text, fm, findings, repo_root):
    """Nudge (severity=review, non-blocking): AC/EC ids with no TC row and no Deliberate Gaps entry."""
    spec_ref = fm.get("spec_ref")
    if not spec_ref:
        return
    spec_text = _find_artifact_text(repo_root, spec_ref, "spec")
    if not spec_text:
        return
    ac_ec_ids = sorted(
        set(i for i in SPEC_ID_HEADING.findall(spec_text) if i.startswith("AC-") or i.startswith("EC-"))
    )
    covered = set()
    for row in parse_md_table(text, "## 2. Test Cases"):
        cells = row["cells"]
        if len(cells) < 2:
            continue
        for spec_id in cells[1].split(","):
            spec_id = spec_id.strip()
            if spec_id:
                covered.add(spec_id)
    gapped = set()
    for row in parse_md_table(text, "## 3. Deliberate Gaps"):
        cells = row["cells"]
        if cells and cells[0].strip():
            gapped.add(cells[0].strip())
    for spec_id in ac_ec_ids:
        if spec_id not in covered and spec_id not in gapped:
            findings.append(finding(path.name, "CATALOG_COVERAGE_GAP",
                                    "acceptance/edge-case id '%s' has no test case in section 2 and is not listed in section 3 Deliberate Gaps"
                                    % spec_id, line=1, severity="review"))


def check_adr_supersede_symmetry(path, text, fm, findings, repo_root):
    self_id = fm.get("id")

    supersedes = fm.get("supersedes")
    if supersedes and supersedes != "null":
        target_text = _find_artifact_text(repo_root, supersedes, "adr")
        if target_text is not None:
            target_fm, _ = parse_frontmatter(target_text)
            actual = (target_fm or {}).get("superseded_by")
            if actual != self_id:
                findings.append(finding(path.name, "ADR_SUPERSEDE_ASYMMETRIC",
                                        "this ADR supersedes %s, but %s's superseded_by does not point back (found '%s')"
                                        % (supersedes, supersedes, actual)))

    superseded_by = fm.get("superseded_by")
    if superseded_by and superseded_by != "null":
        target_text = _find_artifact_text(repo_root, superseded_by, "adr")
        if target_text is not None:
            target_fm, _ = parse_frontmatter(target_text)
            actual = (target_fm or {}).get("supersedes")
            if actual != self_id:
                findings.append(finding(path.name, "ADR_SUPERSEDE_ASYMMETRIC",
                                        "this ADR is marked superseded_by %s, but %s's supersedes does not point back (found '%s')"
                                        % (superseded_by, superseded_by, actual)))


def check_plan_coverage_threshold(path, text, fm, findings, repo_root):
    """coverage_threshold must be 'none' or a complete {line, branch, scope} block.

    Due to the minimal YAML parser's flat-list handling, a `coverage_threshold:`
    block header (no inline value) parses fm["coverage_threshold"] as [] and
    promotes `line`, `branch`, `scope` to top-level frontmatter keys.
    """
    message = ("coverage_threshold must be declared as either 'none' or a "
               "complete {line, branch, scope} block")
    value = fm.get("coverage_threshold")
    if value == "none":
        return
    if value == []:
        if all(fm.get(key) for key in ("line", "branch", "scope")):
            return
        findings.append(finding(path.name, "PLAN_COVERAGE_UNDECLARED", message))
        return
    findings.append(finding(path.name, "PLAN_COVERAGE_UNDECLARED", message))


NAMED_CHECKS = {
    "tasks_tags": check_tasks_tags,
    "tasks_progress": check_tasks_progress,
    "tasks_depends_on": check_tasks_depends_on,
    "tasks_cycles": check_tasks_cycles,
    "discovery_ledger_empty_when_resolved": check_discovery_ledger,
    "catalog_non_empty": check_catalog_non_empty,
    "catalog_ids_resolve": check_catalog_ids_resolve,
    "catalog_coverage_prompt": check_catalog_coverage_prompt,
    "adr_supersede_symmetry": check_adr_supersede_symmetry,
    "plan_coverage_threshold_declared": check_plan_coverage_threshold,
}


def lint_file(path, rules, repo_root):
    text = path.read_text(encoding="utf-8")
    findings = []
    fm, _body_offset = parse_frontmatter(text)
    if fm is None:
        findings.append(finding(path.name, "FM_ABSENT", "file has no YAML frontmatter block"))
        return findings
    artifact_type = fm.get("type")
    spec = rules["artifacts"].get(artifact_type)
    if spec is None:
        findings.append(finding(path.name, "FM_UNKNOWN_TYPE",
                                "unknown artifact type: %s" % artifact_type))
        return findings
    for check in CHECKS:
        check(path, fm, spec, findings)
    for check in ROOT_AWARE_CHECKS:
        check(path, fm, spec, findings, repo_root)
    check_sections(path, text, spec, findings)
    check_body_patterns(path, text, spec, rules, findings)
    for name in spec.get("checks", []):
        handler = NAMED_CHECKS.get(name)
        if handler is not None:
            handler(path, text, fm, findings, repo_root)
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description="SDD Tier 1 linter")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)

    rules = load_rules()
    repo_root = Path(args.repo_root).resolve()
    findings = []
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            findings.append(finding(path.name, "FILE_MISSING", "file does not exist"))
            continue
        findings.extend(lint_file(path, rules, repo_root))

    findings.sort(key=lambda f: (f["file"], f["rule_id"], f["line"]))
    if args.as_json:
        print(json.dumps(findings, indent=None, separators=(", ", ": ")))
    else:
        _print_human(findings)
    return 1 if any(f["severity"] == "blocker" for f in findings) else 0


def _print_human(findings):
    if not findings:
        print("Tier 1: clean")
        return
    current = None
    for f in findings:
        if f["file"] != current:
            current = f["file"]
            print("\n%s" % current)
        print("  [%s] %s:%d %s" % (f["severity"], f["rule_id"], f["line"], f["message"]))
    blockers = sum(1 for f in findings if f["severity"] == "blocker")
    print("\n%d blocker(s), %d review item(s)" % (blockers, len(findings) - blockers))


if __name__ == "__main__":
    sys.exit(main())
