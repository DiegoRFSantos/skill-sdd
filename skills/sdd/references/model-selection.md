# Choosing a Model per Role

`plan.md` assigns four roles — Coder, Tester, Reviewer, Evaluator — and
`references/quality-gate.md` needs a judge model. **Never guess any of them,
and never present the question as a blank.** "Which model do you want for the
Coder role?" is a question that costs the human research; a recommendation with
one line of reasoning is a question they can answer in seconds.

The order below is fixed.

## Step 1 — Ask what they can actually reach

A recommendation naming a model the human cannot use is worse than no
recommendation. Ask first, once, in one message:

> Which models do you have access to? (Whatever your agent harness provides,
> an API key, Bedrock/Vertex/Foundry, a non-Anthropic provider, or a mix — and
> any your org has ruled out.)

Check the repo before asking — `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or a
prior `plan.md` may already answer it, and re-asking a settled question is its own waste.

## Step 2 — Look up what exists now; do not answer from memory

**Model names, prices, and capabilities change faster than this file does.**
Anything written here is a snapshot, not a fact. Before recommending:

- For Claude models, invoke the **`claude-api` skill**, which carries the
  current id/pricing/capability table and is maintained for that purpose. Its
  ids are exact strings — never append a date suffix to one.
- For a non-Anthropic provider the human names, search for its current lineup
  rather than recalling one.

Getting this wrong is not cosmetic: a stale model id fails the dispatch, and
stale pricing sends the human's budget somewhere they did not agree to.

## Step 3 — Match the role to what the role actually does

This is the part that does not go stale. Each role has a different failure
mode, and the failure mode picks the tier.

| Role | What it does | Dominant risk | Points toward |
|---|---|---|---|
| **Coder** | Implements a task against a named contract, with the paths and symbols already given | Subtly wrong multi-rule interaction that tests do not catch | Top tier for domain logic and anything touching an invariant; a mid tier is genuinely fine for scaffolding, DTOs, migrations, and wiring, where the design leaves nothing to decide |
| **Tester** | Writes tests from AC/EC ids that already exist | A harness that passes without actually exercising the rule | Mid tier for volume; step up when the test design itself is the hard part (concurrency, boundaries, failure injection) |
| **Reviewer** | Catches what Coder and Tester missed | A false negative — the whole job is not missing things | Top tier. It runs rarely, so cost barely moves, and a cheap reviewer defeats the point of having one |
| **Evaluator** (Tier 2 judge) | Applies a fixed rubric to artifact text | Rubber-stamping a vague artifact, or inventing a deficiency | Mid tier at high effort. The rubric supplies the structure, so this rewards careful reading over creativity — and it is the highest-frequency role, so it is where model choice moves the bill most |

Two things that matter as much as the tier:

- **Effort is a second dial.** On models that support `output_config.effort`, a
  mid-tier model at `high`/`xhigh` often beats a top-tier model at `low`, for
  less. Recommend a tier *and* an effort, not a tier alone.
- **Context window.** A judge reads a whole artifact plus a referenced one.
  Check the window covers that before recommending; a 200K-context model is
  fine for SDD artifacts, which are budgeted in the low hundreds of lines.

## Step 4 — Propose, with one line of reasoning each

Give a concrete recommendation per role, each justified in one line, and make
it trivially overridable. Never present four blanks.

> Based on what you have access to, I'd suggest:
> - **Coder** — <model>: the domain-logic tasks here touch BR-01..03 together, which is where a cheaper model tends to miss an interaction.
> - **Tester** — <model>: 9 of 16 tasks are harness scaffolding against ids that already exist; this is high-volume, low-ambiguity work.
> - **Reviewer** — <model>: it runs four times total, and its only job is catching what the others missed.
> - **Evaluator** — <model> at high effort: the rubric does the structuring, and this is the role that runs most often.
>
> Say the word and I'll write these into `plan.md`, or swap any of them.

## Two different name-spaces — do not mix them

- **`plan.md`'s `allocated_agents`** records what the human chose, in whatever
  form they gave it.
- **Dispatching a subagent** may take a different form of name than an API id.
  Claude Code's `Agent` tool, for instance, takes a short family name
  (`sonnet`, `opus`, `haiku`), and a full API id passed there will not resolve.
  Check what your harness expects before dispatching.

Record the human's choice, and translate at dispatch time. Do not silently
rewrite what they said into the other form.

## What never changes

- **The human decides.** Recommend, with reasoning, and write nothing into
  `plan.md` without confirmation — `SKILL.md`'s Human Decision Supremacy
  invariant covers model choice explicitly.
- **Never downgrade to save money on your own initiative.** Cost is the
  human's trade to make. Surface it; do not make it for them.
- **Prefer an Anthropic model only on a genuine tie** in suitability. If a
  non-Anthropic model is the better fit for a role and the human has access,
  say so.
- **Re-check on a new plan.** A model recommended six months ago may not be
  the right one now, and may not exist.
