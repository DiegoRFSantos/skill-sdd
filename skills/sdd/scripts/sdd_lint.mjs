#!/usr/bin/env node
// SDD Tier 1 deterministic linter (Node port). Rules come from rules.json; this file only executes them.
import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, basename, resolve } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const RULES = JSON.parse(readFileSync(join(HERE, "rules.json"), "utf8"));
const NOT_APPLICABLE = /^\s*_Not applicable:.+_\s*$/;
const TASK_LINE = /^- \[( |x|\/|!)\] \*\*(Task [\w.]+)\*\*(.*)$/;
const AGENT_TAG = /\[Agent:\s*[^\]]+\]/;
const CRITICALITY_TAG = /\[(REQUIRED|OPTIONAL)\]/;
const FILES_TAG = /\[files:\s*([^\]]+)\]/;
const DEPENDS_TAG = /\[depends_on:\s*([^\]]+)\]/;

function scalar(value) {
  let v = value.split(" #")[0].trim();
  if (v.length >= 2 && v[0] === v[v.length - 1] && (v[0] === '"' || v[0] === "'")) {
    v = v.slice(1, -1);
  }
  return v;
}

function parseFrontmatter(text) {
  const lines = text.split("\n");
  if (lines.length === 0 || lines[0].trim() !== "---") return null;
  let end = -1;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === "---") { end = i; break; }
  }
  if (end === -1) return null;

  const data = {};
  let currentListKey = null;
  for (const raw of lines.slice(1, end)) {
    if (!raw.trim() || raw.trimStart().startsWith("#")) continue;
    const stripped = raw.trim();
    if (stripped.startsWith("- ")) {
      const item = stripped.slice(2).trim();
      if (currentListKey === null) continue;
      const idx = item.indexOf(":");
      if (idx !== -1) {
        data[currentListKey].push({ [item.slice(0, idx).trim()]: scalar(item.slice(idx + 1)) });
      } else {
        data[currentListKey].push(scalar(item));
      }
      continue;
    }
    const idx = stripped.indexOf(":");
    if (idx === -1) continue;
    const key = stripped.slice(0, idx).trim();
    const value = stripped.slice(idx + 1).trim();
    const valueNoComment = value.startsWith("#") ? "" : value.split(" #")[0].trim();
    if (valueNoComment === "") { data[key] = []; currentListKey = key; }
    else { data[key] = scalar(value); currentListKey = null; }
  }
  return data;
}

const finding = (file, ruleId, message, line = 1, severity = "blocker") =>
  ({ file, rule_id: ruleId, severity, line, message });

// Rows of the first pipe table under an exact-text heading line.
// Returns [{cells: [...], line: N}, ...] (1-based line number of that data
// row). Skips the header row and the `---` separator row. Stops at the first
// blank line, non-`|`-prefixed line, or the next heading after the table
// starts.
function parseMdTable(text, heading) {
  const lines = text.split("\n");
  let start = null;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === heading) { start = i; break; }
  }
  if (start === null) return [];
  // find header row (first "|"-prefixed line after heading), then separator,
  // then data rows
  let i = start + 1;
  while (i < lines.length && !lines[i].trim().startsWith("|")) {
    if (lines[i].trim().startsWith("#")) return []; // hit next heading before any table
    i++;
  }
  if (i >= lines.length) return [];
  i++; // skip header row
  if (i < lines.length && lines[i].trim().startsWith("|")) i++; // skip separator row
  const rows = [];
  while (i < lines.length && lines[i].trim().startsWith("|")) {
    const raw = lines[i].trim();
    const inner = raw.replace(/^\|+/, "").replace(/\|+$/, "");
    const cells = inner.split("|").map((c) => c.trim());
    rows.push({ cells, line: i + 1 });
    i++;
  }
  return rows;
}

function walkMarkdown(root) {
  const out = [];
  const stack = [root];
  while (stack.length) {
    const dir = stack.pop();
    let entries;
    try { entries = readdirSync(dir); } catch { continue; }
    for (const entry of entries) {
      const full = join(dir, entry);
      let st;
      try { st = statSync(full); } catch { continue; }
      if (st.isDirectory()) stack.push(full);
      else if (entry.endsWith(".md")) out.push(full);
    }
  }
  return out.sort();
}

