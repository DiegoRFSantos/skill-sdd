---
id: ADR-0002
type: adr
title: New Decision About Write API Retries
created_at: 2026-08-18
updated_at: 2026-08-18
author: Diego
status: accepted
supersedes: ADR-0001
superseded_by: null
tags: [api-standards, resilience]
---

## 1. Status

**Accepted** — set 2026-08-18.

## 2. Context & Problem Statement

The original request-body hashing approach from ADR-0001 could not
distinguish a retry of the same write from a new, coincidentally identical
request, so this ADR replaces that decision with a client-supplied
idempotency key standard.

## 3. Decision Drivers

- The mechanism must distinguish a genuine retry from a new request that
  happens to share the same body.
- The contract must be uniform across services.

## 4. Considered Options

- **Option A — Client-supplied Idempotency Key header.** The client
  generates a unique key per logical write attempt and resends it on retry.
- **Option B — Keep the existing body-hashing approach.** Continue
  deduplicating on a hash of the normalized request body.

## 5. Decision Outcome

**Chosen: Option A — Client-supplied Idempotency Key header.** Continuing
with body hashing (Option B) was rejected because it cannot tell a retried
write apart from a new write that happens to carry an identical body.

## 6. Consequences & Trade-Offs

### Positive Consequences

- Retried writes become safe by construction without ambiguity from
  coincidentally identical bodies.

### Negative Consequences / Risks

- Every write endpoint now carries additional storage cost for the
  key-to-response lookup.

## 7. Compliance Verification

**Agent Rule.** A coding agent MUST reject any write endpoint that does not
accept and enforce an `Idempotency-Key` header per §5.

**Validation Rule.** CI MUST run a contract test sending the same request
twice with the same `Idempotency-Key` and asserting the side effect occurred
exactly once.
