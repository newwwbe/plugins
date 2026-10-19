<!-- orchestrate failure handoff
task: {{taskName}}
branch: {{branch}}
sessionId: {{sessionId}}
failureMode: {{failureMode}}
terminatedAt: {{terminatedAt}}
-->

# {{taskName}} failure handoff

Status: error (agent terminated without writing a handoff)
Failure mode: {{failureMode}}
Claude session: {{sessionId}} (inspect with `claude --resume {{sessionId}}` from the task's worktree)
Started: {{startedAt}}
Terminated: {{terminatedAt}}
Branch: {{branch}}
Log: {{log}}
Error:
```
{{error}}
```

## Suggested next steps
{{suggestions}}
