# Phase 0 — Discovery

## The prohibition

Never open by agreeing with the user's proposed solution. If someone says
"add a split-payment button," do not respond with anything that endorses,
refines, or scopes that button before running the challenge pass below. The
first substantive thing you produce in a discovery session is the challenge
pass, not a plan for the proposal.

This is invariant 5 in `SKILL.md`. It exists because users reliably arrive
with a solution rather than the problem underneath it, and once an agent
validates the solution out loud, every later question gets interpreted as
implementation detail instead of a live "should we build this at all."

## Running the challenge pass

Work through all six subheadings, in order, before writing §3 onward. Each
one goes into `templates/discovery.md` §2 verbatim as a `###` subheading.

**Risks.** What does this solution make worse, harder, or more fragile if
built as proposed? Name concrete failure surfaces, not generic caution.

**What's Missing.** What has the user not told you that the solution's
correctness depends on? If you can't answer this, add a `Q-NN` to the ledger
immediately — don't let it sit unexamined.

**The Cheaper 80% Option.** What existing capability, or a smaller build,
gets most of the outcome at a fraction of the cost? State it concretely
enough that the user could choose it instead.

**The Do-Nothing Option.** What is the actual cost of shipping nothing, and
does it beat the cost of building? Do not assume doing nothing is
unacceptable — quantify it if data exists, or name what data would settle it.

**The Falsification.** Name the concrete case where the user's solution is
the wrong one — a specific measurable condition, not a vague risk.

- Not a falsification: "It might not scale." This hedges; it doesn't commit
  to any outcome that would change the recommendation.
- A falsification: "If fewer than 5% of failed group checkouts involve 3+
  distinct payers, the N-way split is over-engineered and a 2-party
  workaround should replace it." This names a threshold, a data source, and
  the decision that follows from crossing it either way.

The test: could the user go check the falsification and come back with an
answer that changes what gets built? If yes, it's a real falsification. If
the sentence survives no matter what the data says, it's a hedge — rewrite
it.

**When The Proposal Is Right.** State the condition under which the user's
original solution is in fact the correct call. This is not a concession —
it's the mirror image of the falsification, and it's what lets §7 land on a
decision instead of a stalemate.

## Role-play triggers and protocol

Trigger a role-play session whenever the discovery touches any of:

1. UX flows
2. Failure and error handling
3. On-call operations
4. Support edge cases
5. Multi-party negotiation
6. Migration cutover

**Picking a persona.** Pull from the feature's Actors list (the same actors
that will later populate `spec.md` §3). If no Actors list exists yet, name
the actor explicitly before playing them — do not role-play an unnamed
generic "user."

**Protocol.** Play one turn at a time, in character, then stop and wait for
the user's reaction before continuing. Do not narrate the whole scenario
end-to-end in one message — the value of role-play is in the user reacting
to a specific moment and surfacing something they hadn't considered, and
that only happens if you leave room between turns.

**Recording findings.** Every gap, ambiguity, or unhandled state the
role-play surfaces becomes an `EC-XX` candidate, logged in `discovery.md`
§4 against the session that produced it. These feed `spec.md` §7 Edge Cases
& Failure Modes directly — do not paraphrase them away before they land
there.

## The anti-sycophancy rule

When the user pushes back on a concern you raised:

1. Restate the concern once, with whatever evidence backs it.
2. If they still want to proceed, defer to their call.
3. Record the risk under `discovery.md` §6 Accepted Risks, with their
   rationale in their own words.

Do not cave silently — a concern that quietly disappears after pushback
never gets recorded and resurfaces later as a surprise. Do not relitigate —
once it's in Accepted Risks with a rationale, raising it a second time in
the same discovery session is noise, not diligence. One restatement, one
outcome, logged.

## Ledger discipline

Every unknown gets a `Q-NN` id the moment it's noticed — mid-sentence, if
that's when it comes up. Don't defer writing it down until the section
that "belongs" to it is being drafted.

Batch questions into one message. Don't drip-feed the user one question,
wait for the answer, ask the next — collect what's open and ask together so
they can answer in one pass.

**Phase 0 cannot exit while any `Q-NN` row in §5 is `open`.** `status:
resolved` in the frontmatter is a claim that gets checked against this —
the linter's `discovery_ledger_empty_when_resolved` check fails the
artifact if a `status: resolved` file still has an `open` row.

"I'll assume X" is banned outright, with no exception for questions that
feel low-stakes. The ledger isn't a courtesy — it's the mechanism that makes
inference structurally impossible. An assumption made instead of logged is
invisible to review; a logged question is not.

## Exit criteria and the handoff

Phase 0 is done when all four hold:

- The ledger is empty — every `Q-NN` row is `resolved`.
- The problem statement is agreed, and it names an outcome, not a solution.
- A direction is chosen, with the rationale recorded in the user's own
  terms (`discovery.md` §7).
- Rejected alternatives are captured with why they lost (`discovery.md` §3).

Only then set `status: resolved` and hand off. What each section feeds:

| Discovery output | Lands in |
|---|---|
| Problem statement | `spec.md` §1 Context & Purpose |
| Actors identified | `spec.md` §3 Actors |
| Rejected alternatives | `spec.md` §4 Non-Goals |
| Role-play findings | `spec.md` §7 Edge Cases & Failure Modes |
| Architectural forks | ADR "Considered Options" |

An "architectural fork" is any point in the challenge pass or role-play
where two structurally different implementations both satisfy the problem
statement — that fork does not get resolved here. Note it and let
`references/artifact-adr.md` pick it up once design starts.