function findArtifactText(repoRoot, wantedId, targetType) {
  for (const candidate of walkMarkdown(repoRoot)) {
    let text;
    try { text = readFileSync(candidate, "utf8"); } catch { continue; }
    const fm = parseFrontmatter(text);
    if (fm && fm.id === wantedId && fm.type === targetType) return text;
  }
  return null;
}

function idExists(repoRoot, wantedId, targetType) {
  return findArtifactText(repoRoot, wantedId, targetType) !== null;
}

function parseTasks(text) {
  const parsed = [];
  text.split("\n").forEach((line, i) => {
    const m = TASK_LINE.exec(line);
    if (!m) return;
    const rest = m[3];
    const depsMatch = DEPENDS_TAG.exec(rest);
    let deps = [];
    if (depsMatch) {
      const raw = depsMatch[1].trim();
      if (raw.toLowerCase() !== "none") deps = raw.split(",").map((d) => d.trim()).filter(Boolean);
    }
    parsed.push({ id: m[2], state: m[1], deps, line: i + 1, rest });
  });
  return parsed;
}

// A spec declares its ids either as a `### BR-01` heading or, since the
// table-first templates, as the first cell of a table row: `| BR-01 | ... |`.
// Both forms are authoritative; a catalog referencing an id must find it either
// way, or a table-first spec looks to the linter like it declares nothing.
const SPEC_ID_HEADING = /^### ((?:BR|AC|EC)-\d+)/gm;
const SPEC_ID_ROW = /^\|\s*((?:BR|AC|EC)-\d+)\s*\|/gm;

function specIds(specText) {
  return new Set([
    ...[...specText.matchAll(SPEC_ID_HEADING)].map((m) => m[1]),
    ...[...specText.matchAll(SPEC_ID_ROW)].map((m) => m[1]),
  ]);
}

const GLANCE_HEADING = "## 0. At a Glance";
const GLANCE_MAX_LINES = 15;

// Content lines of the At a Glance section: blanks and HTML comments don't count.
function glanceBody(text) {
  const lines = text.split("\n");
  const start = lines.findIndex((l) => l.trim() === GLANCE_HEADING);
  if (start === -1) return null;
  const body = [];
  let inComment = false;
  for (const line of lines.slice(start + 1)) {
    if (line.startsWith("## ")) break;
    if (inComment) {
      if (line.includes("-->")) inComment = false;
      continue;
    }
    if (line.includes("<!--")) { inComment = !line.includes("-->"); continue; }
    if (line.trim()) body.push(line);
  }
  return body;
}

