# Writing a Plan and Tasks Tracker

## Where they live, and how long they live

Both files go in the feature's own folder, beside the artifacts they
execute:

```
.specs/features/<feature>/plan.md
.specs/features/<feature>/tasks.md
```

There is no separate `.specs/plans/` tree. Create the folder only if it does
not already exist — never scaffold it ahead of writing the file.

Unlike `spec.md` and `design.md`, this pair is **ephemeral**. It describes
how one delivery was sequenced, not what the system is, and once every
milestone has shipped it answers a question nobody asks again. The disposal
protocol — mark done, rescue anything durable out of the blocker log, then
let the human choose delete or archive — is in `references/execution.md`
under "Closing out the plan." Write the pair knowing it is temporary: a
decision that needs to outlive the delivery belongs in `spec.md`,
`design.md`, or an ADR, not in a milestone description.

## The five delivery principles

**Vertical delivery slicing.** Every milestone in plan.md §1 must be a
functional increment a stakeholder could recognize as shipped value — "an
organizer can submit a split and have it validated end-to-end" — never a
horizontal technical layer like "all the database work" or "all the API
work." A milestone that only exists because it groups similar-looking code
(every migration, every controller) delivers nothing testable on its own
and cannot be gated on real acceptance criteria. If a milestone's gating
criteria can't cite an AC or EC id from spec.md, it is probably sliced by
layer, not by value, and needs to be re-cut.

**Explicit `depends_on`.** Every task line in tasks.md carries a
`[depends_on: ...]` tag naming the exact upstream task ids it needs, or
`none`. An agent picking up a task must never infer readiness from a
milestone label or task ordering on the page — only from every id in its
`depends_on` list being marked `[x]`. This is what makes tasks.md safe to
execute out of reading-order: the dependency list is the only contract that
matters, and the linter's `tasks_depends_on` check rejects any id that
doesn't resolve to a real task, while `tasks_cycles` rejects any circular
wait.

**Explicit `[files: ...]`.** Every task line also carries the literal
repo-relative paths it may touch, drawn from `design.md` §9's File Map. The
linter's `tasks_tags` check blocks a task line without one, the same as a
missing `[Agent:]` or `[REQUIRED]`. A task dispatched to a fresh subagent — with
no session memory, often on a small model — has no way to find out where it is
meant to write except by being told; an agent left to infer a path produces a
plausible one that does not exist.

**Deterministic concurrency.** Two tasks may run in parallel exactly when
neither is in the other's `depends_on` closure. Group such tasks into
named streams (Stream 1A, Stream 1B, ...) in tasks.md and show them as
independent branches in plan.md §2's DAG, so an agent orchestrating
execution can read the graph once and dispatch every ready stream at once
instead of discovering parallelism by trial and error.

**Execution criticality.** `[REQUIRED]` marks a task that blocks its
milestone's gate — the milestone cannot be considered complete, and the
next milestone cannot start, while any `[REQUIRED]` task is not `[x]`.
`[OPTIONAL]` marks a task that can be deferred past the gate without
blocking downstream work (e.g. a nice-to-have metric). Coverage-verification
tasks (see "Resolving the coverage threshold" below) are always
`[REQUIRED]` — a coverage gate that can be silently skipped is not a gate.

**Pre-implementation test scaffolding.** The test suites in plan.md §3 —
and the corresponding scaffolding tasks in tasks.md — must exist and be
committed *before* the business logic they test. Each harness is derived
directly from spec.md's Gherkin scenarios (§6 Acceptance Criteria): one test
per AC id at minimum, plus the boundary and validation cases named in §7
Edge Cases. Writing the test first is not a style preference here — it is
what makes "Coder implements against a red suite, agent verifies suite goes
green" possible as a mechanical, unambiguous completion signal.

## Deriving milestones from design.md

Read design.md §1.1's Component Inventory and §3's Contracts before
drafting plan.md §1. A milestone should map to a coherent slice of those
components and contracts that can be exercised together — for example
"the Split Validation Service satisfies BR-01..03 against a persisted Split
row" is one milestone because it is independently testable (a unit harness
can prove it without the API existing yet); "the SubmitSplit contract is
live with idempotency and expiry enforcement" is a different milestone
because it adds a new externally-observable capability (a client can now
call the API safely). Do not create a milestone named after a single
component or a single technology (a "Milestone 1: all the database work"
migration-only slice, for instance) — if a milestone's own gating criteria
would only ever be checked by inspecting schema DDL rather than by an AC/EC
id passing, merge it into the milestone that actually delivers behavior on
top of it.

