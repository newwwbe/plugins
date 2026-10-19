# Orchestrate for Claude Code

Claude Code port of the [Orchestrate](../../orchestrate/) Cursor plugin. Fan a large task out across parallel Claude Code agents, each in its own git worktree and branch. Planners publish tasks, workers and verifiers hand off back up, and a script reconciles the tree from disk and git, so the spawn / wait / handoff loop keeps converging without long-running agent state.

The skill lives in [`skills/orchestrate/SKILL.md`](./skills/orchestrate/SKILL.md); its `references/` are the full operating manual.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install orchestrate@cursor-plugins
```

Prerequisites: `git`, `python3` (stdlib only, no install step), and the `claude` CLI on PATH. Run it inside a git repository with at least one commit.

## Usage

```
/orchestrate:orchestrate <goal>
```

This conversation becomes the root planner. It writes `.orchestrate/<slug>/plan.json`, then drives it with the bundled script:

```bash
python3 <plugin>/skills/orchestrate/scripts/orch.py run .orchestrate/<slug>
```

`run` spawns each ready task as a detached headless `claude -p` agent in `.orchestrate/<slug>/worktrees/<task>/` on branch `orch/<slug>/<task>`, then returns on the next event (new handoff, failure, or a 540 s wait) so the planner can read handoffs and replan. Other subcommands: `validate`, `prompt`, `status`, `tree`, `respawn`, `kill`, `andon raise|clear`, `cleanup`, `prepare` / `record` (Agent-tool backend), and `kickoff` (detached root planner).

Ask for a detached run ("kick it off in the background") and the skill launches the root planner itself as a `claude -p` process and returns the workspace path.

| Agent (`subagent_type`) | Description |
|:--|:--|
| `orchestrate:orchestrate-worker` | Agent-tool backend worker. Reads the brief `orch prepare` rendered, works in its worktree, returns a handoff. |
| `orchestrate:orchestrate-verifier` | Agent-tool backend verifier. Runs a target's acceptance checks and returns a `## Verification` verdict. |

**Permissions.** Headless workers can't answer permission prompts. They run with `--permission-mode acceptEdits` and an `--allowedTools` list that includes Bash, so they can run any shell command in their worktree. Change `permissionMode`, `allowedTools`, or `claudeArgs` in `plan.json` to tighten or loosen this. Every worker is a full Claude session; `maxParallel` (default 4) caps concurrency and cost.

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) are dropped. The skill is invoked as `/orchestrate:orchestrate` and stays user-only (`disable-model-invocation: true`).
- **No Cursor cloud agents or Cursor SDK.** The Bun/TypeScript CLI (`scripts/cli.ts`, ~6k lines plus tests) drove Cursor cloud agents through `@cursor/sdk` and is not shipped. It is replaced by `scripts/orch.py`, a stdlib Python driver that runs workers locally as `claude -p` processes in git worktrees, or prepares briefs for parallel Agent-tool subagents. No `CURSOR_API_KEY`, `bun`, or remote VMs.
- **Root planner runs here.** In Cursor, `/orchestrate` was a one-shot dispatcher that started a cloud root planner. Here the invoking conversation is the root planner by default; `orch kickoff` keeps the detached-dispatcher mode with a background `claude -p` root.
- **Subplanners are `claude -p` processes.** Claude Code subagents cannot spawn subagents, so recursive subplanners always run through `orch run`; the Agent-tool backend covers flat worker/verifier fan-out only.
- **Local git instead of pushed cloud branches.** Branches are created up front as `orch/<slug>/<task>` in one shared local repo, so downstream tasks build on upstream branches without pushing. Only `openPR` workers push (and open a draft PR with `gh`). Run state is excluded from git via `.git/info/exclude`; the `syncStateToGit` option is gone.
- **`run` returns on events.** Instead of a long foreground heartbeat with checkpoint exit 100, `run` returns on each new handoff or failure (or after `--max-wait`) so it fits Claude Code's 10-minute Bash limit; agents keep running and the next call reattaches by pid. Exit codes are documented in `references/planner.md`.
- **Slack, comment queue, and Slack-reaction Andon are removed.** Andon is a file flag (`orch andon raise|clear`) in the root `state.json` that subplanner workspaces read through `plan.andonStatePath`. Visibility is `orch status` / `orch tree`, `handoffs/`, and `attention.log`.
- **Models.** The multi-vendor Cursor model catalog (GPT, Composer, Opus variants) is replaced by Claude aliases: `sonnet` for workers and verifiers, `opus` for subplanners and the detached root, `haiku` for cheap mechanical tasks. Override per task with `tasks[].model` or per type with `plan.defaultModels`.
- **Failure handoffs** keep the same failure modes (`cap-hit`, `oom`, `network-drop`, `tool-error`, `unknown`) and the finished-without-handoff sidecar, now derived from `claude -p` JSON results, exit codes, and `plan.taskTimeoutMinutes`. They carry the Claude session id for `claude --resume`.
- Kept: the planner/worker/subplanner/verifier roles, core principles, plan fields (`scopedGoal`, `brief`, `paths*`, `acceptance`, `verify`, `startingRef`, `dependsOn`, `openPR`, `maxAttempts`, `measurements[]`), upstream-handoff relay, verifier `## Verification` taxonomy recorded on the target task, measurement drift checks, merges-as-tasks, and kill/respawn semantics.

## License

MIT. See [`LICENSE`](./LICENSE).
