Operating manual for root and subplanners. Dispatchers read `dispatcher.md`.

# Planner

Root and subplanners behave the same way. The root reports to the user; a subplanner reports to its parent.

`orch` below means `python3 <skill-dir>/scripts/orch.py` with the absolute path.

## Source of truth

Git and disk are the substrate.

- `plan.json` carries the task graph, base branch, model and permission choices.
- `state.json` carries task status, attempts, pids, worktrees, branch names, session ids, and verification results.
- `handoffs/*.md` carries worker and verifier output.
- `attention.log` carries operator-visible failures and decisions (measurement drift, branch mismatches, Andon, retries).
- `prompts/<task>.md` is exactly what each agent was sent; `logs/` holds each `claude -p` run's JSON result and stderr.

The workspace lives at `.orchestrate/<rootSlug>/` in the repo. The script adds `.orchestrate/` to the repo's `.git/info/exclude`, so run state never lands in commits. Worktrees live at `.orchestrate/<rootSlug>/worktrees/<task>/`.

## Phase 1: publish tasks

Write `plan.json` at `<workspace>`; the default workspace is `.orchestrate/<rootSlug>/`. Create the directory first. As root planner in this conversation, set `baseBranch` to the branch the work should start from (usually the current branch).

```json
{
  "$schema": "<skill-dir>/schemas/plan.schema.json",
  "goal": "<verbatim user goal>",
  "summary": "ship the dark-mode toggle end to end",
  "rootSlug": "dark-mode",
  "baseBranch": "main",
  "maxParallel": 4,
  "tasks": [
    {
      "name": "frontend-toggle",
      "type": "worker",
      "scopedGoal": "Add a Settings UI toggle that flips `useDarkMode` in localStorage.",
      "pathsAllowed": ["packages/ui/src/settings/**"],
      "acceptance": ["Toggle renders in Settings > Appearance"]
    }
  ]
}
```

`summary` is for the human reading `status`; `goal` is the agents' full context. Run `orch validate <workspace>` after every edit; `run` refuses an invalid plan.

Optional plan-level knobs:

| Field | Default | Meaning |
|-------|---------|---------|
| `maxParallel` | 4 | Concurrent `claude -p` agents this workspace runs. Each one costs a full Claude session. |
| `taskTimeoutMinutes` | 90 | Per-task wall clock; past it the agent is killed and a `cap-hit` failure handoff is written. |
| `defaultModels` | `{"worker":"sonnet","verifier":"sonnet","subplanner":"opus"}` | Per-type model aliases; `tasks[].model` wins. |
| `permissionMode` | `acceptEdits` | Passed to `claude -p --permission-mode`. |
| `allowedTools` | Bash, Read, Edit, Write, MultiEdit, Glob, Grep, Agent, TodoWrite, WebFetch, WebSearch | Passed to `--allowedTools`. Headless agents cannot answer permission prompts, so anything not allowed is denied. |
| `claudeArgs` | `[]` | Extra CLI args appended to every `claude -p` call (e.g. `["--add-dir", "../shared"]`). |
| `prBase` | `baseBranch` | Base for `openPR` workers' PRs. |
| `andonStatePath` | none | Absolute path of the root `state.json` whose Andon also stops this workspace. Subplanners set it from their prompt. |

Planning rules:

- Merges are tasks. Publish a worker whose `scopedGoal` says which branches to merge, conflict intent, and verification. A worker named `merge-*` is told to merge its `dependsOn` branches in order.
- Prefer a worker unless you can name the decomposition a subplanner would do.
- One worker can carry a lot. Workers and verifiers are full Claude Code sessions: multi-file slices, multi-step refactors, full repro/fix/test cycles all fit in a single spawn. Each spawn costs a full session and your own coordination overhead. Default to fewer, broader workers; reach for finer granularity only when a slice is genuinely independent or has real contention risk.
- Default to verifiers. Use `type: "verifier"` and `verifies: "<target-task-name>"`.
- Use `verify` for the concrete check recipe. Workers read it as target behavior; verifiers inherit it from their target.
- Set `openPR: true` only for independent worker tasks you want shipped as their own draft PRs (needs a pushable `origin` and `gh`).
- Add `measurements[]` for quantitative claims. The script reruns each command in the worker's worktree after handoff and logs drift.
- Keep fan-in small. If a task needs many upstream handoffs, publish an aggregation worker first.
- Minimize path overlap. List forbidden paths when sibling ownership matters.
- Put task specs in `plan.tasks[]`. Put shared artifacts in git (commit them to `baseBranch` before spawning) and reference them by path.
- Model choice per task: `opus` for the hardest judgment, ambiguous or design-heavy slices; `sonnet` for routine implementation and most verification; `haiku` for cheap mechanical, well-specified edits.

