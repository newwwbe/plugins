#!/bin/bash

# Continual Learning Stop hook (Claude Code).
#
# Counts completed turns and, once the cadence thresholds are met and the
# transcript has advanced since the last run, blocks the stop once and asks
# Claude to run the memory update through the `agents-memory-updater` agent.
#
# Claude Code Stop hook contract:
#   Input (stdin JSON): { session_id, transcript_path, cwd, prompt_id?,
#                         stop_hook_active, last_assistant_message, ... }
#   Output: {"decision":"block","reason":"..."} to continue, or nothing.
#
# Cadence state: <project>/.claude/hooks/state/continual-learning.json

set -uo pipefail

command -v jq >/dev/null 2>&1 || exit 0

HOOK_INPUT=$(cat)

CWD=$(jq -r '.cwd // empty' <<< "$HOOK_INPUT" 2>/dev/null)
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-${CWD:-$PWD}}"
STATE_DIR="$PROJECT_DIR/.claude/hooks/state"
STATE_PATH="$STATE_DIR/continual-learning.json"
INDEX_PATH="$STATE_DIR/continual-learning-index.json"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

DEFAULT_MIN_TURNS=10
DEFAULT_MIN_MINUTES=120
TRIAL_DEFAULT_MIN_TURNS=3
TRIAL_DEFAULT_MIN_MINUTES=15
TRIAL_DEFAULT_DURATION_MINUTES=$((24 * 60))

# env_value PRIMARY LEGACY
env_value() {
  local v="${!1:-}"
  [[ -n "$v" ]] || v="${!2:-}"
  printf '%s' "$v"
}