const NAMED_CHECKS = {
  tasks_tags(name, text, fm, out, repoRoot) {
    for (const task of parseTasks(text)) {
      if (!AGENT_TAG.test(task.rest))
        out.push(finding(name, "TASKS_MISSING_AGENT", `${task.id} is missing an [Agent: ...] tag`, task.line));
      if (!CRITICALITY_TAG.test(task.rest))
        out.push(finding(name, "TASKS_MISSING_CRITICALITY", `${task.id} is missing a [REQUIRED] or [OPTIONAL] tag`, task.line));
      const filesTag = FILES_TAG.exec(task.rest);
      if (filesTag === null)
        out.push(finding(name, "TASKS_MISSING_FILES",
          `${task.id} is missing a [files: ...] tag; a fresh subagent cannot infer which paths it may touch`, task.line));
      else if (!filesTag[1].trim())
        out.push(finding(name, "TASKS_EMPTY_FILES", `${task.id} has an empty [files: ...] tag`, task.line));
    }
  },
  tasks_progress(name, text, fm, out, repoRoot) {
    const tasks = parseTasks(text);
    const done = tasks.filter((t) => t.state === "x").length;
    const declared = String(fm.progress ?? "");
    if (!/^\d+\/\d+$/.test(declared)) return;
    const [dDone, dTotal] = declared.split("/").map(Number);
    if (dDone !== done || dTotal !== tasks.length)
      out.push(finding(name, "TASKS_PROGRESS_MISMATCH",
        `progress says ${declared} but the checklist has ${done} completed of ${tasks.length} tasks`));
  },
  tasks_depends_on(name, text, fm, out, repoRoot) {
    const tasks = parseTasks(text);
    const known = new Set(tasks.map((t) => t.id));
    for (const task of tasks)
      for (const dep of task.deps)
        if (!known.has(dep))
          out.push(finding(name, "TASKS_UNKNOWN_DEP", `${task.id} depends_on '${dep}' which does not exist`, task.line));
  },
  tasks_cycles(name, text, fm, out, repoRoot) {
    const graph = new Map(parseTasks(text).map((t) => [t.id, t.deps]));
    const state = new Map();
    const visit = (node, trail) => {
      if (state.get(node) === "done") return null;
      if (state.get(node) === "open") return trail.slice(trail.indexOf(node)).concat(node);
      state.set(node, "open");
      for (const dep of graph.get(node) ?? []) {
        if (!graph.has(dep)) continue;
        const cycle = visit(dep, trail.concat(node));
        if (cycle) return cycle;
      }
      state.set(node, "done");
      return null;
    };
    for (const node of [...graph.keys()].sort()) {
      const cycle = visit(node, []);
      if (cycle) {
        out.push(finding(name, "TASKS_CYCLE", `dependency cycle detected: ${cycle.join(" -> ")}`));
        return;
      }
    }
  },
  discovery_ledger_empty_when_resolved(name, text, fm, out, repoRoot) {
    if (fm.status !== "resolved") return;
    for (const row of parseMdTable(text, "## 5. Open-Question Ledger")) {
      const cells = row.cells;
      if (cells.length > 2 && cells[2] === "open") {
        const rowId = cells[0];
        out.push(finding(name, "DISC_LEDGER_OPEN",
          `open-question ledger row ${rowId} is still 'open' while discovery status is 'resolved'`, row.line));
      }
    }
  },
  catalog_non_empty(name, text, fm, out, repoRoot) {
    const rows = parseMdTable(text, "## 2. Test Cases");
    if (rows.length === 0)
      out.push(finding(name, "CATALOG_EMPTY", "test catalog has no test cases in section 2"));
  },
  catalog_ids_resolve(name, text, fm, out, repoRoot) {
    const specRef = fm.spec_ref;
    if (!specRef) return;
    const specText = findArtifactText(repoRoot, specRef, "spec");
    if (specText === null) return;
    const validIds = specIds(specText);
    for (const row of parseMdTable(text, "## 2. Test Cases")) {
      const cells = row.cells;
      if (cells.length < 2) continue;
      const covers = cells[1].split(",").map((c) => c.trim()).filter(Boolean);
      for (const specId of covers) {
        if (!validIds.has(specId))
          out.push(finding(name, "CATALOG_UNKNOWN_ID",
            `test case covers spec id '${specId}' which does not exist in ${specRef}`, row.line));
      }
    }
  },
  // Nudge (severity=review, non-blocking): AC/EC ids with no TC row and no Deliberate Gaps entry.
  catalog_coverage_prompt(name, text, fm, out, repoRoot) {
    const specRef = fm.spec_ref;
    if (!specRef) return;
    const specText = findArtifactText(repoRoot, specRef, "spec");
    if (!specText) return;
    const acEcIds = [...specIds(specText)]
      .filter((id) => id.startsWith("AC-") || id.startsWith("EC-"))
      .sort();
    const covered = new Set();
    for (const row of parseMdTable(text, "## 2. Test Cases")) {
      const cells = row.cells;
      if (cells.length < 2) continue;
      for (const specId of cells[1].split(",").map((c) => c.trim()).filter(Boolean)) covered.add(specId);
    }
    const gapped = new Set();
    for (const row of parseMdTable(text, "## 3. Deliberate Gaps")) {
      const first = (row.cells[0] ?? "").trim();
      if (first) gapped.add(first);
    }
    for (const specId of acEcIds) {
      if (!covered.has(specId) && !gapped.has(specId))
        out.push(finding(name, "CATALOG_COVERAGE_GAP",
          `acceptance/edge-case id '${specId}' has no test case in section 2 and is not listed in section 3 Deliberate Gaps`,
          1, "review"));
    }
  },
  // coverage_threshold must be 'none' or a complete {line, branch, scope} block.
  // Due to the minimal YAML parser's flat-list handling, a `coverage_threshold:`
  // block header (no inline value) parses fm.coverage_threshold as [] and
  // promotes `line`, `branch`, `scope` to top-level frontmatter keys.
  plan_coverage_threshold_declared(name, text, fm, out, repoRoot) {
    const message = "coverage_threshold must be declared as either 'none' or a complete {line, branch, scope} block";
    const value = fm.coverage_threshold;
    if (value === "none") return;
    if (Array.isArray(value) && value.length === 0) {
      if (["line", "branch", "scope"].every((key) => fm[key])) return;
      out.push(finding(name, "PLAN_COVERAGE_UNDECLARED", message));
      return;
    }
    out.push(finding(name, "PLAN_COVERAGE_UNDECLARED", message));
  },
  glance_length(name, text, fm, out) {
    const body = glanceBody(text);
    if (body === null) return;
    if (body.length > GLANCE_MAX_LINES)
      out.push(finding(name, "GLANCE_TOO_LONG",
        `'${GLANCE_HEADING}' is ${body.length} content lines; the cap is ${GLANCE_MAX_LINES}`));
    else if (body.length === 0)
      out.push(finding(name, "GLANCE_EMPTY", `'${GLANCE_HEADING}' has no content`));
  },

  adr_supersede_symmetry(name, text, fm, out, repoRoot) {
    const selfId = fm.id;

    const supersedes = fm.supersedes;
    if (supersedes && supersedes !== "null") {
      const targetText = findArtifactText(repoRoot, supersedes, "adr");
      if (targetText !== null) {
        const targetFm = parseFrontmatter(targetText) ?? {};
        const actual = targetFm.superseded_by;
        if (actual !== selfId)
          out.push(finding(name, "ADR_SUPERSEDE_ASYMMETRIC",
            `this ADR supersedes ${supersedes}, but ${supersedes}'s superseded_by does not point back (found '${actual}')`));
      }
    }

    const supersededBy = fm.superseded_by;
    if (supersededBy && supersededBy !== "null") {
      const targetText = findArtifactText(repoRoot, supersededBy, "adr");
      if (targetText !== null) {
        const targetFm = parseFrontmatter(targetText) ?? {};
        const actual = targetFm.supersedes;
        if (actual !== selfId)
          out.push(finding(name, "ADR_SUPERSEDE_ASYMMETRIC",
            `this ADR is marked superseded_by ${supersededBy}, but ${supersededBy}'s supersedes does not point back (found '${actual}')`));
      }
    }
  },
};

