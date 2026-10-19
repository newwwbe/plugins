#!/bin/bash

# Incremental transcript index for Continual Learning (Claude Code).
#
# Claude Code stores each session's transcript as JSONL under
# ~/.claude/projects/<project-slug>/<session-id>.jsonl (subagent transcripts
# live in <session-id>/subagents/ and are skipped). The index records the mtime
# of every transcript already mined, so each run only reads what changed.
# Claude Code protects .claude/ from direct writes, so the index is maintained
# by this script.
#
# Usage (run from the project root):
#   transcript-delta.sh list    [--dir DIR]          new or changed transcripts, one path per line
#   transcript-delta.sh extract FILE [--max-chars N] the user's messages (and short assistant
#                                                    replies) from one transcript, as plain text
#   transcript-delta.sh commit  [--dir DIR] [FILE...] record FILEs (default: everything `list`
#                                                    prints) as processed; drop deleted entries
#
# DIR defaults to the transcript directory for $CLAUDE_PROJECT_DIR (or $PWD).
# Index: <project>/.claude/hooks/state/continual-learning-index.json

set -euo pipefail

command -v jq >/dev/null 2>&1 || { echo "continual-learning: jq is required" >&2; exit 1; }

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
INDEX_PATH="$PROJECT_DIR/.claude/hooks/state/continual-learning-index.json"

default_dir() {
  local slug
  slug=$(printf '%s' "$PROJECT_DIR" | sed 's/[^A-Za-z0-9-]/-/g')
  printf '%s/projects/%s' "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" "$slug"
}

file_mtime() {
  stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null
}

load_index() {
  if [[ -f "$INDEX_PATH" ]] && jq -e '.version == 1' "$INDEX_PATH" >/dev/null 2>&1; then
    cat "$INDEX_PATH"
  else
    printf '{"version":1,"transcripts":{}}'
  fi
}

list_delta() {
  local dir="$1" index f m old
  index=$(load_index)
  [[ -d "$dir" ]] || return 0
  for f in "$dir"/*.jsonl; do
    [[ -f "$f" ]] || continue
    m=$(file_mtime "$f")
    old=$(jq -r --arg f "$f" '.transcripts[$f].mtime // empty' <<< "$index")
    if [[ -z "$old" ]] || (( m > old )); then
      printf '%s\n' "$f"
    fi
  done
}

cmd="${1:-}"
shift || true

DIR=""
MAX_CHARS=400
FILES=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) DIR="$2"; shift 2 ;;
    --max-chars) MAX_CHARS="$2"; shift 2 ;;
    *) FILES+=("$1"); shift ;;
  esac
done
DIR="${DIR:-$(default_dir)}"

case "$cmd" in
  list)
    list_delta "$DIR"
    ;;
  extract)
    [[ ${#FILES[@]} -eq 1 && -f "${FILES[0]}" ]] || { echo "Usage: transcript-delta.sh extract FILE" >&2; exit 2; }
    jq -R -r --argjson max "$MAX_CHARS" '
      fromjson? |
      def text: if type == "string" then . else (map(select(.type == "text") | .text) | join("\n")) end;
      select((.type == "user" or .type == "assistant") and (.isMeta != true) and (.isSidechain != true))
      | (.message.content | text) as $t
      | select($t != null and ($t | length) > 0)
      | select(($t | startswith("<local-command") or startswith("Caveat:")) | not)
      | (if ($t | startswith("<command-")) then
           (($t | capture("<command-name>(?<n>[^<]*)</command-name>") | .n)? // "") as $n
           | (($t | capture("<command-args>(?<a>[\\s\\S]*)</command-args>") | .a)? // "") as $a
           | ($n + " " + $a)
         else $t end) as $t
      | if .type == "user" then "USER: " + $t
        else "ASSISTANT: " + (if ($t | length) > $max then $t[0:$max] + " [...]" else $t end) end
    ' "${FILES[0]}"
    ;;
  commit)
    if [[ ${#FILES[@]} -eq 0 ]]; then
      while IFS= read -r f; do FILES+=("$f"); done < <(list_delta "$DIR")
    fi
    index=$(load_index)
    for f in ${FILES[@]+"${FILES[@]}"}; do
      [[ -f "$f" ]] || continue
      index=$(jq -c --arg f "$f" --argjson m "$(file_mtime "$f")" '.transcripts[$f] = {mtime: $m}' <<< "$index")
    done
    # Drop entries for transcripts that no longer exist.
    while IFS= read -r f; do
      [[ -n "$f" && ! -f "$f" ]] && index=$(jq -c --arg f "$f" 'del(.transcripts[$f])' <<< "$index")
    done < <(jq -r '.transcripts | keys[]' <<< "$index")
    mkdir -p "$(dirname "$INDEX_PATH")"
    jq . <<< "$index" > "$INDEX_PATH.tmp.$$" && mv "$INDEX_PATH.tmp.$$" "$INDEX_PATH"
    echo "Indexed $(jq '.transcripts | length' <<< "$index") transcript(s) in $INDEX_PATH"
    ;;
  *)
    echo "Usage: transcript-delta.sh list|extract|commit (see header)" >&2
    exit 2
    ;;
esac
