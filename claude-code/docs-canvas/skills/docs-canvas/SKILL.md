---
name: docs-canvas
description: >-
  Render documentation as a self-contained, navigable HTML page (a "docs
  canvas") that organizes architecture notes, API references, walkthroughs,
  and how-tos into sections with a table of contents and cross-references,
  written to a local file the user opens in a browser. Use when the user asks
  for a docs canvas, documentation overview, architecture walkthrough, API
  reference page, or wants to render structured documentation as an
  interactive page.
---

# Docs Canvas

Build a single HTML page (the "canvas") that presents documentation — architecture notes, API references, design docs, runbooks, or codebase walkthroughs — as an interactive, navigable surface rather than as a flat markdown file.

> **Status:** initial outline, as upstream. Treat the steps below as a
> starting outline and refine as the docs canvas pattern matures.

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

## Gather the source material

Accept any of: a directory of markdown files, a single doc URL, an inline outline, or a question to answer from the codebase. Collect headings, code blocks, diagrams, and any cross-references between documents.

## Plan the canvas layout

Decide the top-level structure before writing any markup. A docs canvas usually has:

1. **Overview** — A short summary card with the purpose of the doc, scope, and audience.
2. **Table of contents** — Navigable list of sections, ideally pinned or sticky so the reader can jump around.
3. **Body sections** — One section per logical unit (architecture, API, examples, gotchas). Each section can mix prose, code blocks, diagrams, and callouts.
4. **References** — Links to related docs, source files, RFCs, and external material.

## Render with the HTML primitives

Use the primitives listed above:

- Use cards/sections to group related content visually.
- Use code blocks with syntax highlighting for snippets.
- Use diagrams (inline SVG or CSS boxes-and-arrows) for architecture.
- Use callouts for "Important", "Warning", "Note", "Deprecated".
- Use tables for API parameter lists and option matrices.

## Tone and content

Write reader-facing prose. Lead with the answer or the headline, then explain. Keep examples small and runnable. Cite source files as `path:line` code references so readers can jump in.

## Be creative

The sections above are a floor, not a ceiling. The goal is the fastest possible path for the reader to understand the topic — so look at the source material in front of you and ask what representation would actually help. A diagram, a sequence chart, a side-by-side comparison, a decision tree, a glossary, a curated FAQ, a single large worked example — whatever fits.
