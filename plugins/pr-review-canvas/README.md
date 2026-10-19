# PR Review Canvas for Claude Code

Claude Code port of the [PR Review Canvas](https://github.com/cursor/plugins/tree/main/pr-review-canvas) Cursor plugin: render a pull request diff as a review page organized for reviewer comprehension rather than file-tree order. Claude Code has no Canvas, so the page is a single self-contained HTML file you open in your browser.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install pr-review-canvas@newwwbe
```

## Usage

Ask for a "PR review canvas", "walk me through this diff", or "change-set overview" with a GitHub PR URL or number, or invoke `/pr-review-canvas:pr-review-canvas <PR URL>`. Without a PR reference, Claude asks which PR you mean (it does not guess from the local branch).

The page groups changes into **Core logic** (full diffs with context), **Wiring & integration** (condensed), and **Boilerplate & mechanical** (file list and stats), adding pseudocode, before/after example traces, and callouts (`Subtle`, `Breaking`, `Race condition`, `Perf`) only where they help. By default it is written to `~/.claude/canvases/<slug>.html` (outside your repo); Claude prints the path and the command to open it.

## Requirements

- [GitHub CLI](https://cli.github.com/) (`gh`) installed and authenticated, with access to the PR's repository.

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) and the avatar asset are dropped.
- Output is a self-contained HTML file (inline CSS/JS, no CDN, works from `file://`, light/dark aware) instead of a Cursor Canvas. The "read `~/.cursor/skills-cursor/canvas/SKILL.md` and the canvas SDK `.d.ts` files" prerequisite is replaced by an inline set of HTML output rules (location, escaping, diff-block styling, self-check).
- Canvas SDK components (diff views, charts, DAG layout, cards, interactive state) map to plain HTML diff blocks, tables, inline SVG, and small vanilla-JS toggles.
- Adds `gh pr view --json ...` for PR metadata and a stop-if-`gh`-unavailable rule.

## License

MIT
