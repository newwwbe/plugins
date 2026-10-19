# Wrike

Search projects, create tasks, and post comments.

## Install

```
/plugin install wrike@newwwbe
```

Or from a terminal: `claude plugin install wrike@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## MCP server

- `wrike`: `https://mcp.wrike.com/v2` (API key/token)

Run `/mcp` in Claude Code to check the connection or to sign in.

## Configuration

Set these with `claude plugin configure wrike`:

- `WRIKE_ACCESS_TOKEN` (required): Permanent access token created in Wrike under Apps & Integrations → API.

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
