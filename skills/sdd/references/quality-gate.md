# The Quality Gate — Tier 2

## Two tiers, and why this one runs second

`SKILL.md` Step 5 runs the gate in two passes. **Tier 1** is
`sdd_lint.py`/`sdd_lint.mjs`: deterministic, rule-driven, cheap — frontmatter
shape, required sections, forbidden patterns, cross-references that resolve,
acyclic task DAGs, empty discovery ledgers, symmetric ADR supersede pointers,
a declared coverage threshold. **Tier 2** is this file: a semantic judge that
reads a Tier-1-clean artifact and scores it against a fixed rubric for the
things no linter can see — a business rule too vague to check, a
design that never mentions what happens when a call fails, an ADR whose
"alternatives" are straw men, a plan whose milestones are just equal-sized
chunks of work.

Tier 2 never runs on an artifact that hasn't passed Tier 1 first. Scoring the
prose quality of a document that's missing a required section or has a
dangling `spec_ref` wastes a judge's attention on a document that's already
known-broken by cheaper means — fix the mechanical failure, get to a clean
Tier 1 pass, and only then spend a Tier 2 pass on it.

## What the gate does not apply to

The 15-line summary from `references/summary-preview.md` is never judged, in
either of the two places it appears — not Tier 1, not Tier 2, not "quickly,
just to check."

- **The chat preview** has no frontmatter and no sections, so Tier 1 has
  nothing to check and Tier 2 has nothing to score.
- **`## 0. At a Glance`**, the same 15 lines persisted as the artifact's first
  section, gets exactly one Tier 1 check: that it is within its cap. **No Tier
  2 criterion scores its content**, and no criterion elsewhere may be justified
  by what it does or does not say.

A rubric written for a 200-line contract scores a 15-line sketch as
catastrophically incomplete, which is true and useless. The human's approval is
the entire gate for those 15 lines. Everything else in the artifact is judged
exactly as below.

## Why the judge must be a stranger to the work

The agent that just authored or heavily revised an artifact is not a
credible grader of that artifact. It has every incentive — visible or not —
to read its own vague sentence as adequate, its own missing case as
acceptable, because it already knows what it *meant*. This is the same
failure mode `references/discovery.md`'s challenge pass exists to prevent on
the interviewing side; here it applies to grading instead.

This is a hard rule, not a judgment call the orchestrating agent gets to
make case by case:

- Tier 2 MUST be dispatched as a genuinely separate subagent — whatever your
  harness calls that (Claude Code: the `Agent` tool; other harnesses: their
  subagent or sub-task mechanism) — never scored inline by the agent that wrote or edited the
  artifact, and never scored by re-reading the authoring conversation.
- The judge receives **only**: the artifact under review, plus any artifact its
  rubric requires as context (a `design.md` review needs the `spec.md` it
  implements; an ADR review may need nothing beyond itself).
- **Hand the judge the file paths and let it read them itself.** Do not read the
  artifacts into the orchestrating context in order to paste them into the
  prompt. A fresh subagent opening a file has seen nothing but that file — it is
  exactly as isolated as pasted text, and it keeps several thousand tokens out
  of the orchestrating context, where everything is re-read on every remaining
  turn of the session. What this rule forbids is the *orchestrator* scoring from
  a context that remembers writing the artifact; a subagent with no history and
  a path is not that.
- The judge never receives the discovery transcript, prior chat turns, or
  any framing beyond the rubric and the artifact text itself. If the judge
  can infer what the author intended beyond what's on the page, the score is
  contaminated.

An orchestrating agent that skips this and self-scores an artifact it just
wrote has not run Tier 2 — it has produced a number that looks like a Tier 2
result and isn't one.

## Exactly one judge per round

One judge subagent per artifact per round. Never dispatch parallel judges for
consensus, never dispatch a second to break a tie, and never dispatch judges
for two artifacts at once. The pipeline is sequential by construction — design
needs an active spec, plan needs an active design — so concurrency buys nothing
and multiplies the tail latency: with four judges in flight, the slowest one
sets the wall-clock for all of them.

If a score looks wrong, the answer is the triage loop below, not a second
opinion. Two judges disagreeing produces a number to argue about, not a better
artifact.

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

**Every criterion below scores facts, not prose volume.** A one-line table row
that names the required fact earns full marks; three paragraphs that never name
it earn zero. The templates these artifacts are written from are table-first by
design (see `references/artifact-spec.md`), and a judge that reads a dense row
as "underspecified" will push a correct artifact back toward length it does not
need. Deduct for a missing fact. Never for a missing paragraph.