## Phase 2: drive the workspace

Pick a backend per task. Both write the same handoffs and state.

### `claude -p` backend (default, required for subplanners)

```bash
orch run <workspace>
```

Run it in the foreground with a 600000 ms Bash timeout. `run` spawns pending tasks whose dependencies have handed off (up to `maxParallel`), each as a detached `claude -p` process in its own worktree, then waits and returns on the next event:

| Exit | Meaning | Your move |
|------|---------|-----------|
| 0 | Every task is terminal. | `orch tree`, then hand off / report. |
| 1 | New failure handoffs. | Read them, decide (see Failure recovery), rerun. |
| 2 | New handoffs. | Read them, publish follow-ups if needed, rerun. |
| 3 | `--max-wait` (default 540 s) elapsed with agents still running. | Rerun. |
| 4 | Pending tasks are blocked (failed or cancelled dependency, Andon, or an open Agent-backend task). | Repair, `respawn`, drop, or record the open Agent task. |

Agents survive between `run` calls; the next call reattaches by pid. `--until-done` keeps waiting through successful handoffs (still bounded by `--max-wait`). `--dry-run` shows what would spawn. Don't end your turn while the workspace has non-terminal tasks.

### Agent-tool backend (workers and verifiers only)

For a flat fan-out driven from this conversation without separate processes:

1. `orch prepare <workspace> <task>` creates the worktree and branch, renders the prompt, marks the task running, and prints `subagent_type`, `model`, `agentPrompt`, and the handoff file path.
2. Call the Agent tool with that `subagent_type` (`orchestrate:orchestrate-worker` or `orchestrate:orchestrate-verifier`), `model`, and `agentPrompt` as the prompt. Launch every ready task in one message so they run in parallel; `run_in_background: true` is fine.
3. When each subagent returns, `orch record <workspace> <task>`. It reads the handoff file the subagent wrote; if that file is missing, save the subagent's final message to a file and pass `--file <path>`. Use `--error <mode>` if the subagent died.

Subagents cannot spawn subagents, so subplanner tasks always use `orch run`. Don't mix backends on the same task.

### Inspecting

`orch status <workspace>` (add `--json` for machine output), `orch tree <workspace>` (recurses into subplanner workspaces under their worktrees), `orch prompt <workspace> <task>` to preview a prompt before spawning.

## Failure recovery

Script handles mechanical liveness. Planner handles meaning.

- A crashed or timed-out agent gets `handoffs/<task>-failure.md` with a failure mode; an agent that ended without the structured template gets `handoffs/<task>-finished-no-handoff.md`. Both leave the task in `error`.
- Retry with `orch respawn <workspace> <task>` (edit the task first if scope or model should change). Workers and verifiers restart from `startingRef` on a fresh branch; the previous attempt's branch is kept as `orch/<slug>/<task>-attempt<N>`. Subplanners resume on their own branch so committed child state survives.
- `maxAttempts` (default 3) caps spawns per task. Bump it only when another attempt is intentional.
- Downstream tasks stay `pending` when an upstream fails, and `run` exits 4. Fix the upstream and rerun, or `orch kill` / remove the abandoned downstream work.
- `orch kill <workspace> <task>` (or `--all`) terminates running `claude -p` agents, recursing into subplanner workspaces, and marks them `cancelled`.
- Removing a task from `plan.json` marks it `pruned`.
- `orch cleanup <workspace>` removes worktrees of terminal tasks; branches stay.

### Andon

Andon pauses new spawns across the tree.

```bash
orch andon <root-workspace> raise --reason "<why>"
orch andon <root-workspace> clear [--note "<what changed>"]
```

`--reason` is required on `raise` and is stored (capped at 500 chars) in the root `state.json`. Subplanner workspaces point `plan.andonStatePath` at that file, so their `run` loops stop spawning too. Running agents are not interrupted; use `kill` for that.

Raise Andon only when continued spawning will produce garbage for the tree: bad upstream output, broken acceptance, or unrecoverable auth/infra. A task's own snag belongs in its handoff, not Andon.

## Finishing

When every task is terminal and you have stopped publishing:

- Root planner: report to the user what shipped, on which branches, with what `## Verification` per deliverable, and what is left. Offer to open a PR from the final merge branch; push and open PRs only when the user asks (or a task set `openPR`). Offer `orch cleanup`.
- Subplanner: your final message is your handoff (see `handoffs.md`).
