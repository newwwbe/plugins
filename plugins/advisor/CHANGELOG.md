# Changelog

## 1.0.0-claude.1

- Claude Code port of Advisor 1.0.0.
- Skill: `advisor` (`/advisor:advisor [opus|sonnet|haiku|off|status|ask ...|nudge on|off]`), with state changes through `scripts/advisor-state.sh`.
- Agent: `advisor:advisor-subagent`, a read-only Opus subagent that returns a verdict and guidance.
- Hooks: `PostToolUse` tracks edits since the last consult, `SubagentStop` logs each consult to `.claude/advisor/log.md`, and `Stop` blocks once to request a pre-completion consult.
