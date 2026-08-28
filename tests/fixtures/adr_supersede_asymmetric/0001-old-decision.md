---
id: ADR-0001
type: adr
title: Old Decision About Write API Retries
created_at: 2026-01-05
updated_at: 2026-01-05
author: Diego
status: accepted
supersedes: null
superseded_by: null
tags: [api-standards]
---

## 1. Status

**Accepted** — set 2026-01-05.

## 2. Context & Problem Statement

Write APIs needed a retry-safety story and this ADR recorded the original
decision for that problem.

## 3. Decision Drivers

- Retries happen above the application layer and cannot be eliminated.
- The contract must be uniform across services.

## 4. Considered Options

- **Option A — Server-side request-body hashing.** Deduplicate retried
  writes by hashing the normalized request body.
- **Option B — No platform standard.** Leave deduplication to each service.

## 5. Decision Outcome

**Chosen: Option A — Server-side request-body hashing.** Leaving the
decision unstandardized (Option B) was rejected because it left every team
free to pick a different, inconsistent mechanism.

## 6. Consequences & Trade-Offs

### Positive Consequences

- A single mechanism existed for every service to depend on.

### Negative Consequences / Risks

- Two legitimately different writes with identical bodies could be
  incorrectly treated as duplicates.

## 7. Compliance Verification

**Agent Rule.** A coding agent MUST reject any write endpoint that does not
implement request-body hashing per §5.

**Validation Rule.** CI MUST run a contract test asserting duplicate bodies
within the dedupe window are treated as the same write.
