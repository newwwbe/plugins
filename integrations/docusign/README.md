# Docusign

Manage envelopes, templates, workflows, and agreements.

## Install

```
/plugin install docusign@newwwbe
```

Or from a terminal: `claude plugin install docusign@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## MCP server

- `docusign`: `https://mcp.docusign.com/mcp` (OAuth sign-in)

Run `/mcp` in Claude Code to check the connection or to sign in.

## Configuration

Set these with `claude plugin configure docusign`:

- `CLIENT_ID` (required): Integration Key from Docusign Apps and Keys (Settings → Apps and Keys → your app).
- `CLIENT_SECRET` (required): Secret Key from the same Docusign Apps and Keys app.

This server uses your own OAuth app. Claude Code finishes sign-in through a callback on `localhost`; if the provider asks for a redirect URI, register the one shown during sign-in.

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
