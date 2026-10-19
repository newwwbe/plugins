---
name: thermos
description: "Launch both thermo-nuclear review subagents in parallel, then synthesize their findings. Use for thermos, double thermo review, or combined bug/security and code-quality branch audits."
disable-model-invocation: true
---

# Thermos

Run the two thermo review passes as background subagents in parallel, then synthesize their results.

## Workflow

1. Determine the review scope from the user request, PR, current branch, or relevant changed files. Default base is `main`; use the repository's default branch if `main` does not exist.
2. Gather the context yourself with Bash and Read: `git diff <base>...HEAD`, the list of changed files, and the full contents of each changed file. Reviewers must be able to evaluate the change without guessing.
3. Launch both subagents with the Agent tool, in the same message, with `run_in_background: true`:
   - `subagent_type: "thermos:thermo-nuclear-review-subagent"` for bugs, breakages, security, devex regressions, feature-flag leaks, and other branch-audit risks.
   - `subagent_type: "thermos:thermo-nuclear-code-quality-review-subagent"` for maintainability, structure, file-size growth, spaghetti, abstractions, and codebase-health risks.
4. Pass each subagent the same prompt: a `### Git / diff output` section and a `### Changed file contents` section, and ask it to return prioritized findings with file:line references and evidence.
5. After both finish, synthesize the results with findings first, deduplicated across reviewers. Weight overlapping findings more heavily, resolve disagreements with your own judgment, and keep summaries brief.

If individual background summaries are already visible to the user, do not restate them wholesale. Surface the unified verdict, the highest-signal findings, and any remaining uncertainty.
