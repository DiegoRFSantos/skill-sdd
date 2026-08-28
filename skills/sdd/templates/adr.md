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
validation:                    # written by the quality gate — see references/quality-gate.md
  - tier1: pass
  - tier1_at: 2026-08-18
  - tier2_score: 96
  - tier2_verdict: PASS
  - tier2_at: 2026-08-18
  - tier2_rounds: 1
  - notes: "Passed first pass. Judge flagged §7 as the weakest section - the lint rule named there is real but unwritten, tracked as an accepted risk by the author."
---

<!--
This is the technical constitution. It captures one macro, cross-cutting
architectural decision — the kind that would matter to a feature that hasn't
been imagined yet (a message broker choice, an auth protocol, a concurrency
strategy) — never a single feature's schema or endpoint contract. Once this
file's status is `accepted`, it is immutable: a changed decision gets a NEW
ADR with `supersedes: ADR-<this one>`, not an edit to this file.

This worked example picks a deliberately neutral, illustrative decision — a
shared Idempotency-Key standard for write APIs — so the template reads as a
structural example rather than a real architectural commitment this plugin
makes on the adopter's behalf. Replace the example content with your own
decision; keep the headings exactly as they are — this file is linted
against skills/sdd/scripts/rules.json and the section headings must match
verbatim.

Illustrative superseding pair (not this file's own values — shown only to
demonstrate the fields above):
  New ADR-0009 (the replacement):  supersedes: ADR-0002
  This ADR-0002 (once replaced):   status: superseded, superseded_by: ADR-0009
-->

## 1. Status

**Accepted** — set 2026-08-18.

## 2. Context & Problem Statement

Every service in the platform exposes write APIs (operations that create or
mutate state). Clients and gateways retry on timeouts and transient network
failures as a matter of course, and each retry resubmits the same logical
write. Today, whether a retried write is safe to resubmit is decided
independently by each service team: some already dedupe on an ad hoc header,
some rely on client-side "don't double-click" UI guards that don't survive a
gateway-level retry, and some do nothing, so a retried request can create a
second record or apply a side effect twice. Support has traced duplicate
records and duplicate downstream side effects directly to this gap. Without
a single, enforceable standard, every new write endpoint reopens the same
question, and reviewers have no fixed rule to check code against.

## 3. Decision Drivers

- Retries happen above the application layer (client, proxy, gateway) and
  cannot be eliminated — the standard must make retries safe, not rarer.
- The contract must be uniform across services so a client integrating with
  service A already knows how to integrate safely with service B.
- The mechanism must work over plain HTTP request/response, without
  introducing a new broker, queue, or out-of-band coordination system.
- Coding and reviewing agents must be able to check compliance from the
  endpoint definition alone, without inspecting runtime behavior.
- The standard must degrade safely: a client that omits the mechanism
  should get a clear rejection, never silent double-processing.

## 4. Considered Options

- **Option A — Client-supplied Idempotency Key header.** The client
  generates a unique key per logical write attempt and sends it on every
  retry of that same attempt; the server stores the key alongside the
  resulting response for a fixed window and replays that response for a
  repeated key instead of reprocessing.
- **Option B — Server-side request-body hashing.** The server computes a
  hash of the normalized request body and treats two writes with the same
  hash within a time window as duplicates, without requiring any new client
  field.
- **Option C — No platform standard; leave deduplication to each service.**
  Continue letting each team decide independently whether and how to
  deduplicate retried writes.

## 5. Decision Outcome

**Chosen: Option A — Client-supplied Idempotency Key header.** Body hashing
(Option B) was rejected because two legitimately different writes can share
an identical body (e.g. two separate "add one unit" calls), so a hash cannot
distinguish "retry of the same attempt" from "a new, coincidentally
identical request" — it would silently drop valid writes. Leaving the
decision unstandardized (Option C) was rejected because it is the status
quo that produced the duplicate-record incidents driving this decision, and
it gives coding/reviewing agents no fixed rule to enforce.

**Architectural Rules & Invariants:**

- Every external-facing write endpoint (an operation that creates or
  mutates state) MUST accept a client-supplied `Idempotency-Key` header,
  a UUID v4 string.
- A request missing `Idempotency-Key` on an endpoint this rule covers MUST
  be rejected before any side effect executes.
- The server MUST persist the mapping of `Idempotency-Key` to the resulting
  response for at least 24 hours from first use.
- A repeated request carrying a previously-seen `Idempotency-Key` within
  that window MUST return the original stored response and MUST NOT
  re-execute the underlying side effect.
- Read-only operations are out of scope for this rule; only writes require
  the header.

## 6. Consequences & Trade-Offs

### Positive Consequences

- Retried writes become safe by construction; clients no longer need
  service-specific knowledge of how to avoid double-submission.
- Coding and reviewing agents can check compliance mechanically: does the
  endpoint definition accept and enforce `Idempotency-Key`, yes or no.
- Incident diagnosis simplifies — a duplicate side effect now points to a
  single, known mechanism to inspect rather than N different ad hoc ones.

### Negative Consequences / Risks

- Every write endpoint now carries additional storage cost and latency for
  the key-to-response lookup, proportional to the 24-hour retention window.
- Clients that fail to generate a genuinely unique key per attempt (e.g.
  reusing one key across unrelated writes) will have later, legitimately
  distinct writes rejected or incorrectly deduplicated — this pushes a
  correctness burden onto every client implementation.
- Existing endpoints built before this decision need a migration to add
  `Idempotency-Key` support, and until they do, they remain non-compliant.

## 7. Compliance Verification

**Agent Rule.** A coding agent MUST reject any new or modified
external-facing write endpoint definition that does not accept and enforce
an `Idempotency-Key` header per §5, and MUST flag any `design.md` that
defines such an endpoint without listing `ADR-0002` in its frontmatter
`dependencies`.

**Validation Rule.** CI MUST run a contract test per write endpoint that
sends the same request twice with the same `Idempotency-Key` and asserts
the second response is byte-identical to the first and that the underlying
side effect (e.g. row count, downstream event count) occurred exactly once.
