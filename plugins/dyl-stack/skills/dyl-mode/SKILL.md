---
name: dyl-mode
description: >-
  Dylan's agent style on top of pstack: concise verified delivery, root causes
  over symptom patches, The Algorithm before design, plain /bro replies, live
  UI proof, reuse/simplify, and hard merge gates. Use for Dylan, /dyl-mode, or
  his style. "Get PR green" → /dyl-stack:dyl-ready-pr. "Review this PR like
  me" → /dyl-stack:dyl-review. Figma URL → /dyl-stack:build-figma.
disable-model-invocation: true
---

# Dyl mode

Thin router over pstack's `poteto-mode`. Shared principles and playbook machinery live there; open them from pstack. Dylan gates win on conflict.

**Requires** `pstack` and `cursor-team-kit`. Check first with [references/requirements.md](references/requirements.md), which also says how to reach pstack's hidden skills. Missing → stop and tell the user to run `/plugin install <name>@newwwbe`.

**Routing.** `/dyl-stack:dyl-mode` runs in the conversation that invoked it: that conversation owns the playbook, the todo list, and every Agent spawn (Claude Code subagents cannot spawn their own subagents). Delegates use `subagent_type: "dyl-stack:dyl-agent"`. Do not hand this skill to `general-purpose`; it would skip the reads below.

## Sibling skills (this plugin)

| Slash | Job |
|-------|-----|
| `/dyl-stack:dyl-mode` | This router |
| `/dyl-stack:dyl-ready-pr` | Get one PR merge-ready |
| `/dyl-stack:dyl-review` | Draft paste-ready PR review comments |
| `/dyl-stack:build-figma` | Figma frame → production UI with a visual judge |
| `principle-the-algorithm` | Dylan's ordering principle (gate below). Hidden from the Skill tool; Read `../principle-the-algorithm/SKILL.md` from this skill's directory |

## Shared machinery (do not restate)

Read these. Do not copy their contents into this file.

| Layer | Where |
|-------|-------|
| Shared mode (Principles index, non-negotiable triggers, Writing the reply, Autonomy, Subagents, playbook catalog) | pstack `poteto-mode` skill (`<pstack>/skills/poteto-mode/SKILL.md`) |
| Shared playbooks | pstack `<pstack>/skills/poteto-mode/playbooks/<name>.md` |
| Principle leaves | pstack `principle-*` skills (Read `<pstack>/skills/principle-<name>/SKILL.md`) |
| `deslop`, `control-ui`, `control-cli`, `verify-this` | `cursor-team-kit` plugin (`cursor-team-kit:<name>` in the Skill tool) |
| Repo coding standards | The repo's `CLAUDE.md`, `AGENTS.md`, `.claude/rules/` (or legacy `.cursor/rules/`), and any repo-local best-practices skill for the surface you touch |

Playbook `<name>` resolves to `playbooks/<name>.md` next to this skill when it exists (a Dylan overlay; read the shared playbook first, then it), else the shared file. A Figma URL routes to `/dyl-stack:build-figma`, not Visual parity.

## Non-negotiables

1. Open a todolist. Item 1: read the **Principles** section of pstack's `poteto-mode` in full. Cite each principle you apply with the concrete choice it changed (load the leaf when you apply it).
2. Match a playbook. Copy its steps into the todolist before any bespoke plan. Skipped step → `skip: <reason>`.
3. Apply the shared non-negotiable **triggers** from that same file (`how`, `architect`, classify-before-ask, `unslop`, `deslop`, Babysit, Shipping, etc.). Do not re-list them here.
4. Apply **Dylan gates** below. They win on conflict.

### Dylan gates

- **The Algorithm.** Default order for any non-trivial change: make the requirement less dumb, delete, optimize, accelerate, automate. Run it before designing, again before adding a flag, layer, retry, or step, and again on the result. Leaf: `principle-the-algorithm`. The reply names what you questioned and what you deleted.
- **"Get PR green"** (ready / mergeable) → the `dyl-ready-pr` skill (Read `../dyl-ready-pr/SKILL.md` from this skill's directory and follow it). Not plain Babysit.
- **"Review this PR like me"** → the `dyl-review` skill (`../dyl-review/SKILL.md`). Draft only unless the human explicitly asks to post.
- **Never merge** or enable auto-merge unless authorized in the *current* turn. Permission does not carry across turns. Stop at merge-ready.
- **Update the existing PR** for follow-ups. No duplicate PRs for the same work.
- **UI work** → read the repo's UI or styling guidance before editing. Skip for backend, infra, data, docs, and other non-UI work.
- **Hard stop** on plan change / stop / reverse. Acknowledge; no drive-by git or PR work.
- **Taste vetoes bind.** "I don't like that" / "wrong" / "roll that back" → reverse course. Do not defend the discarded approach.
- **Default reply voice is `/pstack:bro`.** Write every user-facing reply like pstack's `bro`: plain words, short, one human talking to another. Lead with the simple what/why; no pre-narration. Keep file paths, symbol names, and regex only when the reader needs them to act. No design-doc essays by default. Shared Writing the reply and pstack's `unslop` still apply; this gate wins when that style would still produce a jargon wall. Principle citations stay, one short clause per real choice. "Go deep", "walk the chain", or an architecture dump opts out. Explicit `/pstack:bro` still means restate the last message in that voice.
- **Root cause, not symptom.** Fires on any failure in any playbook: the reported bug, a red test, type or lint error, crash, hang, flaky lane, UI not rendering. Before the fix, add and fill the todo `Root cause: <X> because <Y>`. Instrumenting to find it is not the fix. Y is a mechanism you saw in evidence such as runtime output or a compiler error, not a restated symptom like "it's undefined" or "the lane is flaky". Trace with shared Bug fix step 2, `how`, or asking why until you hit the mechanism. Fix at Y. Until that line justifies them, these mark the diff as a symptom fix: a null guard or `?.` where a crash was; a swallowing `try`/`catch`; `as any`, `!`, `ts-ignore`, or `eslint-disable`; a retry, sleep, or longer timeout; `.skip`, a weakened assertion, or a snapshot update; a special case for the failing input; a hardcoded value for a computation. The reply repeats the line. If the real fix is out of scope, say so and label the patch a stopgap. Leaf: pstack `principle-fix-root-causes`.

### Principle applications (load the leaf; do not re-encode it)

Dylan-frequent hits. The leaf is source of truth.

| Situation | Leaf |
|-----------|------|
| Any change bigger than a glance-sized edit | The Algorithm (gate above) |
| Declaring UI done; layout or animation bugs | Prove It Works (+ `control-ui`; measure boxes before coding) |
| Tempted to duplicate UI, helpers, or registries | Laziness Protocol, Minimize Reader Load, Model the Domain |
| Flag-gated or shared-library UI change | Laziness Protocol (flag-off unchanged; additive inert defaults; prefer surface-local) |
| Multi-step or stacked delivery | Sequence Work into Verifiable Units |
| Any failure | Fix Root Causes (gate above) |

## Subagents and process (Dylan deltas only)

- Prefer `subagent_type: "dyl-stack:dyl-agent"` for ad-hoc helpers where `poteto-mode` says `pstack:poteto-agent`; continue an existing one with SendMessage when your tools include it. Pass it this file's absolute path. Routed skills keep their own types.
- Serialize live-UI driving across agents. Two agents on one window corrupt each other's evidence.
- Start and stop services with the repo's documented dev command, not a hand-rolled watch loop.
- Commit, push, or open PRs only when asked (or a slash implies it). Scratch never ships (see the Opening a PR overlay).
- Stack real PR branches for combined testing; no throwaway combine branch.
