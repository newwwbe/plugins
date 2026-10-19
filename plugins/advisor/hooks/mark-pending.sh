#!/bin/bash

# PostToolUse hook for Advisor (matcher: Edit|Write|MultiEdit|NotebookEdit).
# Remembers that files changed since the last advisor consult, so the Stop hook
# can ask for a pre-completion review if the turn ends without one.
#
# Input:  { session_id, transcript_path, cwd, tool_name,
#           tool_input: { file_path | notebook_path, ... }, tool_response, ... }
# Output: none

set -euo pipefail
command -v jq >/dev/null 2>&1 || exit 0
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

HOOK_INPUT=$(cat)
advisor_init
advisor_require_enabled
advisor_bind_session || exit 0

FILE_PATH=$(jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' <<< "$HOOK_INPUT")

# The plugin's own state is not work product.
case "$FILE_PATH" in
  */.claude/advisor/*|.claude/advisor/*) exit 0 ;;
esac

touch "$PENDING_FILE"
exit 0
