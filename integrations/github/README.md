# GitHub

Manage repos, issues, pull requests, and Actions.

## Install

```
/plugin install github@newwwbe
```

Or from a terminal: `claude plugin install github@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## MCP server

- `github`: `https://api.githubcopilot.com/mcp/` (API key/token)

Run `/mcp` in Claude Code to check the connection or to sign in.

## Configuration

Set these with `claude plugin configure github`:

- `GITHUB_PERSONAL_ACCESS_TOKEN` (required): Fine-grained or classic PAT from https://github.com/settings/tokens with the repo scopes you want the agent to use.

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
