---
id: SPEC-FEAT-002
type: spec
feature: payment-split
created_at: 2026-08-18
updated_at: 2026-08-18
author: Diego
version: 1.0.0
status: draft
---

## 0. At a Glance

An organizer divides one order's cost across several recipients by percentage.
The split is checked before the order is placed, and a split whose shares add
up to more than the whole is refused with a reason the organizer can act on.

Not covered: more than one currency, repeating splits, recipients proposing
their own share.

Nothing open.

## 1. Context & Purpose

The client calls POST /v1/payments to start a split. Data is held in PostgreSQL.

## 2. Ubiquitous Language
## 3. Actors
## 4. Scope & Non-Goals
## 5. Business Rules

BR-01: totals must not exceed 100%. Rounding rules TBD.

## 6. Acceptance Criteria
## 7. Edge Cases & Failure Modes
## 8. Success Metrics
## 9. Traceability Matrix
## 10. Open Questions
