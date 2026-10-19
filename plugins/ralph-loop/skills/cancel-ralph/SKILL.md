---
name: cancel-ralph
description: Cancel an active Ralph Loop. Use when the user wants to stop, cancel, or abort a running ralph loop.
---

# Cancel Ralph

## Trigger

The user wants to cancel or stop an active Ralph loop.

## Workflow

Run the plugin's helper script from the project root (Claude Code protects `.claude/` from direct deletes, so use the script):

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/ralph-state.sh" cancel
```

It removes `.claude/ralph/` and prints either `Cancelled Ralph loop (was at iteration N).` or `No active Ralph loop found.`

## Output

Relay the script's one-line result to the user.
