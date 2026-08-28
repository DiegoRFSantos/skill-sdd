# Fast-Track

Fast-track is a narrow exception to "no code before the gate," not a second
lifecycle. It exists for small, in-scope changes to a feature that is
already gated and shipped, where running discovery → design → test-catalog
→ plan/tasks again would cost more than the change itself. It is not a
faster way to build something new.

## The three eligibility criteria

A change is fast-track eligible only when **all three** hold:

1. It modifies an existing feature without introducing new domain
   invariants or entities.
2. It touches at most 3 files, **and** is under 50 changed lines.
3. It introduces no new tables, message topics, or third-party
   integrations.

This restates `README.md`'s Fast-track section verbatim except for one
deliberate tightening: criterion 2's "at most 3 files, or under 50 changed
lines" is ambiguous about what happens when the two disagree — 2 files but
80 lines, or 5 files at 10 lines each. Read it as **AND, not OR**: a change
is only eligible if it is both `<= 3 files` and `< 50 changed lines`.
Fast-track is meant to be a narrow, low-risk lane; a change that fails
either measure is not narrow, regardless of how it does on the other one.
If this stricter reading and the README ever appear to diverge, this is a
clarification of the README's ambiguous "or," not a contradiction of it —
the three criteria themselves are unchanged.

### What counts as a new domain invariant (criterion 1)

A **new business rule** — a constraint the spec didn't previously state,
governing behavior the spec didn't previously govern. Examples: adding a
rule that allocations must sum to exactly 100% when the spec previously
allowed under-allocation; requiring a new approval step before an action
that previously needed none; introducing a concept (a new actor, a new
state a Split can be in) that isn't already named in the spec's Ubiquitous
Language table.

**Not** a new invariant — these are in-scope tweaks to an existing rule:

- Fixing a typo or off-by-one in existing validation logic (the rule was
  always "allocations <= 100%"; the code checked `< 100%` by mistake).
- Adjusting an existing rule's numeric threshold (the configuration window
  in EC-03 moves from 15 minutes to 20 minutes; the rule itself —
  "configuration must complete within a window" — is unchanged).
