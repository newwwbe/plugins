# Brevo

Manage contacts, email and SMS campaigns, and CRM deals.

## Install

```
/plugin install brevo@newwwbe
```

Or from a terminal: `claude plugin install brevo@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## MCP server

- `brevo`: `https://mcp.brevo.com/v1/brevo/mcp` (API key/token)

Run `/mcp` in Claude Code to check the connection or to sign in.

## Configuration

Set these with `claude plugin configure brevo`:

- `BREVO_MCP_TOKEN` (required): API key created in Brevo under Account → SMTP & API → API Keys with "Create MCP server API key" enabled.

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
