# The Quality Gate — Tier 2

## Two tiers, and why this one runs second

`SKILL.md` Step 3 runs the gate in two passes. **Tier 1** is
`sdd_lint.py`/`sdd_lint.mjs`: deterministic, rule-driven, cheap — frontmatter
shape, required sections, forbidden patterns, cross-references that resolve,
acyclic task DAGs, empty discovery ledgers, symmetric ADR supersede pointers,
a declared coverage threshold. **Tier 2** is this file: a semantic judge that
reads a Tier-1-clean artifact and scores it against a fixed rubric for the
things no linter can see — a business rule so vague it can't be falsified, a
design that never mentions what happens when a call fails, an ADR whose
"alternatives" are straw men, a plan whose milestones are just equal-sized
chunks of work.

Tier 2 never runs on an artifact that hasn't passed Tier 1 first. Scoring the
prose quality of a document that's missing a required section or has a
dangling `spec_ref` wastes a judge's attention on a document that's already
known-broken by cheaper means — fix the mechanical failure, get to a clean
Tier 1 pass, and only then spend a Tier 2 pass on it.

## Why the judge must be a stranger to the work

The agent that just authored or heavily revised an artifact is not a
credible grader of that artifact. It has every incentive — visible or not —
to read its own vague sentence as adequate, its own missing case as
acceptable, because it already knows what it *meant*. This is the same
failure mode `references/discovery.md`'s challenge pass exists to prevent on
the interviewing side; here it applies to grading instead.

This is a hard rule, not a judgment call the orchestrating agent gets to
make case by case:

- Tier 2 MUST be dispatched via the `Agent` tool as a genuinely separate
  subagent — never scored inline by the agent that wrote or edited the
  artifact, and never scored by re-reading the authoring conversation.
- The judge receives **only**: the raw content of the artifact under review,
  plus the raw content of any artifact its rubric requires as context (a
  `design.md` review needs the `spec.md` it implements; an ADR review may
  need nothing beyond itself). Paste file content into the dispatch prompt —
  do not hand the judge a file path and let it read the artifact through a
  session that remembers how the artifact came to be.
- The judge never receives the discovery transcript, prior chat turns, or
  any framing beyond the rubric and the artifact text itself. If the judge
  can infer what the author intended beyond what's on the page, the score is
  contaminated.

An orchestrating agent that skips this and self-scores an artifact it just
wrote has not run Tier 2 — it has produced a number that looks like a Tier 2
result and isn't one.

## Which artifacts get judged

Four of the seven artifact types have a Tier 2 rubric: `spec.md`,
`design.md`, `adr.md`, and the `plan.md`+`tasks.md` pair. `discovery.md` and
`test-catalog.md` are deliberately excluded:

- `discovery.md` is already adversarially validated in-session — the
  challenge pass, the falsification test, and the anti-sycophancy rule in
  `references/discovery.md` are the semantic quality gate for that artifact,
  applied live rather than after the fact.
- `test-catalog.md` is an explicit human sign-off artifact, not a
  semantic-quality target. Its scenarios are supposed to be whatever a human
  agreed carries business risk; there is no rubric a subagent could apply
  that would out-rank the human's own sign-off.

## The four rubrics

Each rubric is exactly 100 points across weighted criteria that sum to 100.
**Pass is >=90/100, on every rubric, no exceptions and no partial credit for
"close enough."** A 100-point scale with a 90-point bar means a single
badly-handled criterion (e.g. a 15-point criterion scored at 3) can sink an
otherwise-strong artifact — that's intentional; semantic defects don't
average out against unrelated strengths.

### spec.md (100 pts)

| Criterion | Points |
|---|---|
| Business rules are falsifiable and testable, not vague aspirations | 20 |
| Acceptance criteria are proper Gherkin, each mapping to exactly one business rule | 20 |
| Edge cases are genuinely edge — boundary, failure, concurrency — not restated happy-path | 15 |
| Non-goals meaningfully fence off adjacent scope creep, not vacuous statements | 10 |
| Zero implementation leakage: no tech stack, table names, endpoints, or library names | 15 |
| Traceability matrix is complete — every BR/EC has AC coverage or an explicit open gap, no orphaned ids | 10 |
| Change log accurately reflects the artifact's real revision history | 10 |

A business rule that reads "the system should handle splits reasonably" is a
zero on the first criterion regardless of how polished the surrounding prose
is — "reasonably" is not a condition anything can be checked against.

### design.md (100 pts)

| Criterion | Points |
|---|---|
| Contracts/schemas are fully specified: types, error shapes, not hand-waved | 20 |
| Interaction flows account for failure modes and partial failure, not only the happy path | 20 |
| Resilience (retries, idempotency, timeouts, backpressure) is addressed wherever the design does I/O or has side effects | 15 |
| Observability (logs/metrics/traces) is specified for operations that matter to debugging or SLOs | 10 |
| Conditional sections (§1.2, §3.3, §3.4, §6.2 per `references/design-extensions.md`) are correctly triggered or explicitly marked not-applicable with a real reason, never silently omitted | 10 |
| Data/schema changes are backward compatible, or a migration path is addressed | 15 |
| Cross-cutting concerns defer to an ADR by reference rather than re-deciding them inline | 10 |

Judging design.md requires the `spec.md` it implements as referenced
context — the judge cannot check "does every failure mode from the spec's
edge cases get handled" without seeing the spec's edge cases.

