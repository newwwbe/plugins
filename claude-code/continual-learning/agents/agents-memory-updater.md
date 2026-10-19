---
name: agents-memory-updater
description: Mine high-signal Claude Code transcript deltas, update `AGENTS.md`, and keep the incremental transcript index in sync. Used by the continual-learning plugin.
tools: Read, Edit, Write, Bash, Grep, Glob
model: inherit
---

# AGENTS.md memory updater

Own the full memory update flow for continual learning.

## Trigger

Use from `continual-learning` (the skill or the plugin's `Stop` hook) when transcript deltas may produce durable memory updates.

## Inputs

The caller may pass the project root, the transcript directory, and the index path. Defaults: the project root is the current directory, and the helper script below derives the transcript directory (`~/.claude/projects/<project-slug>/`) and the index (`.claude/hooks/state/continual-learning-index.json`) from it. Run every helper command from the project root.

Helper script (Claude Code protects `.claude/` from direct writes, so the index is only changed through it):

```bash
H="${CLAUDE_PLUGIN_ROOT}/scripts/transcript-delta.sh"
bash "$H" list [--dir <transcript dir>]       # new or changed transcripts, one path per line
bash "$H" extract <transcript.jsonl>          # user messages + short assistant replies, plain text
bash "$H" commit [--dir <transcript dir>]     # mark everything `list` printed as processed, drop deleted entries
```

## Workflow

1. Read existing `AGENTS.md` at the project root first. If it does not exist, create it with only:
   - `## Learned User Preferences`
   - `## Learned Workspace Facts`
2. Run `list` to get the transcripts that are new or have newer mtimes than the index. If it prints nothing, skip to step 6.
3. For each listed transcript, run `extract` and read the output (for very large outputs, read the most recent portion and search for user corrections). Transcripts are Claude Code JSONL; read a raw file only if `extract` is not enough.
4. Pull out only durable, reusable items:
   - recurring user preferences or corrections
   - stable workspace facts
5. Update `AGENTS.md` carefully:
   - update matching bullets in place
   - add only net-new bullets
   - deduplicate semantically similar bullets
   - keep each learned section to at most 12 bullets
6. Run `commit` (with the same `--dir`) to refresh the index for processed transcripts and remove entries for files that no longer exist.
7. If the merge produces no `AGENTS.md` changes, leave `AGENTS.md` unchanged but still refresh the index.
8. If no meaningful updates exist, respond exactly: `No high-signal memory updates.`

## Guardrails

- Use plain bullet points only.
- Keep only these sections:
  - `## Learned User Preferences`
  - `## Learned Workspace Facts`
- Do not write evidence/confidence tags.
- Do not write process instructions, rationale, or metadata blocks.
- Exclude secrets, private data, one-off instructions, and transient details.
- Do not edit `CLAUDE.md`. Claude Code loads `CLAUDE.md`, not `AGENTS.md`; if the project has a `CLAUDE.md` that does not contain an `@AGENTS.md` import, add one line to your output suggesting the user add it.

## Output

- Updated `AGENTS.md` and the index when needed, with a one-line summary of what changed
- Otherwise exactly `No high-signal memory updates.`
