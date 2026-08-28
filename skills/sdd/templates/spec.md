---
id: SPEC-FEAT-001            # e.g. SPEC-FEAT-001, SPEC-FEAT-PAYMENT-SPLIT
type: spec
feature: payment-split
created_at: 2026-08-18
updated_at: 2026-08-18
author: Diego
version: 1.0.0               # SemVer; bump minor on new rules, major on breaking behavior change
status: draft                # draft | in_review | active | deprecated
dependencies:                # optional; ADRs that constrain this capability
  - ADR-0002                 # e.g. ADR-0002
validation:                    # written by the quality gate — see references/quality-gate.md
  - tier1: pass                # pass | fail | skipped
  - tier1_at: 2026-08-18
  - tier2_score: 94            # 0-100
  - tier2_verdict: PASS        # PASS | FAIL
  - tier2_at: 2026-08-18
  - tier2_rounds: 2            # judge dispatches it took to reach this verdict
  - notes: "Round 1 scored 82 - EC-04 restated the happy path. Rewrote it as a concurrent-submission boundary; edge-case criterion went 6/15 to 14/15."
---

<!--
This is the capability contract. It describes WHAT the system must do and WHY,
in business language a non-engineer stakeholder can read and sign off on. It
must never say HOW: no protocols, no storage engines, no framework names, no
route shapes. That separation is the point — design.md owns HOW, and it must
be able to change without this file changing.

Every section below carries a complete worked example for a payment-split
feature (an organizer divides one order's cost across several recipients by
percentage). Replace the example content with your own feature's content;
keep the headings and table columns exactly as they are — this file is linted
against skills/sdd/scripts/rules.json and the section headings must match
verbatim.
-->

## 1. Context & Purpose

<!--
The business problem, why it matters now, and who is harmed today by its
absence. Pull this from the resolved discovery.md for the same feature —
this section should read like the answer to "why are we building this."
-->

Example: Group orders currently require one payer to cover the full order
total. Support tickets show this causes ~14% of group-cart checkouts to be
abandoned or paid for outside the app (e.g. informal reimbursement between
participants), which we cannot see, support, or report on. Organizers have
asked repeatedly for a way to divide one order's cost among several
recipients at checkout, so nobody has to front the full amount. This
capability lets an organizer configure recipients and allocation percentages
for a single payment, and have the system accept or reject that split before
the order is placed.

## 2. Ubiquitous Language

<!-- Every domain term used anywhere below must appear in this table, once. -->

| Term | Definition |
|---|---|
| Payment | The total amount owed for one order, e.g. 100.00 |
| Recipient | A participant configured to cover part of a payment, e.g. "Maria" |
| Allocation | The percentage of the payment a recipient is responsible for, e.g. 60% |
| Split | The full set of allocations proposed for one payment |
| Total Allocation | The sum of all allocation percentages in a split, e.g. 60% + 45% = 105% |
| Organizer | The recipient who configures the split and submits it for acceptance |
| Rejection Reason | The specific, human-readable cause returned when a split is not accepted, e.g. "total allocation exceeds 100%" |

## 3. Actors

| Actor | Type (human/system) | What they need from this capability |
|---|---|---|
| Organizer | human | Configure recipients and allocation percentages for a payment, and get a clear reason if the split is rejected |
| Recipient | human | See their own allocation before the payment is finalized |
| Payment Ledger | system | Receive only splits that are already valid, so it never has to reconcile an over- or under-allocated payment |

## 4. Scope & Non-Goals

### In Scope

Example: Configuring 2 or more recipients on a single payment, expressing
each recipient's share as a percentage of the total, validating that
allocations do not exceed 100%, and returning a specific rejection reason
when they do.

### Non-Goals

<!-- Each exclusion needs a one-line reason. Not "not doing X" alone. -->

- Splitting a payment across more than one currency — no reported demand, adds conversion-rate business rules this capability does not need yet
- Recurring or scheduled splits (e.g. a split that repeats every month) — out of scope until one-time splits are validated with real usage
- Letting a recipient counter-propose a different allocation — organizer-only configuration keeps the first release's decision surface small
- Splitting by fixed amount instead of percentage — percentage covers the reported use case (dividing a shared bill); fixed-amount splitting is a separate rule set left for a future version

## 5. Business Rules

<!--
One ### block per rule. Statement is the rule in one sentence. Rationale is
why it exists. Invariant is the condition that must always hold, stated so
it could be checked mechanically.
-->

### BR-01: Total allocation must not exceed 100%

**Statement:** The sum of every recipient's allocation percentage in a split
must be less than or equal to 100%.

**Rationale:** A payment can only be fully covered once; allowing the sum to
exceed 100% would mean the payment ledger receives a split it cannot settle
against the actual amount owed.

**Invariant:** sum(allocation percentages in the split) <= 100%, checked
before the split is accepted, e.g. 60% + 45% = 105% must always be rejected.

### BR-02: A split must have at least two recipients

**Statement:** A split is only meaningful when the payment is divided among
two or more recipients.

**Rationale:** A single-recipient "split" is just the existing full-payment
flow; treating it as a split adds validation overhead for no business value.

**Invariant:** count(recipients in the split) >= 2, e.g. a split with only
"Maria: 100%" must be rejected as not a split.

### BR-03: Every recipient must have a positive allocation

**Statement:** Each recipient listed in a split must be allocated a
percentage greater than 0%.

