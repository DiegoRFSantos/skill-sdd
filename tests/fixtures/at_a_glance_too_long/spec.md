---
id: SPEC-FEAT-001
type: spec
feature: payment-split
created_at: 2026-08-18
updated_at: 2026-08-18
author: Diego
version: 1.0.0
status: draft
---

## 0. At a Glance

An organizer divides one order cost across several recipients by percentage.
The split is checked before the order is placed.
A split whose shares add up to more than the whole is refused.
The refusal names the reason the organizer can act on.
Every recipient sees their own share before the payment is final.
A split needs at least two recipients to mean anything.
Shares are expressed as percentages of the whole.
The organizer is the only person who configures the split.
Not covered: more than one currency.
Not covered: repeating or scheduled splits.
Not covered: recipients proposing their own share.
Not covered: splitting by fixed amount.
Not covered: partial settlement of an accepted split.
Not covered: refunds against a settled split.
Not covered: reassigning a share after acceptance.
Nothing open.

## 1. Context & Purpose
## 2. Ubiquitous Language
## 3. Actors
## 4. Scope & Non-Goals
## 5. Business Rules
## 6. Acceptance Criteria
## 7. Edge Cases & Failure Modes
## 8. Success Metrics
## 9. Traceability Matrix
## 10. Open Questions
## 11. Change Log
