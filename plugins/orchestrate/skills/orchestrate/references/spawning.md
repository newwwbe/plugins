# Spawning tasks

Contract between `plan.json` entries and the agents the script spawns.

## Branches and worktrees

Every task gets the branch `orch/<rootSlug>/<task-name>` and a worktree at `<workspace>/worktrees/<task-name>/`, both created by the script from the task's starting ref before the agent starts. Kebab-case names are enforced so task names feed paths, branch names, and prompt text without escaping. There is no auto-managed integration branch: branches live independently until a merge task consolidates them (see `handoffs.md` → "Merges are tasks").

Agents commit to the branch already checked out in their worktree and never create, rename, or switch branches. They do not push unless the task sets `openPR`. Because every worktree shares the one local repository, a downstream task can start from an upstream branch the moment the upstream hands off, with nothing pushed anywhere.

If a handoff's `## Branch` names a different branch than planned (for example a merge worker that merged into a sibling's branch), the script records it as the task's actual branch, logs it to `attention.log`, and uses it for dependents.

## Starting refs and dependencies

| Field | Controls | Default | Pair with |
|-------|----------|---------|-----------|
| `startingRef` | Which ref the task's branch is created from | `plan.baseBranch` (verifiers: their target's branch) | `dependsOn` when depending on another task's work |
| `dependsOn` | When the task is allowed to spawn | `[]` | The upstream's actual branch, resolved after handoff |

`startingRef` may name another task's planned branch (`orch/<rootSlug>/<task>`); the script substitutes that task's actual branch. `startingRef` without `dependsOn` gives a point-in-time snapshot: whatever commits exist on that branch at spawn time, which may be nothing. Pair them unless you really mean "start from the current tip, even if empty".

Verifiers default `startingRef` to their target's branch and auto-include the target in `dependsOn`; the planner doesn't need to wire either explicitly.

Any task can set `verify`: a Markdown-formatted plan (setup, automated, manual, gotchas). Workers see it as a target spec; verifiers inherit the target's `verify` as their recipe.

## Backends

| Backend | How | Good for | Limits |
|---------|-----|----------|--------|
| `claude -p` (`orch run`) | Detached headless Claude Code process per task, `cwd` = the worktree, prompt on stdin, JSON result captured to `logs/` | Everything, including subplanners; long tasks; runs that outlive this conversation's turn | Needs `claude` on PATH; uses `plan.permissionMode` / `plan.allowedTools` since nobody can answer prompts |
| Agent tool (`orch prepare` / `orch record`) | `orchestrate:orchestrate-worker` / `orchestrate:orchestrate-verifier` subagents launched in parallel from this conversation | Flat fan-out of workers and verifiers when you want results inside the conversation | No subplanners (subagents cannot spawn subagents); the planner must record each handoff |

## Spawn design decisions

- **PRs are opt-in per task.** When `openPR: true`, the worker is told to push its branch and open a draft PR against `plan.prBase ?? plan.baseBranch` with `gh pr create --draft`. Subplanners and verifiers never open PRs; they hand off to their parent.
- **PR base vs. worker starting ref.** `plan.baseBranch` is the starting ref for workers that don't specify their own. `plan.prBase` (optional, defaults to `baseBranch`) is where `openPR` workers aim their PRs. Split them when workers should inherit planner-side setup from one branch but open PRs against `main`.
- **No shared integration branch.** Each task is its own island until a merge task consolidates them. An auto-managed integration branch would smuggle planner-level coding decisions into infrastructure, violating Core Principle #1.
- **Retries start clean.** A worker or verifier respawn resets its branch to `startingRef`; the previous attempt survives as `orch/<rootSlug>/<task>-attempt<N>`. A subplanner respawn reuses its branch.

## Task prompt contract

The script renders prompts from `scopedGoal`, `brief`, `pathsAllowed`, `pathsForbidden`, `acceptance`, `verify`, `startingRef`, `type`, `openPR`, and the upstream handoffs. Fix the plan entry if the prompt doesn't match your intent. Don't patch the prompt template. Every spawned prompt tells the agent:

- Its worktree path and branch. It's isolated. No communication with other agents.
- Commit to the checked-out branch. No branch renames, merges (except `merge-*` workers), rebases, or pushes. Open a draft PR only if the task sets `openPR: true`.
- Final message is the handoff in the structure from `handoffs.md`. That's the only thing the planner reads.

Subplanner prompts point at this skill's `SKILL.md` and `references/planner.md` by absolute path, give the subplanner its own workspace under its worktree, and name the root `state.json` for Andon.

Workers cannot ask clarifying questions mid-run. Under-specified `scopedGoal` produces silent drift. Write each task as if you'll never get another chance to steer it.

Do not rely on environment variables for data multiple agents must share. Use the planner-authored artifact pattern instead: commit a file to the base branch and reference it by path in `scopedGoal` so worktrees pick it up. Never paste credentials into `scopedGoal`; it is written to `prompts/` and sent to the model.

## Tracking & recovery

After each spawn the script persists the pid, worktree, branch, model, prompt file, and log paths to `state.json`; after the agent exits it adds the Claude session id and cost. A later `run` re-attaches to live pids and reads finished results from disk, so the planner can exit and resume `run` freely.

After every handoff, dependents resolve their starting ref and upstream relay from the recorded actual branch and handoff body.

## Lineage

Each subplanner's workspace lives at `<its worktree>/.orchestrate/<task-name>/`, with `rootSlug` `<parentSlug>-<task-name>`. `orch tree` and `orch kill` walk that layout downward from the root workspace.
