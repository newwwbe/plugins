# Cursor SDK for Claude Code

Claude Code port of the [Cursor SDK](https://github.com/cursor/plugins/tree/main/cursor-sdk) Cursor plugin: one knowledge skill that helps you build apps, scripts, CI pipelines, and automations on the Cursor TypeScript SDK (`@cursor/sdk`).

> **Cursor dependency.** This plugin teaches Claude how to write code against Cursor's SDK. The code you build runs Cursor agents on Cursor's backend and needs a Cursor account and `CURSOR_API_KEY`. Claude Code itself does not run `@cursor/sdk` agents. For running Claude agents programmatically, use the Claude Agent SDK instead.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install cursor-sdk@newwwbe
```

## Usage

The skill loads automatically when you mention the Cursor SDK, `@cursor/sdk`, `Agent.create`, `Agent.prompt`, `Agent.resume`, `agent.send`, `run.stream`, `CursorAgentError`, or ask to run Cursor agents from a script, CI job, bot, or webhook. You can also invoke it directly with `/cursor-sdk:cursor-sdk`.

It covers the three invocation patterns, the top traps for new integrations, local vs cloud runtime, auth, streaming, MCP, error handling, and ready-to-extend patterns. Reference files are read only when the task needs them:

| If you are...                                                                        | Reference                              |
| ------------------------------------------------------------------------------------ | -------------------------------------- |
| Picking between local and cloud runtime                                              | `references/runtime-choice.md`         |
| Debugging auth (401s, missing key, team vs user keys)                                | `references/auth.md`                   |
| Handling errors, retries, rate limits, `CursorAgentError`, `result.status === error` | `references/error-handling.md`         |
| Consuming streams, picking event types, cancelling, or stream vs wait                | `references/streaming.md`              |
| Configuring MCP servers (HTTP, stdio, transport, auth injection)                     | `references/mcp.md`                    |
| Sub-agents, resume, artifacts, listing/inspecting agents, `Agent.messages`           | `references/advanced.md`               |
| Building a specific integration (CI review bot, triage, chat, webhook)               | `references/patterns.md`               |

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `category`, `tags`) are dropped.
- "Offering a Canvas" (defer to Cursor's `canvas` skill) became "Offering a Visualization": Claude offers to write a self-contained HTML file and gives you its path.
- The skill states up front that it targets Cursor's product and points to the Claude Agent SDK when you actually want Claude agents.
- All reference files are unchanged copies of upstream; mentions of `.cursor/*` config there describe how the Cursor SDK's local runtime loads settings, not Claude Code.

## License

MIT