### spec.md (100 pts)

| Criterion | Points |
|---|---|
| Every business rule names a checkable condition — a threshold, a comparison, an enumerated set. A row stating the condition scores full; prose that never states one scores zero | 20 |
| Each acceptance criterion has a Given/When/Then with a binary outcome and proves exactly one business rule | 20 |
| Each edge case names a boundary, failure, concurrency, or malformed-input trigger. A restated happy path scores zero for that row | 15 |
| Each non-goal names the adjacent scope it excludes and why. "Not doing X" with no reason scores zero | 10 |
| Zero implementation leakage: no tech stack, table names, endpoints, or library names | 15 |
| Every BR and EC id appears in the traceability matrix, mapped to an AC or to a named, explicit gap. No orphaned ids | 10 |
| Change log records the real revision history with the gate score of each version | 10 |

Two calibration points. "The system should handle splits reasonably" is a zero
on the first criterion however polished the surrounding prose — "reasonably" is
not a condition anything can check. And `| BR-01 | total must not exceed 100% |
sum(allocations) <= 100, checked before acceptance | a payment can be covered
once |` is **full marks**: the condition is named, mechanically checkable, and
the row is complete. Do not deduct it for having no rationale paragraph.

### design.md (100 pts)

| Criterion | Points |
|---|---|
| Contracts/schemas are fully specified: types, error shapes, not hand-waved | 20 |
| Interaction flows account for failure modes and partial failure, not only the happy path | 20 |
| Resilience (retries, idempotency, timeouts, backpressure) is addressed wherever the design does I/O or has side effects | 15 |
| Observability (logs/metrics/traces) is specified for operations that matter to debugging or SLOs | 10 |
| Conditional sections (§1.2, §3.3, §3.4, §6.2 per `references/design-extensions.md`) are correctly triggered or explicitly marked not-applicable with a real reason, never silently omitted | 10 |
| Data/schema changes are backward compatible, or a migration path is addressed | 10 |
| Cross-cutting concerns defer to an ADR by reference rather than re-deciding them inline | 5 |
| §9's File Map lists every file the feature touches by literal repo-relative path, and every contract names its exact symbol and signature rather than describing it | 10 |

Judging design.md requires the `spec.md` it implements as referenced
context — the judge cannot check "does every failure mode from the spec's
edge cases get handled" without seeing the spec's edge cases.

The File Map criterion exists because tasks are executed by fresh subagents
with no session memory, often small models. "The validation module" is not a
path a subagent can resolve, so it invents one. `src/payments/split_validator.py`
is. Score the literalness, not the length.

### adr.md (100 pts)

| Criterion | Points |
|---|---|
| The problem is genuinely cross-cutting/architectural, not one feature's local implementation choice | 20 |
| At least two considered options state an honest case a competent engineer would actually make for them; an option written so it obviously loses scores zero for that row | 25 |
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
| Model allocations follow the resolution order in `references/artifact-plan-tasks.md` (repo convention -> user answer -> task-fit justification, Anthropic preferred only on a genuine tie) rather than being arbitrary or hardcoded | 10 |
| Every task's `[files: ...]` tag lists literal repo-relative paths drawn from design.md §9, and the task description names symbols rather than describing them | 5 |

## Two configurable choices: the model, and the depth

Both are the human's call, per `SKILL.md`'s Human Decision Supremacy invariant.
Neither is guessed. Resolve them in this order and stop at the first that
answers:

1. **`.specs/sdd.config.yml`**:

   ```bash
   grep '^judge_model:\|^judge_depth:' .specs/sdd.config.yml 2>/dev/null
   ```

   ```yaml
   judge_model: sonnet     # any model the Agent tool accepts
   judge_depth: fast       # fast | full
   ```

2. **No file, or a key is absent** — ask the human, once, both questions in one
   message, then offer to write the answers into `.specs/sdd.config.yml` so the
   question does not come back every feature.

   **Ask with a recommendation attached, never as a blank.** Follow
   `references/model-selection.md`: find out what they can reach, look up what
   currently exists instead of answering from memory, and propose a specific
   model with one line of reasoning. For the Evaluator role that reasoning is
   usually: the rubric supplies the structure, so this rewards careful reading
   over creativity, and it is the highest-frequency role — which makes it where
   model choice moves the bill most.

