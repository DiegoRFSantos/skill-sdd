---
id: SPEC-FEAT-001            # SPEC-FEAT- plus the feature slug in caps
type: spec
feature: payment-split       # lowercase-kebab, matches the folder under .specs/features/
created_at: 2026-08-18
updated_at: 2026-08-18
author: Diego
version: 1.0.0               # SemVer; bump minor on new rules, major on breaking behavior change
status: draft                # draft | in_review | active | deprecated
dependencies:                # optional; ADRs that constrain this capability
  - ADR-0002
validation:                    # written by the quality gate — see references/quality-gate.md
  - tier1: pass                # pass | fail | skipped
  - tier1_at: 2026-08-18
  - tier2_score: 94            # 0-100
  - tier2_verdict: PASS        # PASS | FAIL
  - tier2_at: 2026-08-18
  - tier2_rounds: 1            # judge dispatches it took to reach this verdict
  - judge_model: sonnet
  - judge_depth: fast
  - notes: "Round 1 scored 82 - EC-04 restated the happy path. Rewrote it as a concurrent-submission boundary; edge-case criterion went 6/15 to 14/15."
---

<!--
The capability contract: WHAT the system must do and WHY, in business language
a non-engineer can sign off on. Never HOW — no protocols, storage engines,
framework names, or route shapes. design.md owns HOW and must be able to change
without this file changing.

Headings and table columns are linted verbatim against scripts/rules.json. Keep
them exactly as they are; replace only the content.

Budget: 200 lines. Over that the linter raises a non-blocking review finding —
allowed for a genuinely large capability, but it should be a decision, not
drift. Tables are the default; prose only where a rule genuinely needs it.

A filled-in example of every section lives in the repository, at
tests/golden/payment-split/.specs/features/payment-split/spec.md. It is not
copied by a manual install and is not needed to use this template - the
worked example below is complete on its own.
-->

## 0. At a Glance

<!--
The persisted 15-line summary. Hard cap, linted: 15 content lines, blanks and
comments excluded. Plain language, no ids, no Gherkin, no jargon. This is what
a reviewer reads before deciding whether to read the other 180 lines — and the
one section never scored by the Tier 2 judge.
-->

An organizer divides one order's cost across several recipients by percentage.
The split is checked before the order is placed, and one whose shares add up to
more than the whole is refused with a reason the organizer can act on.

Not covered: more than one currency, repeating splits, recipients proposing
their own share.

Still open: whether one recipient may hold two shares in the same split.

## 1. Context & Purpose

<!-- The business problem, why now, who is harmed today. From discovery.md. -->

Group orders require one payer to cover the full total. Around 14% of
group-cart checkouts are abandoned or settled outside the app, where we cannot
see, support, or report on them. Organizers have asked repeatedly to divide one
order's cost so nobody has to front the whole amount.

## 2. Ubiquitous Language

<!-- Every domain term used below appears here once. -->

| Term | Definition |
|---|---|
| Payment | The total owed for one order, e.g. 100.00 |
| Recipient | A participant covering part of a payment |
| Allocation | The percentage of a payment one recipient is responsible for |
| Split | The full set of allocations proposed for one payment |
| Organizer | The recipient who configures the split and submits it |
| Rejection Reason | The specific, human-readable cause returned when a split is refused |

## 3. Actors

| Actor | Type | What they need |
|---|---|---|
| Organizer | human | Configure recipients and shares, and get a specific reason on refusal |
| Recipient | human | See their own share before the payment is final |
| Payment Ledger | system | Receive only valid splits, so it never reconciles a mis-allocated payment |

## 4. Scope & Non-Goals

**In scope:** two or more recipients on one payment, shares as percentages,
refusal with a specific reason when the shares are invalid.

<!-- Each exclusion carries a one-line reason. "Not doing X" alone is not one. -->

| Non-goal | Why excluded |
|---|---|
| Multi-currency splits | No reported demand; adds conversion rules this capability does not need yet |
| Recurring or scheduled splits | Out of scope until one-time splits are validated in real use |
| Recipients counter-proposing a share | Organizer-only configuration keeps the first release's decision surface small |
| Splitting by fixed amount | Percentage covers the reported use case; fixed amounts are a separate rule set |

