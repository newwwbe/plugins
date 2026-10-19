# Continual Learning for Claude Code

Claude Code port of the [Continual Learning](../../continual-learning/) Cursor plugin. It automatically and incrementally keeps `AGENTS.md` up to date from Claude Code transcript changes.

The plugin combines:

- A `Stop` hook that decides when to trigger learning.
- A `continual-learning` skill (`/continual-learning:continual-learning`) for running the flow by hand.
- An `agents-memory-updater` agent (`continual-learning:agents-memory-updater`) that mines new or changed transcripts and updates `AGENTS.md`.
- A helper script, `scripts/transcript-delta.sh`, that lists changed transcripts, extracts their user messages, and maintains the incremental index.

It is designed to avoid noisy rewrites by:

- Reading existing `AGENTS.md` first and updating matching bullets in place.
- Processing only new or changed transcript files.
- Writing plain bullet points only (no evidence/confidence metadata).

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install continual-learning@newwwbe
```

The hook and helper need `bash` and `jq` on your `PATH`.

### Making Claude Code read the learned memory

Claude Code loads `CLAUDE.md`, not `AGENTS.md`. Keep the learned bullets in `AGENTS.md` (other agents read it too) and import it from your project's `CLAUDE.md` with one line:

```markdown
@AGENTS.md
```

The updater never edits `CLAUDE.md`; it mentions the missing import in its output when it sees a `CLAUDE.md` without it.

## How it works

On eligible `Stop` events, the hook blocks the stop once (`{"decision": "block", "reason": ...}`) and asks Claude to run the `continual-learning:agents-memory-updater` agent, passing the project root, the transcript directory, and the index path. The agent:

1. runs `transcript-delta.sh list` to find transcripts in `~/.claude/projects/<project-slug>/` that are new or changed since the last run (subagent transcripts are skipped),
2. reads each one through `transcript-delta.sh extract` (user messages, including slash-command arguments, plus short assistant replies),
3. merges durable preferences and workspace facts into `AGENTS.md`,
4. runs `transcript-delta.sh commit` to refresh the index.

Run it any time by hand with `/continual-learning:continual-learning`. The skill is user-invoked only (`disable-model-invocation: true`), as in the Cursor version.

Local runtime state (safe to delete; add `.claude/hooks/state/` to `.gitignore`):

- `.claude/hooks/state/continual-learning.json` (cadence state, written by the hook)
- `.claude/hooks/state/continual-learning-index.json` (incremental transcript index, written by the helper script)

## Trigger cadence

Default cadence:

- minimum 10 completed turns
- minimum 120 minutes since the last run
- transcript mtime must advance since the previous run

A completed turn is the first stop of a user prompt (`stop_hook_active` false, deduplicated by `prompt_id`).

Trial mode (`CONTINUAL_LEARNING_TRIAL_MODE=1`):

- minimum 3 completed turns
- minimum 15 minutes
- automatically expires after 24 hours, then falls back to the default cadence

## Optional env overrides

Set these in your shell or in the `env` block of `.claude/settings.json`:

- `CONTINUAL_LEARNING_MIN_TURNS` (or legacy `CONTINUOUS_LEARNING_MIN_TURNS`)
- `CONTINUAL_LEARNING_MIN_MINUTES` (or legacy `CONTINUOUS_LEARNING_MIN_MINUTES`)
- `CONTINUAL_LEARNING_TRIAL_MODE` (or legacy `CONTINUOUS_LEARNING_TRIAL_MODE`)
- `CONTINUAL_LEARNING_TRIAL_MIN_TURNS` (or legacy `CONTINUOUS_LEARNING_TRIAL_MIN_TURNS`)
- `CONTINUAL_LEARNING_TRIAL_MIN_MINUTES` (or legacy `CONTINUOUS_LEARNING_TRIAL_MIN_MINUTES`)
- `CONTINUAL_LEARNING_TRIAL_DURATION_MINUTES` (or legacy `CONTINUOUS_LEARNING_TRIAL_DURATION_MINUTES`)

## Output format in AGENTS.md

The memory updater writes only:

- `## Learned User Preferences`
- `## Learned Workspace Facts`

Each item is a plain bullet point.

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) are dropped.
- The Bun/TypeScript `stop` hook is rewritten as a bash + `jq` script for the Claude Code hook contract: it reads `session_id`, `transcript_path`, `prompt_id`, and `stop_hook_active` from stdin and answers with `{"decision":"block","reason":...}` instead of `followup_message`. Turn counting uses `stop_hook_active == false` and `prompt_id` in place of Cursor's `status`, `loop_count`, and `generation_id`. Cadence logic and env variables are unchanged.
- Transcripts are Claude Code JSONL files in `~/.claude/projects/<project-slug>/` instead of Cursor's `~/.cursor/projects/<workspace-slug>/agent-transcripts/`. The `extract` helper turns them into plain text for the agent.
- Cursor's hook asked the agent to run the `continual-learning` skill. That skill is hidden from the model in Claude Code (`disable-model-invocation`), so the hook asks Claude to spawn `continual-learning:agents-memory-updater` directly.
- State moved from `.cursor/hooks/state/` to `.claude/hooks/state/`. Claude Code protects `.claude/` from the Write tool and inline shell writes, so the agent maintains the index through `transcript-delta.sh commit` rather than editing the JSON itself (one Bash permission prompt unless you allow it).
- `AGENTS.md` is kept as the memory file; see above for importing it into `CLAUDE.md`.

## License

MIT
