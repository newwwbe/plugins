# Tailscale

Let Grok Bot reach MCP servers on your private Tailscale network. Sign in to Tailscale to connect your tailnet; Grok Bot joins it as one tagged device and only reaches the hosts you grant to tag:grokbot.

## Install

```
/plugin install tailscale@newwwbe
```

Or from a terminal: `claude plugin install tailscale@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## Skills

- `/tailscale:tailscale-setup`

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
