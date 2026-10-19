---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
disable-model-invocation: true
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

Invoke when the user says "reflect" or "/reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## 1. Locate the active transcript

Before fanning out, find this conversation's transcript in this project's Claude Code transcript directory, `~/.claude/projects/<cwd>/`, where `<cwd>` is the absolute working directory with every `/` and `.` replaced by `-`. Do not glob across `~/.claude/projects/*/`. That crosses workspace boundaries and reads private chats from unrelated projects.

```bash
dir=~/.claude/projects/$(pwd | sed 's#[/.]#-#g')
ls -t "$dir"/*.jsonl "$dir"/*/subagents/*.jsonl 2>/dev/null | head -10
```

That covers session transcripts (`<session-id>.jsonl`) and subagent transcripts (`<session-id>/subagents/<agent>.jsonl`). The most recently modified session file is usually this conversation. To confirm, find the first `"type":"user"` entry in each candidate and take the file whose `message.content` contains the conversation's opening user prompt. If none matches, pass a tight digest of the session instead.

## 2. Spawn three reviewers in parallel

One message, three Agent tool calls, `subagent_type: "general-purpose"` (it inherits the session's MCP tools). Reviewers need MCP access to look up the tickets, chat threads, and observability traces the transcript references, so do not use a read-only agent type such as `Explore`.

Each reviewer and the synthesizer name a role line in the pstack model config (the `pstack-models` block in `~/.claude/CLAUDE.md`, written by **setup-pstack**) and a default. Set `model` to that line's value, or to the default if the block or the line is missing. Leave `model` unset when the value is `inherit`. If the Agent tool rejects a value, use the default and say so. Pick each subagent's model for the job, per the Subagents section of the **poteto-mode** skill.

| Lens | Role line | Default `model` | Prompt template |
|---|---|---|---|
| Judgment | `reflect judgment, divergent, synthesizer` | `opus` | `references/judgment-reviewer.md` |
| Tooling | `reflect tooling` | `sonnet` | `references/tooling-reviewer.md` |
| Divergent | `reflect judgment, divergent, synthesizer` | `opus` | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in the Agent tool's result.

## 3. Synthesize

One Agent tool call, `subagent_type: "general-purpose"`, `model` from the `reflect judgment, divergent, synthesizer` line (default `opus`). It spot-verifies citations through MCP, so it must not be a read-only agent type. Pass `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. It returns an Accepted / Rejected / Backlog list.

## 4. Structural enforcement check

Move any Accepted item that a lint rule, script, metadata flag, or runtime check would enforce more reliably to Backlog. See the **encode-lessons-in-structure** principle skill.

## 5. Apply

Present the synthesizer's full Accepted / Rejected / Backlog output and wait for explicit approval before applying any Accepted edit. The user picks the subset and may redirect routings. Skill changes affect every future agent in the org. Do not auto-apply.

File each Backlog item to your team's devex or backlog tracker without waiting. Only the Accepted list waits for approval.

Follow each approved row's Routing exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): the parent does it directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to a skill-authoring skill (`skill-creator` when installed, otherwise the **poteto-mode** skill's `playbooks/authoring-a-skill.md`) and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to that skill-authoring skill and run its description-optimization loop.
- `new skill via create-skill: <kebab-name>`: hand creation to that skill-authoring skill. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done.

## 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