- Extending an existing enum with one new value that fits the enum's
  already-stated purpose (adding a `partially_refunded` status to a
  `PaymentStatus` enum that already models a payment's lifecycle).

The test: does the change require editing the spec's Business Rules (§5) or
Ubiquitous Language (§2) to add a *new* concept, or only to update an
existing rule's stated value or fix a description of what the code always
should have done? The former is not fast-track. The latter is.

## Classification procedure

Work through this before touching any file:

1. **Estimate the diff.** Name the files you expect to touch and roughly
   how many lines each will change. If you can't estimate this without
   first writing the code, the change is not well-understood enough to
   classify — that's itself a signal to slow down.
2. **Check criterion 1 against the actual spec.** Open the feature's
   existing `spec.md` and check whether the change requires adding a new
   `BR-NN` or a new term to §2, versus updating an existing `BR-NN`'s
   stated threshold or wording. Do not answer this from memory of what the
   feature does — read the file.
3. **Check criterion 3.** Does the change add a table, a message topic, or
   a third-party integration that doesn't already exist for this feature?
4. **Apply the AND rule from criterion 2** to the estimate from step 1.
5. **Decide.** All three hold → proceed down this fast-track path. Any one
   fails → this is not fast-track; go back to `SKILL.md` Step 2 and route
   through the full lifecycle (discovery if the change isn't well
   understood yet, otherwise spec → design → test-catalog → plan/tasks).

**If genuinely unsure** — the change sits in a gray area a reasonable
reader could argue either way (does widening an enum's meaning, not just
adding a value, count as a new invariant?) — the answer is never to guess
permissively toward fast-track. Escalate to the full lifecycle. This is the
same zero-inference posture `SKILL.md`'s invariants apply everywhere else:
when a threshold or classification is unstated or unclear, halt and treat
it as the slower, safer, fully-gated path, not a shortcut. A wrongly-slow
classification costs a plan/tasks pass; a wrongly-fast one ships an
unreviewed invariant.

## Precondition: an existing, active spec

Fast-track evolves a feature that already has a `spec.md` with
`status: active`. It is never a way to introduce a feature that has no spec
at all — that gap means the "existing feature" premise of criterion 1
doesn't hold, full stop. Before proceeding:

- Confirm `.specs/features/<feature>/spec.md` exists.
- Confirm its frontmatter `status` is `active` (not `draft`, not
  `in_review`). A spec that hasn't cleared its own gate yet isn't a stable
  base to fast-track a change against.

If either check fails, this isn't a fast-track case — route to
`references/discovery.md` or `references/artifact-spec.md` per `SKILL.md`
Step 2 instead.

## What "update the living spec directly" means

1. Make the actual code change.
2. Edit `spec.md` directly — not a wholesale rewrite. Update only the
   specific `BR`, `AC`, or `EC` the change affects (or add one new `AC`
   under an existing `BR` if the change needed a new observable outcome
   without a new rule). Keep §9's Traceability Matrix consistent with
   whatever you touched.
3. Bump `updated_at` in the frontmatter to today's date.
4. Add a row to §11 Change Log describing:
   - what changed, in one or two sentences,
   - why it qualified for fast-track — the three-criteria check, briefly
     (e.g. "1 file, 12 lines, existing BR-03 threshold only, no new
     tables/topics/integrations"), so a future reader can audit the
     classification decision itself, not just see that a change happened.

Leave `version` and the rest of the spec untouched unless the change you
made actually affects them.

## The gate, scaled down

Fast-track does not skip Tier 1. Run it on the updated `spec.md`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd_lint.py <spec.md> --repo-root .
```

Tier 1 is cheap and deterministic — it catches real mistakes (a broken
cross-reference, a dangling placeholder, a traceability gap introduced by
the edit) regardless of how small the change was, so there is no size
threshold below which it's safe to skip.

Fast-track does **not** require a fresh Tier 2 judge pass on every change.
Tier 2 exists to catch semantic authoring defects — a vague business rule,
an untestable AC — in a document being freshly composed or materially
revised. `references/quality-gate.md` says any material edit to a
Tier-2-passed artifact invalidates that PASS and requires re-running both
tiers. The judgment call here is that a genuinely fast-track-eligible
change is, by the eligibility criteria themselves, defined to be
*non-material* for this purpose: it touches no new invariant, stays within
the 3-file/50-line envelope, and adds no new integration surface. The
existing spec's already-passed Tier 2 score was earned by a document that
this kind of edit doesn't meaningfully change the semantic shape of.

This is a sanity check worth applying explicitly, not just a one-time
justification: **if a change turns out to be material enough that it would
worry a Tier 2 judge, that materiality is itself evidence the change was
never fast-track eligible in the first place.** The eligibility criteria
and the "no fresh Tier 2" exemption are meant to rise and fall together —
if you find yourself wanting a judge pass to be safe, that instinct is a
signal to re-run the classification procedure above, not to run Tier 2
while staying on the fast-track label.

## Execution model

No worktree, no per-task subagent dispatch from `references/execution.md`
— that machinery exists to isolate concurrent streams of a `tasks.md` DAG,
and fast-track has no `tasks.md` and no streams. Make the change directly,
in the current session. Verification is the same standard as any code
change: actually run the project's real tests and confirm they pass, the
same way `references/execution.md`'s "verifying before marking a task
complete" section requires for a Coder task. A claim that "the change
works" without having run anything is not verification.

## The `[fast-track]` commit tag

When the target repo uses git — the norm — commit the change with a
message tagged `[fast-track]`, so the tag and the Change Log entry
together let anyone auditing history find fast-track changes without
reconstructing them from diffs. When the repo has no git history yet (the
same no-git situation `references/execution.md` describes for this
plugin's own dev repo), there is no commit to tag — that alone does not
block fast-track. The §11 Change Log entry is sufficient on its own as the
durable record; it exists in the spec file regardless of git. Say
explicitly when this fallback is in effect, the same way a skipped Tier 1
runtime or a no-git execution fallback gets flagged elsewhere in this
skill.

## Worked examples

**Eligible.** The Payment Split feature's `spec.md` has `EC-03`: "a split
configuration expires if not completed within 15 minutes." Product wants
the window widened to 20 minutes because support tickets show users
frequently get interrupted mid-configuration. This changes one constant in
one validation function and one line in `EC-03`'s Given/When/Then — 1 file,
~6 lines. No new `BR`, no new entity, no new table or integration. All
three criteria hold: fast-track.

**Not eligible — escalate.** The same feature gets a request to let a
Recipient counter-propose a different allocation instead of only the
Organizer configuring the split. `spec.md`'s Non-Goals (§4) explicitly
excludes this today ("organizer-only configuration keeps the first
release's decision surface small"), and it needs a new actor capability, a
new state a Split can be in while a counter-proposal is pending, and likely
a new notification path to the Organizer — a new domain invariant by any
reading, regardless of how few files the first implementation slice
touches. Criterion 1 fails outright; this routes through the full
lifecycle starting at `references/discovery.md` or, if the shape of the
change is already well understood, `references/artifact-spec.md` to revise
the spec properly with its own gate.
