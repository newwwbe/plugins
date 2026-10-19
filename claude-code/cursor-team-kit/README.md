# Cursor Team Kit for Claude Code

Claude Code port of the [Cursor Team Kit](../../cursor-team-kit/) plugin: internal-style workflows for CI, code review, shipping, verification, and test reliability. It does not need any third-party service integrations beyond `git` and the GitHub CLI (`gh`).

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install cursor-team-kit@newwwbe
```

## Usage

Invoke a skill with `/cursor-team-kit:<skill>`. Claude can also load any skill below on its own when the task matches, except `pr-review-canvas`, which you have to invoke yourself (as in the Cursor version).

| Skill | Description |
|:------|:------------|
| `loop-on-ci` | Watch PR checks and iterate on failures until they pass |
| `review-and-ship` | Run a structured review, commit changes, and open a PR |
| `pr-review-canvas` | Generate an interactive HTML PR walkthrough with annotated, categorized diffs |
| `verify-this` | Prove or disprove claims with baseline/treatment artifacts and a clear verdict |
| `control-cli` | Build or adapt a local harness to drive and profile interactive CLIs or TUIs |
| `control-ui` | Build or adapt a local browser/CDP harness for web or Electron UIs |
| `make-pr-easy-to-review` | Clean noisy PR history, improve descriptions, and add reviewer guidance |
| `run-smoke-tests` | Run Playwright smoke tests and triage failures |
| `fix-ci` | Find failing CI jobs, inspect logs, and apply focused fixes |
| `new-branch-and-pr` | Create a fresh branch, complete work, and open a pull request |
| `get-pr-comments` | Fetch and summarize review comments from the active pull request |
| `check-compiler-errors` | Run compile and type-check commands and report failures |
| `what-did-i-get-done` | Summarize authored commits over a given time period into a concise status update |
| `weekly-review` | Generate a weekly recap of shipped work with bugfix/tech-debt/net-new highlights |
| `fix-merge-conflicts` | Resolve merge conflicts, validate build/tests, and summarize decisions |
| `deslop` | Remove AI-generated code slop and clean up code style |
| `workflow-from-chats` | Extract durable working preferences from past Claude Code sessions into skills, CLAUDE.md rules, or docs |

### Agents

| Agent (`subagent_type`) | Description |
|:------------------------|:------------|
| `cursor-team-kit:ci-watcher` | Watches the PR's checks with `gh` and returns a concise pass/fail summary. Runs on `haiku`; spawn it with `run_in_background: true` to keep working while CI runs. |

### Rules

Both rules apply to every session. A `SessionStart` hook prints them (frontmatter stripped) so Claude receives them as context.

| Rule | Description |
|:-----|:------------|
| `typescript-exhaustive-switch` | Require exhaustive switch handling for unions/enums |
| `no-inline-imports` | Keep imports at module top level for readability and consistency |

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) and the explicit `skills`/`agents`/`rules` paths are dropped.
- The `alwaysApply` rules in `rules/` are delivered by a `SessionStart` hook in `hooks/hooks.json` instead of Cursor's rules engine.
- `thermo-nuclear-code-quality-review` (skill and agent) is left out because it is part of the [thermos](../thermos/) plugin. Install `thermos` and use `/thermos:thermo-nuclear-code-quality-review` or the `thermos:thermo-nuclear-code-quality-review-subagent` agent.
- `ci-watcher`: Cursor's `model: fast` becomes `model: haiku`, and `is_background: true` is dropped. Claude Code sets background mode per call with the Agent tool's `run_in_background`. The agent is limited to `Bash` and `Read`.
- `pr-review-canvas`: there is no Cursor in-app browser. The skill writes `/tmp/pr-review-<number>.html` and gives you its path, and can serve it on `127.0.0.1:8432` if you prefer a URL. Asset paths use `${CLAUDE_SKILL_DIR}`, so the assembly script works from any working directory.
- `workflow-from-chats` reads Claude Code transcripts (`~/.claude/projects/<project>/*.jsonl`) instead of Cursor chats. Its output targets `.claude/skills/`, `CLAUDE.md`, or `.claude/rules/`.
- All other skills are unchanged copies of the upstream text.

## License

MIT