## Building the DAG and identifying parallel streams

Walk design.md's component dependency edges (§1.1's "Depends on" column)
and spec.md's BR/EC ids together to list every unit of work, then draw the
edge `A --> B` in plan.md §2's Mermaid `graph TD` whenever B's `depends_on`
names A. Two tasks belong in the same parallel stream — drawn as sibling
branches with no edge between them — exactly when both of the following
hold: (1) neither task is in the other's `depends_on` closure, direct or
transitive, and (2) they do not modify the same files (e.g. two tasks that
both edit the same API controller are sequential even if neither formally
depends on the other, because running them concurrently risks a merge
conflict — see plan.md §2's Concurrency Rules for a worked instance with
the idempotency filter and expiry-window tasks). Render each milestone gate
as its own node (a `{{...}}` hexagon in Mermaid) so the diagram shows, at a
glance, that nothing downstream of a gate can start before every
`[REQUIRED]` task upstream of it is `[x]`.

## Resolving the coverage threshold

`coverage_threshold` in plan.md's frontmatter is never defaulted silently.
Resolve it in this fixed order, stopping at the first source that applies:

1. **Repo convention** — check `AGENTS.md`, `CLAUDE.md` or `GEMINI.md` for a stated
   coverage policy (a line/branch percentage, a scope, or an explicit
   statement that the repo does not gate on coverage). If found, use it
   verbatim and note the source.
2. **The user states it explicitly** — ask, and record exactly what they
   say.
3. **The agent asks** — if neither of the above resolves it, this is a
   planning-time question the agent must put to the user before `status`
   can move past `draft`; it is not a value the agent picks on its own.