Judges are dispatched on `judge_model`. Left unresolved, a judge inherits
whatever model the orchestrating session is running — usually the largest and
slowest available, which is the single biggest reason a gate feels slow. There
is no default worth guessing here: a fast model that misses a semantic defect
and a slow model that finds one are a real trade, and it is not the agent's
trade to make.

## `fast` and `full`

Both lanes use **the same rubric, the same criteria, the same weights, and the
same 90/100 pass bar.** Depth changes how much the judge writes and how many
times it runs — never what it measures.

| | `fast` | `full` |
|---|---|---|
| Criteria scored | all | all |
| Pass bar | >=90/100 | >=90/100 |
| A criterion at full marks | score only | score + justification |
| A criterion below max | score + deficiency + fix | score + justification + deficiency + fix |
| Round cap | **1 re-judge**, then the human decides | uncapped |

In `fast`, a FAIL after the one re-judge is not a loop — it is a decision point.
Present the remaining deficiencies and let the human choose: fix and dispatch
again, or accept the named gap as documented risk. This bounds the worst case at
two dispatches per artifact. `full` keeps the original uncapped behavior for
work where a semantic gap is more expensive than an hour.

`fast` is only affordable because the rubric requirements are also stated as
authoring rules in each `references/artifact-*.md` — the artifact is written to
pass rather than corrected into passing. If artifacts routinely fail round one,
the authoring rules are the thing to fix, not the cap.

## The evaluator subagent prompt template

The literal prompt to pass to the subagent, dispatched on `judge_model`.
Fill in the placeholders; do not paraphrase the instructions away — the
adversarial framing, the anti-length rule, and the per-criterion deficiency
requirement are load-bearing.

```
You are a Tier 2 semantic quality judge for a Spec-Driven Development
artifact. You have NOT seen how this artifact was written, discussed, or
revised. The text below is your only source of truth — do not assume
anything about intent, context, or good faith beyond what is written.

Artifact type: {artifact_type}

Rubric (100 points total, pass threshold 90/100):
{rubric}

Artifact to score: {artifact_path}
Read it now. It is your only source of truth about this artifact.

Referenced artifact (context only — do not score it, use it to check the
primary artifact's claims and traceability): {referenced_artifact_path}

Read only these files. Do not open anything else in the repository, do not
look at git history, and do not go looking for how either file came to be
written — what is in them is the whole of what you are judging.

Instructions:

1. Score each rubric criterion independently, out of its stated point value.
2. Be adversarial. Your default posture is that the artifact is hiding
   vagueness, hand-waving, or an unaddressed gap until you have actively
   checked and ruled that out. Look for: hedge words ("reasonable," "as
   appropriate," "in most cases," "should generally"), restated happy-path
   content dressed up as an edge case, alternatives no competent
   practitioner would seriously propose, and claims of coverage or
   compliance that trace to nothing concrete.
3. Length is not evidence of quality. Never recommend expanding,
   elaborating, or adding narrative. A one-line table row that names the
   required fact scores full marks; three paragraphs that never name it
   score zero. Deduct for a missing fact, never for a missing paragraph.
   These artifacts are written from table-first templates on purpose.
4. You are judging the artifact only. You are NOT challenging whether the
   feature should be built, whether the premise holds, or whether a better
   product decision exists — that argument already happened during
   discovery and is out of your scope.
5. For every criterion below its maximum, name the SPECIFIC deficiency —
   quote the exact passage — and the SPECIFIC change that fixes it.
   "Tighten the business rules" is not acceptable output. "BR-03 says
   'handle splits reasonably' — replace with a numeric threshold and the
   behavior when it is crossed" is.

Output format, exactly this and nothing else. No preamble, no summary
paragraph, no restating the artifact:

CRITERION NAME: 18/20
CRITERION NAME: 20/20
CRITERION NAME: 6/15
  deficiency: <quote the exact passage>
  fix: <the specific change>
TOTAL: 88/100
VERDICT: FAIL

Write the two indented lines ONLY for a criterion scoring below its
maximum. A criterion at full marks gets its score line and nothing else.
VERDICT is exactly "PASS" or "FAIL". Do not soften a FAIL with language
suggesting it is close enough.
```

**In the `full` lane only**, replace the last paragraph with: `Write a
one-sentence justification under every criterion, including those at full
marks, before the deficiency and fix lines.`

