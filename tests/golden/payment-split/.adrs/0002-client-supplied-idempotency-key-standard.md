---
id: ADR-0002                  # e.g. ADR-0002 — four digits, zero-padded, global sequence (NOT per-feature)
type: adr
title: Client-Supplied Idempotency Key Standard for Write APIs
created_at: 2026-08-18
updated_at: 2026-08-18
author: Diego
status: accepted               # draft | proposed | accepted | rejected | deprecated | superseded
supersedes: null                # e.g. ADR-0001 — set when THIS ADR replaces an older one; null if it replaces nothing
superseded_by: null             # e.g. ADR-0009 — set retroactively on this ADR once something replaces it; null while still current
tags: [api-standards, resilience]   # optional; freeform labels for search/filtering
validation:
  - tier1: pass
  - tier1_at: 2026-08-18
  - tier2_score: 96
  - tier2_verdict: PASS
  - tier2_at: 2026-08-18
  - tier2_rounds: 1
  - notes: "Passed on the first dispatch. The lint rule named in Compliance Verification is not yet written; accepted as a known gap by the author."
---

## 1. Status

**Accepted** — set 2026-08-18.

## 2. Context & Problem Statement

Clients and gateways retry write operations on timeout as a matter of course,
and each retry resubmits the same logical write. Whether that is safe is
currently decided per service team: some dedupe on an ad hoc header, some rely
on client-side guards that do not survive a gateway-level retry, and some do
nothing, so a retry can create a second record. Support has traced duplicate
records directly to this gap. Without one enforceable standard, every new write
endpoint reopens the question and reviewers have no fixed rule to check.

## 3. Decision Drivers

| Driver | Why it constrains the choice |
|---|---|
| Retries happen above the application layer | The standard must make retries safe, not rarer — it cannot assume they stop |
| One contract across services | A client integrating with service A should already know how to integrate safely with service B |
| Plain HTTP request/response only | No new broker, queue, or out-of-band coordination |
| Mechanically checkable | An agent must verify compliance from the endpoint definition alone, without observing runtime behavior |
| Safe degradation | A client omitting the mechanism gets a clear rejection, never silent double-processing |

## 4. Considered Options

| Option | Mechanism | Honest case for it |
|---|---|---|
| A: Client-supplied `Idempotency-Key` | Client generates a unique key per logical attempt; server stores key-to-response for a fixed window and replays on repeat | Distinguishes "retry of this attempt" from "a new, identical request" — the only option that can |
| B: Server-side body hashing | Server hashes the normalized body and treats repeats within a window as duplicates | Requires nothing of the client; deployable without touching a single integration |
| C: No platform standard | Each service decides independently | Zero coordination cost, and teams closest to a domain may know its retry semantics best |

## 5. Decision Outcome

**Chosen: Option A.**

Option B was rejected because two legitimately different writes can carry an
identical body — two separate "add one unit" calls are indistinguishable by
hash — so it would silently drop valid writes. Option C was rejected because it
is the status quo that produced the duplicate-record incidents driving this
decision, and it leaves reviewing agents with no fixed rule to check.

**Architectural rules:**

- Every external-facing write endpoint MUST accept a client-supplied `Idempotency-Key` header, a UUID v4 string.
- A covered request missing the header MUST be rejected before any side effect executes.
- The server MUST persist key-to-response for at least 24 hours from first use.
- A repeat within that window MUST return the stored response and MUST NOT re-execute the side effect.
- Read-only operations are out of scope.

## 6. Consequences & Trade-Offs

### Positive Consequences

- Retried writes are safe by construction; clients need no service-specific knowledge.
- Compliance is mechanically checkable: does the endpoint accept and enforce the header, yes or no.
- A duplicate side effect now points at one known mechanism to inspect instead of several ad hoc ones.

### Negative Consequences / Risks

- Every write endpoint carries storage cost and lookup latency proportional to the 24-hour window.
- A client that reuses a key across unrelated writes gets legitimate writes deduplicated away — this pushes a correctness burden onto every client implementation.
- Endpoints built before this decision are non-compliant until migrated.

## 7. Compliance Verification

**Agent rule.** A coding agent MUST reject any new or modified external-facing
write endpoint that does not accept and enforce `Idempotency-Key` per §5, and
MUST flag any `design.md` defining such an endpoint without `ADR-0002` in its
frontmatter `dependencies`.

**Validation rule.** CI MUST run a contract test per write endpoint that sends
the same request twice with the same key and asserts the second response is
byte-identical to the first and that the side effect occurred exactly once.
