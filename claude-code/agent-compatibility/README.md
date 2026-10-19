# Agent Compatibility for Claude Code

Claude Code port of the [Agent Compatibility](../../agent-compatibility/) Cursor plugin. It checks how well a repo holds up under agent workflows by pairing the published `agent-compatibility` CLI with focused reviews for startup, validation, and docs reliability.

By default, the full pass returns one overall score and one short list of the highest-leverage fixes. If you want the full breakdown, ask for it and the component scores and reasoning are shown.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install agent-compatibility@cursor-plugins
```

## Usage

Run `/agent-compatibility:check-agent-compatibility`, or ask Claude for an agent compatibility check of the repo. The skill launches the four review agents in parallel with the Agent tool, then returns a compact result:

```md
## Agent Compatibility Score: 72/100

Top fixes
- First issue
- Second issue
```

Ask for a breakdown if you want the component scores or the weighting.

### Agents

| Agent (`subagent_type`) | Description |
|:------------------------|:------------|
| `agent-compatibility:compatibility-scan-review` | Runs the published CLI and reports the raw deterministic score and problems |
| `agent-compatibility:startup-review` | Tries the cold-start path and scores how much guesswork booting the repo takes |
| `agent-compatibility:validation-review` | Scores how practical it is to verify a small change |
| `agent-compatibility:docs-reliability-review` | Follows the documented setup path and scores where the docs drift from reality |

You can also spawn any one of them on its own.

## Score model

- `Agent Compatibility Score`: final blended score shown to the user
- `Deterministic Compatibility Score`: raw score from the published CLI
- `Startup Compatibility Score`: how much guesswork it takes to boot the repo
- `Validation Loop Score`: how practical it is to verify a small change
- `Docs Reliability Score`: how closely the docs match the real setup path

```text
workflow = round(mean(startup, validation, docs))
Agent Compatibility Score = round((deterministic * 0.7) + (workflow * 0.3))
```

The CLI also reports an accelerator layer for committed agent tooling (`AGENTS.md`, `.claude/` agents or commands, `.cursor/` rules and MCP config, and MCP servers matching the repo's dependencies). That context informs recommendations but does not inflate the deterministic score.

## CLI notes

The plugin does not bundle the scanner. The agents run the published npm package, so the session needs Node.js and access to the npm registry:

```bash
npx -y agent-compatibility@latest .          # compact terminal dashboard
npx -y agent-compatibility@latest --json .   # JSON
npx -y agent-compatibility@latest --md .     # Markdown
npx -y agent-compatibility@latest --text .   # plain text
npx -y agent-compatibility@latest . --config ./agent-compatibility.config.json
```

If the scanner cannot run, the skill says so and does not penalize the repo. The scanner is heuristic: it scores repo signals and surfaces likely friction, but it is not a full quality verdict on the codebase.

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) and the explicit component paths are dropped.
- Agents: Cursor's `model: fast` becomes `model: haiku`. `readonly: true` becomes `tools: Bash, Read, Grep, Glob`, so the agents can run the scanner, start the repo, and run tests, but have no Edit or Write tools (Bash is still available, as Cursor read-only agents keep shell access). To spend more on the behavioral checks, change `model:` to `sonnet` in the agent files.
- The skill names the plugin-namespaced agent types (`agent-compatibility:*`) and launches all four in one message so they run in parallel.
- The "local install" symlink into `~/.cursor/plugins/local` is replaced by the marketplace install above. For local development, use `claude --plugin-dir <path-to-this-directory>`.
- The skill tells Claude not to recommend Cursor-only tooling (`.cursor/` rules or MCP config) for a repo that does not use Cursor, even when the scanner's accelerator layer suggests it.
- Agent and skill text is otherwise unchanged from upstream.

## License

MIT
