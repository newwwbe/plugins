# dyl-stack for Claude Code

Claude Code port of the [dyl-stack](../../dyl-stack/) Cursor plugin: Dylan's agent style, layered on [pstack](../pstack/). pstack does the heavy lifting: principles, playbooks, subagent routing. dyl-stack adds the few gates Dylan keeps correcting agents on, a PR review that fits in a paste, and a Figma-to-UI flow that won't call it done until it looks right.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install pstack@newwwbe
/plugin install cursor-team-kit@newwwbe
/plugin install thermos@newwwbe
/plugin install dyl-stack@newwwbe
```

`/dyl-stack:build-figma` also needs a Figma MCP server connected (for example Figma's Dev Mode MCP server via `claude mcp add`). A Figma plugin that ships a `figma-design-to-code` skill is used when present.

## Usage

| Skill | Use it when |
|---|---|
| `/dyl-stack:dyl-mode` | Default entry for non-trivial work. Routes through pstack's `poteto-mode` playbooks with Dylan's gates on top. User-invoked only. |
| `/dyl-stack:dyl-review` | You want up to 7 paste-ready review comments and one 🟢/🟡/🔴 call. Say "deep" to add the thermos subagents and a bug pass. Never posts. User-invoked only. |
| `/dyl-stack:dyl-ready-pr` | "Get PR green." Deep review until 🟢, mark ready, fix conflicts, babysit CI to merge-ready. Never merges. User-invoked only. |
| `/dyl-stack:build-figma` | You have a `figma.com/design` URL with a `node-id`. Intake first, map to your repo's design system, then a visual judge against the live UI. Also fires on its own from Figma URLs. |
| `principle-the-algorithm` | Referenced by `dyl-mode` (read from disk). Question the requirement, delete, then optimize, accelerate, automate. |

## What dyl-mode adds over poteto-mode

- **Root cause, not symptom.** Any failure gets a `Root cause: X because Y` todo before a fix. Null guards, retries, `.skip`, and snapshot updates are symptom fixes until that line justifies them.
- **The Algorithm** before designing anything bigger than a glance-sized edit.
- **Plain replies.** Default voice is pstack's `/pstack:bro`.
- **Merge gates.** Never merge without permission in the current turn. Update the existing PR, never open a duplicate.
- **Live UI proof** via `cursor-team-kit:control-ui`, and measure before coding layout bugs.
- **Taste vetoes bind.** "Roll that back" means roll it back.

## Agent

| Agent (`subagent_type`) | Description |
|:--|:--|
| `dyl-stack:dyl-agent` | Delegate for code-writing and helper tasks during a dyl-mode run (dyl-stack's counterpart of `pstack:poteto-agent`). Reads `${CLAUDE_PLUGIN_ROOT}/skills/dyl-mode/SKILL.md` first. |

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) and skill frontmatter (`mode`, `icon`, `color`, `reminder`) are dropped. `disable-model-invocation` is kept, so `dyl-mode`, `dyl-review`, `dyl-ready-pr`, and `principle-the-algorithm` stay slash-only; `build-figma` stays model-invocable.
- **Routing.** In Cursor, `/dyl-mode` handed the whole run to a background `dyl-agent`. Claude Code subagents cannot spawn subagents, so `/dyl-stack:dyl-mode` runs in the invoking conversation (which owns the todo list and every Agent spawn) and `dyl-stack:dyl-agent` is a delegate, like `pstack:poteto-agent`. `is_background` is dropped; use the Agent tool's `run_in_background` where wanted.
- **Reaching pstack.** pstack's skills are slash-only and hidden from the Skill tool, so `references/requirements.md` gives a `find ~/.claude/plugins ...` lookup for `poteto-mode/SKILL.md` and the skills Read pstack files from disk. Slash names are `/pstack:<skill>`; the pstack agent is `pstack:poteto-agent`.
- **Bugbot.** Cursor's built-in `/review-bugbot` subagent has no Claude Code equivalent. Deep `dyl-review` runs a `general-purpose` bug-only pass in its place and reads the Bugbot GitHub app's PR comments when the repo uses it. `dyl-ready-pr` still waits for the Bugbot GitHub check when the repo runs it.
- Thermos agents are referenced as `thermos:thermo-nuclear-review-subagent` / `thermos:thermo-nuclear-code-quality-review-subagent`; cursor-team-kit skills as `cursor-team-kit:<name>`.
- Repo-guidance lookups include `CLAUDE.md`, `.claude/rules/`, and `.claude/skills/` alongside `AGENTS.md` and legacy `.cursor/` paths. Missing-plugin messages point at `/plugin install <name>@newwwbe` instead of `/add-plugin`.
- `/loop` ticks map to Claude Code's `/loop` (or a Monitor / scheduled check-in).
- Skill bodies are otherwise unchanged from upstream.

## Not shipped here

- Principles, playbooks, `/pstack:bro`, `/pstack:unslop`, and the babysit watcher ship in `pstack`.
- `deslop`, `control-ui`, `control-cli`, and `verify-this` ship in `cursor-team-kit`.
- The thermos review subagents ship in `thermos`.

## License

MIT
