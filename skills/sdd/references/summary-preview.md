# The Summary Preview

A full `spec.md` or `design.md` runs several hundred lines. Handing one to a
human as the first thing they ever see about the feature asks them to
validate the details before they have validated the shape — and a reviewer
who is still working out what the document is *about* will skim the part
that actually needed their judgment.

The summary preview fixes that ordering. Before the real artifact is
written, the agent shows a **15-line, plain-language sketch** of what it is
about to write. The human confirms the shape. Only then does the full
artifact get authored.

## Where it sits in the order

Fixed, and not negotiable:

```
interview to zero ambiguity  ->  preview (if the preference calls for one)  ->  full artifact  ->  gates
```

The preview comes **after** the interview, never instead of it. It restates
answers the user has already given; it never contains a guess the user has
not confirmed, and it is never a way to get something on the page before
the questions have been asked. `references/elicitation.md` explains why a
draft written *before* the interview is forbidden — a preview that smuggles
in an unasked assumption is that same forbidden draft at a smaller word
count.

## The preference, and how to read it

The preview is **not automatic**. Before authoring any artifact, resolve the
preference in this order and stop at the first that answers:

1. **`.specs/sdd.config.yml`**, key `summary_preview`, one of
   `always` | `never` | `ask`.
2. **No file, or the value is `ask`** — ask the user, this artifact only.

```bash
grep '^summary_preview:' .specs/sdd.config.yml 2>/dev/null
```

The config file is optional and is created only when the user asks for it:

```yaml
# .specs/sdd.config.yml
summary_preview: ask   # always | never | ask
```

When the answer has to be asked, ask it plainly and once:

> Want a 15-line plain-language summary of this spec first, or should I go
> straight to the full document?

Do not ask again for the same artifact after the user has answered, and do
not treat "yes" on one artifact as standing permission for the next one —
`always` in the config file is the only thing that carries forward. If the
user answers with a preference they clearly mean to keep ("always do this",
"stop asking"), offer to write it into `.specs/sdd.config.yml` rather than
remembering it for the session.

## The rules of the preview itself

- **Hard cap: 15 lines.** Not 16 with a note that it was hard to fit. If
  the content will not fit, the preview is doing too much — cut detail, not
  lines.
- **Chat only. Never a file.** The preview is a conversational check, not
  an artifact. It gets no frontmatter, no id, no path under `.specs/`.
- **Plain language.** No `BR-NN`/`AC-NN` ids, no Gherkin, no schema
  fragments, no framework names. A non-engineer stakeholder should follow
  every line. If a sentence needs a glossary to parse, rewrite it.
- **Say what is still unknown.** The preview is the cheapest possible place
  to discover that an open question was never asked. One line, at the end,
  listing anything still unresolved — or an explicit "nothing open."

A workable shape, inside the budget:

```
What this is about       — 2 lines, the outcome being bought
What it will do          — 4-6 bullets, one behavior each, plain words
What it will NOT do      — 2-3 bullets, the boundaries
Still open               — 1-2 lines, or "nothing open"
```

## The preview is never gated

This is the load-bearing rule and it is not a judgment call:

- **Never run `sdd_lint.py`/`sdd_lint.mjs` on a preview.** It has no
  frontmatter and no required sections; Tier 1 is meaningless against it.
- **Never dispatch a Tier 2 judge on a preview.** Not "quickly," not "just
  to check." A rubric written for a 300-line contract scores a 15-line
  sketch as catastrophically incomplete, which is true and useless.
- **The human is the only validator.** Their "yes, that's it" is the entire
  gate for this step.

The gates in `references/quality-gate.md` apply to the full artifact that
comes after, exactly as they always have. The preview does not shorten,
soften, or substitute for any of them.

## After the human responds

**Approved** — write the full artifact now, in one pass, per its own
authoring reference. The preview's content is a sketch the artifact expands,
not a section the artifact quotes.

**Corrections** — apply them, then show the corrected preview again. A
correction at this stage is the preview earning its cost; do not skip ahead
to the full document and fold the correction in silently, because the human
then has to re-find their own correction inside 300 lines to confirm it
landed.

**A correction that reopens a real unknown** — if the human's response
reveals a gap rather than a wording problem ("wait, what happens when two
people submit at once?"), that is not a preview edit. Go back to
`references/elicitation.md` and ask the question properly. Zero inference
applies here the same as everywhere else: the preview is a shorter document,
never a looser standard.
