---
id: TESTS-FEAT-001           # e.g. TESTS-FEAT-001
type: test-catalog
feature: payment-split
spec_ref: SPEC-FEAT-001
design_ref: DESIGN-FEAT-001
created_at: 2026-08-18
updated_at: 2026-08-18
author: Diego
status: draft                # draft | active | deprecated
validation:
  - tier1: pass
  - tier1_at: 2026-08-18
  - tier2_score: n/a
  - tier2_verdict: n/a
  - tier2_at: n/a
  - tier2_rounds: 0
  - notes: "No Tier 2 rubric for a catalog. Human sign-off on 2026-08-18 is the gate; deliberate gaps are recorded in section 3."
---

<!--
This catalog is a human sign-off artifact, not a test plan. It records the
main scenarios worth agreeing on with a stakeholder before implementation
starts — the ones that carry business or risk weight. It is deliberately
NOT exhaustive: it does not attempt to enumerate every input combination,
boundary, or malformed-value variant. Enumerating every case is the
implementer's job, done in the test code itself, at their own discretion.
If you find yourself adding a row just to bump a coverage number, stop —
that row belongs in the test suite, not here.
-->

## 1. Coverage Summary

This catalog captures the main test scenarios agreed with a human for the
payment-split feature; it is deliberately not exhaustive — exhaustive case
enumeration belongs in the test code, not here.

Test case count by level: 5 unit, 1 integration, 0 contract, 0 e2e.

## 2. Test Cases

<!--
TC · Covers (spec ids from spec.md, e.g. BR-01, AC-03, EC-02) · Level
(unit/integration/contract/e2e) · Scenario · Status (`[ ]` open, `[x]` done).
Every id in Covers must actually exist in the referenced spec.md — do not
invent ids.
-->

| TC | Covers | Level | Scenario | Status |
|---|---|---|---|---|
| TC-01 | AC-01, BR-01 | unit | split of 60% and 45% (105% total) on a two-recipient payment is rejected with "total allocation exceeds 100%" | `[ ]` |
| TC-02 | AC-02, BR-01, EC-01 | unit | split of 55% and 45% (exactly 100% total) on a two-recipient payment is accepted | `[ ]` |
| TC-03 | AC-03, BR-02 | unit | single-recipient split at 100% is rejected as not a split | `[ ]` |
| TC-04 | AC-04, BR-03 | unit | split of 100% and 0% is rejected because a recipient has a non-positive allocation | `[ ]` |
| TC-05 | EC-04 | unit | a recipient's allocation submitted as "sixty percent" is rejected, and the total-allocation check does not run first | `[ ]` |
| TC-06 | EC-02 | integration | two organizers submit individually-valid splits for the same payment at once; exactly one is accepted and the other is rejected as already split | `[ ]` |

## 3. Deliberate Gaps

<!--
Spec ids that are legitimately not covered by a TC row above, and why.
"We ran out of time" is not a valid reason — either the case belongs in the
implementer's test suite, is already covered elsewhere, or genuinely needs
more spec work before it can be tested at all.
-->

| Spec id | Why no TC row | Recorded by |
|---|---|---|
| EC-03 | Spec's own Traceability Matrix (section 9 of spec.md) marks EC-03 as having no acceptance criterion yet — a time-boundary AC covering the 15-minute expiry window must be added to spec.md before a test case can be written against it | Diego |
| Q-02 | Open question in spec.md (section 10) — whether the 15-minute window is configurable per payment type is undecided, so no test case can be written until the question resolves | Diego |
