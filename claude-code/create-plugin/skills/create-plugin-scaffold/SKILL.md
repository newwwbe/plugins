---
name: create-plugin-scaffold
description: Create a new Claude Code plugin scaffold with a valid manifest, component directories, and marketplace wiring, then validate it with claude plugin validate. Use when starting a new plugin or adding a plugin to a multi-plugin repository.
---

# Create plugin scaffold

## Trigger

You need to create a new Claude Code plugin from scratch and make it ready for local use or marketplace submission.

## Required Inputs

- Plugin name (lowercase kebab-case)
- Plugin purpose and target users
- Component set to include (`skills`, `agents`, `commands`, `hooks`, `mcpServers`)
- Repository style (`single-plugin` or `multi-plugin marketplace`)

## Output Location

By default, create the plugin in the user's skills directory:

```
~/.claude/skills/<plugin-name>/
```

A directory there that contains `.claude-plugin/plugin.json` auto-loads as `<plugin-name>@skills-dir` in the next session (or right away after `/reload-plugins`), with no install step. If the user explicitly asks to create the plugin elsewhere (for example inside an existing repo or marketplace), respect that choice and tell them how to load it: `claude --plugin-dir <path>` for a quick test, or `/plugin marketplace add <repo-or-path>` followed by `/plugin install <plugin>@<marketplace>`.

## Workflow

1. Validate plugin name format: lowercase kebab-case, starts and ends with an alphanumeric character.
2. Determine the target directory:
   - Default: `~/.claude/skills/<plugin-name>/`
   - Override: use the path the user specifies, if any.
3. Create the skeleton. Prefer the CLI when it is available (`claude plugin init --help` succeeds):
   ```bash
   claude plugin init <plugin-name> --description "<one sentence>" --with skills agents hooks
   ```
   It writes to `~/.claude/skills/<plugin-name>/` only, with a root `SKILL.md`, `"skills": ["./"]` in the manifest, and `TODO` placeholders. Replace every placeholder, and drop the `--with` components the plugin does not need. For a custom location, or when the CLI has no `init`, create the files by hand:
   - `.claude-plugin/plugin.json`
   - `README.md`
   - `LICENSE`
   - optional `CHANGELOG.md`
4. Populate `.claude-plugin/plugin.json`:
   - Required: `name`
   - Recommended: `version`, `description`, `author` (`{"name", "email"}`), `homepage`, `repository`, `license`, `keywords`
   - Add component path fields (`skills`, `agents`, `commands`, `hooks`, `mcpServers`) only when the default folders are not enough. Paths are relative and start with `./`.
5. Create component files at the plugin root (never inside `.claude-plugin/`), with valid frontmatter:
   - Skills: `skills/<skill-name>/SKILL.md` with `name` and `description`. The description says what the skill does and when to use it, with trigger phrases. Optional: `disable-model-invocation: true` (user-invoked only), `allowed-tools`, `argument-hint`. Users invoke it as `/<plugin>:<skill>`.
   - Agents: `agents/<agent-name>.md` with `name`, `description`, optional `tools` (comma-separated) and `model` (`opus`, `sonnet`, `haiku`, or `inherit`). Spawned as subagent type `<plugin>:<agent-name>`.
   - Commands: `commands/<command>.md` with `description` and optional `argument-hint`; the body is the prompt and `$ARGUMENTS` receives user input. Prefer skills for new work.
   - Hooks: `hooks/hooks.json` shaped as `{"hooks": {"<Event>": [{"matcher": "...", "hooks": [{"type": "command", "command": "...", "timeout": 30}]}]}}`. Reference scripts as `"${CLAUDE_PLUGIN_ROOT}/scripts/..."` and make them executable. A `SessionStart` hook's stdout becomes context, which is how to ship always-on guidance (Claude Code has no plugin "rules").
   - MCP servers: `.mcp.json` at the plugin root.
6. If the repository has a `.claude-plugin/marketplace.json`, add a plugin entry:
   - `name`
   - `source` (relative path such as `./plugins/<plugin-name>`)
   - optional `description`, `version`, `author`, `keywords`, `category`
7. Validate and fix until clean:
   ```bash
   claude plugin validate <plugin-dir>
   claude plugin validate <marketplace-repo-root>   # when a marketplace entry was added
   ```
   Use `--strict` when the plugin is headed for a public marketplace.
8. Optional smoke test: `claude -p --plugin-dir <plugin-dir> "List the skills and subagent types whose names contain <plugin-name>"`.

## Guardrails

- Keep the plugin focused on one use case.
- Prefer concise, actionable skill text over long prose.
- Do not reference files that do not exist.
- Use folder discovery defaults unless custom paths are required.
- Save to `~/.claude/skills/<plugin-name>/` unless the user provides a different path.
- Do not report success until `claude plugin validate` passes.

## Output

- Created file tree for the plugin (with full path to the output directory)
- Final `plugin.json`
- Marketplace entry (if applicable)
- `claude plugin validate` result
- How to load it: auto-load as `<plugin-name>@skills-dir` (run `/reload-plugins`), `--plugin-dir`, or marketplace install
