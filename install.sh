#!/usr/bin/env bash
# Install the newwwbe Claude Code plugin set on this machine (macOS, Linux, WSL).
#
#   curl -fsSL https://raw.githubusercontent.com/newwwbe/plugins/main/install.sh | bash
#
# Options (pass after `bash -s --` when piping):
#   --add "a b"       also install these plugins (e.g. MCP integrations: "github notion")
#   --plugins "a b"   install exactly these plugins instead of the default set
#   --with "x y"      opt-in extras: ruflo (multi-agent swarms), headroom (context compression proxy)
#   --no-tools        skip the CLI tools (uv, Graphify)
#   --style NAME      default output style (default: attention-span:Attention-kind)
#   --no-style        leave the output style unchanged
#   --list            print the default set and exit
set -euo pipefail

MARKETPLACE_REPO="${NEWWWBE_MARKETPLACE_REPO:-newwwbe/plugins}"
MARKETPLACE_NAME="newwwbe"
STYLE="attention-span:Attention-kind"
PLUGINS="attention-span anti-slop thermos pstack cursor-team-kit dyl-stack advisor ralph-loop orchestrate create-plugin agent-compatibility cli-for-agent teaching docs-canvas pr-review-canvas ponytail arena-skill markitdown"
EXTRA=""
WITH=""
TOOLS=1

while [ $# -gt 0 ]; do
  case "$1" in
    --add) EXTRA="$2"; shift 2 ;;
    --plugins) PLUGINS="$2"; shift 2 ;;
    --with) WITH="$2"; shift 2 ;;
    --no-tools) TOOLS=0; shift ;;
    --style) STYLE="$2"; shift 2 ;;
    --no-style) STYLE=""; shift ;;
    --list) echo "$PLUGINS"; exit 0 ;;
    -h|--help) echo "Usage: install.sh [--add \"a b\"] [--plugins \"a b\"] [--with \"ruflo headroom\"] [--no-tools] [--style NAME | --no-style] [--list]"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

if ! command -v claude >/dev/null 2>&1; then
  echo "Claude Code is not installed. Install it first:" >&2
  echo "  curl -fsSL https://claude.ai/install.sh | bash" >&2
  exit 1
fi

failed=""
install_plugin() { # plugin@marketplace
  if claude plugin install "$1" >/dev/null 2>&1; then
    echo "    ok  $1"
  else
    echo "    !!  $1 (install failed)"
    failed="$failed $1"
  fi
}

echo "==> Marketplace: $MARKETPLACE_REPO"
claude plugin marketplace add "$MARKETPLACE_REPO" >/dev/null
claude plugin marketplace update "$MARKETPLACE_NAME" >/dev/null || true

for plugin in $PLUGINS $EXTRA; do
  install_plugin "$plugin@$MARKETPLACE_NAME"
done

# uv runs the MarkItDown MCP server (uvx) and installs the Python CLIs below.
ensure_uv() {
  command -v uv >/dev/null 2>&1 && return 0
  [ -x "$HOME/.local/bin/uv" ] && { PATH="$HOME/.local/bin:$PATH"; return 0; }
  echo "==> Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null
  PATH="$HOME/.local/bin:$PATH"
  command -v uv >/dev/null 2>&1
}

if [ "$TOOLS" = 1 ]; then
  if ensure_uv; then
    UV_BIN="$(uv tool dir --bin 2>/dev/null || echo "$HOME/.local/bin")"
    echo "==> Graphify (codebase knowledge graph, /graphify)"
    if uv tool install --upgrade graphifyy >/dev/null 2>&1 && "$UV_BIN/graphify" install --platform claude </dev/null >/dev/null 2>&1; then
      echo "    ok  graphify"
    else
      echo "    !!  graphify (run: uv tool install graphifyy && graphify install)"
      failed="$failed graphify"
    fi
  else
    echo "    !!  uv (install it from https://docs.astral.sh/uv/; markitdown and graphify need it)"
    failed="$failed uv"
  fi
fi

for extra in $WITH; do
  case "$extra" in
    ruflo)
      echo "==> Ruflo (marketplace ruvnet/ruflo)"
      claude plugin marketplace add ruvnet/ruflo >/dev/null || true
      claude plugin marketplace update ruflo >/dev/null || true
      install_plugin "ruflo-core@ruflo"
      install_plugin "ruflo-swarm@ruflo"
      ;;
    headroom)
      echo "==> Headroom (marketplace headroomlabs-ai/headroom)"
      if ensure_uv && uv tool install --upgrade --python 3.13 "headroom-ai[all]" >/dev/null 2>&1 \
         && "$(uv tool dir --bin 2>/dev/null || echo "$HOME/.local/bin")/headroom" init -g claude </dev/null >/dev/null 2>&1; then
        echo "    ok  headroom CLI (undo: headroom unwrap claude)"
      else
        echo "    !!  headroom CLI (see https://github.com/headroomlabs-ai/headroom)"
        failed="$failed headroom-cli"
      fi
      claude plugin marketplace add headroomlabs-ai/headroom >/dev/null || true
      claude plugin marketplace update headroom-marketplace >/dev/null || true
      install_plugin "headroom@headroom-marketplace"
      ;;
    *) echo "    !!  unknown extra: $extra (choose from: ruflo headroom)"; failed="$failed $extra" ;;
  esac
done

if [ -n "$STYLE" ]; then
  settings="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"
  mkdir -p "$(dirname "$settings")"
  [ -s "$settings" ] || echo '{}' > "$settings"
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$settings" "$STYLE" <<'PY'
import json, sys
path, style = sys.argv[1], sys.argv[2]
with open(path) as f:
    data = json.load(f)
data["outputStyle"] = style
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY
  elif command -v node >/dev/null 2>&1; then
    node -e 'const fs=require("fs");const [p,s]=process.argv.slice(1);const d=JSON.parse(fs.readFileSync(p,"utf8"));d.outputStyle=s;fs.writeFileSync(p,JSON.stringify(d,null,2)+"\n")' "$settings" "$STYLE"
  elif command -v jq >/dev/null 2>&1; then
    tmp="$(mktemp)" && jq --arg s "$STYLE" '.outputStyle = $s' "$settings" > "$tmp" && mv "$tmp" "$settings"
  else
    echo "==> Could not set the output style (needs python3, node or jq). Add this to $settings:"
    echo "      \"outputStyle\": \"$STYLE\""
    STYLE=""
  fi
  [ -n "$STYLE" ] && echo "==> Output style: $STYLE"
fi

echo "==> Done. Start a new Claude Code session to use the plugins."
if [ -n "$failed" ]; then
  echo "    Failed:$failed" >&2
  exit 1
fi
