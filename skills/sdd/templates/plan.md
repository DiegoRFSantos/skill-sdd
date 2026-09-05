---
id: PLAN-FEAT-001
type: plan
feature: payment-split
spec_ref: SPEC-FEAT-001      # must resolve to an existing spec artifact
design_ref: DESIGN-FEAT-001  # must resolve to an existing design artifact
created_at: 2026-08-18
updated_at: 2026-08-18
author: Diego
status: active                # draft | active | completed | blocked | cancelled
allocated_agents:
  # Model ids are NEVER hardcoded here. Resolution order, checked in this
  # order and stopping at the first that applies:
  #   1. Repo convention — AGENTS.md / CLAUDE.md states a model for this role.
  #   2. The user's explicit answer when asked.
  #   3. The agent's suggestion, driven by what this plan's tasks actually
  #      build, weighing capability against cost and offered for confirmation.
  # See references/artifact-plan-tasks.md for the full rule.
  - Coder: "resolved at plan time"       # resolved at plan time; never guessed — see references/artifact-plan-tasks.md
  - Tester: "resolved at plan time"       # resolved at plan time; never guessed — see references/artifact-plan-tasks.md
  - Reviewer: "resolved at plan time"             # resolved at plan time; never guessed — see references/artifact-plan-tasks.md
  - Evaluator: "resolved at plan time"      # resolved at plan time; never guessed — see references/artifact-plan-tasks.md
coverage_threshold:
  line: 80                     # e.g. 80; or set the whole block to: none (behavioral coverage only)
  branch: 70                   # e.g. 70
  scope: "changed files only"  # changed files only | whole module | whole app
milestones:
  - M1: "Core Split Engine & Persistence"
  - M2: "API Layer, Idempotency & Concurrency Protection"
  - M3: "Payment Ledger Event Integration & Sign-Off"
dependencies:                  # optional; ADRs this plan's agents must comply with while executing it
  - ADR-0002
validation:                    # written by the quality gate — plan.md and tasks.md are judged as one pair
  - tier1: pass
  - tier1_at: 2026-08-18
  - tier2_score: 91
  - tier2_verdict: PASS
  - tier2_at: 2026-08-18
  - tier2_rounds: 2
  - notes: "Round 1 scored 84 - M2 was a technical-layer slice, not independently shippable. Re-cut M2 around the recipient-notification path; milestone criterion went 11/20 to 19/20."
---

<!--
This is the execution contract. It describes WHO builds WHAT, in WHICH
order, with WHICH quality gates — turning spec.md's WHAT/WHY and design.md's
HOW into a concurrency-aware delivery schedule that tasks.md then tracks
task-by-task. It must never invent new business rules or contracts: every
milestone, harness, and gate here must trace back to an existing BR/AC/EC id
in spec.md or a component/contract in design.md.

CRITICAL: no model id is ever hardcoded in this file — not in
`allocated_agents`, not in §4's table. Model selection per role is resolved
at plan time per the order documented above and in
references/artifact-plan-tasks.md. A plan that ships with a literal model
id (e.g. a specific Claude or GPT version string) instead of a resolved
token is not complete.

This worked example continues the payment-split feature from spec.md
(SPEC-FEAT-001) and design.md (DESIGN-FEAT-001) verbatim — same BR-01..03,
AC-01..04, EC-01..04 ids, and the same components and contracts (Split
Configuration API, Split Validation Service, Split Store, Payment Ledger
Adapter, SubmitSplit, split.accepted). Replace the example content with your
own feature's content; keep the headings exactly as they are — this file is
linted against skills/sdd/scripts/rules.json and the section headings must
match verbatim.
-->

# Execution Plan: Payment Split Engine

## 1. Delivery Milestones & Scope Breakdown

<!--
Each milestone is a vertically-sliced, independently testable increment of
business value — never a horizontal technical layer (see
references/artifact-plan-tasks.md, principle 1 and the milestone-derivation
guidance). Gating criteria must cite real AC/EC ids from spec.md or real
contracts/sections from design.md.
-->

| Milestone / Sprint | Scope & Value Delivered | Target Outcome | Gating Criteria |
|---|---|---|---|
| Milestone 1 (M1) | Core Split Engine & Persistence — Split/Recipient schema (design §2.1) and the Split Validation Service enforcing BR-01, BR-02, BR-03 | Recipients and allocations can be validated and persisted end-to-end against a Split row, without the API surface yet | AC-01, AC-02, AC-03, AC-04, and EC-01 (100% boundary) pass against the unit test harness; Milestone 1's coverage_threshold is met |
| Milestone 2 (M2) | API Layer, Idempotency & Concurrency Protection — Split Configuration API (SubmitSplit contract, §3.1), Idempotency-Key handling per ADR-0002, and the EC-02/EC-03 guards | Organizers can submit a split over the public contract exactly once per Idempotency-Key, with malformed input (EC-04) and expired payments (EC-03) rejected before any business rule runs | Contract test suite for §3.1's request/response/error schemas passes; zero duplicate-accepted splits under a concurrent-submission test (EC-02); Milestone 2's coverage_threshold is met |
| Milestone 3 (M3) | Payment Ledger Event Integration & Sign-Off — Payment Ledger Adapter publishing `split.accepted` (§3.2) with the retry policy and circuit breaker (§5), plus observability (§6.1) | An accepted split reliably reaches the Payment Ledger, survives transient publish failures, and the feature is verified compliant with ADR-0002 before release | End-to-end broker integration tests pass; ADR-0002 conformance (design §7) verified; Milestone 3's coverage_threshold is met; Reviewer sign-off recorded |

