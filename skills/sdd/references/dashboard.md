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
