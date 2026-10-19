#!/bin/bash

# SubagentStop hook for Advisor.
# When the advisor subagent (agent_type "advisor:advisor-subagent") finishes,
# count the consult, clear the pending-edits marker, and append the advice to
# .claude/advisor/log.md so the user can review it later.
#
# Input:  { session_id, transcript_path, cwd, agent_id, agent_type,
#           agent_transcript_path, last_assistant_message, stop_hook_active, ... }
# Output: none

set -euo pipefail
command -v jq >/dev/null 2>&1 || exit 0
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

HOOK_INPUT=$(cat)

AGENT_TYPE=$(jq -r '.agent_type // empty' <<< "$HOOK_INPUT")
case "$AGENT_TYPE" in
  advisor-subagent|*:advisor-subagent) ;;
  *) exit 0 ;;
esac

advisor_init
advisor_require_enabled
advisor_bind_session || exit 0

NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
advisor_state_update '.consults = ((.consults // 0) + 1) | .last_consult_at = $now' --arg now "$NOW"
rm -f "$PENDING_FILE"

SUMMARY=$(jq -r '.last_assistant_message // empty' <<< "$HOOK_INPUT")
if [[ -z "$SUMMARY" ]]; then
  AGENT_TRANSCRIPT=$(jq -r '.agent_transcript_path // empty' <<< "$HOOK_INPUT")
  if [[ -n "$AGENT_TRANSCRIPT" && -f "$AGENT_TRANSCRIPT" ]]; then
    SUMMARY=$(jq -r 'select(.type == "assistant") | .message.content | if type == "string" then . else (map(select(.type == "text") | .text) | join("\n")) end' "$AGENT_TRANSCRIPT" 2>/dev/null | tail -c 6000 || true)
  fi
fi
SUMMARY=$(printf '%s' "$SUMMARY" | head -c 6000)
VERDICT=$(printf '%s\n' "$SUMMARY" | grep -m 1 -i '^verdict:' | sed 's/^[Vv]erdict: *//; s/[.;].*$//' | cut -c1-60 || true)
TITLE="Advisor consult${VERDICT:+ — $VERDICT}"

mkdir -p "$ADVISOR_DIR"
{
  printf '## %s — %s\n\n' "$NOW" "$TITLE"
  if [[ -n "$SUMMARY" ]]; then
    printf '%s\n\n' "$SUMMARY"
  else
    printf '_No summary captured._\n\n'
  fi
} >> "$LOG_FILE"

exit 0
