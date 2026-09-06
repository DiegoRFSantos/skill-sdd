# Context Economy

One relationship explains nearly all of what a session costs:

> **cost ≈ turns × context size**

Everything in context is re-read on every subsequent turn. Measured on a real
session of this skill: 330 turns against an average 206k-token context produced
**66.5 million cache-read tokens — 98.8% of everything billed.** Fresh input was
0.7%. Output was 0.4%.

The consequence that matters: **a file read is not a one-time cost.** A
2,400-token artifact entering context at turn 50 of a 330-turn session costs
2,400 × 280 ≈ 672,000 cache-read tokens, not 2,400. Everything below follows
from that.

## The rules, in order of payoff

**1. Never read a file you are about to hand to a subagent.**
A subagent has its own disposable context. Content it reads dies with it;
content *you* read is re-read for the rest of the session. Give the path, or
give the extractor command. This is why `references/quality-gate.md` hands
judges a path instead of pasted text, and why `references/execution.md` gives
task subagents an `sdd_extract.py` command instead of a slice.

**2. Extract, do not `cat`.**

```bash
python3 "$SDD"/scripts/sdd_extract.py design.md --outline
python3 "$SDD"/scripts/sdd_extract.py design.md --section 3.1
python3 "$SDD"/scripts/sdd_extract.py spec.md --ids BR-01,AC-02
```

`--section 3.1` on the worked design returns 485 characters against the file's
7,048 — a 14x reduction that then keeps paying every turn. Use `--outline`
first when you do not know which section you want; it costs almost nothing and
stops you reading the file to find out.

**3. Grep before you read.** `grep -n '^## ' file` costs a few tokens and often
answers the question. `SKILL.md` Step 1 already detects state with `grep` rather
than reading artifacts, for exactly this reason.

**4. Read late.** A file read at turn 300 of 330 is re-read 30 times. The same
file at turn 20 is re-read 310 times. Deferring a read until the turn you
actually need it is worth more than making the file smaller.

**5. Fresh sessions at phase boundaries.** A new session resets context to near
zero. All SDD state is on disk (`SKILL.md` Step 1), so nothing is lost — this is
the whole argument behind the implementation handoff in
`references/artifact-plan-tasks.md`, and it applies at every phase boundary, not
only before execution.

**6. Fewer turns.** Turns are the other multiplier. Batch independent tool calls
into one message; make one considered edit instead of five small ones. Halving
turns halves the bill as surely as halving context.

**7. Cut output where it is not read.** Output bills highest per token. The
terse judge contract in `references/quality-gate.md` — scores only, prose only
for criteria below max — exists for this, as does `SKILL.md`'s communication
contract.

## What does not work

**Compressing artifacts.** Any encoding an agent must expand to use puts the
full text in context anyway, plus the turn spent expanding it. Minified,
gzipped, base64, or a private shorthand: all cost more than the plain file.
Write short, do not write compressed.

**Compressing what the human types.** Measured on the same session: every human
message together came to 3,389 tokens, 0.005% of the total. There is nothing to
win, and a misread instruction costs one wrong turn — which at a 200k context is
roughly sixty times the entire message history. Ask for more words from a human,
never fewer.

**Skipping the gate to save tokens.** A defect found at implementation costs the
tasks built on it. This is an optimization that spends real money to save
pennies.

## The boundary reset — offer it after every gated artifact

A gated artifact is a natural place to throw the context away, because
**everything durable is now in the file.** The interview, the drafting, the
judge's punch list, the rounds of correction — none of it is needed to write the
next artifact, and all of it is re-read on every remaining turn if it stays.

The arithmetic, measured: rebuilding after a reset at the spec→design boundary
costs about 6,000 tokens (the gated `spec.md`, `references/artifact-design.md`,
`templates/design.md`). Carrying the authoring context forward instead means
100k+ per turn, for every turn that follows. The reset pays for itself
immediately and then keeps paying.

**The agent cannot reset its own context — the human runs the command.**
Name whatever their harness uses; in Claude Code that is `/clear` (drop
everything) and `/compact` (summarize and keep the thread). After
writing the `validation:` block on any artifact, get the real number first — the
agent cannot read its own context size, so this reads the live transcript:

```bash
python3 "$SDD"/scripts/sdd_status.py --context --repo-root .
```

Then offer the reset in one line, **with the estimate attached**, and stop:

```
spec.md — Tier 1 pass, Tier 2 94 PASS (1 round).

Context is at ~221k/turn. Everything is on disk, so clearing here saves
roughly 21.5M tokens over the next 100 turns (rebuild costs ~6k).
  /clear     then: "continue the SDD design for <feature>"
  /compact   if you would rather keep the thread

Or say continue and I'll carry on as-is.
```

**Always attach the number.** A recommendation without one is advice the human
learns to skip; "this saves ~21M tokens" is a decision they can make in a
second. If the transcript is unreadable, say the reset is available and skip the
estimate rather than inventing one.

Which one:

- **A full reset** (`/clear` in Claude Code) at a phase boundary — spec done, design done, plan done. State
  detection (`SKILL.md` Step 1) rebuilds everything needed from disk, so nothing
  is lost. This is the default recommendation.
- **A compaction** (`/compact` in Claude Code) mid-phase, when an interview is still open and the thread
  matters more than the tokens. It costs a summarization pass and keeps some
  context, so it saves less than `/clear` — but it does not drop a conversation
  that is not finished.
- **Neither**, when the next artifact is a few minutes away and the context is
  still small. Early in a session, a reset can cost more than it saves.

Offer it once per boundary. If the human says continue, continue — do not
re-offer at the next tool call, and never re-offer inside the same phase. A
suggestion repeated is narration, which `SKILL.md`'s communication contract
already forbids.
