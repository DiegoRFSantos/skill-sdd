# Running the Elicitation Interview

## The protocol

Interview to zero ambiguity, then write the artifact in one pass. Do not
draft first and ask questions later — a draft anchors the user on the
model's guesses rather than their own answers. Once a sentence exists on the
page, the natural human response is to react to it ("looks about right,"
"sure, close enough") instead of generating the answer from scratch, and
that reaction is systematically weaker than what the user would have said
if asked directly.

This is different from ordinary brainstorming, where the default is to
explore freely and fill small gaps with reasonable judgment. SDD has none of
that latitude: every gap gets a question, not a guess, and the artifact only
gets written once there are no gaps left to fill.

The only time elicitation reopens after the artifact is written is when the
quality gate sends it back — a Tier 2 `user_decisions_required` item, or a
`review`-severity finding the user wants addressed. Both route back into the
interview, not into a silent edit of the artifact.

## The summary preview is not the forbidden draft

`references/summary-preview.md` has the agent show a 15-line sketch before
writing the full artifact. That is not a violation of the rule above, and
the difference is the ordering:

- The forbidden draft comes **before** the interview and contains the
  model's guesses. The user reacts to those guesses instead of generating
  their own answer — which is the whole anchoring problem.
- The preview comes **after** the interview has reached zero ambiguity and
  contains nothing but the user's own answers, restated in plain language.
  There is nothing in it for the user to be anchored on that they did not
  say themselves.

So the order is fixed and not negotiable: interview to zero ambiguity →
preview (if the preference calls for one) → full artifact. Never show a
preview while a question is still open, and never use one as a way to get
the conversation moving before the questions have been asked. A preview
containing a single thing the user did not say is the forbidden draft
wearing a smaller word count.

## Question discipline

One question per message. Resist the urge to list several and let the user
pick which to answer first — that shifts the sequencing decision onto them
and usually gets partial, unordered answers back.

Prefer multiple-choice whenever the option space is closed. "Should
concurrent split submissions be first-write-wins or rejected outright?" gets
a decisive answer in one round-trip. "How should concurrency work?" does
not — it forces the user to first infer what the possible answers even are
before they can pick one.

Batch questions only when both conditions hold: the questions are genuinely
independent of each other, and the user has signaled they want to step away
(e.g. "give me everything at once, I'll answer in one go"). Absent that
signal, default to one at a time — batching independent-looking questions
too early routinely produces answers that don't account for each other,
because the user answered question 3 before seeing how question 1 turned
out.

## Per-artifact question banks

Starter questions to open each interview with — concrete enough to ask
verbatim, not categories to improvise from.

### For a spec

- Who are the actors, and what does each one need from this capability?
- What triggers this capability — what has to happen for it to kick in?
- What must never happen, no matter what the user does?
- What are the boundary values — zero, negative, the maximum?
- What happens if two requests touch the same thing at the same time?
- What does failure look like to the user — what do they see, and what do
  they do next?
- How is success measured, in business terms a non-engineer would recognize?

### For a design

- What shape does the data take, and does it need to be looked up by more
  than one key?
- Is this synchronous or asynchronous from the caller's point of view?
- What makes a retried request safe to retry — what's the idempotency key?
- Who is authorized to do this, and at what granularity — per record, per
  resource type, per tenant?
- What are the actual retry, timeout, and circuit-breaker numbers? Ask for
  the number — never accept "reasonable" or "sensible defaults" as an
  answer.
- What gets logged, and what single business metric proves this capability
  is working?

### For a plan

- How does this break into milestones, where each milestone ships something
  of real value on its own — not just a checkpoint?
- What is the test coverage threshold for this work — or is there
  deliberately none, and why?
- Who resolves each agent role (Coder / Tester / Reviewer / Evaluator), and
  by what source: an existing repo convention, an explicit answer from the
  user, or a suggestion the user confirms?

## The forbidden move

Never write "I'll assume X, and you can correct me if that's wrong" — or
any rephrasing of it. An assumption presented as part of a draft is much
harder for a human to catch and correct than a direct question: phrased as
a statement, it reads as already-decided, and correcting a decision takes
more activation energy than answering a question that was never resolved in
the first place.

Every unknown becomes a `Q-NN` entry instead — logged in `discovery.md`'s
ledger during Phase 0, or asked as a direct question during elicitation for
`spec.md`, `design.md`, or `plan.md`. There is no third path where the model
decides on the user's behalf and moves on.

## Interview until every rule has a checkable condition

The Tier 2 spec rubric scores a business rule on whether it names a condition
something could mechanically check — a threshold, a comparison, an enumerated
set. That is not a grading standard discovered at the gate; it is the exit
condition of this interview.

Before you stop asking, every rule the user has described must survive this:
**write the condition down.** Not the intent, the condition.

| The user said | Not finished — ask | Finished |
|---|---|---|
| "totals shouldn't go over" | over what, and checked when? | `sum(allocations) <= 100`, before acceptance |
| "it should fail gracefully" | fail how, returning what, to whom? | refused with a named reason, before any side effect |
| "reasonably fast" | how fast, measured where, and what happens past it? | 5s, then the caller may retry with the same key |
| "a few recipients" | fewest that makes sense, most allowed? | at least 2; no stated maximum, confirmed by the user |

A rule you cannot write as a condition is a rule the user has not finished
specifying, and the zero-inference invariant applies exactly here: do not pick
the plausible threshold and move on. Ask.

This is about how a rule is *written*. Whether the feature should exist at all
is a different question, already settled in `references/discovery.md`'s
challenge pass — do not reopen it here.