# positive_int VALUE FALLBACK
positive_int() {
  if [[ "$1" =~ ^[0-9]+$ ]] && (( 10#$1 > 0 )); then
    printf '%s' "$((10#$1))"
  else
    printf '%s' "$2"
  fi
}

is_true() {
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

file_mtime() {
  stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null
}

save_state() {
  mkdir -p "$STATE_DIR" || return 0
  printf '%s\n' "$1" > "$STATE_PATH.tmp.$$" && mv "$STATE_PATH.tmp.$$" "$STATE_PATH"
}

main() {
  local state
  state='{"version":1,"lastRunAt":0,"turnsSinceLastRun":0,"lastTranscriptMtime":null,"lastProcessedPromptId":null,"trialStartedAt":null}'
  if [[ -f "$STATE_PATH" ]] && jq -e '.version == 1' "$STATE_PATH" >/dev/null 2>&1; then
    state=$(jq -c --argjson d "$state" '$d + .' "$STATE_PATH")
  fi

  local prompt_id stop_active transcript
  prompt_id=$(jq -r '.prompt_id // empty' <<< "$HOOK_INPUT")
  stop_active=$(jq -r '.stop_hook_active // false' <<< "$HOOK_INPUT")
  transcript=$(jq -r '.transcript_path // empty' <<< "$HOOK_INPUT")

  # Only the first stop of a user prompt counts as a completed turn (Cursor:
  # status == completed && loop_count == 0). A stop that continues because a
  # Stop hook blocked it has stop_hook_active == true.
  local counted=1
  [[ "$stop_active" == "true" ]] && counted=0
  if [[ -n "$prompt_id" && "$prompt_id" == "$(jq -r '.lastProcessedPromptId // empty' <<< "$state")" ]]; then
    counted=0
  fi
  if [[ -n "$prompt_id" ]]; then
    state=$(jq -c --arg p "$prompt_id" '.lastProcessedPromptId = $p' <<< "$state")
  fi

  local now turns trial_started
  now=$(date +%s)
  turns=$(( $(jq -r '.turnsSinceLastRun // 0' <<< "$state") + counted ))

  local trial_enabled=0
  is_true "$(env_value CONTINUAL_LEARNING_TRIAL_MODE CONTINUOUS_LEARNING_TRIAL_MODE)" && trial_enabled=1
  trial_started=$(jq -r '.trialStartedAt // empty' <<< "$state")
  if (( trial_enabled && counted )) && [[ -z "$trial_started" ]]; then
    trial_started=$now
    state=$(jq -c --argjson t "$now" '.trialStartedAt = $t' <<< "$state")
  fi

  local trial_duration trial_min_turns trial_min_minutes min_turns min_minutes
  trial_duration=$(positive_int "$(env_value CONTINUAL_LEARNING_TRIAL_DURATION_MINUTES CONTINUOUS_LEARNING_TRIAL_DURATION_MINUTES)" $TRIAL_DEFAULT_DURATION_MINUTES)
  trial_min_turns=$(positive_int "$(env_value CONTINUAL_LEARNING_TRIAL_MIN_TURNS CONTINUOUS_LEARNING_TRIAL_MIN_TURNS)" $TRIAL_DEFAULT_MIN_TURNS)
  trial_min_minutes=$(positive_int "$(env_value CONTINUAL_LEARNING_TRIAL_MIN_MINUTES CONTINUOUS_LEARNING_TRIAL_MIN_MINUTES)" $TRIAL_DEFAULT_MIN_MINUTES)
  min_turns=$(positive_int "$(env_value CONTINUAL_LEARNING_MIN_TURNS CONTINUOUS_LEARNING_MIN_TURNS)" $DEFAULT_MIN_TURNS)
  min_minutes=$(positive_int "$(env_value CONTINUAL_LEARNING_MIN_MINUTES CONTINUOUS_LEARNING_MIN_MINUTES)" $DEFAULT_MIN_MINUTES)

  if (( trial_enabled )) && [[ -n "$trial_started" ]] && (( now - trial_started < trial_duration * 60 )); then
    min_turns=$trial_min_turns
    min_minutes=$trial_min_minutes
  fi

  local last_run minutes_since=999999999
  last_run=$(jq -r '.lastRunAt // 0' <<< "$state")
  if (( last_run > 0 )); then
    minutes_since=$(( (now - last_run) / 60 ))
  fi

  local mtime="" last_mtime advanced=0
  [[ -n "$transcript" ]] && mtime=$(file_mtime "$transcript")
  last_mtime=$(jq -r '.lastTranscriptMtime // empty' <<< "$state")
  if [[ -n "$mtime" ]] && { [[ -z "$last_mtime" ]] || (( mtime > last_mtime )); }; then
    advanced=1
  fi

  if (( counted && turns >= min_turns && minutes_since >= min_minutes && advanced )); then
    state=$(jq -c --argjson now "$now" --argjson m "$mtime" \
      '.lastRunAt = $now | .turnsSinceLastRun = 0 | .lastTranscriptMtime = $m' <<< "$state")
    save_state "$state"

    local transcript_dir helper reason
    transcript_dir=$(dirname "$transcript")
    helper="$PLUGIN_ROOT/scripts/transcript-delta.sh"
    reason="[Continual learning] Run the continual-learning memory update now. Use the Agent tool with subagent_type \`continual-learning:agents-memory-updater\` for the full flow, and pass it these exact values: project root \`$PROJECT_DIR\`, transcript directory \`$transcript_dir\`, helper script \`$helper\`, incremental index \`$INDEX_PATH\`. It must consider only transcripts that are new or whose mtime is newer than the index (\`bash \"$helper\" list --dir \"$transcript_dir\"\`), commit the index afterwards, and update \`AGENTS.md\` only for high-signal recurring user corrections and durable workspace facts. Exclude one-off/transient details and secrets. Do not mine transcripts or edit AGENTS.md yourself. Relay the agent's result in one line; if no meaningful updates exist, respond exactly: No high-signal memory updates."
    jq -n --arg r "$reason" '{"decision": "block", "reason": $r}'
    return 0
  fi

  state=$(jq -c --argjson t "$turns" '.turnsSinceLastRun = $t' <<< "$state")
  save_state "$state"
  return 0
}

if ! main; then
  echo "[continual-learning-stop] failed" >&2
fi
exit 0
