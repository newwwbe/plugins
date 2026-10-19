#!/bin/bash

# Shared helpers for the Advisor hooks (Claude Code). Source this file; do not run it.
#
# Every hook reads its Claude Code hook input (JSON on stdin) into HOOK_INPUT and
# then calls advisor_init, which resolves the project directory.
#
# State lives in <project>/.claude/advisor/:
#   state.json   written by the advisor skill, kept current here
#   pending      marker: files were edited since the last consult
#   log.md       one entry per completed consult

advisor_init() {
  local cwd
  cwd=$(jq -r '.cwd // empty' <<< "$HOOK_INPUT" 2>/dev/null || true)
  ADVISOR_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-${cwd:-.}}"
  ADVISOR_DIR="$ADVISOR_PROJECT_DIR/.claude/advisor"
  STATE_FILE="$ADVISOR_DIR/state.json"
  PENDING_FILE="$ADVISOR_DIR/pending"
  LOG_FILE="$ADVISOR_DIR/log.md"
}

# Exit quietly unless advisor mode is on.
advisor_require_enabled() {
  [[ -f "$STATE_FILE" ]] || exit 0
  [[ "$(jq -r '.enabled // false' "$STATE_FILE" 2>/dev/null)" == "true" ]] || exit 0
}

# Atomically apply a jq filter to state.json.
# Usage: advisor_state_update '<filter>' [jq args...]
advisor_state_update() {
  local filter="$1"
  shift
  local tmp="${STATE_FILE}.tmp.$$"
  if jq "$@" "$filter" "$STATE_FILE" > "$tmp" 2>/dev/null; then
    mv "$tmp" "$STATE_FILE"
  else
    rm -f "$tmp"
  fi
}

# Bind the state to the first session that touches it and keep transcript_path
# current. Returns 1 when the hook input belongs to a different session, so
# callers stay out of sessions that did not enable the advisor.
# A fresh bind also drops the pending marker so a re-bind cannot inherit the
# previous session's edits.
advisor_bind_session() {
  local sid bound transcript current
  sid=$(jq -r '.session_id // empty' <<< "$HOOK_INPUT")
  bound=$(jq -r '.session_id // empty' "$STATE_FILE")
  if [[ -n "$sid" ]]; then
    if [[ -z "$bound" ]]; then
      advisor_state_update '.session_id = $sid' --arg sid "$sid"
      rm -f "$PENDING_FILE"
    elif [[ "$bound" != "$sid" ]]; then
      return 1
    fi
  fi
  transcript=$(jq -r '.transcript_path // empty' <<< "$HOOK_INPUT")
  current=$(jq -r '.transcript_path // empty' "$STATE_FILE")
  if [[ -n "$transcript" && "$transcript" != "$current" ]]; then
    advisor_state_update '.transcript_path = $path' --arg path "$transcript"
  fi
  return 0
}
