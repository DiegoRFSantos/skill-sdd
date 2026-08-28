---
name: sdd
description: Use when starting any feature, fix, bug, or change — owns the full Spec-Driven Development lifecycle (discovery, spec, design, ADRs, test catalog, plan, tasks, execution) with zero-inference quality gates, plus a fast-track lane for small changes and a troubleshooting lane for defects. Also use when asked to write or review a spec.md, design.md, ADR, plan.md, tasks.md, or to execute an SDD plan.
---

# Spec-Driven Development

Turns an idea into verified, shipped software through gated artifacts. Replaces
ad-hoc brainstorming and planning: no code is written from a conversation, only
from an approved specification.

## Invariants — these are never relaxed

1. **Zero inference.** If a requirement, contract, behavior, model choice, or
   threshold is unstated, **halt and ask**. Never fill a blank with a plausible
   guess. "I'll assume X" is forbidden; open questions go in the ledger.
2. **Zero placeholders.** `TODO`, `TBD`, `etc.`, `...`, and empty schema objects
   are hard blockers, not drafts.
3. **Human decision supremacy.** Architectural trade-offs, business rules,
   edge-case resolutions, model assignments, and coverage thresholds are the
   human's call. Recommend, never decide.
4. **No code before the gate.** Implementation begins only when the discovery
   ledger is empty, `spec.md` and `design.md` are `status: active`,
   `test-catalog.md` exists, and `tasks.md` has passed its gate. The only
   exceptions are the fast-track and troubleshooting lanes.
5. **Challenge before agreement.** Never open by agreeing with a proposed
   solution. Run the challenge pass first (see `references/discovery.md`).
6. **Gate once, record the result.** An artifact is gated when it is authored
   or materially revised, never again at implementation time. The score lives
   in the artifact's `validation:` frontmatter block; execution reads it
   instead of re-running it.

## Step 1 — Detect state before doing anything

State lives on disk, not in memory. A cold session reconstructs it:

```bash
ls .specs/features/ 2>/dev/null
ls .adrs/ 2>/dev/null
grep -H '^status:\|^progress:\|^current_milestone:' .specs/features/*/*.md 2>/dev/null
```

Report where the feature stands in one line, then continue from that phase.
Never restart a phase that already produced an `active` artifact.

**Directories are created lazily — only when a file is about to be written
into them.** Do not scaffold empty folders as a setup step: an empty
directory tells a future reader that a phase was started and abandoned, when
in fact it was never reached. If `.specs/` and `.adrs/` do not exist, this
repo has not adopted SDD — say so, and create the one directory the artifact
you are about to write actually needs.

All of a feature's artifacts live in one folder, `plan.md` and `tasks.md`
included:

```
.specs/features/<feature>/{discovery,spec,design,test-catalog,plan,tasks}.md
.adrs/NNNN-slug.md
```

A repo that already uses the older `.specs/plans/<plan-dir>/` layout keeps
working — `ls .specs/plans/ 2>/dev/null` during state detection, and read
whatever is there. Do not create that directory for new work.

## Step 2 — Triage the lane before routing to a phase

Not every request is a feature. Pick the lane first; routing into the full
phase table below is the answer for one of three cases, not the default for
all of them.

| The request is | Read | Lane |
|---|---|---|
| Something is broken — a bug, a test failure, unexpected behavior | `references/troubleshooting.md` | Understand the defect, then the **user** picks direct fix / fast-track / full lifecycle |
| A small change to an already-gated, active feature (≤3 files **and** <50 LOC, no new entities, tables, topics, or integrations) | `references/fast-track.md` | Code + living spec update |
| Anything else — new capability, new feature, real change of behavior | Step 3 below | Full lifecycle |

When a request is genuinely ambiguous between lanes, escalate to the slower
one. A wrongly-slow classification costs a plan pass; a wrongly-fast one
ships an unreviewed invariant.

## Step 3 — Route to the phase

| Situation | Read | Produces |
|---|---|---|
| New idea, or the user is unsure what they need | `references/discovery.md` | `discovery.md` |
| Discovery resolved, no spec | `references/elicitation.md` + `references/artifact-spec.md` + `templates/spec.md` | `spec.md` |
| Spec active, no design | `references/artifact-design.md` + `references/design-extensions.md` + `templates/design.md` | `design.md` |
| A cross-cutting decision surfaced | `references/artifact-adr.md` + `templates/adr.md` | `.adrs/NNNN-slug.md` |
| Design active, no catalog | `references/artifact-plan-tasks.md` + `templates/test-catalog.md` | `test-catalog.md` |
| Catalog done, no plan | `references/artifact-plan-tasks.md` + `templates/plan.md` + `templates/tasks.md` | `plan.md`, `tasks.md` |
| Any artifact drafted | `references/quality-gate.md` | score report + sign-off |
| Tasks gated, ready to build | `references/execution.md` | working code |

## Step 4 — Offer the summary preview before writing

Long artifacts are validated badly when the human's first look at the
feature is a 300-line document. Before authoring `discovery.md`, `spec.md`,
`design.md`, an ADR, `test-catalog.md`, or the `plan.md`+`tasks.md` pair,
resolve the preference and — unless it says `never` — show a 15-line
plain-language sketch first.

```bash
grep '^summary_preview:' .specs/sdd.config.yml 2>/dev/null
```

No file, or the value is `ask` → ask the user for this artifact. Read
`references/summary-preview.md` for the format, the 15-line cap, and the
rule that **the preview is never linted and never judged** — the human is
its only validator.

## Step 5 — Gate every artifact before moving on

Run Tier 1 first — it is cheap and deterministic:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd_lint.py <artifact> --repo-root .
```

If `python3` is unavailable, use the Node runner:

```bash
node ${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd_lint.mjs <artifact> --repo-root .
```

If neither runtime exists, walk the Tier 1 checklist in `references/quality-gate.md`
manually **and state explicitly that the deterministic pass was skipped**.

Then run Tier 2 and the triage loop per `references/quality-gate.md`, and
write the outcome into the artifact's `validation:` frontmatter block —
score, verdict, date, and the notes. An artifact that passed a gate without
recording it has not finished the gate: the next phase reads that block
instead of re-running the judge.

## Never do these

- Write `plan.md` or `tasks.md` before `spec.md` and `design.md` are `active`.
- Pick a model, a coverage threshold, or a rollout strategy on the user's behalf.
- Re-gate an artifact at implementation time when its `validation:` block
  already records a PASS and nothing has changed since — read the block.
- Lint or dispatch a Tier 2 judge on a summary preview.
- Create a directory before there is a file to put in it.
- Mark a task `[x]` without running its tests.
- Continue past a milestone gate without human sign-off.
- Write a troubleshooting fix before the user has seen the proposal and picked a lane.
- Edit an ADR that is already `accepted` — supersede it instead.
