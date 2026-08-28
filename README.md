# sdd

A Claude Code plugin implementing Spec-Driven Development (SDD): a gated
artifact pipeline that replaces ad-hoc planning with discovery, spec, design,
ADRs, a test catalog, and a plan/tasks pair, each checked before the next is
started. The core rule is zero inference — if a requirement, contract,
behavior, model choice, or threshold is unstated, the skill halts and asks
rather than guessing at a plausible answer. Implementation begins only after
the gate is passed, with a fast-track lane for small changes that don't
warrant the full chain.

## Install

```bash
/plugin marketplace add ~/Developer/sdd-skill
/plugin install sdd@sdd-marketplace
```

## The lifecycle

```
discovery → spec → design (+ADRs) → test-catalog → plan/tasks → execute
```

- **discovery** — is this problem well understood, and what alternatives and
  risks were considered before committing to a direction?
- **spec** — what are we building and why, expressed as business rules,
  Gherkin acceptance criteria, non-goals, and edge cases?
- **design (+ADRs)** — how will it be built: contracts, schemas, interaction
  flows, resilience, and observability, plus any cross-cutting architectural
  decisions recorded as ADRs?
- **test-catalog** — what are the concrete test scenarios, agreed with a
  human and mapped back to spec ids, that will prove the spec is met?
- **plan/tasks** — what are the milestones, the dependency graph, the agent
  allocation, and the live checklist that will execute the design?
- **execute** — write the working code against the gated tasks, checking off
  each one only once its tests pass.

## Artifact map

| Path | Purpose |
|---|---|
| `.specs/features/<feature>/discovery.md` | Phase 0: problem statement, challenge pass, role-play log, open-question ledger |
| `.specs/features/<feature>/spec.md` | What and why — business rules, Gherkin acceptance criteria, non-goals, edge cases |
| `.specs/features/<feature>/design.md` | How — contracts, schemas, interaction flows, resilience, observability |
| `.specs/features/<feature>/test-catalog.md` | The main test scenarios agreed with a human, mapped to spec ids |
| `.adrs/NNNN-slug.md` | Immutable cross-cutting architectural decisions |
| `.specs/plans/<plan-dir>/plan.md` | Milestones, dependency DAG, agent roles, blocker protocol |
| `.specs/plans/<plan-dir>/tasks.md` | Live task checklist and execution scratchpad |

## Running the linter standalone

The Tier 1 linter is deterministic and rule-driven (`skills/sdd/scripts/rules.json`).
Either runner accepts the same CLI contract — one or more artifact paths, plus:

- `--repo-root <path>` — root used to resolve cross-artifact `refs` (e.g. a
  spec's `spec_ref` pointing at a real `spec` artifact). Defaults to `.`.
- `--json` — emit findings as a JSON array instead of the human-readable report.

Exit code `0` means no blockers were found (there may still be `review`
findings). Exit code `1` means at least one `blocker` finding was found.
Every finding carries a `severity` of either `blocker` (fails the gate, exit 1)
or `review` (informational only, does not affect the exit code).

The first (and so far only) rule to emit `review` is `catalog_coverage_prompt`
on `test-catalog` artifacts: it reports acceptance/edge-case ids (`AC-NN`,
`EC-NN`) from the referenced spec that have no test case in section 2 and are
not listed in section 3 Deliberate Gaps (`CATALOG_COVERAGE_GAP`), as a nudge
without failing the gate.

Python runner:

```bash
python3 skills/sdd/scripts/sdd_lint.py <artifact.md> --repo-root .
```

Node runner (same behavior, no Python dependency):

```bash
node skills/sdd/scripts/sdd_lint.mjs <artifact.md> --repo-root .
```

Example, against a fixture with a deliberately missing `author` key:

```bash
python3 skills/sdd/scripts/sdd_lint.py tests/fixtures/spec_missing_author/spec.md --repo-root tests/fixtures/spec_missing_author
```

```
spec.md
  [blocker] FM_MISSING_KEY:1 frontmatter missing required key: author

1 blocker(s), 0 review item(s)
```

This exits `1`. The `node skills/sdd/scripts/sdd_lint.mjs` equivalent produces
the same finding and exit code.

## Fast-track

A change is fast-track eligible only when all three hold:

1. It modifies an existing feature without introducing new domain invariants
   or entities.
2. It touches at most 3 files, or under 50 changed lines.
3. It introduces no new tables, message topics, or third-party integrations.

Fast-track skips `plan.md` and `tasks.md` entirely. Instead, update the
living spec directly and commit with a `[fast-track]` tag.

## Status

Complete: the plugin skeleton (`.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`), the router (`skills/sdd/SKILL.md`), the
rules file for all seven artifact types (`skills/sdd/scripts/rules.json`),
both linter runners (`skills/sdd/scripts/sdd_lint.py`,
`skills/sdd/scripts/sdd_lint.mjs`), and 18 fixture cases under
`tests/fixtures/`, all passing on both runners via `tests/run_fixtures.py`.

Also built: all seven artifact templates and their authoring references
(`skills/sdd/templates/`, `skills/sdd/references/`), a golden worked example
under `tests/golden/payment-split/` that lints clean end to end, the
Tier 2 quality-gate rubrics (`skills/sdd/references/quality-gate.md`) — four
100-point rubrics, a fresh-subagent dispatch contract, and the triage loop,
covering `spec.md`, `design.md`, `adr.md`, and the `plan.md`+`tasks.md` pair
— and the execution engine (`references/execution.md`) and fast-track lane
(`references/fast-track.md`). The router can now take a feature all the way
from discovery through gated execution or, for a small change, straight
down the fast-track lane.

The full lifecycle has been exercised end to end in scratch repos outside
this plugin: a complete discovery-through-execution walkthrough using
worktree-based execution, a session-resumption test (cold-start state
detection mid-plan) that surfaced and led to fixing a real linter gap, and
a fast-track eligibility/classification test. These were dry runs in
throwaway repos, not an install inside a live Claude Code session via
`/plugin` — that step still belongs to whoever installs it, per the Install
section above.
