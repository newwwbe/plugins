Loop hygiene:
- Drive the workspace with `{{orch}} run <workspace>` in the foreground (Bash timeout 600000). It spawns ready tasks as detached `claude -p` workers, then returns on the next event. Workers keep running between calls; the next `run` reattaches by pid.
- Exit 2: new handoffs. Read each new `handoffs/<task>.md`, publish follow-ups in `plan.json` if needed, rerun.
- Exit 3: `--max-wait` elapsed with tasks still running. Rerun immediately.
- Exit 1: a task failed. The script wrote `handoffs/<task>-failure.md` (crash, timeout) or `handoffs/<task>-finished-no-handoff.md` (no structured handoff). Decide, then rerun.
- Exit 4: pending tasks are blocked (a dependency errored or was cancelled, Andon is raised, or an Agent-backend task is still open). Repair, `respawn`, or drop them from `plan.json`.
- Exit 0: every task is terminal. Call `{{orch}} tree <workspace>` and confirm before you hand off.
- Don't end your turn while this workspace has non-terminal tasks.

Reacting to failure handoffs:
For each task with `status: "error"` and a matching `handoffs/<task>-failure.md`, read the `Failure mode` line and decide:
- `cap-hit` or `oom`: retry with smaller scope (split into narrower tasks, tighter `pathsAllowed`, leaner `scopedGoal`), or raise `plan.taskTimeoutMinutes` if it was converging.
- `network-drop`: retry as-is; treat as transient.
- `tool-error`: retry with a different `model`.
- `unknown`: read the log and stderr paths in the failure handoff; if no signal, treat as transient and retry as-is; abandon if it fails again.
For `<task>-finished-no-handoff.md`, read the raw output at `handoffs/<task>.md` and decide whether the worker's intent was recoverable; retry or abandon.
Retry with `{{orch}} respawn <workspace> <task>` (after editing the task in `plan.json` if scope or model changes). Each retry costs another full agent run; budget your decisions. After 2 retries on the same task, prefer abandon (drop the task from `plan.json`, replan around it) over a 3rd attempt unless you have specific evidence the next retry will succeed.
