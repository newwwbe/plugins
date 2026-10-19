---
name: advisor
description: >-
  Advisor mode. Consult a stronger model (Opus by default) at key checkpoints:
  before major decisions, when stuck on an error, and before declaring a task
  done. Use when the user types /advisor:advisor, asks to turn the advisor on or
  off, picks an advisor model, or explicitly asks for a second opinion from a
  stronger model. Never enable it on your own.
argument-hint: "[model | off | status | ask <question> | nudge on|off]"
---

# Advisor

You are the main model. Advisor mode adds a second, stronger model that you consult at a few key points. The advisor gets your briefing (and the full transcript when available), thinks hard, and returns a verdict with guidance. It does not edit files. You still do the work and make the final call.

State lives in `.claude/advisor/state.json` at the project root. When that file exists with `"enabled": true`, advisor mode is on for this project. Claude Code protects `.claude/` from direct writes, so every state change goes through the plugin's helper script:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/advisor-state.sh" <enable [model] | off | nudge on|off | status>
```

Run it from the project root. Reading `state.json` with the Read tool is fine.

## Commands

Arguments, if any: $ARGUMENTS

The text after `/advisor:advisor` selects the action.

| Input | Action |
| --- | --- |
| `/advisor:advisor` | Enable for this conversation with the default advisor, `opus`. If a state file already exists, from this or another conversation, re-bind it here, keeping its `model` and `nudge` settings. |
| `/advisor:advisor <model>` | Same, with the given model: `opus`, `sonnet`, or `haiku`. |
| `/advisor:advisor off` | Disable: `advisor-state.sh off` (deletes `.claude/advisor/`). |
| `/advisor:advisor status` | Report model, consult count, and whether the end-of-turn nudge is on (`advisor-state.sh status`). Changes nothing. |
| `/advisor:advisor ask <question>` | Consult now about the current work, regardless of checkpoint. |
| `/advisor:advisor nudge on` / `off` | Toggle the end-of-turn reminder posted by the plugin's `Stop` hook (default on). |

If the message also contains a task (`/advisor:advisor, then refactor the cache layer`), enable first, then do the task under advisor mode.

### Choosing the model

Claude Code subagents run Claude models only. The default is `opus`, the strongest. For `/advisor:advisor <model>`, map the request to one of the aliases `opus`, `sonnet`, `haiku` (a family or version name such as "Opus 4" or "sonnet latest" resolves to its alias). A non-Claude model name (Grok, GPT, Composer, ...) is not available here: say so in one line and keep the current model.

## Enabling

1. Resolve the model as described above.
2. Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/advisor-state.sh" enable [model]`. It rewrites `.claude/advisor/state.json`, carrying over the existing `model` (unless you pass one) and `nudge`, resetting every other field, and deleting the `pending` marker; `log.md` is kept. That re-binds the mode to this conversation: the hooks fill `session_id` and `transcript_path` on their next run. Leave those fields, `consults`, and `last_consult_at` alone.
3. Confirm in one line: `Advisor on: <model>. I'll consult it before major decisions, when I'm stuck, and before I call the task done.` Then continue with any task in the same message.

Never stage or commit `.claude/advisor/`.

## Checkpoints

Consult at these points and nowhere else. Each consult is a strong-model call; the value comes from using it selectively.

1. **Before a major decision.** Choosing between architectures or approaches; changes that are hard to reverse or have a wide blast radius (schema or data migrations, deleting or rewriting a module, public API or config format changes, dependency swaps, auth, payments, or other security-sensitive code); or a request that is ambiguous in a way that would change the work materially. Consult once you have a concrete plan and the options in hand, not before you understand the problem. One consult covers the plan; do not re-consult per file.
2. **When stuck.** The same error or failing test after two genuine fix attempts; behavior you cannot explain from the code; or when you are about to reach for a workaround: a retry loop, a `sleep`, a broad `try/except`, skipping a test, or disabling a check to get past something.
3. **Before declaring done.** Any task that changed logic or touched more than a couple of files: consult once before writing the final summary, and include what you verified and how. Skip for trivial edits (typos, comments, a one-line config change) and say so in one line.
4. **On request.** `/advisor:advisor ask ...`, or the user asks what the advisor thinks.

