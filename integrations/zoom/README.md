# Zoom

Search meetings, pull transcripts, and work with Zoom Docs.

## Install

```
/plugin install zoom@newwwbe
```

Or from a terminal: `claude plugin install zoom@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## MCP server

- `zoom`: `https://mcp.zoom.us/mcp/zoom/streamable` (OAuth sign-in)

Run `/mcp` in Claude Code to check the connection or to sign in.

## Configuration

Set these with `claude plugin configure zoom`:

- `CLIENT_ID` (required): Public Client ID (recommended) or Client ID from your Zoom App Marketplace General app → Basic Information → App Credentials. The Public Client ID appears after turning on Use Public Client OAuth.
- `CLIENT_SECRET`: Optional. Leave blank with a Public Client ID; Cursor then signs in with PKCE and no secret. Only set it alongside the confidential Client ID from the same app.

This server uses your own OAuth app. Claude Code finishes sign-in through a callback on `localhost`; if the provider asks for a redirect URI, register the one shown during sign-in.

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
