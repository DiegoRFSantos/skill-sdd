# SDD skill — speed, brevity, and handoff

**Date:** 2026-09-05
**Status:** approved for implementation (items 1–5 build; item 6 deferred)

## Problem

Real usage over several days surfaced four defects and one gap:

1. The Tier 2 gate dominates wall-clock time. Judges inherit Opus (no model is
   named anywhere in `references/quality-gate.md`), the prompt demands prose
   justification for all 7 criteria including ones scoring full marks, and the
   triage loop is explicitly uncapped ("looping is cheap") — true for cost,
   false for latency. Nothing forbids parallel consensus judges, so several can
   be in flight at once and the slowest sets the pace.
2. The skill talks too much, and the extra words do not carry extra meaning.
   No file in the skill states what the agent should *say*, only what it should
   think.
3. Artifacts run 300–500 lines for small features. The templates are the cause:
   `templates/design.md` is 399 lines with a full worked example inline, and
   business rules are `###` blocks with three prose paragraphs each. The model
   reproduces the shape it is given.
4. Implementation starts in the same session that authored the plan, carrying a
   context window full of discovery transcript it no longer needs.
5. There is no way to watch a run in progress without reading chat output.

## Goals

- Cut gate wall-clock without lowering the bar for what ships.
- Make every agent-to-human message shorter than the thing it describes.
- Make an artifact reviewable in ~15 lines, with the full detail still present.
- Start implementation on a clean context window.
- Make the technical artifacts safe for a small model to execute without guessing.

## Non-goals

- Lowering the 90/100 pass bar, or changing what the rubrics measure.
- Removing Tier 2 from any artifact that has a rubric today.
- ~~Building the progress dashboard in this pass~~ — built in a follow-up pass, see §6.

---

## 1. Shift-left: requirements move to authoring, the judge verifies

This is the change that makes everything else in §2 affordable. Today, rules
like "every business rule names a checkable condition," "no implementation
leakage," and "edge cases must be boundary/failure/concurrency, not restated
happy path" exist **only** in the Tier 2 rubric. The agent writes the artifact
without them, the judge discovers the violation, and a round is spent fixing
what should never have been written. A 1-round cap is only realistic once the
artifact is born passing.

Every rubric criterion gets restated as an **authoring rule** in the reference
that governs writing that artifact:

| Rubric criterion lives in | Authoring rule added to |
|---|---|
| spec.md rubric (7 criteria) | `references/artifact-spec.md`, `references/elicitation.md` |
| design.md rubric (7 criteria) | `references/artifact-design.md` |
| adr.md rubric (5 criteria) | `references/artifact-adr.md` |
| plan+tasks rubric (6 criteria) | `references/artifact-plan-tasks.md` |

Each authoring reference gains a short **"Written to pass"** section listing the
criteria as imperatives the author applies while writing, not as a rubric to be
graded against afterwards.

**Naming fix.** The word *falsifiable* currently means two different things in
this skill. `references/discovery.md`'s falsification test challenges the
*user's premise* — trying to prove the idea wrong before anything is written —
and that stays exclusively in discovery. The spec rubric's "business rules are
falsifiable" means something else entirely: whether a written rule names a
condition that can be mechanically checked. That criterion is renamed to
**"Business rules name a checkable condition"** so the two stop colliding. The
judge never challenges the premise; it assesses the artifact only.

## 2. The judge lane

### 2.1 Two configurable choices, asked once

Both are the human's call, consistent with the Human Decision Supremacy
invariant. Resolved from `.specs/sdd.config.yml` first; if absent, asked once
and offered for persistence:

```yaml
# .specs/sdd.config.yml
judge_model: sonnet     # any model the Agent tool accepts
judge_depth: fast       # fast | full
```

The ask is one message with both questions, not two round-trips.

### 2.2 `fast` (default) vs `full`

Both lanes use **the same rubric, the same criteria, the same weights, and the
same 90/100 pass bar.** They differ only in output verbosity and round cap.