Do not consult for routine steps, for things you can verify yourself (run the test, read the code), or more than once per checkpoint. If you would consult more than about four times in one task, the task should probably be split, or you should ask the user.

## How to consult

1. Read `.claude/advisor/state.json` and decide which situation you are in:
   - **Mode on here**: the file exists with `enabled: true` and you ran the Enabling steps in this conversation. Checkpoint consults and `/advisor:advisor ask` both follow the steps below in full.
   - **Not on here**: the file is missing, `enabled` is false, or you did not enable it in this conversation. A file you did not write belongs to another chat; only `/advisor:advisor` re-binds it, so leave it alone. Do not consult at checkpoints. If the user explicitly asks for a consult in this message (`/advisor:advisor ask ...`, or a request for a second opinion), run it as a one-off: a fresh spawn on the file's `model` if there is one, otherwise `opus`; no state changes, and no `transcript_path` (another chat's transcript is not yours to share; write "not available"). Mention that `/advisor:advisor` turns the mode on for this conversation.
2. Build the briefing from `references/briefing-template.md` (in this skill's directory). Give the advisor everything it needs to disagree with you:
   - The user's request verbatim, plus constraints or corrections they added later.
   - What has happened so far, in order: what you investigated, decided, changed, tried, and ruled out.
   - Relevant tool results verbatim: error messages, stack traces, test output, diffs. Trim unrelated noise and mark trims with `[...]`, but never paraphrase evidence.
   - Current state: `git status --short`, `git diff --stat`, files you touched, anything half-done.
   - Your specific questions, the options you see, and your current leaning with reasons.
   - The `transcript_path` from `state.json` when set and the mode is on in this conversation, so the advisor can read the full conversation itself.
   - Earlier verdicts in this task, if any (one line each), since every consult is a fresh advisor.
   - No secrets. Redact tokens, keys, and `.env` values.
3. Spawn the advisor in the foreground with the Agent tool and wait for it:
   - `subagent_type: "advisor:advisor-subagent"`
   - `model: <state.model>` (the agent defaults to `opus`; omit `model` if the Agent tool rejects it)
   - `description: "Advisor: <checkpoint>"`, for example `Advisor: pre-completion review`
   - `run_in_background: false`. Wait for the verdict before you continue or reply.
4. Act on the verdict:
   - `proceed`: go.
   - `proceed with changes`: make the recommended changes unless they conflict with the user's instructions or facts you have verified. Say which you skipped and why.
   - `stop`: do not continue with the plan. Rethink, or bring the disagreement to the user if it is a product or scope question.
   - If the advisor asks for something it needs, spawn it once more with the original briefing plus exactly what it asked for. Do not ping-pong.
   - You are accountable for the result. The advisor is a strong second opinion, not an authority. If it is wrong about the codebase, show it the evidence once, or overrule it and tell the user why.
5. Report each consult to the user in one or two lines: `Advisor (<model>): <verdict>. <One-line summary>. <What you did about it.>` Keep the advisor's full response out of the chat unless the user asks; the plugin's `SubagentStop` hook also appends it to `.claude/advisor/log.md`.

## End-of-turn nudge

When files changed since the last consult and a turn ends without one, the plugin's `Stop` hook blocks the stop once with a message that starts with `[Advisor]`. Treat it as the "before declaring done" checkpoint: run the pre-completion consult, or answer in one line that the change was trivial, or that you are waiting on the user, and stop. It fires at most once per batch of edits, and stays quiet when your last message ended with a question for the user. `/advisor:advisor nudge off` disables it.

## Disabling

`/advisor:advisor off`: run `advisor-state.sh off` and confirm in one line. Do not consult again in this conversation unless the user re-enables the mode or explicitly asks for a one-off consult.

## Guardrails

- Never enable advisor mode unasked. "Get a second opinion on this" is a one-off consult, not a mode change.
- The advisor is read-only. Never ask it to edit files or do the task.
- Never loop on the advisor: at most one follow-up per checkpoint.
- If the `advisor:advisor-subagent` agent is unavailable (no Agent tool, or a hook denies it), tell the user once and continue without it.
