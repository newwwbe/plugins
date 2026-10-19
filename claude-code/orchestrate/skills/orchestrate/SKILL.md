---
name: orchestrate
description: Use only when the user explicitly types `/orchestrate:orchestrate <goal>` to decompose a large task, fan it out across parallel Claude Code workers/subplanners/verifiers running in their own git worktrees, and collect structured handoffs; do not invoke autonomously.
disable-model-invocation: true
---

# Orchestrate

An explicit `/orchestrate:orchestrate <goal>` fans out a large task across parallel Claude Code agents, each in its own git worktree and branch. Workers don't talk to each other; they talk up through structured handoffs. The spawn, wait, and handoff loop lives in `scripts/orch.py` (Python 3, stdlib only). The planner writes `plan.json`, the script executes it, and the planner reads handoffs to decide what comes next. Long-running agent loops drift; a script with a JSON state file keeps its footing.

In the commands below, `orch` means `python3 <this skill's directory>/scripts/orch.py`. Use the absolute path.

## Setup

- `git` and `python3` on PATH, and the current directory inside a git repository with at least one commit.
- `claude` on PATH for the `claude -p` backend (the default, and required for subplanners).
- Workers launched by `orch run` are headless `claude -p` processes. They run with `plan.permissionMode` (default `acceptEdits`) and `plan.allowedTools` (default: Bash, Read, Edit, Write, MultiEdit, Glob, Grep, Agent, TodoWrite, WebFetch, WebSearch). That allowlist lets workers run any shell command in their worktree without asking. Tell the user this before the first `run`, and narrow `allowedTools` in `plan.json` if they want less.

## Core principles

These rules make the tree self-converging without global coordination.

1. **Planners own scopes and publish tasks. They do no coding.** Writing `plan.json`, reading handoffs, and deciding what's next are planner work. Editing files, running `git merge`, and fixing conflicts inline are not. If a planner feels the urge to code, it publishes a task for a worker instead.
2. **Planners don't know who picks up their tasks.** The script routes each task to an agent. The planner's mental model stays at the task level.
3. **Workers are isolated.** One task, one worktree on its own branch, no channel to any other agent. One handoff when done.
4. **Subplanners are recursive planners.** A planner publishes a "subplan this slice" task; the subplanner fully owns that slice and hands back an aggregated handoff.
5. **Continuous motion via handoffs.** A planner that thought it was done can receive a late handoff and replan. No "finished" state until the planner decides to stop publishing.
6. **Propagation, not synchronization.** No cross-talk between siblings. No shared state between levels. Each level sees only its children's handoffs.

## Node types

| Node           | Runs the loop? | Scope                            | Output                                  | Runs as |
| -------------- | -------------- | -------------------------------- | --------------------------------------- | ------- |
| Planner        | yes            | Entire user goal                 | User-facing message + optional PR       | This conversation (or a detached `claude -p` via `kickoff`) |
| Subplanner (↻) | yes            | One slice of parent's scope      | Handoff to parent                       | `claude -p` process (needs its own Agent tool and `orch`) |
| Worker         | no             | One concrete task                | Handoff to spawning planner             | `claude -p` process, or an `orchestrate:orchestrate-worker` subagent |
| Verifier       | no             | One target's acceptance criteria | Verdict handoff to spawning planner     | `claude -p` process, or an `orchestrate:orchestrate-verifier` subagent |
| Git            | n/a            | Shared medium                    | Branches (code) + handoffs/ (meaning)   | Local repo; worktrees under the workspace |

## Role

Two roles, one skill. Read your role's reference file and skip the other.

**Planner (root or sub).** The default. The user typed `/orchestrate:orchestrate <goal>` in this conversation, or you were spawned with a prompt that opens with "You are the root planner for:" or "You are a subplanner for:". You own a scope, publish tasks, read handoffs, decide what's next. See `references/planner.md`.

**Dispatcher.** Only when the user asks for the run to proceed in the background without this conversation driving it ("kick it off and let it run", "detached"). Launch a detached root planner and return its workspace path. See `references/dispatcher.md`. One-shot; you are not the planner.

Shared contracts: `references/handoffs.md` (handoff formats, verifiers, merges) and `references/spawning.md` (branches, worktrees, backends, prompts).