## 5. Business Rules

<!--
One row per rule. The invariant must name a condition something could
mechanically check — a threshold, a comparison, an enumerated set. "Handled
reasonably" is not a condition. Use a ### block below the table only for a rule
whose nuance genuinely does not fit a row.
-->

| Id | Rule | Invariant (checkable) | Why it exists |
|---|---|---|---|
| BR-01 | Total allocation must not exceed 100% | sum(allocations) <= 100, checked before acceptance | A payment can be covered once; over-allocation cannot settle against the amount owed |
| BR-02 | A split needs at least two recipients | count(recipients) >= 2 | A one-recipient split is the existing full-payment flow with extra validation |
| BR-03 | Every recipient holds a positive allocation | for each recipient, allocation > 0 | A 0% recipient is not participating, and hides the real number of paying parties |

## 6. Acceptance Criteria

<!-- One row per criterion, each proving exactly one business rule, each with a binary outcome. -->

| Id | Proves | Given | When | Then |
|---|---|---|---|---|
| AC-01 | BR-01 | a payment of 100.00 with two recipients | a split of 60% and 45% is submitted | it is refused, reason "total allocation exceeds 100%" |
| AC-02 | BR-01 | a payment of 100.00 with two recipients | a split of 60% and 40% is submitted | it is accepted |
| AC-03 | BR-02 | a payment of 100.00 with one recipient | a split of 100% is submitted | it is refused, reason "a split requires at least two recipients" |
| AC-04 | BR-03 | a payment of 100.00 with two recipients | a split of 100% and 0% is submitted | it is refused, reason "every recipient must have an allocation greater than 0%" |

## 7. Edge Cases & Failure Modes

<!--
Boundaries, concurrency, timeouts, malformed input. A case that restates the
happy path is not an edge case, and the Tier 2 rubric scores it as zero.
-->

| Id | Trigger | Expected behavior | Why it matters |
|---|---|---|---|
| EC-01 | Shares sum to exactly 100% | Accepted — 100% is the inclusive upper boundary | Off-by-one refusals hit the organizer's most natural input |
| EC-02 | Two organizers submit competing splits for one payment at once | Exactly one is accepted; the other is refused naming the existing split | Otherwise the payment is double-allocated and cannot settle |
| EC-03 | Organizer stalls and the payment's 15-minute window elapses | Refused, naming the closed window; organizer starts from a fresh payment | An unbounded half-configured state blocks reporting and retries |
| EC-04 | An allocation arrives non-numeric or negative | Refused naming the recipient, before any total is computed | A negative share would otherwise reduce the sum and slip past BR-01 |

## 8. Success Metrics

<!-- Business observables only. No technical metrics. -->

| Metric | Baseline | Target |
|---|---|---|
| Group-cart checkout abandonment | 14% (July 2026 sample) | Below 5% within one quarter of release |
| Monthly "manual reimbursement" tickets | 40 | Below 10 within one quarter of release |
| Splits refused for allocation errors | none (capability does not exist) | Below 8% by the second month post-release |

## 9. Traceability Matrix

<!-- Every BR and EC id appears. An uncovered id names what it still needs. -->

| BR/EC id | Covered by |
|---|---|
| BR-01 | AC-01, AC-02 |
| BR-02 | AC-03 |
| BR-03 | AC-04 |
| EC-01 | AC-02 |
| EC-02 | uncovered — needs a concurrency criterion before this spec reaches in_review |
| EC-03 | uncovered — needs a time-boundary criterion before this spec reaches in_review |
| EC-04 | uncovered — needs an input-validation criterion before this spec reaches in_review |

## 10. Open Questions

<!--
Must be empty before status becomes active. Delete the example rows and keep
the header row once every question is resolved.
-->

| Id | Question | Status |
|---|---|---|
| Q-01 | May one recipient hold two separate shares in the same split? | open |
| Q-02 | Is EC-03's 15-minute window fixed, or configurable per payment type? | open |

## 11. Change Log

| Version | Date | Change | Gate score |
|---|---|---|---|
| 1.0.0 | 2026-08-18 | Initial draft: allocation percentages, minimum recipients, positive allocations | 94 |
