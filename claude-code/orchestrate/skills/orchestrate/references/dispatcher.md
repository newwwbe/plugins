Operating manual for the dispatcher. If you were spawned with a prompt starting "You are the root planner for:" or "You are a subplanner for:", read `planner.md` instead. If the user typed `/orchestrate:orchestrate <goal>` and did not ask for a detached run, you are the root planner: read `planner.md`.

# Dispatcher

The dispatcher is one-shot. Take the user's goal, launch a detached root planner, return the workspace path, stop.

## The job

1. Take the user's goal. Ask for clarification only if the goal is missing or ambiguous. The user chose parallel orchestration deliberately; push back only if the task is genuinely trivial.
2. Tell the user the permission posture (headless `claude -p` agents with `acceptEdits` and the default tool allowlist, which includes unrestricted Bash in their worktrees) and get a yes if they have not already given one.
3. Run kickoff from inside the target repository:

   ```bash
   orch kickoff "<goal>" [--slug <kebab-slug>] [--base <branch>] [--model opus|sonnet|haiku]
   ```

   It creates `.orchestrate/<slug>/` with a skeleton `plan.json` (goal, rootSlug, baseBranch), renders `prompts/root.md`, and starts a detached `claude -p` root planner in the repo root. It prints `{ workspace, pid, log, stderr, status }` JSON.
4. Return the workspace path and the status command to the user. Stop. The planner self-drives.

## Minimal-goal discipline

Pass the user's goal through without expanding it. Don't add planning heuristics, subplanner counts, or structural prescriptions. The planner reads the orchestrate skill and decides its own decomposition. Over-prescribing leaks dispatcher context into the planner's window and invalidates the skill as a realistic test of the planner's judgment.

## Observability after kickoff

- `orch status <workspace>` for the task table; `orch tree <workspace>` for the recursive tree including subplanner workspaces.
- `handoffs/*.md` and `attention.log` in the workspace.
- `logs/_root.json` holds the root planner's final JSON result (its `result` field is the user-facing report) once it exits.
- Stop the whole run with `orch kill <workspace> --all`, then `kill <pid>` for the root planner if it is still alive.