| | `fast` | `full` |
|---|---|---|
| Rubric | all criteria | all criteria |
| Pass bar | ≥90/100 | ≥90/100 |
| Output for a criterion at full marks | score only | score + justification prose |
| Output for a criterion below max | score + specific deficiency + specific fix | same |
| Round cap | **1** — then the punch list goes to the human | uncapped, as today |
| Model | `judge_model` | `judge_model` |

In `fast`, a FAIL after the single re-judge is not a loop; it is a decision
point. The agent presents the remaining deficiencies and the human picks: fix
and re-dispatch, or accept the named gap as documented risk (recorded exactly
as `references/discovery.md` §6 records Accepted Risks). This bounds the
worst case at two dispatches per artifact instead of unbounded.

### 2.3 The terse output contract

Replaces the current free-form judge output. The judge returns:

```
CRITERION_NAME: 18/20
CRITERION_NAME: 20/20
CRITERION_NAME: 6/15
  deficiency: EC-04 restates the happy path — "the organizer submits a valid split"
  fix: replace with a concurrent-submission boundary: two organizers submit at once
TOTAL: 88/100
VERDICT: FAIL
```

No prose for criteria at full marks. No preamble, no summary paragraph, no
restating the artifact. Since latency tracks output tokens, this is the single
largest speed lever available.

### 2.4 Anti-length instruction in the judge prompt

Added to the prompt template verbatim:

> Length is not evidence of quality. Never recommend expanding, elaborating, or
> adding narrative. A one-line table row that names the required fact scores
> full marks; three paragraphs that never name it score zero. Deduct for a
> missing fact, never for a missing paragraph.

Paired with a rubric-wording retune: same 7/7/5/6 criteria and same weights,
reworded to score *facts present* rather than implying prose volume.

### 2.5 One judge per round — hard rule

Added to `references/quality-gate.md`:

> Exactly one judge subagent is dispatched per artifact per round. Never
> dispatch parallel judges for consensus, never dispatch a second judge to
> break a tie, and never dispatch judges for two artifacts concurrently — the
> pipeline is sequential by construction (design needs an active spec), so
> concurrency buys nothing and multiplies the tail latency.

## 3. The communication contract

A new top-level section in `SKILL.md`, and the shortest one in the file.

- **State report:** one line. `payment-split: spec active (94 PASS), design draft`
- **Gate result, PASS:** one line. `spec.md — Tier 1 pass, Tier 2 94 PASS (1 round)`
- **Gate result, FAIL:** the one line, then the deficiencies as bullets. Nothing else.
- **Never restate an artifact you just wrote.** The At a Glance section (§4) is
  the summary; point at the file.
- **Never narrate the process.** No "now I'll move to the design phase," no
  explaining what SDD is, no announcing which reference file is being read.
- **Questions:** ask in one batch where they are independent, numbered, no
  preamble, no restating the question in prose before asking it.
- **Never explain a rule of this skill unless asked.** Applying it is enough.

## 4. Artifact slimming

### 4.1 Templates become skeletons

The payment-split worked examples move out of `templates/*.md` into
`references/examples/payment-split/`. Templates keep the headings, the table
columns, and a one-line comment per section saying what belongs there. The
authoring reference points to the example for an agent that needs to see a
filled-in one. Expected: `templates/design.md` 399 → ~120 lines,
`templates/spec.md` 282 → ~90.

**Deviation from this design, taken during implementation:** the golden fixture
under `tests/golden/payment-split/` was *not* left as it was, and no separate
`references/examples/` directory was created. The golden artifacts were the same
content as the templates' inline examples, so a separate examples directory
would have been a third copy of the same document guaranteed to rot. Instead the
golden artifacts were regenerated from the new slim templates and the authoring
references cite them as the worked example. They ship with the plugin
(`marketplace.json` sources the whole repo) and the test runner now asserts they
lint clean, so the example cannot go stale without a test failing.

### 4.2 Tables instead of prose blocks

Business rules, edge cases, and acceptance criteria become one table row each:

```
| Id | Rule | Invariant (checkable) | Why |
|---|---|---|---|
| BR-01 | Total allocation must not exceed 100% | sum(allocations) <= 100, checked before accept | a payment can only be covered once |
```

Prose is permitted where a rule genuinely needs it, and only there. This is the
change §2.4 exists to protect.

### 4.3 `## 0. At a Glance` becomes a real section

The 15-line summary preview currently lives in chat and is discarded. It
becomes the **first section of the artifact itself**, so a human reviewing the
file reads 15 lines before deciding whether to read 200.

- Added to the `sections` list in `scripts/rules.json` for `spec` and `design`.
- Same 15-line cap, same plain-language rules as
  `references/summary-preview.md`.
- **Still never judged.** Tier 1 checks only that the heading exists and the
  section is at most 15 lines; Tier 2 does not score it. The rule that a rubric
  written for a 300-line contract scores a 15-line sketch as catastrophically
  incomplete still holds — it is now inside the file rather than outside it.
- `references/summary-preview.md` is rewritten: the preview shown in chat before
  authoring and the persisted section are the same 15 lines, written once.

### 4.4 One capped mermaid diagram per artifact, from a closed vocabulary

**One diagram per artifact, never two.** The point of this section is that a
reader gets the shape in one glance; two diagrams is two glances and re-opens
the length problem the rest of §4 exists to close.

The type is not the author's free choice. Nine types are permitted, each with
the artifact it belongs to and its own cap — a "node" cap is meaningless for a
gantt, so each type carries the cap that matches its shape:

| Diagram | Mermaid syntax | Belongs in | Cap |
|---|---|---|---|
| Flowchart (control flow, incl. failure edges) | `flowchart` | `design.md`, `tasks.md` (milestone DAG) | 12 nodes |
| Data flow | `flowchart` with labeled edges and store nodes | `design.md` | 12 nodes |
| C4 (context or container level only) | `C4Context` / `C4Container` | `design.md`, ADR | 10 elements |
| Architecture | `architecture-beta` | `design.md`, ADR | 12 nodes |
| Gantt | `gantt` | `plan.md` | 20 bars |
| Git graph | `gitGraph` | `plan.md`, ADR (branching or release strategy) | 12 commits |
| Sankey | `sankey-beta` | `design.md` (volume or flow distribution) | 10 links |
| Event modeling | `flowchart LR`, swimlane convention | `discovery.md`, `spec.md` | 12 nodes |
| Ishikawa / fishbone | `mindmap`, fallback `flowchart LR` | troubleshooting lane output | 6 bones, 3 causes each |

Rules that apply to all nine:

- **Over cap means dropped, not shrunk.** A 40-node flowchart that needs
  scrolling is worse than no diagram. Exceeding the cap is a signal the artifact
  covers more than one feature, and the response is to split the feature, not to
  shrink the font.
- **Never a substitute for the contract text.** A diagram is an index into the
  prose and tables, not a place where a requirement lives on its own. If a fact
  exists only in the diagram, it is not specified.
- **`spec.md` gets event modeling or nothing.** It is a business-language
  contract; a box-and-arrow component diagram there invites exactly the
  implementation leakage the spec rubric penalizes. Event modeling is permitted
  because it is expressed in the ubiquitous language — commands, events, read
  models — and names no technology.
- **C4 stops at container level.** Component and code level are design detail
  that the contracts section already carries in a more checkable form.
- **Beta syntax is a real risk.** `sankey-beta` and `architecture-beta` are
  beta in mermaid, and C4 support is experimental; renderers disagree about all
  three. The authoring reference instructs: if the repo's own viewer does not
  render the chosen type, fall back to a `flowchart` rather than shipping a
  fenced block that displays as an error. Ishikawa has no native mermaid type at
  all — `mindmap` is the approximation, and it is the fallback-prone one to
  watch.

### 4.5 Line budgets as non-blocking lint

The linter already has a `review` severity (`scripts/sdd_lint.py:72`) that does
not fail the run. A `max_lines` key per artifact type in `rules.json` emits a
`review` finding when exceeded:

