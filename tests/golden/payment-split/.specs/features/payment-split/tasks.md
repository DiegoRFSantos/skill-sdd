---
id: TASKS-FEAT-001
type: tasks
plan_ref: PLAN-FEAT-001
feature: payment-split
created_at: 2026-08-18
updated_at: 2026-08-18
status: in_progress            # ready | in_progress | blocked | done
progress: 4/16
current_milestone: M1
---

<!--
This is the execution tracker. It is the live, task-by-task checklist that
turns plan.md's milestones into individually gated units of work an agent
can pick up, execute, and mark complete. It must stay in lock-step with
plan.md: every task here traces to a milestone in plan.md §1, and every
`depends_on` closure must match the DAG in plan.md §2.

Only the "## Execution Scratchpad & Blocker Log" heading below is linted
verbatim against skills/sdd/scripts/rules.json — everything else (milestone
headings, stream groupings, task lines) is free-form markdown parsed with
regex, not heading matching. That said, task lines MUST follow the exact tag
format shown below, because the linter's named checks (`tasks_tags`,
`tasks_progress`, `tasks_depends_on`, `tasks_cycles`) parse it mechanically:

    - [ ] **Task <id>** `[REQUIRED|OPTIONAL]` `[Agent: <Role>]` `[depends_on: <Task id>, ...]` <description>

`<Role>` is always a role name from plan.md §4 (Coder, Tester, Reviewer,
Evaluator) — NEVER a literal model id. This worked example continues the
payment-split feature from plan.md (PLAN-FEAT-001) verbatim — same
milestones, same task ids, same dependency graph as plan.md §2's DAG.
Replace the example content with your own feature's content; keep the
Scratchpad heading exactly as it is.
-->

# Task Execution Tracker: Payment Split Engine

> Status Notation Guide:
> - [ ] Pending execution
> - [/] In progress
> - [x] Completed and verified by automated tests
> - [!] BLOCKED (Requires human intervention or remediation)

## Milestone 1 (M1): Core Split Engine & Persistence

### Stream 1A: Persistence Layer (Sequential)
- [x] **Task 1.1** `[REQUIRED]` `[Agent: Coder]` `[depends_on: none]` Create the Split/Recipient schema migration (design.md §2.1), including the partial unique index on `payment_id` + `status = accepted`.
- [x] **Task 1.2** `[REQUIRED]` `[Agent: Tester]` `[depends_on: Task 1.1]` Validate migration apply and rollback scripts on a clean test database.

### Stream 1B: Domain Validation Rules (Parallel with Stream 1A)
- [x] **Task 1.3** `[REQUIRED]` `[Agent: Tester]` `[depends_on: none]` Scaffold the unit test harness covering BR-01, BR-02, BR-03, EC-01, and EC-04 (spec.md §5/§7), one test per AC-01..AC-04.
- [x] **Task 1.4** `[REQUIRED]` `[Agent: Coder]` `[depends_on: Task 1.3]` Implement the Split Validation Service (design.md §1.1) satisfying all unit tests, including the fixed evaluation order in the `validate_fail` guard (design.md §2.2).

### Stream 1C: Non-Blocking Observability & Coverage Gate
- [ ] **Task 1.5** `[OPTIONAL]` `[Agent: Coder]` `[depends_on: Task 1.4]` Add the `split.validation.latency_ms` histogram metric (design.md §6.1).
- [ ] **Task 1.6** `[REQUIRED]` `[Agent: Tester]` `[depends_on: Task 1.2, Task 1.4]` Verify Milestone 1 line/branch coverage meets the plan's `coverage_threshold`.

## Milestone 2 (M2): API Layer, Idempotency & Concurrency Protection

### Stream 2A: Contracts & Scaffolding (Parallel)
- [ ] **Task 2.1** `[REQUIRED]` `[Agent: Tester]` `[depends_on: Task 1.2, Task 1.4, Task 1.6]` Scaffold API contract tests for the `SubmitSplit` request, 201 response, and 422 error schemas (design.md §3.1).
- [ ] **Task 2.2** `[REQUIRED]` `[Agent: Coder]` `[depends_on: Task 1.4, Task 1.6]` Implement request/response DTOs with schema validation rules (`recipients` `minItems: 2`, `allocation_percent` `exclusiveMinimum: 0`).

### Stream 2B: Implementation & Middleware
- [ ] **Task 2.3** `[REQUIRED]` `[Agent: Coder]` `[depends_on: Task 2.1, Task 2.2]` Implement the Split Configuration API controller and wire the Split Validation Service.
- [ ] **Task 2.4** `[REQUIRED]` `[Agent: Coder]` `[depends_on: Task 2.3]` Implement the Idempotency-Key filter per ADR-0002 (24-hour key-to-response retention), closing the EC-02 concurrent double-submit gap at the API layer.
- [ ] **Task 2.5** `[REQUIRED]` `[Agent: Coder]` `[depends_on: Task 2.4]` Implement the `expires_at` / `window_elapsed` transition for EC-03 (design.md §2.2).
- [ ] **Task 2.6** `[REQUIRED]` `[Agent: Tester]` `[depends_on: Task 2.4, Task 2.5]` Verify Milestone 2 line/branch coverage meets the plan's `coverage_threshold`.

## Milestone 3 (M3): Payment Ledger Event Integration & Sign-Off

- [ ] **Task 3.1** `[REQUIRED]` `[Agent: Coder]` `[depends_on: Task 2.4, Task 2.5, Task 2.6]` Implement the Payment Ledger Adapter publishing the `split.accepted` event (design.md §3.2), with the retry policy and circuit breaker (design.md §5).
- [ ] **Task 3.2** `[REQUIRED]` `[Agent: Tester]` `[depends_on: Task 3.1]` Run end-to-end broker integration tests asserting event delivery, retry backoff, and circuit-breaker behavior.
- [ ] **Task 3.3** `[REQUIRED]` `[Agent: Tester]` `[depends_on: Task 3.1]` Verify Milestone 3 line/branch coverage meets the plan's `coverage_threshold`.
- [ ] **Task 3.4** `[REQUIRED]` `[Agent: Reviewer]` `[depends_on: Task 3.2, Task 3.3]` Run static analysis, verify ADR-0002 conformance (design.md §7), and record sign-off.

## Execution Scratchpad & Blocker Log

*(Use this section to record runtime blockers, test failures, and remediation notes)*
