# Writing a Spec

## The five core pillars

**Strict Abstraction Isolation.** A spec describes WHAT the system must do
and WHY, never HOW. No protocol names, no storage engines, no framework or
library names, no route shapes, no SQL. The isolation test is the mechanical
check for this, and it applies verbatim: "If the entire technical stack were
replaced, would this spec still be 100% valid with zero edits? If not, the
leak is the thing to remove." Run every sentence through it before it goes
in — if swapping the database, the transport, or the language would force an
edit, the sentence is describing HOW, and it belongs in `design.md` instead.

**Explicit Non-Goals.** Every capability the spec deliberately excludes gets
listed, and every exclusion carries a reason — not a bare "not doing X." The
reason is what keeps the exclusion from silently reversing itself later:
without it, nobody reviewing a future change knows whether the boundary was
a considered decision or an oversight. A non-goal without a reason is
indistinguishable from a gap.

**Binary Acceptance Criteria.** Every `AC` is Gherkin (`Given`/`When`/`Then`)
and every outcome it asserts is pass or fail — never "should generally,"
"in most cases," or "as appropriate." If an acceptance criterion can't be
run against a system and get a yes-or-no answer, it isn't one yet; tighten
it or split it until it is.

**Edge Case & Failure Mapping.** The happy path is the easy 20% — boundary
values, concurrent access, timeouts, and validation failures are the other
80%, and they're where real systems actually break. Every spec must map
these deliberately, not leave them to be discovered in production.

**Ubiquitous Domain Language.** Every term used in a `BR`, `AC`, or `EC` must
already be defined in §2 before it's used anywhere else. If a term shows up
in a business rule that isn't in the glossary, either the glossary is
incomplete or the rule is reaching for a concept nobody has agreed on yet —
both block the rule from being trustworthy.

## Id conventions

- `BR-NN` — Business Rules (§5)
- `AC-NN` — Acceptance Criteria (§6); each one names the `BR` it proves
- `EC-NN` — Edge Cases & Failure Modes (§7)
- `Q-NN` — Open Questions (§10)

Numbering is per-artifact, not per-project: `BR-01` in this spec has nothing
to do with `BR-01` in another feature's spec. Numbering does not reset
across features and does not need to stay globally unique — only unique
within its own artifact.

## The traceability rule

Every `BR` and every `EC` in the spec must be referenced by at least one
`AC` in §9's Traceability Matrix. There is no exception for rules or edge
cases that feel "obviously" covered — if it isn't in the matrix, it isn't
traced.

An unreferenced `BR` or `EC` means one of two things, and both need fixing
before the spec can move to `active`:

- The rule or edge case is untestable as written — it needs to be rewritten
  until it can be proven by a concrete Given/When/Then.
- The rule or edge case is testable, but the traceability table has a gap —
  the `AC` needs to be added, or an existing `AC` needs to be linked to it.

## Authoring checklist

Work through this before handing the spec to the linter — it mirrors the
Tier 1 checks the linter runs, so catching the problem here is faster than
catching it there.

- [ ] All 11 section headings are present, in order, and match the template
      verbatim — headings are matched literally, not fuzzily.
- [ ] No `POST`, `GET`, `SQL`, framework names, or database names appear
      anywhere in the body (frontmatter is exempt).
- [ ] No `TODO`, `TBD`, `etc.`, or empty `{}` appears anywhere.
- [ ] Every `BR` and every `EC` is covered by at least one `AC` in the §9
      Traceability Matrix.
- [ ] §10 Open Questions has no rows before requesting `status: active` —
      an active spec cannot carry an unresolved question.