| Artifact | Budget |
|---|---|
| spec.md | 200 |
| design.md | 250 |
| discovery.md | 170 |
| adr.md | 120 |
| test-catalog.md | 120 |
| plan.md | 150 |
| tasks.md | 120 |

These numbers were estimates and one was wrong: discovery.md was set at 150 and
raised to 170 during implementation, because a filled seven-section worksheet
plus its ledger does not fit in 150 and the template could not pass its own
budget without losing content that earns its place.

Non-blocking on purpose: a genuinely large feature is allowed to exceed the
budget, it just has to be a visible decision. Implemented in both
`sdd_lint.py` and `sdd_lint.mjs` so the two runtimes stay in parity.

## 5. Fresh-session handoff for implementation

When `tasks.md` passes its gate, execution does **not** begin in the authoring
session. The session that ran discovery, elicitation, and four gate rounds is
carrying context that implementation does not need and will not benefit from.

`references/artifact-plan-tasks.md` ends the gate by printing:

```
tasks.md gated — 5 milestones, 23 tasks, coverage threshold 80% line.

Implementation is best started in a fresh session so the context window
isn't carrying the discovery transcript. Copy this into a new session:

  Execute the SDD plan at .specs/features/payment-split/tasks.md
```

Then it offers to continue in this session instead — the recommendation is not
a refusal, and a small plan may not be worth a new session. `SKILL.md` Step 1's
state detection already reconstructs everything a cold session needs from disk,
so the handoff requires no new state-passing mechanism.

## 5b. Written for a small executing model

Execution dispatches each task to a **fresh subagent with no session memory**,
and that subagent is often a small model — Haiku-class. A small model with no
context does not fail loudly on a vague reference; it invents one. "The
validation module" becomes a plausible path that does not exist, and "the
relevant handler" becomes a function name nobody wrote.

This does not conflict with §4. Shorter *prose* and more precise *structure*
are the same change: the tokens freed by deleting rationale paragraphs are
spent on literal paths and symbol names, which are dense and unambiguous where
narrative is neither.

Four concrete requirements:

1. **`design.md` gains a required `## 9. File Map`** — a table of every file
   the feature touches: repo-relative path, what it holds, and whether it is
   new or modified. Paths are literal. A path that does not exist yet is still
   written out in full, because the task that creates it needs to be told
   exactly where.
2. **Every contract names its symbol.** A contract in `design.md` states the
   exact function, class, or type name and its signature — not a description of
   what the thing does. An executing model should never have to choose a name.
3. **Every task line carries a `[files: ...]` tag**, linted as a blocker
   exactly like `[Agent: ...]` and `[REQUIRED]`. The tag lists the literal
   repo-relative paths that task is allowed to touch. This bounds the blast
   radius of a small model as much as it guides it.
4. **The dispatch prompt carries both verbatim.** `references/execution.md`
   already sends the task's own slice of `design.md`/`spec.md`; it now also
   sends the task's file list and the named symbols, so the subagent never has
   to search the repo to find out where it is meant to write.

The authoring rule stated in `references/artifact-design.md` and
`references/artifact-plan-tasks.md`: **never refer to a file or a symbol by
description.** Not "the split service" — `src/payments/split_validator.py`.
Not "the validation function" — `validate_split(payment, allocations)`.

## 6. Live progress dashboard

Deferred in the first pass, built in the second, as designed below.

**Architecture: derived from disk, plus tiny event pings.**

- `scripts/sdd_status.py --serve [--port 4517]` reuses the existing lint parser
  to read what is already on disk — `tasks.md` checkbox marks, frontmatter
  `status`/`progress`/`current_milestone`, each artifact's `validation:` block
  — and emits `status.json`. This costs **zero tokens**, because the skill
  already maintains that state as its source of truth (`SKILL.md` Step 1).
- A single static `dashboard.html`, no external assets, polls `/status.json`
  every second and renders: the phase pipeline with per-artifact gate scores,
  the current milestone, the task list with `[ ]`/`[/]`/`[x]`/`[!]`, and the
  blocker log.
