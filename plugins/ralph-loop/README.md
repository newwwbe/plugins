# Ralph Loop for Claude Code

Claude Code port of the [Ralph Loop](https://github.com/cursor/plugins/tree/main/ralph-loop) Cursor plugin. It runs Claude in a self-referential loop, feeding the same prompt back after every turn until the task is complete. It implements the [Ralph Wiggum technique](https://ghuntley.com/ralph/) pioneered by Geoffrey Huntley.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install ralph-loop@newwwbe
```

The hook needs `bash`, `jq`, and `perl` on your `PATH`.

## How it works

A `Stop` hook fires whenever Claude finishes a turn. If a loop is active (`.claude/ralph/scratchpad.md` exists at the project root), the hook checks Claude's final message for a `<promise>` tag matching the completion phrase. If the promise is not there and the iteration limit has not been reached, the hook blocks the stop (`{"decision": "block", "reason": ...}`) and hands Claude the original prompt again as its next instruction. Claude sees its own previous edits in the working tree and git history, iterates on them, and repeats. The prompt never changes. The code does.

## Quick start

```
/ralph-loop:ralph-loop "Build a REST API for todos. CRUD operations, input validation, tests. Output COMPLETE when done." --completion-promise "COMPLETE" --max-iterations 50
```

You can also ask in plain words ("Start a ralph loop: ..."); the skill is model-invocable.

## Skills

| Command | What it does |
|:--------|:-------------|
| `/ralph-loop:ralph-loop` | Writes the loop state file and starts working on the task. Options: `--max-iterations <N>` (default unlimited), `--completion-promise <text>`. |
| `/ralph-loop:cancel-ralph` | Removes `.claude/ralph/` (via `scripts/ralph-state.sh cancel`) and reports the iteration it stopped at. |
| `/ralph-loop:ralph-loop-help` | Explains the technique and usage. |

## Writing good prompts

Define explicit completion criteria. Vague goals like "make it good" give Claude nothing to verify against.

```markdown
Build a REST API for todos.

When complete:
- All CRUD endpoints working
- Input validation in place
- Tests passing (coverage > 80%)
- Output: <promise>COMPLETE</promise>
```

Break large tasks into phases. Encourage self-correction by including test/fix cycles in the prompt. Always pass `--max-iterations` to prevent runaway loops.

Works well for tasks with clear, verifiable success criteria: getting tests to pass, completing a migration, building a feature from a spec. Not a good fit for tasks that need human judgment or have ambiguous goals.

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) are dropped.
- State moved from `.cursor/ralph/` to `.claude/ralph/` at the project root (`$CLAUDE_PROJECT_DIR`, falling back to the hook's `cwd`).
- Claude Code protects `.claude/` from the Write tool and inline shell writes, so the skills create and remove the state through `scripts/ralph-state.sh` (`start` reads the prompt from a heredoc on stdin; `cancel`; `status`) instead of writing the file directly. Starting or cancelling a loop asks once for permission to run that Bash command unless you allow it.
- Cursor's `stop` hook returned `{"followup_message": ...}`; the Claude Code `Stop` hook returns `{"decision": "block", "reason": ...}`, which keeps the same turn going with the prompt as the next instruction. `stop_hook_active` is deliberately ignored, matching Cursor's `loop_limit: null`; `--max-iterations` and the completion promise are the bounds.
- Cursor's separate `afterAgentResponse` hook (`capture-response.sh`) and its `done` flag file are gone. Claude Code gives the Stop hook the final reply as `last_assistant_message` (the hook falls back to reading the last assistant entries in `transcript_path` JSONL), so promise detection happens in `stop-hook.sh`.
- New: the hook writes `session_id:` into the state file on the first turn end and ignores Stop events from other Claude Code sessions in the same project.
- Hook commands use `${CLAUDE_PLUGIN_ROOT}` instead of Cursor's relative `./hooks/...` paths.

## Learn more

- [Original technique by Geoffrey Huntley](https://ghuntley.com/ralph/)
- [Ralph Orchestrator](https://github.com/mikeyobrien/ralph-orchestrator)

## License

MIT
