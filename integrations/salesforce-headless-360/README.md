# Salesforce (Headless 360, Beta)

Manage records, users, and org setup across Salesforce.

## Install

```
/plugin install salesforce-headless-360@newwwbe
```

Or from a terminal: `claude plugin install salesforce-headless-360@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## MCP server

- `salesforce-headless-360`: `${user_config.SALESFORCE_MCP_URL}` (OAuth sign-in)

Run `/mcp` in Claude Code to check the connection or to sign in.

## Configuration

Set these with `claude plugin configure salesforce-headless-360`:

- `SALESFORCE_MCP_URL` (required): Headless 360 server URL from Salesforce Setup → MCP Servers. Production and Developer orgs: https://api.salesforce.com/platform/mcp/v1/platform/headless-360. Sandbox and scratch orgs: https://api.salesforce.com/platform/mcp/v1/sandbox/platform/headless-360.
- `CLIENT_ID` (required): Your Salesforce admin creates the External Client App and enters its Consumer Key here once for the whole team (Setup → External Client App Manager → your app → Settings → Consumer Key and Secret). Team members don't need this value; they only sign in to Salesforce.
- `CLIENT_SECRET` (required): Consumer Secret from the same External Client App, entered once by your Salesforce admin for the whole team. Team members don't need this value.

This server uses your own OAuth app. Claude Code finishes sign-in through a callback on `localhost`; if the provider asks for a redirect URI, register the one shown during sign-in.

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
