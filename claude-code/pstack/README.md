# pstack for Claude Code

Claude Code port of the [pstack](../../pstack/) Cursor plugin by [poteto](https://x.com/poteto). If you want to go fast, go deep first. pstack helps you write less, but higher quality code: a mode skill that routes each task to a playbook, situational workflow skills (`how`, `why`, `architect`, `arena`, `swarm`, `interrogate`, `reflect`, ...), and twenty-four one-rule principle skills.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install pstack@newwwbe
```

For the full set, also install `cursor-team-kit` from the same marketplace. pstack's playbooks call its `deslop`, `control-cli`, and `control-ui` skills.

## Get started

1. Run `/pstack:setup-pstack`. Pick a budget and the Claude model (`opus`, `sonnet`, `haiku`, or `inherit`) for each role. It writes a `pstack-models` block into `~/.claude/CLAUDE.md` (or the project's `CLAUDE.md` if you ask), between `<!-- pstack-models:start -->` and `<!-- pstack-models:end -->` markers. Start a new session afterwards.
2. Start any task that needs rigor with `/pstack:poteto-mode`, a goal, and a check that can pass or fail:

```
/pstack:poteto-mode this pr has a subtle bug where the scroll drifts every 750ms even when idle. repro first, then fix and verify.
```

New here? Ask `/pstack:poteto-help`, or read the [pstack guide](./docs/guide/README.md). The guide and the skills write commands as `/name`. In Claude Code, type them as `/pstack:name`.

Default model split (the `large` budget): code delegates (feature, refactoring, bug fix, perf, hillclimb), explorers, investigators, and swarm workers run on `sonnet`. The hardest changes, prose, judgment, explainers, and synthesizers run on `opus`. Review panels (arena, architect, interrogate) run one `opus` and one `sonnet` member.

## Usage

| Command | What it does |
|:--------|:-------------|
| `/pstack:poteto-mode` | Default entry point. Matches the task to one of 23 playbooks (bug fix, feature, perf, investigation, babysit, shipping, orchestrate, autopilot, ...), copies its steps into the todo list, and runs the other skills as the steps need them. |
| `/pstack:poteto-help` | Finds the right skill, playbook, or principle and hands you a prompt to send. |
| `/pstack:setup-pstack` | Per-role Claude model configuration. The only skill the model may load on its own. |
| `/pstack:how`, `/pstack:why`, `/pstack:teach` | How a subsystem works, why it was built that way (fans out one investigator per MCP evidence source), or both explained plainly. |
| `/pstack:architect`, `/pstack:arena`, `/pstack:swarm`, `/pstack:interrogate` | Design exploration, N-candidate bakeoff with grafting, parallel workers with one report, multi-model adversarial review. |
| `/pstack:recall`, `/pstack:ketchup`, `/pstack:bro` | Rebuild context from your Claude Code transcripts, catch up on this chat, restate the last reply plainly. |
| `/pstack:blast-radius`, `/pstack:tdd`, `/pstack:benchmark-checklist` | Breakage outside the diff, test-first bug fixing, vetting a measured number. |
| `/pstack:no-comments`, `/pstack:unslop`, `/pstack:technical-writing`, `/pstack:typescript-best-practices` | Comment stripping via the Comment Sicko agent, prose cleanup, doc standard, TypeScript rules. |
| `/pstack:figure-it-out`, `/pstack:show-me-your-work` | Bespoke rigorous playbook for big or unattended work, and an auditable decision log. |
| `/pstack:create-verification-skill`, `/pstack:maintain-verification-skill` | Generate or repair a project-local `.claude/skills/verify-<app>/` skill that drives the real app. |
| `/pstack:automate-me`, `/pstack:reflect`, `/pstack:correct`, `/pstack:sharpen`, `/pstack:in-your-own-words` | Personal mode skill from your history, lessons into skill edits, recurring-mistake enforcement, aim a task higher, play back your goal. |
| `/pstack:principle-<name>` | One principle each (laziness-protocol, prove-it-works, model-the-domain, ...). `poteto-mode` indexes and reads them. |
| `/pstack:make-bot-ui` | Cursor only. See limitations. |

All skills except `setup-pstack` are user-invoked only (`disable-model-invocation: true`), as in the Cursor version. `poteto-mode` reads the other skills by path (`../<name>/SKILL.md` from its own directory) when a step needs them.

## Agents

| Agent (`subagent_type`) | Description |
|:------------------------|:------------|
| `pstack:poteto-agent` | Delegate for code-writing and helper steps inside a `poteto-mode` run. Reads `${CLAUDE_PLUGIN_ROOT}/skills/poteto-mode/SKILL.md` in full before any work. |
| `pstack:comment-sicko` | Comment-hating reviewer spawned by `/pstack:no-comments`. Report only. |

## Scripts

`skills/poteto-mode/scripts/` ships the playbook tooling. It needs [Bun](https://bun.sh) (and Node for `check-plan.mjs`). The first run of `orch` or `watch-pr` installs its one dependency (`commander`) into `scripts/node_modules`.

- `bun scripts/orch/orch.ts --store <dir> <command>` (or `ORCH_STORE=<dir>`): bookkeeping for the Orchestrate playbook.
- `scripts/watch-pr/watch-pr`: GitHub PR and stack watcher for the Babysit and Shipping playbooks (needs `gh`).
- `node scripts/check-plan.mjs <plan.md>`: lints a Multi-phase plan.
- `scripts/worktree-audit.sh`: worktree cleanup audit. It now reads Claude Code transcripts under `~/.claude/projects/<slug>/`.

`bun test orch watch-pr check-plan.test.ts` passes (68 tests).

## Differences from the Cursor version

- The manifest lives in `.claude-plugin/plugin.json`. Cursor-only fields (`displayName`, `logo`, `category`, `tags`) are dropped, and the duplicate root `plugin.json` is not shipped. Skill names are unchanged, except that `Poteto Mode` and `Make Bot UI` use their directory names (`poteto-mode`, `make-bot-ui`) as `name`. The Cursor-only `icon`/`color` frontmatter and the agent's `is_background` are dropped.
- **Model routing.** Cursor routed roles across vendors (`grok-4.7-xhigh-fast` for code, `claude-opus-5-5-xhigh` for judgment) with a reasoning-effort ladder and fast/standard speed. Claude Code only runs Claude models and has no per-subagent effort setting, so every role maps to an Agent tool alias (`opus`, `sonnet`, `haiku`, or `inherit` in place of `auto`/`inherit-parent`). The "match the model to the job" rule moves between tiers instead of effort levels. Multi-model panels are `opus` + `sonnet`, which gives less diversity than two vendors.
- **Model configuration.** `setup-pstack` writes a marked `pstack-models` block into `~/.claude/CLAUDE.md` (or a project `CLAUDE.md`) instead of the always-applied rule `~/.cursor/rules/pstack-models.mdc`. It only rewrites the text between its markers. Budgets are `unlimited` / `large` / `medium` / `small` as before, defined as a per-role table of aliases.
- **Subagents.** Cursor `Task` calls become Agent tool calls. `generalPurpose` becomes `general-purpose`. `readonly: true` becomes a read-only instruction in the prompt (a read-only agent type such as `Explore` lacks MCP tools). Plugin agents are namespaced (`pstack:poteto-agent`, `pstack:comment-sicko`). Resuming an agent uses `SendMessage`.
- **Cloud agents.** Cursor cloud agents (`environment: "cloud"`, `cloud_base_branch`, a VM per worker) have no Claude Code equivalent. `swarm`, `arena`, Orchestrate, Autopilot-full, and Shipping use background subagents with `isolation: "worktree"` on the local machine. Orchestrate notes `claude -p` processes or Claude Code on the web for sub-coordinators and heavy units, because Claude Code subagents cannot spawn their own subagents.
- **Paths.** Transcripts are read from `~/.claude/projects/<slug>/` (Claude Code's JSONL layout) instead of `~/.cursor/projects/<slug>/agent-transcripts/`, in `reflect`, `recall`, `automate-me`, `show-me-your-work`, the Eval and Session pickup playbooks, and `worktree-audit.sh`. Project skills go in `.claude/skills/`. The agent store that Cursor named in its system prompt is `~/.claude/pstack/store/<repo-name>/`.
- **Built-ins.** `AskQuestion` becomes `AskUserQuestion`. Cursor's `create-skill` becomes `skill-creator` when installed, otherwise the Authoring a skill playbook. `/loop` is Claude Code's own `/loop` (or a scheduled task). Cursor Custom Modes, Plan Mode, and `/visualize` are replaced by plain guidance (restart each task with `/pstack:poteto-mode`, Claude Code's plan mode, ASCII diagrams). `cursor-team-kit` skills are referenced as `/cursor-team-kit:<skill>`.
- The `README`, the guide under `docs/guide/`, and `poteto-help` describe Claude Code installation and commands. The rest of the skill text, playbooks, principles, and references are upstream text.

## Limitations

- **`make-bot-ui`** drives a Cursor Grok Bot (`update_state` routines, `SendToUser` secret requests, the `api2.cursor.sh` webhook). It is kept as reference with a Cursor-dependency note and does not work inside Claude Code.
- **`automations/benny/`** is a dormant pack for Cursor Automations (Slack-triggered cloud runs set up through Cursor's `/automate`). It ships unchanged. Its README explains how to approximate it in Claude Code with a scheduled task or `/loop` that polls Slack through an MCP server.
- Bugbot and the agentic security review are Cursor's GitHub reviewers. The triage rules and `watch-pr` still handle their comments when they run on your repository.
- Background subagents share this machine's CPU, ports, and credentials, so very large Orchestrate or Autopilot fan-outs need a smaller in-flight window than Cursor cloud agents allowed.

## License

MIT
