# Create Plugin for Claude Code

Claude Code port of the [Create Plugin](../../create-plugin/) Cursor plugin: meta workflows for scaffolding Claude Code plugins and checking that they are ready for a marketplace.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install create-plugin@newwwbe
```

## Usage

| Skill | What it does |
|:------|:-------------|
| `/create-plugin:create-plugin-scaffold` | Scaffolds a plugin (via `claude plugin init` when available), fills in manifest and components, adds a marketplace entry if the repo has one, and runs `claude plugin validate`. |
| `/create-plugin:review-plugin-submission` | Runs `claude plugin validate` (and `--strict`), then audits manifest, discovery paths, frontmatter, marketplace wiring, and README. Returns a pass/fail report and fix list. |

Claude also loads either skill on its own when you ask it to create or review a plugin.

### Agents

| Agent (`subagent_type`) | Description |
|:------------------------|:------------|
| `create-plugin:plugin-architect` | Read-only (`Read`, `Grep`, `Glob`) planner that recommends the component mix, layout, and manifest shape for a new plugin. |

### Rules

`plugin-quality-gates` applies to every session. A `SessionStart` hook prints it (frontmatter stripped) into context. It requires a valid `.claude-plugin/plugin.json`, relative paths, component frontmatter, a passing `claude plugin validate`, and `~/.claude/skills/<plugin-name>/` as the default location.

## Typical flow

1. Ask for a new plugin, or run `/create-plugin:create-plugin-scaffold`, with a name, purpose, and the components you want.
2. Fill in the skills, agents, and hooks.
3. Run `/create-plugin:review-plugin-submission` before publishing.

New plugins go to `~/.claude/skills/<plugin-name>/` by default. Claude Code auto-loads that location as `<plugin-name>@skills-dir`; run `/reload-plugins` to pick it up in the current session.

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) and the explicit component paths are dropped.
- The skills, agent, and rule now target the Claude Code plugin format: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `skills/`, `agents/`, `commands/`, `hooks/hooks.json`, `.mcp.json`, and `${CLAUDE_PLUGIN_ROOT}`. Cursor `.mdc` rules are not part of that format; the skills advise a `SessionStart` hook for always-on guidance, or a skill otherwise.
- Validation uses `claude plugin validate` (with `--strict` for public submissions) and an optional `claude -p --plugin-dir` smoke test, on top of the manual checklist.
- The default output location is `~/.claude/skills/<plugin-name>/` instead of `~/.cursor/plugins/local/<plugin-name>/`. When the installed CLI has `claude plugin init`, the scaffold skill uses it.
- The `alwaysApply` rule `plugin-quality-gates` is delivered by a `SessionStart` hook in `hooks/hooks.json`.
- `plugin-architect`: Cursor's `readonly: true` becomes a `tools: Read, Grep, Glob` allowlist.
- The upstream README lists a `create-plugin` command that the Cursor plugin never shipped. Use `/create-plugin:create-plugin-scaffold` instead.

## License

MIT
