# Set up pstack

In this page you install the plugin, pick which models pstack uses, and run your first task. Setup is one command plus a short conversation.

## Install the plugin

In Claude Code, run:

```text
/plugin marketplace add newwwbe/plugins
/plugin install pstack@newwwbe
```

Claude Code confirms the plugin is installed. Plugin skills are namespaced, so every `/name` in this guide is typed as `/pstack:name`, for example `/pstack:poteto-mode`.

## Pick your models

Run:

```text
/pstack:setup-pstack
```

[`/setup-pstack`](../../skills/setup-pstack/SKILL.md) asks for a budget, shows you each role (code delegates, judgment, the review panels) with a Claude model alias (`opus`, `sonnet`, or `haiku`), and asks what you want. Answer the questions. It writes a `pstack-models` block into `~/.claude/CLAUDE.md`, which Claude Code loads into every session and every pstack skill reads. It only touches the text between its `<!-- pstack-models:start -->` and `<!-- pstack-models:end -->` markers.

The defaults match the `large` budget: `opus` for judgment, prose, and the hardest tasks, `sonnet` for code delegates, explorers, and swarm workers, and an `opus` plus `sonnet` pair on each review panel. `unlimited` puts every role on `opus`. `medium` and `small` move roles down to `sonnet` and `haiku` and spend fewer tokens. Claude Code has no per-subagent reasoning-effort setting, so the model alias is the only dial.

You only override what you care about. A role with no line in the rule keeps the skill's default. To restore a default, delete that role's line. A rerun of `/setup-pstack` keeps any role whose model differs from the default. When a default changes, a block written before the change still pins the old default, so delete those role lines, or the whole block, then run `/setup-pstack` again.

Set a role to `inherit` and pstack omits the Agent tool's `model` field, so the subagent runs on your parent chat model. For a panel role the value is a list, and one subagent runs per entry, so the list length sets the panel size. Setup also configures `swarm workers`, the default model for every `/swarm` worker unless a race names a model for each arm.

## Accept the verification offer, or don't

At the end of setup, `/setup-pstack` looks for a way to prove app behavior in your project, either a `verify-*` skill or an existing harness. If it finds neither, it offers once to generate one with [`/create-verification-skill`](../../skills/create-verification-skill/SKILL.md).

Say yes and it writes `.claude/skills/verify-<app>/`, a project-local skill that teaches agents to drive your app the way a user does. It proves the skill works once before handing it over. Say no and setup moves on. You can run `/create-verification-skill` yourself any time. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers it in depth.

If you're new to pstack, say yes. An agent that can check its own work keeps going until the check passes. An agent that can't hands every result back to you to check by hand. Of everything in this guide, the verification skill pays off the most.

After setup, start a new session. `CLAUDE.md` loads at session start.

## Keep the cost in check

pstack spends extra tokens on subagents and review panels. That's the price of the rigor. To spend fewer:

- Rerun `/setup-pstack` and pick a smaller budget or cheaper models. A strong model in the main chat with `sonnet` or `haiku` in the code roles is a good split.
- Set a role to `inherit` so it runs on the chat's own model.
- Shorten a panel list. Each entry runs one subagent.
- Save `/poteto-mode` for work that needs rigor. A small, obvious edit doesn't.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
/pstack:poteto-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the todo list. Its first items are the matched playbook's steps copied in, the Feature playbook for this prompt. If `/poteto-mode` skips a step, the step stays in the list with `skip: <reason>`, so you can see what it chose not to do.

From here you can type normal follow-ups. Claude Code has no Custom Modes, so the skill is loaded once and its pull fades as the chat moves on. Start each new task with `/pstack:poteto-mode`. To make the style the default in a repository, add a line to its `CLAUDE.md` that tells the agent to read the poteto-mode `SKILL.md` at the start of every task.

Next: [Route work through `/poteto-mode`](./02-poteto-mode.md).
