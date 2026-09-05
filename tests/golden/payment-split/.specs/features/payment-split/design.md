---
id: DESIGN-FEAT-001
type: design
feature: payment-split
spec_ref: SPEC-FEAT-001
created_at: 2026-08-18
updated_at: 2026-08-18
author: Diego
version: 1.0.0
status: draft
dependencies:
  - ADR-0002
validation:
  - tier1: pass
  - tier1_at: 2026-08-18
  - tier2_score: 92
  - tier2_verdict: PASS
  - tier2_at: 2026-08-18
  - tier2_rounds: 1
  - notes: "Round 1 scored 79 - the flows covered only the happy path. Added partial-failure and timeout branches; interaction-flow criterion went 8/20 to 18/20."
---

## 0. At a Glance

A validation service checks a proposed split before anything reaches the
ledger, and returns the specific reason when it refuses one. Submissions carry
a caller-supplied key so a retried submission settles exactly once.

Not covered here: currency conversion, scheduled splits.

Nothing open.

## 1. Architecture & Components

### 1.1 Component Inventory

| Component | Symbol | Responsibility | Talks to |
|---|---|---|---|
| Split Validator | `SplitValidator` in `src/payments/split_validator.py` | Applies BR-01..BR-03 and returns an accept or a reason | Split Controller |
| Split Controller | `SplitController` in `src/payments/split_controller.py` | Accepts submissions, enforces idempotency, calls the validator | Validator, Ledger Client |
| Ledger Client | `LedgerClient` in `src/payments/ledger_client.py` | Sends accepted splits to the payment ledger | Payment Ledger |

```mermaid
flowchart LR
  O[Organizer] --> C[SplitController]
  C --> V[SplitValidator]
  V -->|accepted| L[LedgerClient]
  V -->|refused: reason| C
  L --> P[(Payment Ledger)]
  L -->|timeout| C
```

### 1.2 Downstream Dependencies & Cross-Feature Impact

_Not applicable: this capability is additive and no existing consumer reads split state._

## 2. Data Model

### 2.1 Schemas

| Field | Type | Constraint |
|---|---|---|
| `payment_id` | uuid | required, references `payments.id` |
| `recipient_id` | uuid | required |
| `allocation_pct` | decimal(5,2) | required, > 0, <= 100 |
| `idempotency_key` | varchar(64) | required, unique per `payment_id` |
| `state` | enum | one of `proposed`, `accepted`, `refused` |

Table: `payment_splits`, new. Migration `db/migrations/001_payment_splits.sql`.
Backward compatible: additive table, no change to `payments`.

### 2.2 State Machine

`proposed` -> `accepted` on validation success; `proposed` -> `refused` on any
BR violation. `accepted` and `refused` are terminal.

## 3. Contracts

### 3.1 API Contracts

`SplitValidator.validate(payment: Payment, allocations: list[Allocation]) -> ValidationResult`

| Outcome | Shape |
|---|---|
| accepted | `ValidationResult(accepted=True, reason=None)` |
| refused | `ValidationResult(accepted=False, reason: RefusalReason)` |

`RefusalReason` is an enum in `src/payments/errors.py`: `TOTAL_EXCEEDS_100`,
`TOO_FEW_RECIPIENTS`, `NON_POSITIVE_ALLOCATION`, `MALFORMED_ALLOCATION`,
`PAYMENT_WINDOW_CLOSED`, `SPLIT_ALREADY_ACCEPTED`.

### 3.2 Event Contracts

`SplitAccepted` published by `LedgerClient.publish_accepted`, payload
`{payment_id: uuid, allocations: [{recipient_id: uuid, allocation_pct: decimal}], accepted_at: timestamp}`.

### 3.3 UI & Client-Side Architecture

_Not applicable: this release exposes no new client surface; the existing checkout form submits the split._

### 3.4 Zero-Downtime Migration Lifecycle

_Not applicable: the migration adds a table no running code reads yet._

## 4. Interaction Flows

| Flow | Happy path | Failure branches |
|---|---|---|
| Submit a split | Controller checks the idempotency key, validator applies BR-01..BR-03, ledger client publishes | Duplicate key returns the first result unchanged; validator refusal returns the reason without calling the ledger; ledger timeout leaves the split `proposed` and the submission retriable |
| Concurrent submissions (EC-02) | First writer wins on the unique `payment_id` constraint | Second write fails the constraint and is refused with `SPLIT_ALREADY_ACCEPTED`, not a generic error |

## 5. Resilience & Security

| Concern | Decision |
|---|---|
| Idempotency | Caller-supplied key, unique per payment, per ADR-0002 |
| Ledger timeout | 5s, then the split stays `proposed` and the caller may retry with the same key |
| Retries | Ledger publish retries 3 times with exponential backoff; validation never retries |
| Authorization | Only the payment's organizer may submit a split for it |

## 6. Observability

### 6.1 Logs & Metrics

| Signal | Emitted by | Why |
|---|---|---|
| `split.refused` counter, tagged by `RefusalReason` | `SplitValidator.validate` | Feeds the spec's "splits refused for allocation errors" metric |
| `split.ledger_publish_ms` histogram | `LedgerClient.publish_accepted` | Detects the timeout branch before it becomes a support ticket |

### 6.2 Feature Flag Configuration

_Not applicable: released without a flag; the capability is additive and reversible by migration._

## 7. ADR Conformance

| ADR | How this design complies |
|---|---|
| ADR-0002 | `idempotency_key` is caller-supplied and unique per `payment_id`, exactly as the ADR's compliance check specifies |

## 8. Traceability

| Spec id | Answered by |
|---|---|
| BR-01 | `SplitValidator.validate`, §3.1 |
| BR-02 | `SplitValidator.validate`, §3.1 |
| BR-03 | `SplitValidator.validate`, §3.1 |
| EC-01 | §3.1 boundary is inclusive (`<= 100`) |
| EC-02 | §4 concurrent-submission flow |
| EC-03 | `PAYMENT_WINDOW_CLOSED`, §3.1 |
| EC-04 | `MALFORMED_ALLOCATION`, checked before totals, §3.1 |

## 9. File Map

| Path | Holds | Status |
|---|---|---|
| `src/payments/split_validator.py` | `SplitValidator`, BR-01..BR-03 | new |
| `src/payments/split_controller.py` | `SplitController`, idempotency handling | new |
| `src/payments/ledger_client.py` | `LedgerClient.publish_accepted` | new |
| `src/payments/errors.py` | `RefusalReason` enum | modified |
| `db/migrations/001_payment_splits.sql` | `payment_splits` table | new |
| `tests/payments/test_split_validator.py` | AC-01..AC-04, EC-01, EC-04 | new |
| `tests/payments/test_split_controller.py` | EC-02, EC-03, idempotency | new |

## 10. Change Log

| Version | Date | Change | Gate score |
|---|---|---|---|
| 1.0.0 | 2026-08-18 | Initial design: validator, controller, ledger client, idempotency per ADR-0002 | 92 |
