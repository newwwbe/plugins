#!/bin/bash

# State helper for the Advisor skill (Claude Code).
# Claude Code treats .claude/ as a protected path for the Write tool and for
# inline shell redirects, so the skill changes advisor state through this script.
#
# Usage (run from the project root):
#   advisor-state.sh enable [model]   turn on / re-bind to the next session that fires a hook
#   advisor-state.sh off              delete .claude/advisor/
#   advisor-state.sh nudge on|off     toggle the end-of-turn reminder
#   advisor-state.sh status           print state.json (changes nothing)

set -euo pipefail

command -v jq >/dev/null 2>&1 || { echo "advisor: jq is required" >&2; exit 1; }

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
DIR="$PROJECT_DIR/.claude/advisor"
STATE="$DIR/state.json"

cmd="${1:-}"
shift || true

case "$cmd" in
  enable)
    MODEL="${1:-}"
    OLD_MODEL="" OLD_NUDGE="true"
    if [[ -f "$STATE" ]]; then
      OLD_MODEL=$(jq -r '.model // empty' "$STATE" 2>/dev/null || true)
      OLD_NUDGE=$(jq -r 'if .nudge == false then "false" else "true" end' "$STATE" 2>/dev/null || echo true)
    fi
    MODEL="${MODEL:-${OLD_MODEL:-opus}}"
    mkdir -p "$DIR"
    rm -f "$DIR/pending"
    jq -n --arg model "$MODEL" --argjson nudge "$OLD_NUDGE" \
      --arg now "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '{
        enabled: true,
        model: $model,
        nudge: $nudge,
        session_id: null,
        transcript_path: null,
        consults: 0,
        last_consult_at: null,
        enabled_at: $now
      }' > "$STATE.tmp.$$"
    mv "$STATE.tmp.$$" "$STATE"
    echo "advisor enabled: model=$MODEL nudge=$OLD_NUDGE state=$STATE"
    ;;
  off)
    rm -rf "$DIR"
    echo "advisor disabled: removed $DIR"
    ;;
  nudge)
    [[ -f "$STATE" ]] || { echo "advisor is not enabled in this project" >&2; exit 1; }
    case "${1:-}" in
      on) VAL=true ;;
      off) VAL=false ;;
      *) echo "Usage: advisor-state.sh nudge on|off" >&2; exit 2 ;;
    esac
    jq --argjson v "$VAL" '.nudge = $v' "$STATE" > "$STATE.tmp.$$" && mv "$STATE.tmp.$$" "$STATE"
    echo "advisor nudge: ${1}"
    ;;
  status)
    if [[ -f "$STATE" ]]; then
      cat "$STATE"
      [[ -f "$DIR/pending" ]] && echo "pending: edits since last consult"
    else
      echo "advisor is not enabled in this project"
    fi
    ;;
  *)
    echo "Usage: advisor-state.sh enable [model] | off | nudge on|off | status" >&2
    exit 2
    ;;
esac
