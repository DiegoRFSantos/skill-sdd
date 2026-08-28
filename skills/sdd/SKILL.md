---
name: sdd
description: Use when starting any feature, fix, or change — owns the full Spec-Driven Development lifecycle (discovery, spec, design, ADRs, test catalog, plan, tasks, execution) with zero-inference quality gates. Also use when asked to write or review a spec.md, design.md, ADR, plan.md, tasks.md, or to execute an SDD plan.
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
   exception is the fast-track lane.
5. **Challenge before agreement.** Never open by agreeing with a proposed
   solution. Run the challenge pass first (see `references/discovery.md`).

## Step 1 — Detect state before doing anything

State lives on disk, not in memory. A cold session reconstructs it:

```bash
ls .specs/features/ 2>/dev/null
ls .adrs/ 2>/dev/null
ls .specs/plans/ 2>/dev/null
grep -H '^status:\|^progress:\|^current_milestone:' .specs/features/*/*.md .specs/plans/*/*.md 2>/dev/null
```

Report where the feature stands in one line, then continue from that phase.
Never restart a phase that already produced an `active` artifact.

If `.specs/` and `.adrs/` do not exist, this repo has not adopted SDD: create
`.adrs/`, `.specs/features/`, and `.specs/plans/`, and say so.

## Step 2 — Route to the phase

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
| Small change (≤3 files, <50 LOC, no new entities) | `references/fast-track.md` | code + living spec update |

## Step 3 — Gate every artifact before moving on

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

Then run Tier 2 and the triage loop per `references/quality-gate.md`.

## Never do these

- Write `plan.md` or `tasks.md` before `spec.md` and `design.md` are `active`.
- Pick a model, a coverage threshold, or a rollout strategy on the user's behalf.
- Mark a task `[x]` without running its tests.
- Continue past a milestone gate without human sign-off.
- Edit an ADR that is already `accepted` — supersede it instead.