- For in-flight work that is not on disk — a judge running, a subagent
  dispatched — the agent appends one line to `.specs/.events.jsonl` via a
  single shell append, ~15 tokens. Without this a three-minute judge run looks
  like nothing is happening.

The token saving is real but indirect: it comes from the agent no longer
narrating progress in chat, which is §3, not from the dashboard itself.

**As built**, one addition the design did not anticipate: the page re-renders
only when `status.json` actually changed. Rebuilding the DOM on every poll
throws away the scroll position once a second, which makes a task list longer
than the viewport unreadable. It is also gated behind `dashboard: on` in
`sdd.config.yml` and off by default, and the agent gives the URL exactly once —
re-announcing it every phase would be the same narration §3 removes.

---

## Files touched

| File | Change |
|---|---|
| `skills/sdd/SKILL.md` | communication contract; judge config resolution in Step 5; fresh-session handoff pointer |
| `skills/sdd/references/quality-gate.md` | fast/full lanes, terse output contract, one-judge-per-round rule, anti-length instruction, retuned rubric wording, criterion rename |
| `skills/sdd/references/summary-preview.md` | preview becomes the persisted `## 0. At a Glance` section |
| `skills/sdd/references/artifact-spec.md` | "Written to pass" authoring rules; table-first rules |
| `skills/sdd/references/artifact-design.md` | "Written to pass"; mermaid vocabulary and caps |
| `skills/sdd/references/artifact-adr.md` | "Written to pass" |
| `skills/sdd/references/artifact-plan-tasks.md` | "Written to pass"; mermaid DAG; fresh-session handoff block |
| `skills/sdd/references/elicitation.md` | checkable-condition rule at interview time |
| `skills/sdd/references/troubleshooting.md` | ishikawa diagram permitted in the defect write-up |
| `skills/sdd/references/discovery.md` | event-modeling diagram permitted |
| `skills/sdd/references/execution.md` | reads `judge_depth`; cold-session entry point |
| `skills/sdd/templates/*.md` | worked examples removed; tables throughout; `## 0. At a Glance` added to `spec.md` and `design.md` only |
| `skills/sdd/references/examples/payment-split/` | new — the extracted worked examples |
| `skills/sdd/scripts/rules.json` | `## 0. At a Glance` and `## 9. File Map` sections; `max_lines` budgets |
| `skills/sdd/scripts/sdd_lint.py` | `max_lines` check, `review` severity; At a Glance 15-line check; `[files: ...]` task tag |
| `skills/sdd/scripts/sdd_lint.mjs` | same, kept at parity |
| `skills/sdd/scripts/sdd_status.py` | new — derives state from disk, serves it |
| `skills/sdd/scripts/dashboard.html` | new — the static page |
| `skills/sdd/references/dashboard.md` | new — how it works, and the event-ping rules |

## Testing

- `python3 tests/run_fixtures.py` must stay green — the existing 20 fixtures are
  the regression baseline for every parser change.
- New fixtures: `at_a_glance_missing`, `at_a_glance_too_long`,
  `max_lines_exceeded` (asserts `review` severity, exit code 0).
- Both runtimes run against every fixture; `sdd_lint.py` and `sdd_lint.mjs` must
  produce identical findings.
- The golden `tests/golden/payment-split/` `spec.md` and `design.md` get an
  `## 0. At a Glance` section added, since they are linted as valid artifacts.
  No other golden file changes.

## Risks

- **Slim templates plus a 1-round cap could let a thin artifact through.** §1 is
  the mitigation — the requirements move to authoring, so the artifact is
  written correctly rather than corrected. If artifacts start failing round 1
  regularly after this lands, §1 is under-done, not §2.
- **A weaker judge model misses semantic defects.** Mitigated by making the
  model an explicit human choice rather than a default buried in a reference.
- **`## 0. At a Glance` becomes stale** when the artifact is revised. The
  existing rule that a material edit invalidates the `validation:` block is
  extended to cover the At a Glance section.