**Rationale:** A recipient configured at 0% is not actually participating in
the payment; including them hides the real number of paying parties from the
organizer and from reporting.

**Invariant:** for every recipient in the split, allocation > 0%, e.g. a
recipient entered as "Diego: 0%" must be rejected.

## 6. Acceptance Criteria

<!--
One ### block per criterion, each proving exactly one business rule, each
with a complete Gherkin example and a binary pass/fail outcome — no
"should probably" language.
-->

### AC-01 (proves BR-01)

```gherkin
Given a payment of 100.00 with two configured recipients
When a split of 60% and 45% is submitted
Then the split is rejected
And the reason returned is "total allocation exceeds 100%"
```

### AC-02 (proves BR-01)

```gherkin
Given a payment of 100.00 with two configured recipients
When a split of 60% and 40% is submitted
Then the split is accepted
```

### AC-03 (proves BR-02)

```gherkin
Given a payment of 100.00 with one configured recipient
When a split of 100% for that single recipient is submitted
Then the split is rejected
And the reason returned is "a split requires at least two recipients"
```

### AC-04 (proves BR-03)

```gherkin
Given a payment of 100.00 with two configured recipients
When a split of 100% and 0% is submitted
Then the split is rejected
And the reason returned is "every recipient must have an allocation greater than 0%"
```

## 7. Edge Cases & Failure Modes

<!--
One ### block per edge case. Must cover boundaries, concurrency, timeouts,
and validation failures at minimum — not just the happy-path validation
already covered by acceptance criteria.
-->

### EC-01: Total allocation equals exactly 100%

**Trigger:** A split's allocation percentages sum to exactly 100%, e.g. 55%
and 45%.

**Expected behavior:** The split is accepted; 100% is the inclusive upper
boundary, not an excluded one.

**Why it matters:** Boundary conditions are the most common place an
off-by-one validation bug hides; the organizer's most natural input (a full,
exact split) must not be rejected.

### EC-02: Two organizers submit competing splits for the same payment at once

**Trigger:** Two submissions for allocations on the same payment arrive
concurrently, each individually valid, but only one payment exists to be
split.

**Expected behavior:** Exactly one split is accepted for that payment; the
second submission is rejected with a reason indicating the payment already
has an accepted split, not a generic error.

**Why it matters:** Without this, both submissions could be accepted against
the same payment, leaving the payment double-allocated and the ledger unable
to settle it.

### EC-03: Organizer stalls mid-configuration and the payment expires

**Trigger:** An organizer begins configuring a split but does not submit it
before the payment's validity window elapses, e.g. no submission within 15
minutes of the payment being created.

**Expected behavior:** The split submission is rejected with a reason
indicating the payment is no longer open for splitting; the organizer must
start over against a fresh payment.

**Why it matters:** Without a bound on configuration time, a payment could
sit indefinitely in a half-configured state, blocking reporting and any
retry the organizer might attempt on the same order.

### EC-04: Allocation submitted as a non-numeric or malformed value

**Trigger:** A recipient's allocation is submitted as something other than a
valid percentage, e.g. "sixty percent" or a negative number like -10%.

**Expected behavior:** The split is rejected with a reason identifying which
recipient's allocation was invalid, before any total-allocation check runs.

**Why it matters:** Validating input shape before validating business
totals prevents a malformed value from silently corrupting the sum used in
BR-01, e.g. treating "-10%" as reducing the total below 100% and letting an
otherwise-invalid split slip through.

## 8. Success Metrics

<!-- Business observables only — no technical metrics. -->

| Metric | Baseline | Target |
|---|---|---|
| Group-cart checkout abandonment rate | 14% (July 2026 ticket sample) | Below 5% within one quarter of release |
| Support tickets tagged "manual reimbursement" per month | 40 | Below 10 within one quarter of release |
| Splits rejected due to allocation errors, as a share of all split attempts | N/A (capability does not exist yet) | Below 8% once organizers are familiar with the flow (measured in the second month post-release) |

## 9. Traceability Matrix

| BR/EC id | Covered by AC ids |
|---|---|
| BR-01 | AC-01, AC-02 |
| BR-02 | AC-03 |
| BR-03 | AC-04 |
| EC-01 | AC-02 |
| EC-02 | (no AC yet — requires a concurrency-focused acceptance criterion before this spec can move to in_review) |
| EC-03 | (no AC yet — requires a time-boundary acceptance criterion before this spec can move to in_review) |
| EC-04 | (no AC yet — requires an input-validation acceptance criterion before this spec can move to in_review) |

## 10. Open Questions

<!--
Table of Q-NN, Question, Status. This table must be empty before status
can become `active` — an active spec cannot carry unresolved questions.
Below is the shape while status is draft or in_review; delete the example
rows and leave only the header row once every question is resolved.
-->

| Q-NN | Question | Status |
|---|---|---|
| Q-01 | Should a recipient be allowed to appear more than once in the same split (e.g. covering two separate shares)? | open |
| Q-02 | Does the 15-minute configuration window in EC-03 need to be configurable per payment type, or is a single fixed value acceptable? | open |

## 11. Change Log

| Version | Date | Change | Gate score |
|---|---|---|---|
| 1.0.0 | 2026-08-18 | Initial draft covering allocation-percentage splitting, minimum recipient count, and positive-allocation rules | 0.72 |
