# Troubleshooting — the fix lane

Something is broken: a failing test, a production defect, a behavior nobody
expected. This lane exists because routing a bug through
discovery -> spec -> design -> catalog -> plan -> tasks is almost always the
wrong shape for a fix, and because the alternative most agents reach for —
patching whatever looks guilty — is worse.

It is a **fast lane**, not a third lifecycle. Its whole job is: understand
the problem properly, then let the human choose how much process the fix
deserves.

**PREFERRED BACKGROUND:** the root-cause discipline itself lives in
`superpowers:systematic-debugging` — reproduce, trace, single hypothesis,
failing test before fix, stop and question the architecture after three
failed fixes. When that skill is available, use it for the investigation in
Step 1 and do not duplicate its work here.

When it is not installed, do not skip the investigation — run this minimum
in its place, in order, and say that you are using the fallback:

1. **Read the error completely** — full stack trace, line numbers, codes.
   Do not skim past a warning on the way to a theory.
2. **Reproduce it reliably.** If you cannot, gather data; do not guess.
3. **Check what changed recently** — the diff, the last commits, config and
   dependency changes.
4. **Trace the bad value back to where it originates**, not to where it
   first became visible. Fix at the source.
5. **One hypothesis at a time**, stated out loud as "X is the cause because
   Y," tested with the smallest possible change. If it was wrong, form a new
   hypothesis — never stack a second fix on top of a failed one.
6. **After three failed fixes, stop** and question the design rather than
   attempting a fourth.

Either way, what follows is only what SDD adds on top: classifying the
defect against the artifacts, and the choice of lane.

## The Iron Law of this lane

```
NO FIX IS WRITTEN BEFORE THE USER HAS SEEN WHAT THE FIX IS AND PICKED A LANE
```

Not a one-line fix. Not an obvious typo. Not "while I was in there." The
proposal step below is the gate, and it is never skipped for being small —
a fix that looks trivial is exactly the one most likely to be silently
changing a rule somebody agreed to on purpose.

## Step 1 — Understand, do not guess

Run the investigation (that skill, or the fallback above) until you can
state the root cause as a specific claim about specific code: *this function
does X when the input is Y, and it should do Z.*

Two SDD-specific additions to that investigation:

- **Read the artifact, not your memory of it.** If the affected area has a
  `spec.md`, open it and find the `BR`/`AC`/`EC` the behavior belongs to.
  "I remember this feature allows partial allocation" is not evidence.
- **Check whether a test should already have caught this.** If
  `test-catalog.md` exists and lists a scenario covering this behavior, the
  gap is in the test suite as much as in the code, and the fix has two
  parts, not one.

If the problem is not reproducible, say so and gather more data. An
unreproducible report never advances to Step 2.

## Step 2 — Classify the defect

Root cause in hand, put it in exactly one of three buckets. The bucket is
what makes the lane options in Step 3 meaningful.

| Bucket | What it means | Test |
|---|---|---|
| **Code defect** | The artifacts are right; the code disagrees with them | An active `spec.md`/`design.md` already states the correct behavior, and the code does something else |
| **Artifact defect** | The code did what it was told; the instruction was wrong, missing, or ambiguous | You cannot point to a line in the spec or design that the code violates — because the case was never covered, or was covered wrongly |
| **Ungoverned area** | The code has no spec at all | No `spec.md` exists for this feature, or its `status` is not `active` |

A code defect that is *also* revealing a missing edge case is an artifact
defect too — classify it as **artifact defect**, since the spec change is
the part that stops it recurring.

## Step 3 — Propose, then let the human choose the lane

Before touching a single file, state all of this in chat, compactly:

1. **Root cause** — one or two sentences, specific.
2. **The fix** — what changes, in which files, roughly how many lines.
3. **Blast radius** — what else touches this code path; what could break.
4. **Classification** — the bucket from Step 2, and why.
5. **Which spec ids are affected** — the `BR`/`AC`/`EC`, or "none, this area
   has no spec."

Then offer the lanes and **stop**. The user picks; you never pick for them.

| Lane | Fits when | What happens |
|---|---|---|
| **A — Fix directly** | Code defect, small, no artifact text changes | Failing regression test first, then the fix, then the real suite. No spec edit, because nothing the spec says was wrong. |
| **B — Fast-track** | Code defect or small artifact defect that changes an existing rule's wording or threshold | Route to `references/fast-track.md`. Run its three eligibility criteria for real — do not assume a bug fix is automatically eligible. Fix + living spec update + Tier 1. |
| **C — Full lifecycle** | Artifact defect introducing a new rule, entity, or state; or an ungoverned area | Route to `SKILL.md` Step 3. Start at `references/discovery.md` if the right behavior is genuinely unsettled, otherwise at `references/artifact-spec.md`. |

Recommend one — you did the investigation, you have an opinion, say it — but
present all three and wait. "This looks like Lane A to me, but it does touch
the allocation rule, so tell me which you want" is the shape. Choosing
silently because the answer seems obvious is the failure this lane exists to
prevent.

### When the user says "just fix it"

That is a real answer: it selects Lane A. It is not permission to skip the
regression test, and it is not permission to edit `spec.md` on the way past.
If your investigation says the fix cannot be done without changing what the
spec asserts, say that plainly in one sentence and re-offer B and C — a Lane
A fix that quietly rewrites a business rule is the worst outcome available
here.

## Step 4 — Fix, with a regression test that came first

Whichever lane was chosen, the fix itself is the same discipline:

1. **Write the failing test first.** It must fail for the reason the bug
   exists, and it must be a real test in the project's real suite — not a
   scratch script that gets deleted. If `test-catalog.md` exists and this
   scenario belongs in it, add the row.
2. **One fix, at the root cause.** No bundled refactoring, no "while I'm
   here" improvements.
3. **Run the project's actual test suite** and read the output. A claim that
   the fix works, without having run anything, is not verification — the
   same standard `references/execution.md` applies to a Coder task.
4. **Disclose any scope expansion.** If fixing this surfaced a genuine
   second defect and you fixed it too, say so explicitly and say why, the
   same way `references/execution.md`'s escalation rule requires. An
   undisclosed extra fix is indistinguishable from scope creep.

## Step 5 — Record it where it will be found again

- **Lane A** — commit tagged `[fix]`. No artifact changes by definition, so
  the commit and the new test are the record.
- **Lane B** — the `[fast-track]` tag and the `spec.md` §11 Change Log entry,
  per `references/fast-track.md`. Say in the Change Log that this was a
  defect fix, not a feature change.
- **Lane C** — the revised artifact carries its own Change Log row and
  re-runs both gate tiers, recording the new score in its `validation:`
  frontmatter block per `references/quality-gate.md`.

If the repo has no git history, there is no commit to tag; the test and the
Change Log entry are the durable record. Say explicitly when that fallback
is in effect.

## Red flags — stop and go back to Step 1

- "The fix is obvious, I'll just make it and explain after."
- "It's one line, the proposal step is overkill."
- "The spec is probably wrong here" — *probably* is not a classification.
- "I'll fix the symptom now and file the real fix for later."
- Three fixes attempted and the test still fails — that is the architecture
  checkpoint, not a fourth attempt.

## Optional: one Ishikawa diagram

When a defect has several candidate causes and the point of the write-up is to
show which were considered, a single fishbone diagram earns its place: mermaid
`mindmap`, cap 6 bones with at most 3 causes each, falling back to
`flowchart LR` where `mindmap` does not render.

Use it to show the causes you ruled out, not to decorate a defect with one
obvious cause. A fishbone with a single populated bone is a sentence pretending
to be a diagram.
