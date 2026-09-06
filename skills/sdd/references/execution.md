# Executing the Plan

## This should be a fresh session

`references/artifact-plan-tasks.md` hands off to a new session once `tasks.md`
is gated, and this file is where that session lands. If you are executing in
the same session that authored the plan, that is allowed — the human may have
chosen it — but the context window is carrying the discovery transcript and
every gate round, and each task dispatch inherits that weight.

Everything execution needs is on disk. `SKILL.md` Step 1 reconstructs it:

```bash
grep -H '^status:\|^progress:\|^current_milestone:' .specs/features/*/*.md 2>/dev/null
```

## Preconditions

Execution does not start on a hunch that `tasks.md` "looks ready." It starts
when all of the following are true:

- `plan.md` and `tasks.md` exist, `plan.md` is `status: active`, and
  `tasks.md`'s frontmatter shows `status: ready` or `in_progress`.
- Their `validation:` frontmatter blocks record a Tier 1 pass and a Tier 2
  `PASS`, per `references/quality-gate.md`.

If either file is missing, still `draft`, or its recorded verdict is `FAIL`,
go back to `references/artifact-plan-tasks.md` and
`references/quality-gate.md` — do not patch the gap by executing anyway and
fixing it "along the way." A `tasks.md` that hasn't earned its gate is not a
safe map to build from: a milestone sliced by technical layer instead of
value, or a missing `depends_on`, turns into a real ordering bug once agents
start touching files in parallel.

## Read the recorded gate — do not re-run it

**Execution does not re-validate artifacts. By default it re-runs nothing —
not Tier 1, not Tier 2, not on `plan.md`, `tasks.md`, `spec.md`, or
`design.md`.** The gate already ran when each artifact was authored, and the
result is recorded in that artifact's `validation:` block. Checking the
precondition above means *reading those blocks*, not reproducing the work
they describe.

The temptation to "just re-lint quickly before we start" is the thing this
rule exists to stop. It burns a judge dispatch and several minutes on a
document nobody has touched since it passed, it delays the code the user
actually asked for, and it teaches the human that the recorded score means
nothing — which is precisely how a recorded score stops being written.

Two situations, and only two, change this:

- **A `validation:` block is missing or incomplete** — the artifact predates
  this convention, or a gate ran without recording. Do not silently
  re-validate and do not silently proceed. Say which artifact lacks a
  recorded gate, and ask: run the gate now, or proceed on the human's word
  that it passed? Their answer decides. If they choose to proceed, note in
  the session that execution started on an unrecorded gate.
- **The artifact changed after its recorded gate** — `updated_at` is later
  than `tier2_at`, or the human says they edited it. That is a material
  edit, and `references/quality-gate.md` already governs it: re-run both
  tiers on the changed artifact before its work is executed.

A `validation:` block also records `judge_model` and `judge_depth`. Read them,
do not act on them: an artifact gated in the `fast` lane is gated. If the human
decides a fast-lane PASS was not enough for a particular artifact, that is their
call to make explicitly, not a re-validation you start on your own.

If the human explicitly asks for a re-validation at implementation time,
run it — an explicit request outranks the default, the same way it does
everywhere else in this skill. What is forbidden is deciding to re-validate
on your own initiative because it felt safer.

## The worktree-and-subagent execution model

This skill's standing convention for execution is git worktrees plus fresh
subagent dispatch per task — not one option among several, the default.

**One worktree per stream.** `tasks.md` groups tasks into named streams
(`Stream 1A`, `Stream 1B`, ...) exactly where plan.md §2's DAG shows two
branches with no edge between them. Each such stream gets its own worktree,
checked out from the same base branch, so that streams running concurrently
never contend for the same working tree or risk one stream's half-finished
edit leaking into another's view of the files. Tasks *within* a stream run
sequentially in that stream's worktree, in `depends_on` order — a stream is
a single lane, not itself a source of parallelism. When a stream's tasks are
all `[x]`, merge its worktree back and tear it down; don't let worktrees
accumulate past the milestone that opened them.