When the dashboard is on (`references/dashboard.md`), append one line before
dispatching — a three-minute judge changes nothing on disk until it finishes,
so without this the dashboard looks frozen:

```bash
echo "{\"at\":\"$(date +%H:%M:%S)\",\"event\":\"Tier 2 judge dispatched for design.md\"}" >> .specs/.events.jsonl
```

The terse output is the largest speed lever available. Latency tracks output
tokens, and justification prose for criteria that scored full marks is the bulk
of what a judge writes and nobody reads.

## Recording the result in the artifact

A score that exists only in a chat transcript is a score nobody can find
again. Every gate run — both tiers — ends by writing its outcome into the
artifact's own frontmatter, in a `validation:` block. This is not
bookkeeping: `references/execution.md` reads this block instead of
re-running the gate when implementation starts, so an artifact with no
`validation:` block forces execution to stop and ask.

Write it as a list of single-key pairs, the same YAML shape
`allocated_agents` already uses — the Tier 1 parser handles that form, and
handles nested mappings badly:

```yaml
validation:
  - tier1: pass                # pass | fail | skipped
  - tier1_at: 2026-08-27
  - tier2_score: 94            # 0-100, or n/a for discovery.md and test-catalog.md
  - tier2_verdict: PASS        # PASS | FAIL | n/a
  - tier2_at: 2026-08-27
  - tier2_rounds: 1            # how many judge dispatches it took to reach this verdict
  - judge_model: sonnet        # the model the judge ran on
  - judge_depth: fast          # fast | full
  - notes: "Round 1 scored 82 - EC-04 restated the happy path. Rewrote it as a concurrent-submission boundary; edge-case criterion went 6/15 to 14/15. Accepted risk: success metric SM-02 has no instrumentation yet, per the human."
```

Rules for the block:

- **Every field, every time.** `tier1: skipped` is a legitimate value when
  neither runtime was available — an omitted key is not, because a reader
  cannot tell a skipped pass from a forgotten one. `judge_model` and
  `judge_depth` are recorded too: a 91 from a fast judge and a 91 from a full
  one are not the same evidence, and a reader six months later cannot tell
  which they are looking at unless the block says.
- **`notes` is where the judgment lives.** It names what the judge actually
  caught and what changed in response, plus any gap the human accepted
  rather than fixed (with their rationale, per the triage loop below). "All
  criteria passed" is not a note; it is the score restated.
- **`n/a` for the two unjudged types.** `discovery.md` and
  `test-catalog.md` have no Tier 2 rubric, so they carry the Tier 1 fields
  and `n/a` on the Tier 2 ones. They still get the block.
- **A FAIL gets recorded too**, while the artifact is being fixed. The
  block reflects the last run, not only the last happy run — an artifact
  sitting at `tier2_verdict: FAIL` is exactly the signal the next phase
  needs to refuse to start.
- **Avoid angle brackets and the placeholder words** (`TODO`, `TBD`,
  `etc.`) inside `notes` — Tier 1 scans frontmatter-adjacent text for them
  and will block on your own note.
- **A material edit invalidates the block.** Re-run both tiers and
  overwrite it; do not leave a stale score describing text that no longer
  exists.

## After the block is written, offer the reset

The artifact is now durable and the authoring context is not needed to write
the next one. Run `sdd_status.py --context` for the real number, then offer a context reset
in one line **with the estimate attached** — naming whatever command your
harness uses (Claude Code: `/clear`, or `/compact` mid-phase), per
`references/context-economy.md`, then stop. Once per boundary; if the human
declines, carry on without mentioning it again.

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
4. **Stop at the cap.** In `fast`, that is one re-judge: if round 2 still
   FAILs, do not dispatch a third. Present the remaining deficiencies and let
   the human choose between fixing and accepting. In `full`, repeat until
   PASS. Looping is cheap in tokens and expensive in wall-clock, and an
   artifact that fails twice is usually telling you something the third judge
   will not — the requirement was never settled, and that is a question for
   the human, not another dispatch.
5. When a gap is accepted rather than fixed, record it the way
   `references/discovery.md` §6 records Accepted Risks: the specific
   deficiency, in the human's own rationale for accepting it, never silently
   dropped from the score report.

A PASS is not a promotion out of scrutiny for future revisions — any
material edit to a Tier-2-passed artifact means re-running both tiers
against the new content, since a passing score describes the text that
existed at judge time, not a property of the file going forward.
