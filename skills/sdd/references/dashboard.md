# The Progress Dashboard

A local web page showing where a feature stands: which artifacts exist and what
they scored, the current milestone, every task's state, and the blocker log.
Optional, off unless asked for.

## Why it costs nothing

Everything it shows is **already on disk**, because this skill keeps its state
there rather than in a session (`SKILL.md` Step 1). `scripts/sdd_status.py`
reuses the linter's own parsers to read `tasks.md`'s checkbox marks, each
artifact's frontmatter `status`, and each `validation:` block, and serves the
result as JSON. The agent reports nothing and writes nothing extra.

The saving is real but indirect: it comes from the agent no longer narrating
progress in chat, per `SKILL.md`'s communication contract. The dashboard is
what makes that silence tolerable — you can see progress instead of reading
about it.

## Running it

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd_status.py --serve --repo-root .
```

Then open `http://127.0.0.1:4517`. `--port` changes the port. A server is
needed rather than opening the file directly because `fetch()` from a `file://`
page is blocked by CORS.

One-shot, no server, for piping into something else:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/sdd/scripts/sdd_status.py --json --repo-root .
```

The page polls once a second and re-renders only when the state actually
changed, so scrolling a long task list is not fought by the refresh. If the
server stops, the page keeps the last state on screen and says so rather than
going blank.

## Turning it on

```yaml
# .specs/sdd.config.yml
dashboard: on    # on | off
```

`on` means: start the server in the background at the beginning of a session,
give the human the URL **once**, and never mention it again. Do not re-announce
it each phase, do not describe what it is showing — that is exactly the
narration the dashboard exists to replace.

Absent or `off`, do not start it and do not offer it more than once per
session.

## Event pings — the one thing not on disk

A judge running for three minutes looks identical to nothing happening, because
nothing on disk changes until it finishes. For that, and only that, the agent
appends one line:

```bash
echo "{\"at\":\"$(date +%H:%M:%S)\",\"event\":\"Tier 2 judge dispatched for design.md (sonnet, fast)\"}" >> .specs/.events.jsonl
```

Rules:

- **Only for work in flight that disk cannot show.** A judge dispatched, a
  subagent dispatched, a long test run started. Never for something that is
  about to be written to a file anyway — the file is the record.
- **One line, one sentence.** Roughly 15 tokens. An event that needs a
  paragraph is a chat message pretending to be an event.
- **Never a substitute for telling the human something they must act on.** A
  blocker goes in `tasks.md`'s Blocker Log and gets said out loud. An event
  ping is ambient, and ambient information is not consent.
- The file is append-only and disposable. A malformed line is shown verbatim
  rather than crashing the page; deleting the file loses nothing.

Add `.specs/.events.jsonl` to `.gitignore` — it is session noise, not a record
of the system.

## Liveness costs nothing now

The page shows "last change 12s ago — spec.md", read from file mtimes. A
running session writes files; nothing written for a long time means finished or
stuck, and either way that is what you want to see. This replaced the event
ping as the default liveness signal because it costs the agent nothing.

Event pings are now **optional and off by default**. Write one only when naming
what is happening is genuinely worth ~20 tokens — a judge dispatch that will run
for minutes is the case that qualifies. Most sessions should write none.

## The token usage panel

The dashboard reads this project's Claude Code transcripts from
`~/.claude/projects/<encoded-repo-path>/*.jsonl` and shows, per session: turns,
average context, cache reads, fresh input, and output. **This costs zero agent
tokens** — those files are written by the harness whether or not anything reads
them.

What the panel is for is one relationship:

> **cost ≈ turns × context size**

Everything in context is re-read on every subsequent turn. A 2,400-token
artifact that enters context at turn 50 of a 330-turn session is not a
2,400-token cost — it is 2,400 × 280 in cache reads. This is why the artifact
budgets, the section extractor, and the fresh-session handoff matter more than
their file sizes suggest, and why an artifact read late is cheaper than the same
artifact read early.

Cache reads bill at a fraction of fresh input, so they are shown separately
rather than summed into one misleading number. Output is the priciest per token,
which is what the terse judge output contract in `references/quality-gate.md`
exists to cut.

If the panel is empty, this repo has no transcripts under `~/.claude/projects/`
yet — nothing is broken.