**A fresh subagent per task, never a shared one.** Each task is dispatched
to a new subagent instance with a self-contained prompt containing exactly
four things and nothing else:

1. The task's own description and tags.
2. **The literal paths from its `[files: ...]` tag**, and the matching rows of
   `design.md` §9's File Map. The subagent is told where to write; it never
   searches for it.
3. The exact slice of `design.md` and/or `spec.md` the task implements — the
   section, contract, or BR/AC/EC ids the task line cites, not the whole
   document — **including the named symbols and signatures verbatim.** Give the
   subagent the extractor command rather than pasting the slice, so the text
   lands in its disposable context instead of the orchestrating one:

   ```bash
   python3 "$SDD"/scripts/sdd_extract.py \
     .specs/features/<feature>/design.md --section 3.1
   python3 "$SDD"/scripts/sdd_extract.py \
     .specs/features/<feature>/spec.md --ids BR-01,AC-02
   ```

   Never `cat` the whole artifact for this. A section is a fraction of the file,
   and — because context is re-read on every later turn — that fraction keeps
   paying for the rest of the session.
4. How its work will be verified.

When the dashboard is on, append one event line per dispatch
(`references/dashboard.md`) — a task moves from `[ ]` to `[/]` on disk, but the
minutes in between are invisible without it.

Points 2 and 3 are what make a small model safe here. A subagent on a
Haiku-class model does not fail loudly on a vague reference: it produces a
plausible path and a plausible function name, both wrong, and the failure only
surfaces at merge. Never send a task description that says "the validation
module" when `design.md` says `src/payments/split_validator.py`.

The subagent has no memory of any other task dispatch, this session's earlier
conversation, or how a sibling task in the same stream was implemented. This mirrors how this
plugin's own Plans 1–3 were built: read the task, dispatch fresh, verify
independently, never trust the subagent's self-report without checking. If
two tasks need to share context beyond what's in `design.md`/`spec.md`,
that's a sign the task boundary itself is wrong — fix the task split, don't
patch it by carrying session memory across dispatches.

**No-git fallback.** Worktrees require git. When the target repo has no git
history yet — which, as it happens, is exactly the situation this plugin's
own repo was built under — the engine falls back to sequential execution in
a single working copy: no parallel streams, no worktree isolation, and
verification happens at manual checkpoints after each task instead of via
a merge. The dependency graph and the fresh-subagent-per-task rule still
apply; only the filesystem isolation and the "streams run concurrently"
property are lost. Say explicitly when this fallback is in effect, the same
way Tier 1's absence gets flagged in `SKILL.md` Step 5 — a silently
degraded execution mode is as dangerous as a silently skipped gate.

## Model resolution: read, never re-decide

Every task line's `[Agent: <Role>]` tag names a role — Coder, Tester,
Reviewer, or Evaluator — never a model id. The model for that role was
already fixed when `plan.md` was authored, following the resolution order
in `references/artifact-plan-tasks.md` (repo convention, then the user's
explicit answer, then the agent's task-fit-driven suggestion confirmed by
the user, Anthropic preferred only on a genuine tie). Execution's only job
here is a lookup: read the role off the task tag, look up that role's
resolved model in `plan.md`'s `allocated_agents` block, and dispatch the
subagent on that model.

Execution never re-opens this decision — not to second-guess a choice that
looks off, not because a task turned out harder than its role's write-up in
plan.md §4 suggested, and not because a different model is more convenient
in the moment. If a role's already-resolved model genuinely looks wrong for
what the tasks are turning out to require, that's a blocker (see below), not
a silent substitution: surface it to the human rather than picking a
different model on the plan's behalf.

## Verifying before marking a task complete

A subagent finishing a task and reporting success is not evidence the task
is done — it's a claim. `SKILL.md`'s "Never do these" list says it plainly:
never mark a task `[x]` without running its tests. What "independent
verification" means depends on the task:

- **A Coder task** (implement the Split Validation Service, wire a
  controller, ...): the orchestrating agent — or a dedicated Reviewer-role
  subagent, per the task's own tags — actually runs the test suite the
  task was implemented against, reads the real diff, and confirms the
  tests that were red before the task are green after it, not just that
  *some* tests somewhere pass. A subagent's transcript saying "all tests
  pass" is not a substitute for running them.
- **A Tester/scaffolding task** (stand up a harness before the logic
  exists): verification confirms the harness actually exercises the AC/EC
  ids it claims to (spot-check that a harness written for BR-02 would in
  fact fail if BR-02 were violated), not merely that the test files exist
  and execute without error.
- **The coverage-verification task** (one per milestone, always
  `[REQUIRED]` — Task 1.6, 2.6, 3.3 in the worked example): this one can
  never be marked `[x]` by claim alone, full stop. The engine runs the
  project's real coverage tool against the milestone's changed code and
  compares the actual line/branch numbers to `plan.md`'s declared
  `coverage_threshold`. If the threshold is `none (behavioral coverage
  only)`, this task instead walks the milestone's AC/EC ids and confirms
  each one has a passing test tracing to it — still a check against
  something concrete, never "looks well-tested."
- **A Reviewer task** (static analysis, ADR conformance, milestone
  sign-off): verification means the orchestrating agent confirms the
  Reviewer subagent's findings against the actual artifact or code it
  reviewed — an ADR-conformance claim gets checked against the ADR's
  Compliance Verification section, not accepted because the subagent said
  "conformant."

Only after this independent check passes does the task line flip from `[/]`
to `[x]`. If it fails, the task stays `[/]` (or moves to `[!]` if it's now
blocked — see below) and does not get a second attempt from the same
subagent's context; dispatch fresh, same as the first attempt.

## `[REQUIRED]` vs `[OPTIONAL]`, and milestone completion

`[REQUIRED]` marks a task the milestone's gate depends on: the milestone is
not complete, and the next milestone does not start, while any `[REQUIRED]`
task under it is not `[x]`. `[OPTIONAL]` marks work that adds value but
doesn't gate anything — a nice-to-have metric, an extra log field — and can
be deferred or skipped outright. Skipping one is not silent, though: it
still needs a line in the Blocker Log (or an equivalent note) saying it was
deferred and why, so the tracker's history reflects a decision rather than
an omission.

A milestone is complete exactly when every `[REQUIRED]` task under it is
`[x]`, including its coverage-verification task — the coverage task is
`[REQUIRED]` by construction (see `references/artifact-plan-tasks.md`'s
"Execution criticality" principle), so a milestone can never close on
unverified coverage. `[OPTIONAL]` tasks left `[ ]` do not block the gate.

## The blocker protocol

When a task cannot proceed — an ambiguity the task description doesn't
resolve, a dependency that turns out to fail, a gap in `design.md` only
visible once implementation is underway — mark the task `[!]` and stop.
Do not guess past it, and do not quietly work around it by making a design
decision the task was never given authority to make; this is the same
zero-inference invariant `SKILL.md` applies everywhere else in this skill,
applied here to execution.

Write an entry in `tasks.md`'s "## Execution Scratchpad & Blocker Log"
section — this heading is linted verbatim, so it is never renamed or
restructured — naming:

- which task is blocked and since when,
- exactly what is blocking it (the specific ambiguity, the specific failing
  dependency, the specific gap),
- what decision or input would unblock it, concretely enough that the human
  reading the log can answer it in one pass rather than having to
  reconstruct the problem.

A blocked task is not abandoned; it is parked with a legible reason. Once
the human resolves it, the task resumes — either by updating `design.md`
or `spec.md` first (which, per `references/quality-gate.md`, means
re-running both gate tiers on whatever artifact was revised before the
task picks the change back up) or by the human supplying the missing
decision directly in the log.

## Session boundaries and resuming cold

All execution state lives in `tasks.md` on disk: the `[ ]`/`[/]`/`[x]`/`[!]`
marks, the frontmatter `progress: N/M`, and `current_milestone`. Nothing
about where execution stands is carried in a session's memory. A cold
session picks execution back up the same way `SKILL.md` Step 1 detects
state for any other phase: re-read `tasks.md` from disk, don't assume
anything from a prior conversation.

