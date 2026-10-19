# Shopify

Connect your Shopify store so Grok can answer questions about your products, orders, customers, inventory, and sales. You sign in with Shopify and approve the store access Grok requests; Grok keeps that authorization so the connector can work, and Grok Bot's privacy mode still controls whether your conversations are stored or used for training. xAI never sees or stores your Shopify password, and you can disconnect the store anytime from grok.com.

## Install

```
/plugin install shopify-store@newwwbe
```

Or from a terminal: `claude plugin install shopify-store@newwwbe` (after `claude plugin marketplace add newwwbe/plugins`).

## MCP server

- `shopify`: `https://setup.shopify.com/mcp` (sign-in when the server asks)

Run `/mcp` in Claude Code to check the connection or to sign in.

Routing rules in `rules/` are added to every session through a SessionStart hook.

## License

MIT. Adapted from the Cursor plugin catalog (https://github.com/cursor/plugins).
