#!/bin/bash

# Ralph Loop Stop hook (Claude Code).
# When Claude finishes a turn, decide whether to feed the same prompt back for
# another iteration or let the session end.
#
# Claude Code Stop hook contract:
#   Input (stdin JSON): { session_id, transcript_path, cwd, hook_event_name: "Stop",
#                         stop_hook_active, last_assistant_message, ... }
#   Output: {"decision":"block","reason":"<next prompt>"} on stdout keeps Claude
#           working with <reason> as its next instruction; exit 0 with no output
#           lets the turn end.
#
# The Cursor version used a separate afterAgentResponse hook to spot the
# <promise> tag. Claude Code passes the final assistant message to the Stop hook
# (last_assistant_message, with a transcript_path fallback), so both steps live here.

set -euo pipefail

command -v jq >/dev/null 2>&1 || exit 0

HOOK_INPUT=$(cat)

CWD=$(jq -r '.cwd // empty' <<< "$HOOK_INPUT")
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-${CWD:-.}}"
STATE_DIR="$PROJECT_DIR/.claude/ralph"
STATE_FILE="$STATE_DIR/scratchpad.md"

# No active loop. Let the session end.
if [[ ! -f "$STATE_FILE" ]]; then
  exit 0
fi

stop_loop() {
  echo "$1" >&2
  rm -rf "$STATE_DIR"
  exit 0
}

frontmatter_value() {
  sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$STATE_FILE" | grep "^$1:" | head -n 1 | sed "s/^$1: *//" || true
}

ITERATION=$(frontmatter_value iteration)
MAX_ITERATIONS=$(frontmatter_value max_iterations)
COMPLETION_PROMISE=$(frontmatter_value completion_promise | sed 's/^"\(.*\)"$/\1/')
BOUND_SESSION=$(frontmatter_value session_id | sed 's/^"\(.*\)"$/\1/')
SESSION_ID=$(jq -r '.session_id // empty' <<< "$HOOK_INPUT")

# Bind the loop to the first session whose turn ends after it was started, and
# stay out of other sessions working in the same project.
if [[ -n "$SESSION_ID" ]]; then
  if [[ -z "$BOUND_SESSION" || "$BOUND_SESSION" == "null" ]]; then
    TMP="${STATE_FILE}.tmp.$$"
    # Insert (or fill) session_id inside the frontmatter only.
    awk -v sid="$SESSION_ID" '
      /^---$/ { fences++; if (fences == 2 && !done) { print "session_id: " sid; done = 1 } print; next }
      fences == 1 && /^session_id:/ { if (!done) { print "session_id: " sid; done = 1 } next }
      { print }
    ' "$STATE_FILE" > "$TMP"
    mv "$TMP" "$STATE_FILE"
  elif [[ "$BOUND_SESSION" != "$SESSION_ID" ]]; then
    exit 0
  fi
fi

if [[ ! "$ITERATION" =~ ^[0-9]+$ ]]; then
  stop_loop "Ralph loop: state file corrupted (iteration: '$ITERATION'). Stopping."
fi
if [[ ! "$MAX_ITERATIONS" =~ ^[0-9]+$ ]]; then
  stop_loop "Ralph loop: state file corrupted (max_iterations: '$MAX_ITERATIONS'). Stopping."
fi

# Completion promise: look for <promise>TEXT</promise> in the final reply.
if [[ -n "$COMPLETION_PROMISE" && "$COMPLETION_PROMISE" != "null" ]]; then
  RESPONSE_TEXT=$(jq -r '.last_assistant_message // empty' <<< "$HOOK_INPUT")
  if [[ -z "$RESPONSE_TEXT" ]]; then
    TRANSCRIPT=$(jq -r '.transcript_path // empty' <<< "$HOOK_INPUT")
    if [[ -n "$TRANSCRIPT" && -f "$TRANSCRIPT" ]]; then
      RESPONSE_TEXT=$(tail -n 200 "$TRANSCRIPT" \
        | jq -r 'select(.type == "assistant") | .message.content | if type == "string" then . else (map(select(.type == "text") | .text) | join("\n")) end' 2>/dev/null \
        | tail -c 20000 || true)
    fi
  fi
  if [[ "$RESPONSE_TEXT" == *"<promise>"* ]]; then
    PROMISE_TEXT=$(printf '%s' "$RESPONSE_TEXT" | perl -0777 -ne 'if (/<promise>(.*?)<\/promise>/s) { $p = $1; $p =~ s/^\s+|\s+$//g; $p =~ s/\s+/ /g; print $p }' 2>/dev/null || true)
    if [[ -n "$PROMISE_TEXT" && "$PROMISE_TEXT" == "$COMPLETION_PROMISE" ]]; then
      stop_loop "Ralph loop: completion promise fulfilled at iteration $ITERATION."
    fi
  fi
fi

if [[ $MAX_ITERATIONS -gt 0 && $ITERATION -ge $MAX_ITERATIONS ]]; then
  stop_loop "Ralph loop: max iterations ($MAX_ITERATIONS) reached."
fi

# Prompt text: everything after the closing --- of the frontmatter.
PROMPT_TEXT=$(awk '/^---$/{i++; next} i>=2' "$STATE_FILE")
if [[ -z "${PROMPT_TEXT//[[:space:]]/}" ]]; then
  stop_loop "Ralph loop: no prompt text found in state file. Stopping."
fi

NEXT_ITERATION=$((ITERATION + 1))
TMP="${STATE_FILE}.tmp.$$"
sed "s/^iteration: .*/iteration: $NEXT_ITERATION/" "$STATE_FILE" > "$TMP"
mv "$TMP" "$STATE_FILE"

if [[ -n "$COMPLETION_PROMISE" && "$COMPLETION_PROMISE" != "null" ]]; then
  HEADER="[Ralph loop iteration $NEXT_ITERATION. To complete: output <promise>$COMPLETION_PROMISE</promise> ONLY when genuinely true.]"
else
  HEADER="[Ralph loop iteration $NEXT_ITERATION.]"
fi

# Block the stop: Claude continues with the same prompt as its next instruction.
# stop_hook_active is intentionally ignored; max_iterations and the promise
# are the loop bounds, as in the Cursor version (loop_limit: null).
jq -n --arg msg "$HEADER

$PROMPT_TEXT" '{"decision": "block", "reason": $msg}'
exit 0