### adr.md (100 pts)

| Criterion | Points |
|---|---|
| The problem is genuinely cross-cutting/architectural, not one feature's local implementation choice | 20 |
| At least two considered options are real alternatives with honest tradeoffs, not straw men set up to lose | 25 |
| The decision outcome follows demonstrably from the stated decision drivers, not asserted by fiat | 15 |
| Consequences & trade-offs section is honest about downsides and costs, not only upside | 20 |
| Compliance verification gives a concrete, checkable test of adherence (a lint rule, a code pattern, a review checklist item) | 20 |

The straw-man check is the one a judge has to work hardest at: an ADR can
list two "alternatives" and still fail this criterion if the second option
is described in a way no competent engineer would ever have actually
proposed it.

### plan.md + tasks.md (100 pts, judged as a pair)

tasks.md only makes sense as an execution of plan.md, so the two are scored
together — the judge needs both files as primary artifacts, not one as
context for the other.

| Criterion | Points |
|---|---|
| Milestones are independently shippable and verifiable, not arbitrary size-based chunks | 20 |
| The dependency graph is acyclic and matches genuine ordering constraints, not just declared to look complete | 15 |
| Every task is scoped to one verifiable outcome, has an agent allocation, and a REQUIRED/OPTIONAL criticality tag | 20 |
| `coverage_threshold` is declared and at least one coverage-verification task exists per milestone | 15 |
| The blocker/circuit-breaker protocol names who decides and what concretely triggers escalation, not "the team will figure it out" | 15 |
| Model allocations follow the resolution order in `references/artifact-plan-tasks.md` (repo convention -> user answer -> task-fit justification, Anthropic preferred only on a genuine tie) rather than being arbitrary or hardcoded | 15 |

## The evaluator subagent prompt template

This is the literal prompt to pass to the `Agent` tool when dispatching a
Tier 2 judge. Fill in the placeholders; do not paraphrase the instructions
away — the adversarial framing and the per-criterion deficiency requirement
are load-bearing, not boilerplate.

```
You are a Tier 2 semantic quality judge for a Spec-Driven Development
artifact. You have NOT seen how this artifact was written, discussed, or
revised. The text below is your only source of truth — do not assume
anything about intent, context, or good faith beyond what is written.

Artifact type: {artifact_type}

Rubric (100 points total, pass threshold 90/100):
{rubric}

Artifact content:
{artifact_content}

Referenced artifact content (context only — do not score this directly,
use it to check the primary artifact's claims and traceability):
{referenced_artifact_content}

Instructions:

1. Score each rubric criterion independently, out of its stated point
   value. For each one, write a one- or two-sentence justification before
   you commit to a number — do not start from a gut-feel total and
   backfill justifications to match it.
2. Be adversarial. Your default posture is that the artifact is hiding
   vagueness, hand-waving, or an unaddressed gap until you've actively
   checked and ruled that out — not that it's fine until proven otherwise.
   Look specifically for: hedge words ("reasonable," "as appropriate," "in
   most cases," "should generally"), restated happy-path content dressed
   up as an edge case, alternatives that no competent practitioner would
   seriously propose, and claims of coverage or compliance that don't
   trace to anything concrete in the text.
3. Sum the criterion scores to a total out of 100. State the total and a
   single explicit verdict line: "PASS (>=90)" or "FAIL (<90)". Do not
   soften a FAIL with language suggesting it's close enough.
4. For every criterion that scored below its maximum, state the SPECIFIC
   deficiency — quote or point to the exact passage that's the problem —
   and the SPECIFIC change that would fix it. "Tighten the business
   rules" is not acceptable output; "BR-03 says 'handle splits
   reasonably' — replace with a numeric threshold and the concrete
   behavior when it's crossed" is.

Output format: one block per criterion (name, score/max, justification,
deficiency + fix if below max), then the total, then the PASS/FAIL verdict
line.
```

## The triage loop

A FAIL is not a signal to argue with the judge or re-run it hoping for a
better roll. It's a punch list.

1. The orchestrating agent takes the judge's per-criterion deficiencies back
   to the human or the authoring context.
2. Fix the specific gaps named — the exact business rule, the exact missing
   failure mode, the exact straw-man alternative. Not a blanket rewrite of
   the artifact; a blanket rewrite re-opens every criterion the judge
   already scored well and wastes the next judge's time re-verifying
   sections that weren't broken.
3. Re-dispatch a **fresh** judge subagent — never the same one, and never by
   sending it a diff or a "here's what changed" message. A judge that has
   seen a prior revision anchors on it, and a judge that anchors on its own
   earlier score is no longer independent. Give the new judge the same
   inputs a first-time judge would get: the revised artifact content (and
   referenced content) and nothing else.
4. Repeat until PASS, or until a human explicitly decides to accept a named,
   scored gap as documented risk rather than fix it. There is no fixed
   retry cap — looping is cheap, shipping an artifact with an unexamined
   semantic gap is not. When a gap is accepted rather than fixed, record it
   the way `references/discovery.md` §6 records Accepted Risks: the
   specific deficiency, in the human's own rationale for accepting it, not
   silently dropped from the score report.

A PASS is not a promotion out of scrutiny for future revisions — any
material edit to a Tier-2-passed artifact means re-running both tiers
against the new content, since a passing score describes the text that
existed at judge time, not a property of the file going forward.
