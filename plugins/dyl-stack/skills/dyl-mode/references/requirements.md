# Requirements

dyl-stack layers on other plugins. Check the ones your skill needs before any work. If one is missing, stop, name it, and tell the user to run `/plugin install <name>@newwwbe`. Do not improvise the missing piece.

| Plugin | Installed when | Reach its files |
|---|---|---|
| `pstack` | `pstack:poteto-agent` is an available Agent `subagent_type`, or `/pstack:setup-pstack` is in your skill list | Most pstack skills are slash-only (`disable-model-invocation`) and hidden from the Skill tool, so Read them from disk. Find the pstack root with the lookup below, then read `<pstack>/skills/poteto-mode/SKILL.md`, `<pstack>/skills/poteto-mode/playbooks/<name>.md`, `<pstack>/skills/principle-<name>/SKILL.md`, `<pstack>/skills/bro/SKILL.md`, `<pstack>/skills/unslop/SKILL.md`. |
| `cursor-team-kit` | `cursor-team-kit:control-ui`, `cursor-team-kit:verify-this`, and `cursor-team-kit:deslop` are in your skill list | Load them with the Skill tool. |
| `thermos` | `thermos:thermo-nuclear-review-subagent` and `thermos:thermo-nuclear-code-quality-review-subagent` are available Agent subagent types | Launch them by subagent type. |
| `figma` | A Figma MCP server is connected (tools such as `get_design_context` and `get_screenshot`) and one of its calls succeeds. A Figma plugin that ships a `figma-design-to-code` skill is optional; use it when present | The MCP's tools, plus that skill's listed path when present. |

## Locating pstack on disk

`<dyl-stack>` is this plugin's root: two directories above the `dyl-mode` skill's base directory (`${CLAUDE_PLUGIN_ROOT}` inside agents). Marketplace installs live under `~/.claude/plugins/`, and pstack usually sits beside dyl-stack. Run:

```bash
find ~/.claude/plugins "<dyl-stack>/.." "<dyl-stack>/../.." -maxdepth 6 -path '*pstack*/skills/poteto-mode/SKILL.md' 2>/dev/null
```

`<pstack>` is the directory three levels above the match (the one holding `skills/`). If several match, use the one whose `.claude-plugin/plugin.json` has the highest `version`. If pstack was loaded with `--plugin-dir` from somewhere else, the lookup can miss even though `pstack:poteto-agent` is listed: ask the user for the path once rather than guessing.
