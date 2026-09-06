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

## How to talk while doing this

Every message costs the human attention and the session context. These are as
binding as the invariants above.

- **State report: one line.** `payment-split: spec active (94 PASS), design draft.`
- **Gate PASS: one line.** `spec.md — Tier 1 pass, Tier 2 94 PASS (1 round).`
- **Gate FAIL: that line, then the deficiencies as bullets.** Nothing else. No
  reassurance, no plan for what you will do about it — the triage loop already
  says what happens next.
- **Never restate an artifact you just wrote.** `## 0. At a Glance` is its
  summary; link the file and stop.
- **Never narrate the process.** Not "now I'll move to the design phase," not
  "let me read the reference for that," not an explanation of what SDD is. Do
  the thing.
- **Never explain a rule of this skill unless asked.** Applying it is the
  explanation.
- **Questions: batch the independent ones, numbered, no preamble.** Do not
  restate a question in prose before asking it, and do not pad the options with
  reassurance about there being no wrong answer.
- **Say the thing that is actually true**, including when it is inconvenient: a
  skipped Tier 1, a fast-lane gate, an assumption you had to make. Brevity is
  never a reason to leave out a caveat that changes what the human would do.

Terseness applies to your messages, not to the artifacts — and never to a
question that zero inference requires you to ask.

## Context economy — read before reading anything large

**Cost is turns times context size.** Everything in context is re-read on every
later turn, so a file read is never a one-time cost. Three rules cover most of
it; `references/context-economy.md` has the rest and the measurements.

- **Never read a file you are about to hand to a subagent.** Give it the path,
  or the `sdd_extract.py` command. Its context is disposable; yours is not.
- **Extract, do not `cat`.** `sdd_extract.py <file> --outline` to find the
  section, `--section N.N` or `--ids BR-01,AC-02` to take only it.
- **Grep before you read.** State detection in Step 1 never reads an artifact.
- **Offer a context reset after every gated artifact**, with the saving
  attached: `sdd_status.py --context` gives the number. `/clear` at a phase
  boundary, `/compact` mid-phase. You cannot run either — offer once, in one
  line, and accept the answer.

## Configuration

Four optional keys, all in `.specs/sdd.config.yml`, all documented in
`references/configuration.md`:

```bash
cat .specs/sdd.config.yml 2>/dev/null
```

`summary_preview`, `judge_model`, `judge_depth`, `dashboard`. The file is
optional; an absent key means ask. **`judge_model` and `judge_depth` are never
guessed.** `dashboard: on` → start it once, give the URL once, never mention it
again (`references/dashboard.md`).

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
| A model must be chosen for any role | `references/model-selection.md` | a confirmed `allocated_agents` block |
| A cross-cutting decision surfaced | `references/artifact-adr.md` + `templates/adr.md` | `.adrs/NNNN-slug.md` |
| Design active, no catalog | `references/artifact-plan-tasks.md` + `templates/test-catalog.md` | `test-catalog.md` |
| Catalog done, no plan | `references/artifact-plan-tasks.md` + `templates/plan.md` + `templates/tasks.md` | `plan.md`, `tasks.md` |
| Any artifact drafted | `references/quality-gate.md` | score report + sign-off |
| Tasks gated, ready to build | `references/execution.md` | working code |

## Step 4 — The 15-line summary, written once

Artifacts are validated badly when the human's first look at a feature is a
200-line document. One 15-line plain-language sketch fixes that, and it is used
in two places: shown in chat before the artifact is written, and persisted as
the artifact's `## 0. At a Glance` section.

The **section** is required in `spec.md` and `design.md`, linted, cap enforced.
The **chat preview** is a preference:

```bash
grep '^summary_preview:' .specs/sdd.config.yml 2>/dev/null
```

No file, or the value is `ask` → ask the user for this artifact. Read
`references/summary-preview.md` for the format and the rule that **neither
the preview nor `## 0. At a Glance` is ever judged** — Tier 1 checks the
section's cap, and the human is the only validator of its content.

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

Tier 2 needs two answers before it can dispatch — which model the judge runs
on, and whether the gate runs `fast` or `full`:

```bash
grep '^judge_model:\|^judge_depth:' .specs/sdd.config.yml 2>/dev/null
```

Missing either one, ask the human once, both in the same message, and offer to
save the answers. Never guess a judge model: unset, the judge inherits the
orchestrating session's model — usually the slowest available — which is the
single biggest reason a gate feels slow.

Then run Tier 2 and the triage loop per `references/quality-gate.md`, and
write the outcome into the artifact's `validation:` frontmatter block —
score, verdict, date, judge model and depth, and the notes. An artifact that passed a gate without
recording it has not finished the gate: the next phase reads that block
instead of re-running the judge.

## Step 6 — Hand off before executing

A gated `tasks.md` is the end of this session's job, not the start of the next
phase in it. The session that ran discovery, the interview and the gate rounds
is carrying a context window implementation does not need, and every task
dispatch inherits that weight. Print the handoff command from
`references/artifact-plan-tasks.md`, offer to continue here in one line, and
let the human choose. Everything execution needs is on disk, so nothing is lost
either way.

## Never do these

- Write `plan.md` or `tasks.md` before `spec.md` and `design.md` are `active`.
- Pick a model, a coverage threshold, or a rollout strategy on the user's behalf.
- Re-gate an artifact at implementation time when its `validation:` block
  already records a PASS and nothing has changed since — read the block.
- Lint or dispatch a Tier 2 judge on a summary preview or on `## 0. At a Glance`.
- Dispatch more than one judge per artifact per round, or judge two artifacts
  at once.
- Pick a judge model, or a `fast`/`full` depth, without asking.
- Ask which model to use without first checking what the human can reach and
  proposing one per role, each with a line of reasoning. A blank question makes
  the human do the research.
- Name a model id from memory — look it up (`claude-api` skill for Claude), and
  never append a date suffix to an exact id.
- Write a task line without a `[files: ...]` tag, or refer to a file or symbol
  by description when the design names it literally.
- Ship a mermaid diagram over its node cap — drop it instead.
- Create a directory before there is a file to put in it.
- Mark a task `[x]` without running its tests.
- Continue past a milestone gate without human sign-off.
- Read an artifact into your own context in order to paste it to a subagent —
  hand over the path or the `sdd_extract.py` command instead.
- Re-offer a context reset the human already declined for this phase.
- Write a troubleshooting fix before the user has seen the proposal and picked a lane.
- Edit an ADR that is already `accepted` — supersede it instead.
