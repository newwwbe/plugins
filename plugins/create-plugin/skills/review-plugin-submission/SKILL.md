---
name: review-plugin-submission
description: Audit a Claude Code plugin for marketplace readiness. Use when validating manifests, component metadata, discovery paths, and submission quality before publishing.
---

# Review plugin submission

## Trigger

A plugin is implemented and needs a final quality check before submission or release.

## Workflow

1. Run the validator first and keep its output as evidence:
   ```bash
   claude plugin validate <plugin-dir>
   claude plugin validate --strict <plugin-dir>    # warnings become failures
   claude plugin validate <marketplace-repo-root>  # for multi-plugin repos
   ```
   Every error is a blocker. Strict-mode warnings (unrecognized fields, missing metadata) should be fixed before public submission. If the installed CLI has no `plugin validate`, do the checks below by hand.
2. Verify manifest validity:
   - `.claude-plugin/plugin.json` exists and is the only file in `.claude-plugin/` (plus `marketplace.json` for a marketplace root)
   - `name` is valid lowercase kebab-case
   - metadata fields are coherent (`description`, `version`, `author`, `license`, `homepage`, `repository`)
   - no fields from other plugin formats (for example Cursor's `displayName`, `logo`, `category`, `tags`, `rules`)
3. Verify component discoverability:
   - Skills in `skills/*/SKILL.md`
   - Agents in `agents/*.md`
   - Commands in `commands/*.md`
   - Hooks in `hooks/hooks.json` (wrapped in a top-level `"hooks"` key) or inline in `plugin.json` (the event map directly, without the wrapper)
   - MCP config in `.mcp.json` (or `mcpServers` override)
   - Hook commands and agent/skill bodies reference bundled files through `${CLAUDE_PLUGIN_ROOT}`, and referenced scripts exist and are executable
4. Verify component metadata:
   - Skills include `name` and `description` frontmatter, and the description says when to use the skill
   - Agents include `name` and `description`; `model` is one of `opus`, `sonnet`, `haiku`, `inherit` when present
   - Commands include `description`
5. Verify repository integration:
   - For marketplace repos, the plugin entry exists in `.claude-plugin/marketplace.json`
   - `source` resolves to the plugin directory and names are unique
6. Verify documentation quality:
   - `README.md` states purpose, installation (`/plugin marketplace add ...` then `/plugin install <plugin>@<marketplace>`), and component coverage
7. Optional smoke test: `claude -p --plugin-dir <plugin-dir> "List the skills and subagent types whose names contain <plugin-name>"` and confirm every component shows up.

## Checklist

- `claude plugin validate` passes (and `--strict` for public submissions)
- Manifest exists and parses as valid JSON
- All declared paths exist and are relative
- No broken file references
- No missing frontmatter on skills/agents/commands
- Plugin scope is clear and focused
- Marketplace registration complete (if multi-plugin repo)

## Output

- Validator output (summarized)
- Pass/fail report by section
- Prioritized fix list
- Final submission recommendation
