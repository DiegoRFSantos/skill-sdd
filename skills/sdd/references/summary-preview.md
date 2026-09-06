# The Summary Preview, and `## 0. At a Glance`

A reviewer handed a 200-line contract as the first thing they ever see about a
feature validates the details before they have validated the shape — and
someone still working out what a document is *about* skims the part that
needed their judgment.

The fix is one 15-line plain-language sketch, written once, used twice:

- **Before the artifact exists**, shown in chat so the human can confirm the
  shape before 200 lines get written against it.
- **Inside the artifact**, as its `## 0. At a Glance` section, so the same 15
  lines are what any later reader meets first.

Same content, same cap. Write it once.

## Where it sits in the order

Fixed, and not negotiable:

```
interview to zero ambiguity  ->  preview (if the preference calls for one)  ->  full artifact  ->  gates
```

The preview comes **after** the interview, never instead of it. It restates
answers the user has already given; it never contains a guess the user has not
confirmed. `references/elicitation.md` explains why a draft written *before*
the interview is forbidden — a preview that smuggles in an unasked assumption
is that same forbidden draft at a smaller word count.

## The chat preview is optional; the section is not

The **chat** step is a preference. `## 0. At a Glance` is a required section of
`spec.md` and `design.md`, linted, cap enforced — it is written whether or not
the preview was shown.

Resolve the chat preference in this order, stopping at the first that answers:

1. **`.specs/sdd.config.yml`**, key `summary_preview`, one of
   `always` | `never` | `ask`.
2. **No file, or the value is `ask`** — ask the user, this artifact only.

```bash
grep '^summary_preview:' .specs/sdd.config.yml 2>/dev/null
```

The config file is optional and created only when the user asks for it:

```yaml
# .specs/sdd.config.yml
summary_preview: ask   # always | never | ask
```

When it has to be asked, ask plainly and once:

> Want the 15-line summary of this spec first, or straight to the full document?

Do not ask twice for the same artifact, and do not treat "yes" on one artifact
as standing permission for the next — `always` in the config is the only thing
that carries forward. If the user answers with a preference they clearly mean
to keep, offer to write it into `.specs/sdd.config.yml` rather than remembering
it for the session.

## The rules of the 15 lines

- **Hard cap: 15 content lines.** Blank lines and HTML comments don't count;
  the linter enforces this on the section. Not 16 with a note that it was hard
  to fit. If it will not fit, the summary is doing too much — cut detail, not
  lines.
- **Plain language.** No `BR-NN`/`AC-NN` ids, no Gherkin, no schema fragments,
  no framework names. A non-engineer stakeholder should follow every line.
- **Say what is still unknown.** One line at the end naming anything
  unresolved, or an explicit "nothing open." This is the cheapest possible
  place to discover that a question was never asked.

A workable shape inside the budget:

```
What this is about       — 2 lines, the outcome being bought
What it will do          — 4-6 lines, one behavior each, plain words
What it will NOT do      — 2-3 lines, the boundaries
Still open               — 1 line, or "nothing open"
```

## Never gated, in either form

This is load-bearing and not a judgment call:

- **Never lint a chat preview.** It has no frontmatter and no sections; Tier 1
  is meaningless against it.
- **Never dispatch a Tier 2 judge on the preview or on `## 0. At a Glance`.**
  Not "quickly," not "just to check." A rubric written for a 200-line contract
  scores a 15-line sketch as catastrophically incomplete, which is true and
  useless. Tier 1 checks the section's cap and nothing else about it; no
  rubric criterion scores its content.
- **The human is the only validator of the summary.** Their "yes, that's it"
  is the entire gate for this step.

The gates in `references/quality-gate.md` apply to the rest of the artifact
exactly as they always have.

## After the human responds

**Approved** — write the full artifact now, in one pass. The approved 15 lines
become `## 0. At a Glance` verbatim; do not paraphrase them into something new,
and do not repeat them again further down the document.

**Corrections** — apply them, show the corrected preview again. A correction
here is the preview earning its cost; do not skip ahead and fold it into the
full document silently, or the human has to re-find their own correction inside
200 lines to confirm it landed.

**A correction that reopens a real unknown** — if the response reveals a gap
rather than a wording problem ("wait, what happens when two people submit at
once?"), that is not a preview edit. Go back to `references/elicitation.md` and
ask the question properly. Zero inference applies here the same as everywhere:
the summary is a shorter document, never a looser standard.

## Keeping it true

`## 0. At a Glance` describes the artifact it sits in. A material edit to the
artifact means re-reading those 15 lines and correcting them if they now
describe something that is no longer there — the same rule that invalidates the
`validation:` block, applied to the summary. A stale At a Glance is worse than
none: it is the one section a reader trusts without checking.
