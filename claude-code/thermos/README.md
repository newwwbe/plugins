# Thermos for Claude Code

Claude Code port of the [Thermos](../../thermos/) Cursor plugin: deep correctness and security audits, harsh maintainability rubrics, and parallel subagent orchestration.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install thermos@cursor-plugins
```

## Usage

| Command | What it does |
|:--------|:-------------|
| `/thermos:thermos` | Gathers the branch diff, runs both review subagents in parallel in the background, and synthesizes one deduplicated verdict. |
| `/thermos:thermo-nuclear-review` | Deep bug/security/devex/feature-leak audit in the main conversation. |
| `/thermos:thermo-nuclear-code-quality-review` | Strict maintainability audit in the main conversation. |

The skills are user-invoked only (`disable-model-invocation: true`), as in the Cursor version.

## Agents

| Agent (`subagent_type`) | Description |
|:------------------------|:------------|
| `thermos:thermo-nuclear-review-subagent` | Diff-scoped deep review. Reads its rubric from `${CLAUDE_PLUGIN_ROOT}/skills/thermo-nuclear-review/SKILL.md`. |
| `thermos:thermo-nuclear-code-quality-review-subagent` | Diff-scoped code-quality review. Reads its rubric from `${CLAUDE_PLUGIN_ROOT}/skills/thermo-nuclear-code-quality-review/SKILL.md`. |

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) are dropped.
- Cursor `Task` calls with `subagent_type: "shell"` / `"explore"` are replaced by the Agent tool: the parent collects the diff with Bash/Read (or an `Explore` agent) and spawns the plugin-namespaced `thermos:*` agents.
- Agents load their rubric from an exact path via `${CLAUDE_PLUGIN_ROOT}`, because the rubric skills are hidden from the model and cannot be loaded through the Skill tool.
- The rubric skills `thermo-nuclear-review` and `thermo-nuclear-code-quality-review` are unchanged copies of the upstream text.

## License

MIT
