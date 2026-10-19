# Gong

Pull account summaries, deal insights, and call briefs.

## Install

```
/plugin install gong@newwwbe
```

Or from a terminal: `claude plugin install gong@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## MCP server

- `gong`: `https://mcp.gong.io/mcp` (OAuth sign-in)

Run `/mcp` in Claude Code to check the connection or to sign in.

## Configuration

Set these with `claude plugin configure gong`:

- `CLIENT_ID` (required): OAuth Client ID from Gong Admin → Company Settings → Ecosystem → API → Integrations (MCP integration).
- `CLIENT_SECRET` (required): OAuth Client Secret from the same Gong MCP integration.

This server uses your own OAuth app. Claude Code finishes sign-in through a callback on `localhost`; if the provider asks for a redirect URI, register the one shown during sign-in.

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
