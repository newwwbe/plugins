---
name: ralph-loop
description: Start a Ralph Loop for iterative self-referential development. Use when the user asks to run a ralph loop, start an iterative loop, or wants repeated autonomous iteration on a task until completion.
argument-hint: '"<task prompt>" [--max-iterations N] [--completion-promise TEXT]'
---

# Ralph Loop

## Trigger

The user wants to start a Ralph loop. An iterative development loop where the same prompt is fed back after every turn, and the agent sees its own previous work each iteration.

Arguments, if any: $ARGUMENTS

## Workflow

1. Gather the user's task prompt and optional parameters:
   - `max_iterations` (number, default 0 for unlimited)
   - `completion_promise` (single-line text, or none)

2. Create the loop state with the plugin's helper script (Claude Code protects `.claude/` from direct writes, so do not write the state file yourself). Run from the project root, passing the prompt on stdin through a quoted heredoc so it is stored verbatim:

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/ralph-state.sh" start --max-iterations 20 --completion-promise "COMPLETE" <<'RALPH_PROMPT'
   Build a REST API for todos with CRUD operations, input validation, and tests.
   RALPH_PROMPT
   ```

   Omit `--max-iterations` for unlimited and `--completion-promise` for none. The script writes `.claude/ralph/scratchpad.md`:

   ```markdown
   ---
   iteration: 1
   max_iterations: 20
   completion_promise: "COMPLETE"
   ---

   Build a REST API for todos with CRUD operations, input validation, and tests.
   ```

3. Confirm to the user that the Ralph loop is active, then begin working on the task.

4. The plugin's `Stop` hook intercepts each turn end and blocks it, feeding the same prompt back as your next instruction. You will see it prefixed with `[Ralph loop iteration N.]`. On the first turn end the hook adds a `session_id:` line to the state, binding the loop to this session.

## Guardrails

- If a completion promise is set, you may ONLY output `<promise>TEXT</promise>` when the statement is completely and genuinely true.
- Do not output false promises to escape the loop.
- Always recommend setting `max_iterations` as a safety net.
- Do not ask the user questions mid-loop and wait: the loop feeds the prompt back regardless. Make reasonable decisions and record them in the files.

## Output

Confirm the loop is active (prompt, iteration limit, promise if set), then start working on the task immediately.
