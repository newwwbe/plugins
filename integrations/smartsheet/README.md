# Smartsheet

Query and update sheets, rows, and workspaces.

## Install

```
/plugin install smartsheet@newwwbe
```

Or from a terminal: `claude plugin install smartsheet@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## MCP server

- `smartsheet`: `https://mcp.smartsheet.com` (API key/token)

Run `/mcp` in Claude Code to check the connection or to sign in.

## Configuration

Set these with `claude plugin configure smartsheet`:

- `SMARTSHEET_API_TOKEN` (required): API access token generated in Smartsheet under Account → Personal Settings → API Access.

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