Declining a percentage threshold entirely is a valid, recordable answer:
set the block to `coverage_threshold: none (behavioral coverage only)`
rather than inventing a number. What is not valid is leaving the key out of
the frontmatter, or filling in a percentage nobody actually decided on —
the `plan_coverage_threshold_declared` check exists specifically to catch a
plan that skipped this decision. Once resolved, the threshold is enforced
mechanically: tasks.md carries one `[REQUIRED]` coverage-verification task
per milestone (see plan.md's Task 1.6, 2.6, 3.3) so the number is checked
at the gate, not remembered — or forgotten — after the fact.

## Authoring the test catalog

`test-catalog.md`'s `TC` rows are derived from the `AC` and `EC` ids
already established in spec.md — never invented independently. For each
`AC`/`EC` id worth a human sign-off, add one `TC` row citing it in the
`Covers` column (see templates/test-catalog.md §2 for the exact table
shape). As templates/test-catalog.md states directly: this catalog "is
deliberately NOT exhaustive — it does not attempt to enumerate every input
combination, boundary, or malformed-value variant." Capture MAIN scenarios
only — the ones carrying business or risk weight, the ones a stakeholder
would want to see agreed on before implementation starts. Exhaustive case
enumeration (every malformed-value variant, every combinatorial edge)
belongs in the test code the Tester agent writes against plan.md §3's
harnesses, not in this catalog. If a candidate `TC` row exists only to
inflate a coverage number rather than to record a scenario worth a human's
attention, it does not belong here.

## The model-resolution order and rule

No template in this plugin ever hardcodes a model id — not
`claude-3-7-sonnet`, not `gpt-4o`, not any other literal version string.
`plan.md`'s `allocated_agents` and §4 table instead carry a placeholder
token per role (`<model-for-implementation>`, `<model-for-test-authoring>`,
`<model-for-review>`, `<model-for-tier-2-judge>`) with the resolution rule
documented inline as a YAML comment. Resolve each role's actual model in
this fixed order, stopping at the first source that applies:

1. **Repo convention** — `AGENTS.md`, `CLAUDE.md` or `GEMINI.md` names a required or
   preferred model for this role or for the repo generally. If present,
   use it and note the source; this always wins over the agent's own
   judgment.
2. **The user's explicit answer** — if asked ("which model should the
   Coder run as?") and the user states one, use exactly what they said.
3. **The agent's suggestion, offered for confirmation** — only if neither
   of the above resolves it. The suggestion must be driven by what the
   tasks in *this specific plan* actually build, not by habit or a
   previous plan's choice:
   - A role doing **mechanical scaffolding** (migration files, DTO
     boilerplate, fixture generation — e.g. Task 1.1, 2.2 above) can
     usually run on a smaller, cheaper model; the work is low-ambiguity
     and easy to verify mechanically.
   - A role doing **domain logic** (the Split Validation Service, the
     idempotency filter — e.g. Task 1.4, 2.4) needs enough reasoning
     capability to get multi-rule interactions and ordering right the
     first time, since a subtle bug here is exactly the kind a cheap model
     tends to miss.
   - A role doing **contract/schema design** (API request/response/error
     shapes, event schemas) benefits from a model strong at precise,
     typed output where an ambiguous field is a real downstream cost.
   - A role doing **review** (static analysis, ADR conformance, gate
     scoring — e.g. Task 3.4, the Evaluator role) benefits from a model
     with strong judgment and low false-negative rate, since its entire
     job is catching what the Coder/Tester missed.
   Weigh capability against cost per role using that breakdown, and prefer
   an Anthropic model on a genuine tie in suitability — but the choice is
   never restricted to Anthropic; if a non-Anthropic model is the better
   fit for a role, suggest that instead. State the justification for each
   suggested role in one line, so the user can confirm or override it
   quickly rather than re-deriving the reasoning themselves.

See `references/model-selection.md` for the full procedure: ask what the human
can actually reach, look up what currently exists rather than answering from
memory, match each role to its dominant failure mode, and propose a concrete
model per role with one line of reasoning. **Never present the question as four
blanks** — a bare "which model for the Coder role?" makes the human do the
research, which is the opposite of recommending.

Nothing is ever written into `plan.md`'s `allocated_agents` without the
user's confirmation. The agent may propose a model per role; it may never
decide on the user's behalf and silently commit that decision to the plan.

## Written to pass

- **Milestones are independently shippable.** Each delivers business value on
  its own and can be verified without the next one. A milestone sliced by
  technical layer ("all the models," then "all the controllers") is the failure
  mode this criterion exists to catch.
- **Every task has one verifiable outcome**, an `[Agent: Role]` tag, a
  `[REQUIRED]`/`[OPTIONAL]` tag, and a `[files: ...]` tag. Two outcomes in one
  line means neither can be marked done honestly.
- **`[files: ...]` lists literal repo-relative paths**, drawn from `design.md`
  §9's File Map. Every task is dispatched to a fresh subagent with no session
  memory — often a small model — and a subagent that has to guess a path
  invents one. The tag is both the instruction and the blast radius.
- **Task descriptions name symbols, not descriptions.** "Implement
  `SplitValidator.validate` per design §3.1", not "implement the validation
  logic."
- **`coverage_threshold` is declared** and every milestone has a coverage
  verification task, `[REQUIRED]` by construction.
- **The blocker protocol names who decides and what triggers escalation.**
  "The team will figure it out" is not a protocol.
- **The DAG in §2 is milestone-level only.** Per-task ordering lives in
  `tasks.md`'s `depends_on` tags, where the linter checks it for cycles and
  dangling references. Drawing it twice guarantees one copy goes stale, and a
  per-task graph does not fit on a screen.

Optional single diagram in `plan.md`: a `gantt` (cap 20 bars) for a schedule,
or a `flowchart` milestone DAG (cap 12 nodes). Over cap, it is dropped, not
shrunk.

## Hand off to a fresh session before executing

When `tasks.md` passes its gate, **do not start executing in this session.**
The session that ran discovery, the interview, and four gate rounds is carrying
a context window full of material implementation does not need — and every task
dispatch inherits that weight.

Print the handoff, then stop:

```
tasks.md gated — <N> milestones, <M> tasks, coverage threshold <T>.

Implementation runs best in a fresh session, so the context window is not
carrying the discovery transcript. Copy this into a new session:

  Execute the SDD plan at .specs/features/<feature>/tasks.md
```

Then offer to continue here instead, in one line. This is a recommendation, not
a refusal: a three-task plan may not be worth a new session, and that is the
human's call. `SKILL.md` Step 1's state detection reconstructs everything a cold
session needs from disk, so nothing is lost either way and no state has to be
passed by hand.