function lintFile(path, repoRoot) {
  const name = basename(path);
  const text = readFileSync(path, "utf8");
  const out = [];
  const fm = parseFrontmatter(text);
  if (fm === null) { out.push(finding(name, "FM_ABSENT", "file has no YAML frontmatter block")); return out; }
  const spec = RULES.artifacts[fm.type];
  if (!spec) { out.push(finding(name, "FM_UNKNOWN_TYPE", `unknown artifact type: ${fm.type}`)); return out; }

  for (const key of spec.frontmatter.required) {
    const v = fm[key];
    if (v === undefined || v === "" || (Array.isArray(v) && v.length === 0))
      out.push(finding(name, "FM_MISSING_KEY", `frontmatter missing required key: ${key}`));
  }
  for (const key of Object.keys(spec.frontmatter.enums).sort()) {
    const v = fm[key];
    if (v !== undefined && !spec.frontmatter.enums[key].includes(v))
      out.push(finding(name, "FM_BAD_ENUM",
        `frontmatter key '${key}' has value '${v}'; allowed: ${spec.frontmatter.enums[key].join(", ")}`));
  }
  for (const key of Object.keys(spec.frontmatter.patterns).sort()) {
    const v = fm[key];
    const pattern = spec.frontmatter.patterns[key];
    if (typeof v === "string" && v && !new RegExp(pattern).test(v))
      out.push(finding(name, "FM_BAD_PATTERN",
        `frontmatter key '${key}' value '${v}' does not match ${pattern}`));
  }
  for (const key of Object.keys(spec.frontmatter.refs ?? {}).sort()) {
    const target = spec.frontmatter.refs[key];
    const value = fm[key];
    if (!value) continue;
    for (let wanted of Array.isArray(value) ? value : [value]) {
      if (wanted && typeof wanted === "object") wanted = Object.values(wanted)[0] ?? "";
      if (typeof wanted !== "string" || !wanted || wanted === "null") continue;
      if (!idExists(repoRoot, wanted, target))
        out.push(finding(name, "REF_UNRESOLVED",
          `${key} '${wanted}' does not resolve to an existing ${target} artifact`));
    }
  }
  for (const heading of spec.sections)
    if (!text.includes(heading))
      out.push(finding(name, "SECTION_MISSING", `missing required section: ${heading}`));

  // Forbidden per-artifact patterns plus the global placeholder patterns.
  // Fenced code blocks are skipped (a design.md legitimately quotes SQL and
  // routes), and so are HTML comment blocks: illustrative syntax explained to
  // a future reader (e.g. `<!-- - [ ] **Task <id>** ... -->`) is
  // documentation, not artifact prose, the same way fenced code isn't.
  const patterns = (spec.forbidden ?? []).concat(RULES.placeholder_patterns);
  let inFence = false;
  let inComment = false;
  text.split("\n").forEach((line, i) => {
    if (line.trimStart().startsWith("```")) { inFence = !inFence; return; }
    if (inComment) {
      if (line.includes("-->")) inComment = false;
      return;
    }
    if (line.includes("<!--")) {
      inComment = true;
      if (line.includes("-->")) inComment = false;
      return;
    }
    if (inFence || NOT_APPLICABLE.test(line)) return;
    for (const rule of patterns)
      if (new RegExp(rule.regex).test(line))
        out.push(finding(name, rule.id, rule.message, i + 1));
  });

  // Non-blocking: an artifact over its budget is allowed, but visibly so. A
  // genuinely large feature may need the room; what is not allowed is drifting
  // past the budget without anyone noticing.
  if (spec.max_lines) {
    const count = text.replace(/\n+$/, "").split("\n").length;
    if (count > spec.max_lines)
      out.push(finding(name, "LINE_BUDGET",
        `${count} lines against a budget of ${spec.max_lines}; trim, or say why it needs the room`,
        1, "review"));
  }

  for (const checkName of spec.checks ?? []) NAMED_CHECKS[checkName]?.(name, text, fm, out, repoRoot);
  return out;
}

