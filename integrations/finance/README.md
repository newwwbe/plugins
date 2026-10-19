# Finance

Link your bank, card, and investment accounts through Plaid so Grok can answer questions about balances, spending, subscriptions, and investments. You'll share contact details, account and balance info, transactions, credit and loans, and investments. Grok syncs and stores your linked account data so the connector can work, and Grok Bot's privacy mode still controls whether your conversations are stored or used for training. Access is read-only, xAI never sees or stores your bank login, and you can unlink accounts anytime from cursor.com.

## Install

```
/plugin install finance@newwwbe
```

Or from a terminal: `claude plugin install finance@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## MCP server

- `finance`: `https://connectors-gateway.grok.com/gateway/v1/finance/mcp` (sign-in when the server asks)

Run `/mcp` in Claude Code to check the connection or to sign in.

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
