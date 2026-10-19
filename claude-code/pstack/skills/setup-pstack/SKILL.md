---
name: setup-pstack
description: Configure which Claude model pstack uses per role. Writes a pstack-models block into ~/.claude/CLAUDE.md that overrides the skill defaults. Use for /setup-pstack, "configure pstack models", "pstack budget", or changing pstack's model choices.
---

# Setup pstack

Write the `pstack-models` block in `~/.claude/CLAUDE.md`. Claude Code loads that file into every session, so the block works as an always-applied rule that sets pstack's model per role.

## Steps

### 1. Know the available models

Claude Code subagents run on Claude models only. The Agent tool's `model` parameter takes the aliases `opus`, `sonnet`, and `haiku`. The value `inherit` is also valid in this block. It means the role runs on the parent chat model, so the skill omits `model`. Do not write a full model ID or any non-Claude model name. If the user says their plan lacks a model (for example no `opus`), do not offer that alias.

### 2. Load current state

The default role-to-model mapping is the `large` column in step 3. If `~/.claude/CLAUDE.md` already has a block between `<!-- pstack-models:start -->` and `<!-- pstack-models:end -->`, read it and treat its `# budget` line and its role values as the current choices. Otherwise start from the defaults. A line whose role is not in the table in step 3 is from a retired role. Drop it. A value that is not `opus`, `sonnet`, `haiku`, or `inherit` (for example a Cursor slug such as `grok-4.7-xhigh-fast`) is invalid. Mark that role as needing a choice.

### 3. Budget, map, and confirm

**(a) Ask for a budget.** Use `AskUserQuestion` with these four options and these exact labels, and name the current budget when the block records one. With no block, say that `large` matches the skill defaults.

- `unlimited — opus everywhere`
- `large — opus for judgment, sonnet for code`
- `medium — sonnet, opus only for the hardest tasks`
- `small — haiku and sonnet`

**(b) Apply it.** Build the working table from the column for the chosen budget. On a re-run, keep any role the user changed by hand, and keep every `inherit` value.

| Role | unlimited | large (default) | medium | small |
|---|---|---|---|---|
| `feature, refactoring` | `opus` | `sonnet` | `sonnet` | `sonnet` |
| `bug-fix` | `opus` | `sonnet` | `sonnet` | `sonnet` |
| `perf-issue` | `opus` | `sonnet` | `sonnet` | `sonnet` |
| `hillclimb` | `opus` | `sonnet` | `sonnet` | `sonnet` |
| `judgment and prose` | `opus` | `opus` | `sonnet` | `sonnet` |
| `hardest tasks` | `opus` | `opus` | `opus` | `sonnet` |
| `how explorer` | `opus` | `sonnet` | `sonnet` | `haiku` |
| `how explainer` | `opus` | `opus` | `sonnet` | `sonnet` |
| `why investigators` | `opus` | `sonnet` | `sonnet` | `haiku` |
| `why synthesizer` | `opus` | `opus` | `sonnet` | `sonnet` |
| `reflect tooling` | `opus` | `sonnet` | `sonnet` | `haiku` |
| `reflect judgment, divergent, synthesizer` | `opus` | `opus` | `sonnet` | `sonnet` |
| `arena runners` | `opus, opus, sonnet` | `opus, sonnet` | `sonnet, sonnet` | `sonnet, haiku` |
| `arena cross-judge pool` | `opus, sonnet` | `opus, sonnet` | `opus, sonnet` | `sonnet, haiku` |
| `swarm workers` | `opus` | `sonnet` | `sonnet` | `haiku` |
| `architect runners` | `opus, opus, sonnet` | `opus, sonnet` | `sonnet, sonnet` | `sonnet, haiku` |
| `interrogate reviewers` | `opus, sonnet` | `opus, sonnet` | `opus, sonnet` | `sonnet, haiku` |

**(c) Show the roles and confirm.** Show every role with its model. Also list each line step 2 dropped and each role marked as needing a choice. Ask whether to accept as-is or change specific roles, offering `opus`, `sonnet`, `haiku`, and `inherit` as the options. Use `AskUserQuestion` when it fits, otherwise ask in chat. For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, `inherit` entries included, so the list length sets the count. `arena cross-judge pool` is also a list, but Arena selects one value from it that differs from the parent's model when possible. `swarm workers` is the default model for every worker unless a race or comparison assigns another model per arm.

### 4. Validate

Every value written must be `opus`, `sonnet`, `haiku`, or `inherit`. If a chosen value is anything else, stop and ask again.

### 5. Write the block

Edit `~/.claude/CLAUDE.md` (create it if it does not exist). Replace everything between the `<!-- pstack-models:start -->` and `<!-- pstack-models:end -->` markers, markers included, with the new block. If there are no markers, append the block at the end of the file. Never change content outside the markers, because the user's own instructions live in the same file. Re-runs stay idempotent. If the user asks for a per-project setting instead, write the same block into the project's `CLAUDE.md`. A project block wins over the user-level block for that project.

Shape:

````markdown
<!-- pstack-models:start -->
## pstack model configuration

Overrides the pstack skill defaults. One line per role. Delete a line to fall back to the skill default. Values are Agent tool `model` aliases. `inherit` means the role runs on the parent chat model (omit `model`). `inherit` entries in a panel list still count toward its fan-out.

```text
# budget: large
feature, refactoring: sonnet
bug-fix: sonnet
perf-issue: sonnet
hillclimb: sonnet
judgment and prose: opus
hardest tasks: opus
how explorer: sonnet
how explainer: opus
why investigators: sonnet
why synthesizer: opus
reflect tooling: sonnet
reflect judgment, divergent, synthesizer: opus
arena runners: opus, sonnet
arena cross-judge pool: opus, sonnet
swarm workers: sonnet
architect runners: opus, sonnet
interrogate reviewers: opus, sonnet
```
<!-- pstack-models:end -->
````

### 6. Confirm

Tell the user the block was written, give the file path, and say that it applies to new sessions (run `/memory` or start a new session to reload it). Re-running this skill updates it.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill under `.claude/skills/`, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /pstack:create-verification-skill." On yes, read `../create-verification-skill/SKILL.md` from this file and follow it. On no, move on without pushing.