A task marked `[/]` (in progress) at the moment a session ends deserves
suspicion, not trust, on resume. `[/]` is not proof the work is underway or
even that it's real — the previous session may have died mid-task with the
mark left dangling, or a subagent may have been dispatched and never
verified before the session ended. Before continuing a `[/]` task, check
what actually exists: does the branch/worktree for that task show real
work, do any tests related to it exist and pass, is there evidence the task
was genuinely started rather than just flagged as started. Only then decide
whether to resume it in place, re-dispatch it fresh, or treat it as blocked
if the previous attempt left something inconsistent.

## Milestone checkpoints: report, don't silently continue

Finishing a milestone — every `[REQUIRED]` task `[x]`, coverage task
included — is a natural point to report to the human before the next
milestone's tasks start dispatching. This is a courtesy checkpoint, not
another zero-inference hard gate the way the spec-to-design or
design-to-plan transitions are: there is no separate artifact or Tier 1/2
score attached to a milestone boundary the way there is between phases.
Report what shipped, what (if anything) was deferred as `[OPTIONAL]`, and
any blockers that got resolved along the way, and give the human a chance
to redirect before momentum carries into the next milestone's streams. Do
not, however, silently roll from one milestone straight into the next
without that report — `SKILL.md`'s "Never do these" list is explicit that
continuing past a milestone gate without human sign-off is not allowed,
even though the gate here is lighter-weight than an artifact gate.

## Escalating bugs found mid-task

If executing one task surfaces a genuine defect outside that task's own
scope — a parser bug, a broken assumption in already-merged code, anything
that's wrong regardless of the task at hand — fix it immediately in-session
rather than deferring it to a future task or quietly coding around it. This
mirrors this plugin's own build history: a parser bug found while building
a template got fixed on the spot, not filed away. The one rule attached to
this is disclosure, not restraint: say explicitly that scope expanded and
why, so the human can see the fix happened and isn't left wondering why a
diff touches a file the task never mentioned. Silence is the failure mode
here, not the fix itself — an undisclosed scope expansion is indistinguishable
from scope creep even when the underlying fix was the right call.


## Closing out the plan — `plan.md` and `tasks.md` are ephemeral

`spec.md`, `design.md`, `test-catalog.md` and the ADRs are durable: they
describe what the system is, and they stay. `plan.md` and `tasks.md` are
not. They describe how one delivery was sequenced — milestones, streams,
`depends_on` edges, a checklist that is now entirely `[x]`. Once the work
has shipped, they answer a question nobody asks again, and leaving them in
the feature folder makes a shipped feature look like it has work still in
flight.

Both live in the feature's own folder alongside everything else:

```
.specs/features/<feature>/{discovery,spec,design,test-catalog,plan,tasks}.md
```

When the final milestone closes — every `[REQUIRED]` task `[x]`, coverage
task included:

1. **Mark them done.** `plan.md` gets `status: completed`, `tasks.md` gets
   `status: done`, both get today's `updated_at`. Do this first, so the
   state is correct on disk no matter what the human chooses next.
2. **Make sure nothing durable only lives here.** Walk `tasks.md`'s
   "## Execution Scratchpad & Blocker Log" before disposing of anything. A
   blocker whose resolution changed how the feature actually behaves belongs
   in `spec.md` or `design.md`, not in a file about to be deleted. Move it,
   then continue.
3. **Ask the human what to do with the pair.** Two options, and it is their
   call, never a silent cleanup:
   - **Delete** both files. Recommended when the repo has git — history
     keeps them, and the feature folder stays down to the artifacts that
     still describe the system.
   - **Archive** both into `.specs/features/<feature>/archive/`. Recommended
     when the repo has no git history, since deletion there is
     unrecoverable.
4. **Say which happened**, in one line, with the milestone summary.

Never delete or archive on your own initiative, and never do either while
any `[REQUIRED]` task is still `[ ]`, `[/]`, or `[!]` — an unfinished plan
being tidied away is indistinguishable from work silently dropped.
