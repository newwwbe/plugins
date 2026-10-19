#!/usr/bin/env python3
"""Generate Claude Code manifests (.claude-plugin/plugin.json) for third_party/* Cursor plugins.

The Cursor files are left untouched; the Claude manifest is written next to them.
- Cursor `variables` become Claude `userConfig`, and `${VAR}` becomes `${user_config.VAR}`.
- Cursor MCP `auth` (CLIENT_ID / CLIENT_SECRET / scopes) becomes Claude MCP `oauth`.
- alwaysApply rules are injected at session start through a SessionStart hook.
Plugins with neither MCP servers nor skills (Cursor-native integrations) are skipped.

Usage: python3 scripts/convert-third-party-to-claude.py  (prints a JSON summary)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SENSITIVE = re.compile(r"TOKEN|SECRET|KEY|PASSWORD", re.I)


def user_config(variables):
    if not variables:
        return {}
    required = set(variables.get("required", []))
    out = {}
    for key, spec in variables.get("properties", {}).items():
        entry = {
            "type": "string",
            "title": spec.get("title", key),
            "description": spec.get("description", spec.get("title", key)),
            "required": key in required,
        }
        if spec.get("writeOnly") or spec.get("format") == "password" or SENSITIVE.search(key):
            entry["sensitive"] = True
        out[key] = entry
    return out


def substitute(value, keys):
    if isinstance(value, str):
        return re.sub(
            r"\$\{([A-Za-z_][A-Za-z0-9_]*)(:-[^}]*)?\}",
            lambda m: "${user_config.%s}" % m.group(1) if m.group(1) in keys else m.group(0),
            value,
        )
    if isinstance(value, list):
        return [substitute(v, keys) for v in value]
    if isinstance(value, dict):
        return {k: substitute(v, keys) for k, v in value.items()}
    return value


def convert_server(server, config):
    keys = set(config)
    server = dict(server)
    if "url" in server and "type" not in server:
        server["type"] = "http"
    auth = server.pop("auth", None)
    client_id = re.fullmatch(r"\$\{(\w+)\}", auth.get("CLIENT_ID", "")) if auth else None
    # An optional client ID may be left blank, and an empty clientId breaks the OAuth flow.
    # Fall back to the server's own (dynamic) client registration in that case.
    if client_id and not config.get(client_id.group(1), {}).get("required"):
        auth = None
    if auth:
        oauth = {}
        if auth.get("CLIENT_ID"):
            oauth["clientId"] = auth["CLIENT_ID"]
        if auth.get("CLIENT_SECRET"):
            oauth["clientSecret"] = auth["CLIENT_SECRET"]
        if auth.get("scopes"):
            oauth["scope"] = " ".join(auth["scopes"])
        if oauth:
            server["oauth"] = oauth
    return substitute(server, keys)


def always_apply_rules(plugin_dir):
    rules = []
    for rule in sorted((plugin_dir / "rules").glob("*.mdc")):
        head = rule.read_text().split("---")
        if len(head) >= 3 and re.search(r"^alwaysApply:\s*true", head[1], re.M):
            rules.append(rule.name)
    return rules


def rule_hook(rule_names):
    # Strip the YAML frontmatter and print the rule body; SessionStart stdout becomes context.
    command = " ; ".join(
        "awk 'f>=2{print} /^---$/{f++}' \"${CLAUDE_PLUGIN_ROOT}/rules/%s\"" % name for name in rule_names
    )
    return {"SessionStart": [{"hooks": [{"type": "command", "command": command}]}]}


def convert(plugin_dir):
    cursor = json.loads((plugin_dir / ".cursor-plugin" / "plugin.json").read_text())
    mcp_path = plugin_dir / "mcp.json"
    servers = json.loads(mcp_path.read_text())["mcpServers"] if mcp_path.exists() else {}
    has_skills = (plugin_dir / "skills").is_dir()
    if not servers and not has_skills:
        return None

    config = user_config(cursor.get("variables"))
    manifest = {
        "name": cursor["name"],
        "version": cursor["version"],
        "description": cursor["description"],
        "author": cursor["author"],
        "homepage": cursor.get("homepage"),
        "repository": cursor.get("repository"),
        "license": cursor.get("license"),
        "keywords": cursor.get("keywords", []),
    }
    if config:
        manifest["userConfig"] = config
    if servers:
        manifest["mcpServers"] = {name: convert_server(s, config) for name, s in servers.items()}
        used = json.dumps(manifest["mcpServers"])
        config = {k: v for k, v in config.items() if "${user_config.%s}" % k in used}
        manifest.pop("userConfig", None)
        if config:
            manifest["userConfig"] = config
    rules = always_apply_rules(plugin_dir)
    if rules:
        manifest["hooks"] = rule_hook(rules)

    out = plugin_dir / ".claude-plugin" / "plugin.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({k: v for k, v in manifest.items() if v is not None}, indent=2, ensure_ascii=False) + "\n")
    return {"name": cursor["name"], "source": "./" + plugin_dir.relative_to(ROOT).as_posix(), "description": cursor["description"]}


def main():
    converted, skipped = [], []
    for plugin_dir in sorted((ROOT / "third_party").iterdir()):
        if not (plugin_dir / ".cursor-plugin" / "plugin.json").exists():
            continue
        entry = convert(plugin_dir)
        (converted if entry else skipped).append(entry or plugin_dir.name)
    json.dump({"converted": converted, "skipped": skipped}, sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
