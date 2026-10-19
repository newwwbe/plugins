<!-- orchestrate finished-no-handoff
task: {{taskName}}
branch: {{branch}}
sessionId: {{sessionId}}
terminatedAt: {{terminatedAt}}
-->

# {{taskName}} finished without handoff

Status: error (agent ended cleanly but never wrote the structured handoff)
Claude session: {{sessionId}}
Branch: {{branch}}
Terminated: {{terminatedAt}}

## Suggested next steps
- Inspect the raw output at `handoffs/{{taskName}}.md` to see what the agent actually emitted.
- Retry as-is if this looks like a prompt misfire (prose instead of the structured template).
- Abandon: drop the task and replan around it if the goal genuinely has no acceptable output.

## Raw snippet
```
{{rawSnippet}}
```
