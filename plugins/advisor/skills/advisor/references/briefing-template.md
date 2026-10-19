# Advisor briefing

Fill every section. Quote evidence verbatim; summarize only narrative. Redact secrets. Each consult spawns a fresh advisor, so write every section in full; point to `.claude/advisor/log.md` for earlier verdicts when they matter.

```markdown
## Checkpoint

<major decision | stuck | pre-completion | on request> — <one line on why now>

## User's request

<the original request, verbatim>

<later constraints or corrections from the user, verbatim, in order>

## What has happened so far

<chronological and compact: what you investigated, decided, changed, tried, and ruled out, with the reason for each>

## Evidence

<verbatim tool output relevant to this checkpoint: errors, stack traces, test output, command output, the relevant diff hunks. Trim unrelated noise and mark trims with [...]>

## Current state

<`git status --short` and `git diff --stat` output; files touched; anything half-done>

## Questions for the advisor

1. <specific question>
2. ...

<For a decision: the options with the tradeoffs as you see them, and your current leaning with reasons.
For stuck: what you expected vs. what you observed, and the hypotheses you have ruled out.
For pre-completion: what you verified and how, and what you did not verify.>

## What I need back

<for example: "a verdict and the single best next step", "confirm or refute hypothesis 2", "anything I missed before I call this done">

## Full transcript

<`transcript_path` from `.claude/advisor/state.json` when advisor mode is on in this conversation; otherwise "not available">
```
