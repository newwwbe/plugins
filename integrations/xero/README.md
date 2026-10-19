# Xero

Read and write invoices, contacts, reports, and payroll.

## Install

```
/plugin install xero@newwwbe
```

Or from a terminal: `claude plugin install xero@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## MCP server

- `xero`: `npx -y @xeroapi/xero-mcp-server@latest` (API key/token)

Run `/mcp` in Claude Code to check the connection or to sign in.

## Configuration

Set these with `claude plugin configure xero`:

- `XERO_CLIENT_ID` (required): Client ID of the Custom Connection you created at developer.xero.com. A Custom Connection is bound to a single Xero organisation.
- `XERO_CLIENT_SECRET` (required): Client secret generated alongside the Custom Connection's client ID at developer.xero.com.

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
