#!/bin/bash

# State helper for Ralph Loop (Claude Code).
# Claude Code treats .claude/ as a protected path for the Write tool and for
# inline shell redirects, so the skills create and remove the loop state
# through this script instead.
#
# Usage:
#   ralph-state.sh start [--max-iterations N] [--completion-promise TEXT] <<'RALPH_PROMPT'
#   <task prompt>
#   RALPH_PROMPT
#   ralph-state.sh cancel
#   ralph-state.sh status

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
STATE_DIR="$PROJECT_DIR/.claude/ralph"
STATE_FILE="$STATE_DIR/scratchpad.md"

iteration() {
  sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$STATE_FILE" | grep '^iteration:' | head -n 1 | sed 's/^iteration: *//'
}

cmd="${1:-}"
shift || true

case "$cmd" in
  start)
    MAX=0
    PROMISE=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --max-iterations) MAX="${2:-0}"; shift 2 ;;
        --completion-promise) PROMISE="${2:-}"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
      esac
    done
    if [[ ! "$MAX" =~ ^[0-9]+$ ]]; then
      echo "--max-iterations must be a non-negative integer (got '$MAX')." >&2
      exit 2
    fi
    if [[ "$PROMISE" == *$'\n'* ]]; then
      echo "--completion-promise must be a single line." >&2
      exit 2
    fi
    PROMPT=$(cat)
    if [[ -z "${PROMPT//[[:space:]]/}" ]]; then
      echo "No task prompt given on stdin." >&2
      exit 2
    fi
    if [[ -n "$PROMISE" && "$PROMISE" != "null" ]]; then
      # The hook strips only the outer quotes, so store the value literally.
      PROMISE_YAML="\"$PROMISE\""
    else
      PROMISE_YAML="null"
    fi
    mkdir -p "$STATE_DIR"
    {
      printf -- '---\n'
      printf 'iteration: 1\n'
      printf 'max_iterations: %s\n' "$MAX"
      printf 'completion_promise: %s\n' "$PROMISE_YAML"
      printf -- '---\n\n'
      printf '%s\n' "$PROMPT"
    } > "$STATE_FILE"
    echo "Ralph loop active: max_iterations=$MAX, completion_promise=${PROMISE:-none}. State: $STATE_FILE"
    ;;
  cancel)
    if [[ ! -f "$STATE_FILE" ]]; then
      echo "No active Ralph loop found."
      exit 0
    fi
    N=$(iteration || true)
    rm -rf "$STATE_DIR"
    echo "Cancelled Ralph loop (was at iteration ${N:-?})."
    ;;
  status)
    if [[ -f "$STATE_FILE" ]]; then
      cat "$STATE_FILE"
    else
      echo "No active Ralph loop found."
    fi
    ;;
  *)
    echo "Usage: ralph-state.sh start|cancel|status" >&2
    exit 2
    ;;
esac
