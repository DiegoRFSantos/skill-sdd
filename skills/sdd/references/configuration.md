# `.specs/sdd.config.yml`

Every setting this skill reads, in one place. The file is **optional** and is
created only when the user asks for it — an absent file is a valid state, and
each key falls back to asking.

```yaml
# .specs/sdd.config.yml
summary_preview: ask     # always | never | ask   — show the 15-line sketch in chat before authoring
judge_model: sonnet      # any model the Agent tool accepts — which model Tier 2 judges run on
judge_depth: fast        # fast | full            — judge verbosity and round cap
dashboard: off           # on | off               — the local progress page
```

| Key | Default when absent | Resolved by | Detail |
|---|---|---|---|
| `summary_preview` | ask the user, this artifact only | `references/summary-preview.md` | Only the chat preview is optional. `## 0. At a Glance` is a required section either way. |
| `judge_model` | **ask** — never guessed | `references/quality-gate.md` | Unset, a judge inherits the session's model, usually the slowest available. |
| `judge_depth` | **ask** — never guessed | `references/quality-gate.md` | `fast` caps at one re-judge and drops justification prose for criteria at full marks. Same rubric, same 90 bar. |
| `dashboard` | off, and offered at most once per session | `references/dashboard.md` | `on` starts the server and gives the URL **once**. |

Two of these are never guessed. `judge_model` and `judge_depth` are a real
trade — a fast model that misses a semantic defect against a slow one that
finds it — and Human Decision Supremacy means the trade is the human's. Ask
both in one message, then offer to write the answers here so the question does
not come back every feature.

When a user answers with a preference they clearly mean to keep ("always do
this", "stop asking"), offer to write it into this file rather than remembering
it for the session. Session memory does not survive the cold start that
`SKILL.md` Step 1 is built around.
