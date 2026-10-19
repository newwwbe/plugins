# benny

> **Claude Code port note.** benny is a pack for **Cursor Automations**: Slack-triggered cloud runs set up through Cursor's built-in `/automate` and the Automations editor. Claude Code has no Slack-message trigger, so this pack is shipped unchanged as reference and its setup flow (`FOR_AGENTS.md`, `skills/setup-benny/`) still targets Cursor. The two operational files, `skills/triage-issue-reports/SKILL.md` and `skills/reproduce-and-fix-issues/SKILL.md`, are plain agent instructions. To approximate benny in Claude Code, run them from a scheduled task or a `/loop` that polls the source channel through a Slack MCP server and processes each new top-level report once (record handled `message_ts` values in a file so reruns stay idempotent). Their references to pstack skills (`how`, `why`, `tdd`, `unslop`, `principle-*`) resolve to this plugin's `skills/` directory. Read those `SKILL.md` files directly, because they are user-invoked only.

benny gives you two cursor automations for slack issue reports. one triages each report. the other reproduces confirmed bugs and may prepare a small draft fix.

the files in this directory are dormant setup and automation sources. they do not appear as slash skills.

## set it up

1. point cursor at [`FOR_AGENTS.md`](./FOR_AGENTS.md) and name the target repository.
2. let setup merge this whole directory into the target at `.cursor/automations/benny/`. it must preserve destination-only files and review conflicts instead of overwriting local edits.
3. let setup enable pstack in the target repository's `.cursor/settings.json` for shared dependencies:

```json
{
	"plugins": {
		"pstack": { "enabled": true }
	}
}
```

4. keep user-owned configuration outside the copied pack, for example in `.cursor/benny/`. adapt [`configuration.example.yaml`](./templates/configuration.example.yaml) and [`feature-map.example.md`](./skills/reproduce-and-fix-issues/references/feature-map.example.md).
5. commit `.cursor/settings.json`, `.cursor/automations/benny/`, and any secret-free configuration before enabling either automation.
6. review each new automation draft or update existing automations in their editors. then send a harmless test report and verify every source-channel post stays in the original thread.
