---
id: DISC-FEAT-PAYMENT-SPLIT # must match ^DISC-FEAT-[A-Z0-9-]+$
type: discovery
feature: payment-split # lowercase, hyphen-separated
created_at: 2026-08-18 # YYYY-MM-DD, date this file was first created
updated_at: 2026-08-18 # YYYY-MM-DD, date of the most recent edit
author: Diego # e.g. Diego, or "Payments Team"
status: resolved # draft while any §5 ledger row reads "open"
validation:                    # discovery.md has no Tier 2 rubric — it is validated live, in-session
  - tier1: pass
  - tier1_at: 2026-08-18
  - tier2_score: n/a
  - tier2_verdict: n/a
  - tier2_at: n/a
  - tier2_rounds: 0
  - judge_model: sonnet
  - judge_depth: fast
  - notes: "Challenge pass and falsification test run in-session; §5 ledger closed with all five questions resolved before status moved to resolved."
---

<!--
This worksheet runs Phase 0 of SDD. It exists because users often arrive with a
solution already in mind ("add a split-payment button") instead of a problem
("customers abandon checkout when they can't share the cost"). Fill it by
interview, in order. Do not skip to §7 — the decision must be earned by the
sections above it.

Every section carries a short payment-split example so the shape is obvious.
Replace the content; keep headings and table columns verbatim — they are linted
against skills/sdd/scripts/rules.json.

Budget 170 lines. Optional: one event-modeling diagram, cap 12 nodes.
-->

## 1. Problem Statement

<!--
State the outcome being bought, WITHOUT naming a solution. "Users want a split-
payment button" is a solution in disguise; "group orders abandon checkout when
one payer can't cover the full amount" is a problem.
-->

Example: Group orders on the checkout page fail to complete when the one payer
on the account cannot cover the full cart amount alone. This happens on ~14%
of group-cart checkouts (support ticket sample, July 2026). The outcome we are
buying is: a group of people can jointly pay for one order without any one
person fronting the whole total.

**What happens if we never build this:** Group carts keep failing at checkout;
those users either abandon the order or coordinate payment manually outside
the app (e.g. one person pays, others Venmo them back), which we cannot see or
support, and which produces the support tickets driving this discovery.

## 2. Challenge Pass

<!-- Run every subheading below before proposing or endorsing any solution. -->

### Risks

Example: Splitting a single order across multiple payment methods increases
the number of partial-failure states (one payer's card declines after two
others already succeeded) that refund and support tooling must handle.

### What's Missing

Example: We don't yet know whether "split" means splitting one card
transaction, or collecting N separate authorizations. That materially changes
the failure-state design and has not been asked yet — see Q-01.

### The Cheaper 80% Option

Example: Instead of building split payment, let the organizer pay in full and
generate a shareable request-money link (reusing our existing peer-transfer
feature) for the other participants to reimburse them post-purchase.

### The Do-Nothing Option

Example: Leave checkout as single-payer. Cost: ~14% of group carts keep
failing, ticket volume stays flat. Benefit: zero engineering cost, no new
partial-failure surface in the payments pipeline.

### The Falsification

<!--
A falsification names the concrete case where the proposed solution is WRONG
— not a hedge like "it might not scale." State the scenario that would make
you recommend against building it.
-->

Example: If fewer than 5% of failed group checkouts involve more than 2
distinct payers (pulled from the same ticket sample used above), then split
payment is over-engineered for the actual distribution — a simpler "invite a
co-payer" (max 2 parties) covers the bulk of cases at a fraction of the
complexity, and full N-way split should be rejected in favor of that.

### When The Proposal Is Right

Example: If the data shows group carts commonly involve 3+ payers (not just
2), and those users are disproportionately high-order-value customers, the
full N-way split is justified because the 2-party workaround would still lose
the highest-value segment.

## 3. Alternatives Considered

| Option | How it works | Why rejected / chosen |
|---|---|---|
| Request-money link (80% option) | Organizer pays in full; app generates a shareable link for others to reimburse via existing peer-transfer | Rejected — pilot data (Q-04, once resolved) needed to confirm ticket volume actually involves 3+ payers before ruling this out |
| Full N-way split payment | Cart total is divided across up to N payment methods at checkout, each authorized separately | Chosen, pending confirmation of the falsification threshold in §2 — group carts show 3+ payers in 61% of the ticket sample |

## 4. Role-Play Log

<!-- One entry per role-play session. Findings become EC-XX candidates for spec.md §7. -->

**Persona:** Organizer (Maria, splits a $180 dinner order 4 ways)
**Scenario:** Maria starts checkout, adds 3 co-payers, 2 confirm their share, 1 co-payer's card declines mid-flow.
**What it revealed:** No defined behavior for what happens to the 2 already-authorized shares when the 3rd declines — hold, refund, or let Maria cover the gap? Nothing in the current proposal answers this.
**Resulting EC-XX candidates:** EC-01 (partial-authorization decline mid-split), EC-02 (organizer prompted to cover a declined co-payer's share)

## 5. Open-Question Ledger

<!--
Every unknown gets a Q-NN id the moment it's noticed. Status is literally
`open` or `resolved` — nothing else. Phase 0 cannot exit while any row is
`open`. "I'll assume X" is banned; if it's not answered here, it's not decided.
-->

| ID | Question | Status | Decision recorded |
|---|---|---|---|
| Q-01 | Does "split" mean one transaction split across methods, or N separate authorizations? | resolved | N separate authorizations — confirmed with Payments team, single-transaction split not supported by current processor |
| Q-02 | What happens to already-authorized shares when a later co-payer's card declines? | resolved | Hold the successful authorizations for 15 minutes, prompt organizer to cover the gap or cancel the whole order |
| Q-03 | Is there a cap on number of co-payers per order? | resolved | Cap at 6, matches existing group-cart size limit |
| Q-04 | What fraction of failed group checkouts actually involve 3+ distinct payers? | resolved | 61% per July 2026 ticket sample — supports building full N-way split over the 2-party workaround |

## 6. Accepted Risks

<!--
When the user pushes back on a raised concern, restate it once with evidence,
then defer to their call and record it here with their rationale. Do not
relitigate it later.
-->

| Risk | Raised concern | User's rationale for accepting |
|---|---|---|
| Partial-authorization holds add a 15-minute state that support has to reason about during refund disputes | Flagged that this expands the support runbook | Accepted — support volume from unhandled group-cart failures today is already higher than the projected volume of split-specific disputes |

## 7. Decision & Rationale

Example: Build full N-way split payment (up to 6 co-payers), with declined
shares held for 15 minutes before prompting the organizer to cover the gap or
cancel. Chosen over the request-money-link workaround because 61% of failed
group checkouts involve 3+ payers, which the 2-party workaround would not
fix — in the user's words, "the whole point is nobody has to front the money
first, and reimbursement-after-the-fact doesn't solve that."
