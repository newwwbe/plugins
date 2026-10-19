# Advisor for Claude Code

Claude Code port of the [Advisor](../../advisor/) Cursor plugin. Advisor gives Claude a stronger second model to consult at key points: before a major decision, when it is stuck on an error, and before it declares a task done. The main model keeps doing the work; the advisor reads a full briefing (and the conversation transcript when available), thinks hard, and returns a verdict with concrete guidance. You pay for the strong model only where it matters.

The default advisor is `opus`. Because the advisor is a subagent with its own model, it does not have to be the model you are chatting with: run your session on Sonnet and let Opus review the checkpoints.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install advisor@cursor-plugins
```

The hooks and the state script need `bash` and `jq` on your `PATH`.

## Quick start

```text
/advisor:advisor                     turn on with the default advisor (opus)
/advisor:advisor sonnet              turn on with a different Claude model (opus | sonnet | haiku)
/advisor:advisor ask is this migration safe to run twice?
/advisor:advisor status
/advisor:advisor nudge off
/advisor:advisor off
```

Then work as usual. When Claude hits a checkpoint it consults the advisor and reports back in a line or two:

```text
Advisor (opus): proceed with changes. The retry wrapper hides the real failure; the 401
comes from a stale token cache. Dropped the retry, fixed the cache key.
```

## How it works

- **Skill `advisor`** (`/advisor:advisor`) implements the command and the checkpoint protocol: when to consult, how to write the briefing ([template](skills/advisor/references/briefing-template.md)), how to act on the verdict, and how to report it. State changes go through `scripts/advisor-state.sh`.
- **Agent `advisor:advisor-subagent`** is a read-only subagent (`tools: Read, Grep, Glob, Bash`, `model: opus`, overridable per session). It verifies the briefing against the repository, reads the JSONL transcript when a path is given, and answers with `Verdict / Why / Recommendations / Risks / Answers / Confidence`.
- **Hooks** (`hooks/hooks.json`) keep the mode honest without adding chatter:
  - `PostToolUse` on `Edit|Write|MultiEdit|NotebookEdit` records that files changed since the last consult.
  - `SubagentStop` (filtered to `agent_type` `advisor:advisor-subagent`) counts each consult, clears the marker, and appends the advice (`last_assistant_message`) to `.claude/advisor/log.md`.
  - `Stop` blocks the stop once with an `[Advisor]` message when a turn ends with unreviewed edits, so the pre-completion consult is not skipped. It fires at most once per batch of edits, never when `stop_hook_active` is set, stays quiet when Claude's last message ended with a question for you, and can be disabled with `/advisor:advisor nudge off`.
  - Every hook binds the state to the first session that touches it (`session_id`) and records its `transcript_path`, and ignores other sessions.

## Checkpoints

| Checkpoint | Trigger |
| --- | --- |
| Major decision | Choosing between approaches; migrations, deletions, public API or config changes, dependency swaps, auth or payment code; requests ambiguous enough to change the work. |
| Stuck | Same error or failing test after two real attempts; unexplained behavior; about to add a workaround (retry loop, `sleep`, broad `try/except`, skipped test, disabled check). |
| Before declaring done | Any task that changed logic or touched more than a couple of files. Trivial edits are skipped and said so. |
| On request | `/advisor:advisor ask ...`, or asking what the advisor thinks. |

The skill caps this at roughly four consults per task and never consults for routine steps or things Claude can verify itself.

## State

Everything lives in `.claude/advisor/` at the project root and is safe to delete at any time:

| File | Purpose |
| --- | --- |
| `state.json` | Mode, model, nudge setting, consult count, bound session, transcript path. |
| `log.md` | Every completed consult with its verdict, for later review. |
| `pending` | Marker: files changed since the last consult. |

Add `.claude/advisor/` to your `.gitignore` if you do not want it in the repository; the skill never stages it.

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) are dropped. The skill is invoked as `/advisor:advisor` and the agent is `advisor:advisor-subagent`.
- **Models:** the Cursor version defaulted to Grok 4.6 (xhigh) and accepted any Cursor subagent model slug (Grok, Composer, ...). Claude Code runs Claude models only, so the agent is pinned to `model: opus` and `/advisor:advisor <model>` accepts `opus`, `sonnet`, or `haiku`. Cross-vendor second opinions are not possible.
- **No resume:** Cursor resumed the same advisor across consults (`advisor_agent_id` + `resume`). Each consult here is a fresh `Agent` spawn; the briefing carries earlier verdicts and `log.md` keeps the history. The `advisor_agent_id` field is gone.
- **State:** `.cursor/advisor/` became `.claude/advisor/`. Claude Code protects `.claude/` from the Write tool and inline shell writes, so the skill enables, disables, and toggles the nudge with `scripts/advisor-state.sh` (one Bash permission prompt unless you allow it). The hooks, which are not subject to permissions, update the rest.
- **Hook mapping:** `afterFileEdit` -> `PostToolUse` (`Edit|Write|MultiEdit|NotebookEdit`); `subagentStop` -> `SubagentStop` (filtered on the namespaced `agent_type` inside the script; the advice comes from `last_assistant_message`); `stop` with `followup_message` and `loop_limit: 3` -> `Stop` with `{"decision":"block","reason":...}` guarded by `stop_hook_active`; `afterAgentResponse` (`capture-response.sh`, `last-response.txt`) is folded into the Stop hook, which reads `last_assistant_message` (falling back to the `transcript_path` JSONL). Conversation binding uses `session_id` instead of `conversation_id`.
- File changes made through Bash (`sed -i`, `printf > file`, code generators) do not arm the nudge, as with Cursor's `afterFileEdit`.
- Cursor's "Custom Mode" (Option+Enter) tip is dropped; the state file keeps the mode on across messages.

## Cost

Each consult is one call to the advisor model with a briefing of a few thousand tokens plus whatever the advisor chooses to read. Selective use is the point: a typical feature takes one to three consults. Opus consults cost more than Sonnet or Haiku ones; pick the model per project with `/advisor:advisor <model>`.

## Limitations

- State is per project, bound to the session that enabled it. Running `/advisor:advisor` in a second session on the same project re-binds the mode there (model and nudge settings carry over; the consult count starts fresh). Use `/advisor:advisor status` to look without re-binding.
- The advisor only reads the full transcript once a hook has recorded `transcript_path` (after the first edit or turn end). It always receives the briefing.
- The end-of-turn nudge relies on the plugin's hooks; where hooks do not run, the skill still performs the pre-completion consult on its own.

## License

MIT
