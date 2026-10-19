#!/bin/bash

# Stop hook for Advisor.
# If files changed since the last advisor consult and the turn ended without
# one, block the stop once per batch of edits and ask Claude to run the
# pre-completion consult.
#
# Input:  { session_id, transcript_path, cwd, stop_hook_active,
#           last_assistant_message, ... }
# Output: {"decision":"block","reason":"<text>"} to continue, or nothing.

set -euo pipefail
command -v jq >/dev/null 2>&1 || exit 0
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

HOOK_INPUT=$(cat)
advisor_init
advisor_require_enabled
advisor_bind_session || exit 0

# Already continuing because of a Stop hook: do not nudge again
# (replaces Cursor's loop_limit).
if [[ "$(jq -r '.stop_hook_active // false' <<< "$HOOK_INPUT")" == "true" ]]; then
  exit 0
fi

if [[ "$(jq -r 'if .nudge == false then "false" else "true" end' "$STATE_FILE")" != "true" ]]; then
  exit 0
fi

[[ -f "$PENDING_FILE" ]] || exit 0

# Claude stopped to ask the user something. Stay quiet and leave the marker
# armed so the reminder fires after the user answers and the work resumes.
# (Cursor captured this with an afterAgentResponse hook; Claude Code passes the
# final message as last_assistant_message, with transcript_path as fallback.)
LAST=$(jq -r '.last_assistant_message // empty' <<< "$HOOK_INPUT")
if [[ -z "$LAST" ]]; then
  TRANSCRIPT=$(jq -r '.transcript_path // empty' <<< "$HOOK_INPUT")
  if [[ -n "$TRANSCRIPT" && -f "$TRANSCRIPT" ]]; then
    LAST=$(tail -n 50 "$TRANSCRIPT" | jq -r 'select(.type == "assistant") | .message.content | if type == "string" then . else (map(select(.type == "text") | .text) | join("\n")) end' 2>/dev/null | tail -c 400 || true)
  fi
fi
LAST_CHAR=$(printf '%s' "$LAST" | tail -c 400 | tr -d '[:space:]*_`' | tail -c 1)
if [[ "$LAST_CHAR" == "?" ]]; then
  exit 0
fi

rm -f "$PENDING_FILE"

MODEL=$(jq -r '.model // "opus"' "$STATE_FILE")
MESSAGE="[Advisor] Files changed since the last advisor consult and the turn ended without one. If this work is done, or you were about to declare it done, run the pre-completion consult now per the advisor skill: build the briefing, spawn the \`advisor:advisor-subagent\` agent (model: $MODEL), act on the verdict, and report it in one line. If the change was trivial, or you are waiting on the user, say so in one line and stop."

jq -n --arg msg "$MESSAGE" '{"decision": "block", "reason": $msg}'
exit 0