## 2. Dependency Graph & Concurrency Model (DAG)

<!--
Milestone level only. The per-task DAG is NOT drawn here: task ordering lives
in tasks.md's `depends_on` tags, where the linter checks it for cycles and
dangling references. Drawing it twice means one copy silently goes stale, and a
twenty-node diagram does not fit on a screen anyway.

Cap: 12 nodes, from the permitted diagram set in
references/artifact-plan-tasks.md. Over cap, the diagram is dropped, not shrunk.
-->

```mermaid
flowchart TD
    M1["M1: Core Split Engine & Persistence"] --> G1{{"M1 Gate: AC-01..04, EC-01, coverage met"}}
    G1 --> M2["M2: API, Idempotency & Concurrency"]
    M2 --> G2{{"M2 Gate: contract tests, zero duplicate accepts, coverage met"}}
    G2 --> M3["M3: Ledger Integration & Sign-Off"]
    M3 --> G3{{"M3 Gate: broker e2e, ADR-0002 conformance, sign-off"}}
```

### Concurrency Rules

<!--
Name the streams that run at once and the reason each pair is safe or unsafe —
"they do not overlap" is only a real rule when it names the files.
-->

* Stream 1A (persistence: Task 1.1 -> 1.2) and Stream 1B (validation: Task 1.3 -> 1.4 -> 1.5) run simultaneously: neither is in the other's `depends_on` closure, and `db/migrations/` and `src/payments/split_validator.py` do not overlap.
* Milestone 2 does not begin until Task 1.2 and Task 1.6 are both `[x]`.
* Within Milestone 2, Task 2.1 and Task 2.2 run in parallel, then converge on Task 2.3.
* Task 2.4 and Task 2.5 are deliberately sequential: both modify `src/payments/split_controller.py`, so running them concurrently risks a conflict in the same file.

## 3. Pre-Implementation Test Harness Strategy

<!-- Test suites must exist before the business logic they test — see references/artifact-plan-tasks.md, principle 5. -->

Before generating business code, automated test scaffolding must be instantiated:

* **Domain Unit Harness** (Task 1.3): assertions for BR-01 (total allocation ≤ 100%), BR-02 (≥ 2 recipients), BR-03 (every allocation > 0%), and the EC-01 boundary (exactly 100% is accepted) — one test per AC-01..AC-04 and EC-01 in spec.md §6/§7.
* **API Contract Harness** (Task 2.1): JSON Schema validation for the `SubmitSplit` request, the 201 response, and the 422 error schema (design.md §3.1), including the `error_code` enum mapping so a rejected split always returns the exact code documented for its failing rule.
* **Idempotency Verification Harness** (folded into Task 2.4's acceptance test, per ADR-0002 §7's Validation Rule): asserts that two `SubmitSplit` calls carrying the same `Idempotency-Key` return a byte-identical response and that the underlying Split row is created exactly once — verifying EC-02's duplicate-submission protection at the API layer.
* **Event Contract Harness** (Task 3.2): schema validation for the `split.accepted` event (design.md §3.2) plus a retry/circuit-breaker simulation asserting the §5 backoff (500ms doubling, capped at 8000ms) and the 10-failure/60-second circuit-open threshold.

## 4. Agent Roles & Allocation

<!--
Designated Model is never a literal model id — always the resolved token
from this plan's frontmatter `allocated_agents`. See
references/artifact-plan-tasks.md for the resolution order and how each
suggestion below would be justified once a real model is proposed.
-->

| Role Name | Designated Model | Execution Domain |
|---|---|---|
| Coder | the model resolved into `allocated_agents.Coder` | Schema migrations, Split Validation Service, Split Configuration API controller, Idempotency-Key filter, expiry handling, Payment Ledger Adapter. |
| Tester | the model resolved into `allocated_agents.Tester` | Unit/contract/integration test scaffolding, migration validation, coverage_threshold verification per milestone (Task 1.6, 2.6, 3.3). |
| Reviewer | the model resolved into `allocated_agents.Reviewer` | Static analysis, ADR-0002 conformance verification (design §7), final Milestone 3 sign-off. |
| Evaluator | the model resolved into `allocated_agents.Evaluator` | Tier-2 gate scoring of spec.md/design.md/plan.md artifacts (the Gate score recorded in each artifact's Change Log) — independent of the Coder/Tester/Reviewer execution loop. |

## 5. Circuit Breaker & Blocker Protocol

* **Self-Correction Cap:** agents are limited to 3 consecutive retry attempts on a failing test before the task is treated as blocked.
* **Blocker Escalation:** if a task cannot resolve within 3 cycles, update tasks.md to `[!]` BLOCKED, log the exact failure (error message, failing assertion, or the AC/EC id that will not pass) in the Execution Scratchpad & Blocker Log, and halt execution on that task.
* **Human Gate Requirement:** the workflow cannot proceed past any milestone gate (G1, G2 above, or Milestone 3's sign-off) until every `[REQUIRED]` item in that milestone is marked `[x]` in tasks.md — including its coverage-verification task.
