# newwwbe Claude Code plugins

A Claude Code plugin marketplace (`newwwbe`). It bundles [anti-slop](https://github.com/newwwbe/anti-slop), [attention-span](https://github.com/newwwbe/attention-span), and Claude Code ports of the [Cursor plugin catalog](https://github.com/cursor/plugins): workflow plugins in `plugins/` and MCP integrations in `integrations/`. Only Claude Code files are kept here.

## Set up any machine in one line

macOS / Linux / WSL:

```bash
curl -fsSL https://raw.githubusercontent.com/newwwbe/plugins/main/install.sh | bash
```

Windows (PowerShell):

```powershell
irm https://raw.githubusercontent.com/newwwbe/plugins/main/install.ps1 | iex
```

This adds the marketplace, installs the default set at user scope, and sets the default output style to `attention-span:Attention-kind`. Run it again any time; it is safe to repeat and picks up updates.

Default set: `attention-span anti-slop thermos pstack cursor-team-kit dyl-stack advisor ralph-loop orchestrate create-plugin agent-compatibility cli-for-agent teaching docs-canvas pr-review-canvas`

Options (bash: `curl ... | bash -s -- <options>`):

| Option | Effect |
|:--|:--|
| `--add "github notion"` | Also install these (e.g. MCP integrations; set their keys with `claude plugin configure <name>`) |
| `--plugins "a b"` | Install exactly these instead of the default set |
| `--style NAME` / `--no-style` | Choose or skip the default output style |

Not in the default set: the 84 MCP integrations (each needs its own sign-in), `continual-learning` (edits AGENTS.md automatically), and `cursor-sdk`, `origin-apps`, `grok-voice` (Cursor/xAI-specific).

## Without the script

Put this in `~/.claude/settings.json` (all machines), or in a repository's `.claude/settings.json` to share it with everyone who opens that repo. Claude Code fetches the plugins on the next start and loads them from the start after that.

```json
{
  "extraKnownMarketplaces": {
    "newwwbe": { "source": { "source": "github", "repo": "newwwbe/plugins" } }
  },
  "enabledPlugins": {
    "attention-span@newwwbe": true,
    "anti-slop@newwwbe": true,
    "thermos@newwwbe": true,
    "pstack@newwwbe": true
  },
  "outputStyle": "attention-span:Attention-kind"
}
```

Or inside Claude Code: `/plugin marketplace add newwwbe/plugins`, then `/plugin install <name>@newwwbe`.

## Claude Code on the web

Cloud sessions start from a fresh container, so add the one-line installer to the environment's **Setup script** (environment menu in the session title bar → Edit), or commit the settings block above to the repository's `.claude/settings.json`.

## Plugins

| Name | Source | Description |
|:--|:--|:--|
| `attention-span` | [github.com/newwwbe/attention-span](https://github.com/newwwbe/attention-span) | Answer-first output styles (Attention-kind, Spartan, Rundown), the /style switcher, and /tldr. |
| `anti-slop` | [github.com/newwwbe/anti-slop](https://github.com/newwwbe/anti-slop) | install-anti-slop skill: vendors the anti-slop Oxlint rules into a TypeScript/JavaScript repo and configures them. |
| `origin-apps` | [plugins/origin-apps](plugins/origin-apps/) | Skills for building on the Cursor Origin API. Fetch the live spec first, then follow the Origin rules for credentials, scopes, webhooks, paging, and errors. Includes a skill that plans the port of an existing GitHub App. |
| `thermos` | [plugins/thermos](plugins/thermos/) | Thermo-nuclear branch review for Claude Code: deep correctness/security audit and harsh code-quality audit as parallel subagents, synthesized into one verdict. |
| `cursor-sdk` | [plugins/cursor-sdk](plugins/cursor-sdk/) | Knowledge skill for building apps, scripts, CI pipelines, and automations on the Cursor TypeScript SDK (@cursor/sdk), usable from Claude Code. Requires a Cursor account and API key at run time of the code you build. |
| `docs-canvas` | [plugins/docs-canvas](plugins/docs-canvas/) | Render documentation (architecture notes, API references, runbooks, codebase walkthroughs) as a navigable, self-contained HTML page you open in a browser. |
| `pr-review-canvas` | [plugins/pr-review-canvas](plugins/pr-review-canvas/) | Render PR diffs as a self-contained HTML review page grouped by reviewer importance, with pseudocode, example traces, and callouts for tricky hunks. |
| `grok-voice` | [plugins/grok-voice](plugins/grok-voice/) | Add Grok voice to an app: realtime speech-to-speech, speech-to-text dictation, text-to-speech read-aloud, and a log-driven fix loop for voice sessions. |
| `cursor-team-kit` | [plugins/cursor-team-kit](plugins/cursor-team-kit/) | Internal engineering team workflows for CI, code review, shipping, control-cli, control-ui, verify-this, test reliability, code cleanup, and work summaries. Designed to work without requiring third-party service integrations. |
| `create-plugin` | [plugins/create-plugin](plugins/create-plugin/) | Scaffold and validate new Claude Code plugins. Handles directory setup, manifest generation, marketplace wiring, and pre-submission quality checks with claude plugin validate. |
| `agent-compatibility` | [plugins/agent-compatibility](plugins/agent-compatibility/) | CLI-backed repo compatibility scans plus agents that audit startup, validation, and docs against reality. |
| `cli-for-agent` | [plugins/cli-for-agent](plugins/cli-for-agent/) | Patterns for designing CLIs that coding agents can run reliably: non-interactive flags, layered help with examples, pipelines, actionable errors, idempotency, and dry-run. |
| `teaching` | [plugins/teaching](plugins/teaching/) | Skill mapping, practice plans, and learning retrospectives. Builds personalized roadmaps with milestones and practice checkpoints, and runs periodic reviews to adjust based on progress. |
| `pstack` | [plugins/pstack](plugins/pstack/) | if you want to go fast, go deep first. pstack helps you write less, but higher quality code: rigorous agent workflows, playbooks, and principles you can parallelize with confidence, ported to Claude Code. |
| `advisor` | [plugins/advisor](plugins/advisor/) | Consult a stronger model at key checkpoints: before major decisions, when stuck on an error, and before declaring a task done. A read-only Opus advisor subagent gets a full briefing plus the conversation transcript, returns guidance, and the main model keeps doing the work. |
| `continual-learning` | [plugins/continual-learning](plugins/continual-learning/) | Incrementally learns durable user preferences and workspace facts from Claude Code transcript changes and keeps AGENTS.md up to date with plain bullet points. |
| `ralph-loop` | [plugins/ralph-loop](plugins/ralph-loop/) | Continuous self-referential AI loops for iterative development in Claude Code, implementing the Ralph Wiggum technique: a Stop hook feeds the same prompt back every turn until the task is complete. |
| `orchestrate` | [plugins/orchestrate](plugins/orchestrate/) | Fan a large task out across parallel Claude Code agents in git worktrees: planners publish tasks, workers and verifiers hand off back up, and a script reconciles the tree from disk and git. |
| `dyl-stack` | [plugins/dyl-stack](plugins/dyl-stack/) | Dylan's agent style on top of pstack for Claude Code: root causes over symptom patches, The Algorithm before design, terse verified delivery, a PR review that fits in a paste, and Figma-to-UI with a visual judge. |

## MCP integrations

Install with `/plugin install <name>@newwwbe`; each folder's README lists the sign-in or keys it needs.

[`ahrefs`](integrations/ahrefs/) · [`amplemarket`](integrations/amplemarket/) · [`ashby`](integrations/ashby/) · [`attio`](integrations/attio/) · [`beehiiv`](integrations/beehiiv/) · [`brevo`](integrations/brevo/) · [`brex`](integrations/brex/) · [`buffer`](integrations/buffer/) · [`calendly`](integrations/calendly/) · [`circleback`](integrations/circleback/) · [`clay`](integrations/clay/) · [`coda`](integrations/coda/) · [`coinbase`](integrations/coinbase/) · [`craft`](integrations/craft/) · [`customer-io`](integrations/customer-io/) · [`daloopa`](integrations/daloopa/) · [`docusign`](integrations/docusign/) · [`etoro-trading`](integrations/etoro-trading/) · [`excalidraw`](integrations/excalidraw/) · [`fathom`](integrations/fathom/) · [`finance`](integrations/finance/) · [`finary`](integrations/finary/) · [`fireflies`](integrations/fireflies/) · [`gamma`](integrations/gamma/) · [`github`](integrations/github/) · [`gmail`](integrations/gmail/) · [`godaddy`](integrations/godaddy/) · [`gong`](integrations/gong/) · [`google-calendar`](integrations/google-calendar/) · [`google-cloud-bigquery`](integrations/google-cloud-bigquery/) · [`google-docs`](integrations/google-docs/) · [`google-drive`](integrations/google-drive/) · [`google-sheets`](integrations/google-sheets/) · [`google-slides`](integrations/google-slides/) · [`greenhouse`](integrations/greenhouse/) · [`guru`](integrations/guru/) · [`highlevel`](integrations/highlevel/) · [`hubspot`](integrations/hubspot/) · [`hunter`](integrations/hunter/) · [`interactive-brokers`](integrations/interactive-brokers/) · [`intercom`](integrations/intercom/) · [`jotform`](integrations/jotform/) · [`juicebox`](integrations/juicebox/) · [`klaviyo`](integrations/klaviyo/) · [`mailerlite`](integrations/mailerlite/) · [`meltwater`](integrations/meltwater/) · [`mem`](integrations/mem/) · [`navan`](integrations/navan/) · [`onedrive`](integrations/onedrive/) · [`otter`](integrations/otter/) · [`outlook`](integrations/outlook/) · [`outlook-calendar`](integrations/outlook-calendar/) · [`outreach`](integrations/outreach/) · [`plaud`](integrations/plaud/) · [`playwright`](integrations/playwright/) · [`posthog-mcp`](integrations/posthog-mcp/) · [`profound`](integrations/profound/) · [`readwise`](integrations/readwise/) · [`robinhood`](integrations/robinhood/) · [`salesforce`](integrations/salesforce/) · [`salesforce-headless-360`](integrations/salesforce-headless-360/) · [`semrush`](integrations/semrush/) · [`sharepoint`](integrations/sharepoint/) · [`shopify-store`](integrations/shopify-store/) · [`similarweb`](integrations/similarweb/) · [`smartsheet`](integrations/smartsheet/) · [`sp-global`](integrations/sp-global/) · [`square`](integrations/square/) · [`statsig`](integrations/statsig/) · [`tailscale`](integrations/tailscale/) · [`teams`](integrations/teams/) · [`tinyfish`](integrations/tinyfish/) · [`todoist`](integrations/todoist/) · [`trello`](integrations/trello/) · [`typeform`](integrations/typeform/) · [`upwork`](integrations/upwork/) · [`webull`](integrations/webull/) · [`workable`](integrations/workable/) · [`wrike`](integrations/wrike/) · [`x`](integrations/x/) · [`x-ads`](integrations/x-ads/) · [`x-money`](integrations/x-money/) · [`xero`](integrations/xero/) · [`zoom`](integrations/zoom/)

## Repository structure

```
.claude-plugin/marketplace.json   # marketplace catalog (name: newwwbe)
plugins/<name>/                   # workflow plugins: .claude-plugin/plugin.json, skills/, agents/, hooks/
integrations/<name>/              # MCP integrations: .claude-plugin/plugin.json (+ skills/ or rules/)
install.sh, install.ps1           # one-line machine setup
```

Validate after changes: `claude plugin validate .` (marketplace) and `claude plugin validate plugins/<name>`.

## License

MIT, per plugin (see each `LICENSE`). Ported plugins are adapted from [cursor/plugins](https://github.com/cursor/plugins); anti-slop and attention-span keep their own licenses.
