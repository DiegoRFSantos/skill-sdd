# Writing a Design

## The five pillars

**Deterministic Contracts.** Every request, response, error, and event
schema in §3 must be complete and typed: required fields, concrete types,
constraints (min/max/regex/enum) where they matter, and a matching error
schema with domain error codes — never a placeholder shape like `{ data:
object }` and never a field typed `any`. A schema someone could implement
two different ways is not yet a contract; if a reviewer has to guess a
constraint, tighten the schema until they don't.

**Visual Sequence Mapping.** §4 exists because prose describes temporal
execution ambiguously and a Mermaid `sequenceDiagram` doesn't. Every flow
worth documenting names its real participants (components from §1.1, not
generic actors), shows every step in order with no skips, and traces back to
the spec ids (`BR`/`AC`/`EC`) it realizes. If a step would surprise someone
reading the diagram cold, it's the step most worth drawing.

**Explicit Data Lifecycle.** §2 pairs a real schema (§2.1 — keys, types,
nullability, indexes) with a complete state machine (§2.2 — every state,
every event, every guard condition, including terminal states). A schema
without a state machine tells you what a record looks like but not how it's
allowed to change; a state machine without guard conditions tells you the
shape of the graph but not what's actually enforced at each edge.

**Tactical Resilience & Security.** §5 is where "reasonable" and
"appropriate" are banned words. Idempotency key strategy, RBAC scopes, retry
counts and backoff curves, timeouts, and circuit-breaker thresholds are all
literal numbers with units — `5 retries, 500ms initial backoff, doubling,
capped at 8000ms`, not "a sensible retry policy." A number that isn't
written down is a number every implementer picks differently.

**Observability by Design.** §6.1 fixes the structured log field names and
metric keys before the first line of implementation code is written —
`split_id`, `total_allocation_percent`, `split.rejected.count{error_code}`,
not "we'll log the relevant fields." Naming these in the design, not during
implementation, is what makes two independently-built components emit
comparable telemetry.

## The traceability rule

Every `BR` and every `EC` from the spec must appear in §8's Traceability
table, mapped to the concrete component, contract, or flow step that
implements it. This is the design-side mirror of the spec's own
traceability rule (every `BR`/`EC` must be covered by an `AC`) — together
they form an unbroken chain from business rule to acceptance test to
implementing mechanism. A `BR` or `EC` with no row in §8 means one of two
things, and both block the design from being trustworthy: the rule was
designed for but the table wasn't updated, or the rule was never actually
addressed and the design is incomplete.

## The boundary against ADRs

System-wide, cross-cutting standards — which message broker the platform
uses, the auth protocol every service speaks, the concurrency strategy
applied across features — belong in `.adrs/`, not in a design. A design
consumes those decisions (§7 ADR Conformance records how) but never
re-litigates them. Conversely, feature-local schemas, endpoint contracts,
event payloads, and state machines belong in the design, never in an ADR —
an ADR that embeds one feature's schema has smuggled a design decision into
a document meant to outlive any single feature.

When in doubt, ask: would this decision matter to a feature that hasn't
been imagined yet? If yes — a storage engine choice, a broker choice, a
retry-budget standard applied platform-wide — it's an ADR. If the decision
only makes sense in the context of this one capability's data and contracts,
it's a design.

## Authoring checklist

Work through this before handing the design to the linter — it mirrors the
Tier 1 checks the linter runs, so catching the problem here is faster than
catching it there.

- [ ] All 9 section headings are present, in order, and match the template
      verbatim — headings are matched literally, not fuzzily.
- [ ] Every conditional subsection (§1.2, §3.3, §3.4, §6.2) is present with
      either real content or a `_Not applicable: <reason>_` line — never
      silently omitted, and never left with just the heading and no
      resolution either way.
- [ ] No field anywhere is typed `any`, and no schema is a bare `object`
      with no properties — both are hard-blocked by the linter's
      `DESIGN_LOOSE_TYPE_ANY` and `DESIGN_BARE_OBJECT` rules.
- [ ] §4 contains at least one Mermaid `sequenceDiagram` with named
      participants and no skipped steps.
- [ ] §5's resilience numbers are literal values with units (`5 retries`,
      `3000ms`, `10 failures / 60s window`) — never "reasonable,"
      "appropriate," or "as needed."
- [ ] §6.1 names concrete structured log fields and metric keys, not a
      description of what will eventually be logged.
- [ ] Every `BR` and every `EC` from the referenced spec has a row in §8's
      Traceability table.
- [ ] `spec_ref` in the frontmatter resolves to an existing `spec` artifact,
      and every id in `dependencies` resolves to an existing `adr` artifact.


## Written to pass

Apply these while writing, so the gate confirms rather than corrects.

- **Contracts name their symbols.** Not "the validation service" —
  `SplitValidator.validate(payment, allocations) -> ValidationResult`. Not "an
  error shape" — the named enum and its members. An executing agent should
  never have to choose a name that the design should have given it.
- **§9's File Map lists every file the feature touches**, by literal
  repo-relative path, marked new or modified. A file that does not exist yet is
  still written out in full: the task that creates it needs to be told exactly
  where. This is what `tasks.md`'s `[files: ...]` tags draw on.
- **Every interaction flow states its failure branches.** Timeout, partial
  failure, duplicate submission, the dependency being down. A flow with only a
  happy path scores zero on that criterion, and correctly so.
- **Resilience numbers are literal, with units.** `5s timeout`, `3 retries with
  exponential backoff`, `10 failures / 60s`. Never "reasonable," "appropriate,"
  or "as needed."
- **Observability names concrete signals** — the metric key, the log field —
  not a description of what will eventually be logged.
- **Conditional sections are triggered or explicitly marked
  `_Not applicable: <reason>_`.** Silently omitting one is the failure mode
  this rule exists to catch; the reason has to be real, not "not needed."
- **Cross-cutting concerns defer to an ADR by reference.** If you find yourself
  deciding auth, idempotency, or a concurrency strategy inline, that is an ADR,
  not a design section.
- **Schema changes are backward compatible, or the migration path is stated.**

### The one diagram

One per artifact, from this set, each with its own cap. Over cap, the diagram
is **dropped, not shrunk** — a diagram that needs scrolling is worse than none,
and exceeding the cap usually means the artifact covers more than one feature.

| Diagram | Syntax | Cap |
|---|---|---|
| Flowchart, control flow with failure edges | `flowchart` | 12 nodes |
| Data flow | `flowchart` with labeled edges and store nodes | 12 nodes |
| C4, context or container level only | `C4Context` / `C4Container` | 10 elements |
| Architecture | `architecture-beta` | 12 nodes |
| Sankey, volume or flow distribution | `sankey-beta` | 10 links |

`sankey-beta` and `architecture-beta` are beta in mermaid and C4 support is
experimental; renderers disagree about all three. If the repo's own viewer does
not render the type you picked, fall back to a `flowchart` rather than shipping
a fenced block that displays as an error.

A diagram is an index into the contracts and tables, never a place a
requirement lives on its own. If a fact appears only in the diagram, it is not
specified.
