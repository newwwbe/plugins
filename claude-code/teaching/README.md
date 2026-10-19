# Teaching for Claude Code

Claude Code port of the [Teaching](../../teaching/) Cursor plugin: skill mapping, practice plans, and feedback loops for learning a topic over several sessions.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install teaching@newwwbe
```

## Usage

| Skill | Description |
|:------|:------------|
| `/teaching:create-learning-path` | Build a personalized learning roadmap with milestones and practice checkpoints |
| `/teaching:run-learning-retrospective` | Evaluate progress, identify blockers, and adjust the learning plan |

Both skills interview the learner first. Claude also loads them on its own when you ask for a study plan or a progress review.

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) and the explicit `skills` path are dropped.
- "Use Ask user tool" now names Claude Code's `AskUserQuestion` tool, with a plain-text fallback for non-interactive runs.
- Skill text is otherwise unchanged from upstream.

## License

MIT
