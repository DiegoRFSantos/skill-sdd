---
id: DESIGN-FEAT-CCG
type: design
feature: catalog-coverage-gap
spec_ref: SPEC-FEAT-CCG
created_at: 2026-08-19
updated_at: 2026-08-19
author: Test
version: 1.0.0
status: draft
---

## 0. At a Glance

A validation service checks a proposed split before anything is written to the
ledger, and returns the specific reason when it refuses one. Retries carry a
caller-supplied key so a repeated submission settles once.

Not covered: currency conversion, scheduled splits.

Nothing open.

## 1. Architecture & Components

A single service handles widget creation requests.

## 2. Data Model

| Field | Kind | Notes |
|---|---|---|
| name | string | required, non-empty |

## 3. Contracts

The create-widget contract accepts a name field and returns the created widget.

## 4. Interaction Flows

A user submits a name; the service validates it and stores the widget.

## 5. Resilience & Security

Whitespace-only names are rejected before any storage write occurs.

## 6. Observability

Widget creation attempts and rejections are both recorded.

## 7. ADR Conformance

No ADRs apply to this fixture.

## 8. Traceability

| Spec id | Covered by |
|---|---|
| BR-01 | Contracts section |
| EC-01 | Resilience & Security section |

## 9. File Map

| Path | Holds | Status |
|---|---|---|
| `src/payments/split_validator.py` | validation rules | new |

## 10. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-08-19 | Initial fixture design |
