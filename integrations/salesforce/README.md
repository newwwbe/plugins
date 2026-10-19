# Salesforce

Query, create, and update records in your org.

## Install

```
/plugin install salesforce@newwwbe
```

Or from a terminal: `claude plugin install salesforce@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## MCP server

- `salesforce`: `${user_config.SALESFORCE_MCP_URL}` (OAuth sign-in)

Run `/mcp` in Claude Code to check the connection or to sign in.

## Configuration

Set these with `claude plugin configure salesforce`:

- `SALESFORCE_MCP_URL` (required): Server URL from Setup → MCP Servers. Production: https://api.salesforce.com/platform/mcp/v1/platform/sobject-all. Sandbox or scratch: https://api.salesforce.com/platform/mcp/v1/sandbox/platform/sobject-all. For custom servers, replace platform/ with custom/.
- `CLIENT_ID` (required): Consumer Key of the External Client App you created for this integration (Setup → External Client App Manager → your app → Settings → Consumer Key and Secret).

This server uses your own OAuth app. Claude Code finishes sign-in through a callback on `localhost`; if the provider asks for a redirect URI, register the one shown during sign-in.

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
