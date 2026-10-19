---
name: pr-review-canvas
description: >-
  Render a PR diff review as a self-contained HTML page (a "review canvas")
  that groups changes by reviewer importance, separates boilerplate from core
  logic, and highlights tricky or unexpected code, written to a local file the
  user opens in a browser. Use when reviewing a pull
  request, summarizing a diff for review, or when the user asks for a
  PR review canvas, diff walkthrough, or change-set overview.
---

# PR Review Canvas

Build a single HTML page (the "canvas") that presents a PR diff reorganized for reviewer comprehension — not in file-tree order.

## Output: a self-contained HTML file

Claude Code has no canvas surface, so the "canvas" is a single HTML file the user opens in a browser.

- **Location.** If the user named a path, use it. Otherwise write to `~/.claude/canvases/<slug>.html` (create the directory; `<slug>` is a short kebab-case name for the topic), so nothing is added to the user's repository. When done, print the absolute path and the command to open it (`open <path>` on macOS, `xdg-open <path>` on Linux, `start <path>` on Windows). Do not open it yourself unless asked.
- **Self-contained.** One file. All CSS in a `<style>` block, all JS in a `<script>` block, no external scripts, stylesheets, fonts, or images, no build step. It must render correctly from `file://` with no network. Use the system font stack and a monospace stack for code.
- **Escape everything.** HTML-escape every piece of source text you embed (`&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`, and quotes inside attributes). Unescaped code is the most common way these pages break. Generating the file from a small script (Python/Node) that escapes content is fine and often safer than writing it by hand; delete the script afterwards if you created it in the repo.
- **Theme and layout.** Define colors as CSS variables with a `@media (prefers-color-scheme: dark)` override. Readable max width for prose, responsive down to phone width, no horizontal page scroll (code blocks scroll on their own).
- **Primitives to build with** (plain HTML/CSS, a few lines of vanilla JS at most):
  - cards/sections (`<section>` with a border and padding) to group content;
  - a sticky table of contents linking to section `id`s;
  - `<pre><code>` blocks; simple syntax coloring is optional, never at the cost of correctness;
  - diff blocks: one line per row, classes for added/removed/context lines (green/red backgrounds), line numbers optional;
  - callouts: a bordered box with a short tag ("Note", "Warning", "Subtle", "Breaking", ...);
  - tables for parameter lists, option matrices, and file stats;
  - `<details>`/`<summary>` for collapsible content;
  - diagrams as inline SVG or CSS boxes-and-arrows (no Mermaid or other CDN libraries).
- **Code references.** Cite source files as `path/to/file.ts:42`. If the files are local, you may also link them with `file://` absolute URLs; for GitHub PRs, link to the file in the PR when you know the URL.
- **Self-check before reporting.** Re-read the generated file (or grep it) to confirm: no raw `<` from embedded code broke the markup, every TOC link has a matching `id`, no external URLs are loaded as resources, and nothing is invented that is not in the source material.

## Gather the diff

Expect a GitHub PR link (a full URL like `https://github.com/<owner>/<repo>/pull/<n>`, or an equivalent `gh`-resolvable reference). Use `gh pr diff <pr>` to collect every file's path, additions, deletions, and hunks (`gh pr view <pr> --json title,body,files,commits` gives the title, description, and per-file stats). `gh` must be installed and authenticated; if it is not, tell the user and stop.

**If the user didn't provide a PR link, stop and ask.** Do not guess at the current branch, infer from recent history, or fall back to a local `git diff`. Ask the user which diff they want to review — a specific PR URL or number — and wait for their reply before continuing.

## Group changes for comprehension

Do **not** present files in alphabetical or tree order. Reorganize into sections ordered by reviewer value:

1. **Core logic** — New behavior, algorithm changes, state transitions, API surface changes. Show full diffs with surrounding context.
2. **Wiring & integration** — Route registration, dependency injection, config plumbing that connects the core logic. Condensed — enough to confirm correctness.
3. **Boilerplate & mechanical** — Import reordering, renames, generated code, formatting, type re-exports. Summarize as a list of file names and stats. No inline diffs unless specifically relevant.

Lead with core logic. The reviewer's attention is freshest at the top.

## Distill complex logic into pseudocode

When a core change involves dense or intricate logic — deeply nested conditions, state machines, retry/backoff flows, multi-step transformations — add a short pseudocode summary next to the diff. The pseudocode should strip away language syntax, error handling, and boilerplate to expose the essential algorithm or control flow in a few lines. This lets the reviewer confirm intent before reading the real code.

Only do this when the actual diff is hard to scan. Straightforward changes don't need a pseudocode mirror.

## Trace tricky logic on a concrete example

Pseudocode shows the shape of the change; an example trace shows it executing. When a hunk changes behavior in a way that's hard to predict from reading it — reordered effects, new short-circuits, altered edge cases — pick a concrete input and walk it through both the old and new code paths side-by-side, highlighting the step where they diverge and what the observable outcome is. Keep the input small and realistic.

Use this for genuinely surprising behavior changes, not every core hunk.

## Call attention to tricky things

When a hunk contains something surprising, risky, or easy to miss, visually separate it from the surrounding diff and pair it with a short tag (e.g. "Subtle", "Breaking", "Race condition", "Perf") and a one-sentence explanation so the reviewer sees the concern and the code together.

Reserve these callouts for genuinely tricky items — overuse destroys signal.

## Tone and content

Write reviewer-facing commentary, not a changelog. Focus on:
- **Why** something changed, not just what changed.
- Interactions between files — e.g. "The new validator in `core.ts` is invoked by the route added in `routes.ts`."
- Anything the diff alone doesn't make obvious.

Keep commentary terse. One or two sentences per note.

## Be creative

The sections above are a floor, not a ceiling. The goal is the fastest possible path for the reviewer to understand this specific change — so look at the diff in front of you and ask what representation would actually help. A tiny state diagram, a before/after call graph, a table of input→output pairs, a timeline of commits, a confidence annotation per file, a single large callout with everything else collapsed — whatever fits the change.

HTML gives you tables, diff blocks, inline SVG diagrams and charts, cards, stat rows, collapsible sections, and small bits of vanilla-JS interactivity (e.g. a "show boilerplate" toggle). Reach for whichever best serve the change at hand. A review of a refactor looks different from a review of a bug fix looks different from a review of a new feature — let the page reflect that.