function main(argv) {
  const asJson = argv.includes("--json");
  const rootIdx = argv.indexOf("--repo-root");
  const rootValue = rootIdx === -1 ? null : argv[rootIdx + 1];
  const repoRoot = resolve(rootValue ?? ".");
  const targets = argv.filter((a) => !a.startsWith("--") && a !== rootValue);

  let findings = [];
  for (const p of targets) {
    if (!existsSync(p)) { findings.push(finding(basename(p), "FILE_MISSING", "file does not exist")); continue; }
    findings = findings.concat(lintFile(p, repoRoot));
  }
  findings.sort((a, b) =>
    (a.file < b.file ? -1 : a.file > b.file ? 1 : 0) ||
    (a.rule_id < b.rule_id ? -1 : a.rule_id > b.rule_id ? 1 : 0) ||
    a.line - b.line);

  if (asJson) {
    console.log(JSON.stringify(findings));
  } else {
    printHuman(findings);
  }
  return findings.some((f) => f.severity === "blocker") ? 1 : 0;
}

function printHuman(findings) {
  if (findings.length === 0) { console.log("Tier 1: clean"); return; }
  let current = null;
  for (const f of findings) {
    if (f.file !== current) { current = f.file; console.log(`\n${current}`); }
    console.log(`  [${f.severity}] ${f.rule_id}:${f.line} ${f.message}`);
  }
  const blockers = findings.filter((f) => f.severity === "blocker").length;
  console.log(`\n${blockers} blocker(s), ${findings.length - blockers} review item(s)`);
}

process.exit(main(process.argv.slice(2)));
