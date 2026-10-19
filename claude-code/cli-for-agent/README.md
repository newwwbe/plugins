# CLI for Agents for Claude Code

Claude Code port of the [CLI for Agents](../../cli-for-agent/) Cursor plugin. It has a single skill with patterns for **CLIs meant to be driven by coding agents**: non-interactive flags first, layered `--help` with examples, stdin and pipelines, fast actionable errors, idempotency, `--dry-run`, and predictable command structure.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install cli-for-agent@newwwbe
```

## Usage

| Skill | Description |
|:------|:------------|
| `/cli-for-agent:cli-for-agents` | Design and review guidance for agent-friendly command-line tools |

Claude also loads the skill on its own when you build or refactor a CLI, write subcommand help, or ask whether an existing tool will block agents (interactive prompts, missing examples, ambiguous errors).

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `category`, `tags`) and the explicit `skills` path are dropped.
- The skill is an unchanged copy of the upstream text; it has no Cursor-specific content.

## License

MIT
