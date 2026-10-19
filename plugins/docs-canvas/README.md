# Docs Canvas for Claude Code

Claude Code port of the [Docs Canvas](https://github.com/cursor/plugins/tree/main/docs-canvas) Cursor plugin: render documentation — architecture notes, API references, runbooks, codebase walkthroughs — as a navigable page instead of a flat markdown file. Claude Code has no Canvas, so the page is a single self-contained HTML file you open in your browser.

## Installation

```
/plugin marketplace add newwwbe/plugins
/plugin install docs-canvas@newwwbe
```

## Usage

Ask for a "docs canvas", "documentation overview", "architecture walkthrough", or "API reference page", or invoke `/docs-canvas:docs-canvas` directly. Source material can be a directory of markdown files, a single doc URL, an inline outline, or a question to answer from the codebase.

The page leads with an overview card, a sticky table of contents, body sections mixing prose/code/diagrams/callouts, and a references block. By default it is written to `~/.claude/canvases/<slug>.html` (outside your repo); Claude prints the path and the command to open it. Name a different path in your request to override.

## Differences from the Cursor version

- Manifest lives in `.claude-plugin/plugin.json`; Cursor-only fields (`displayName`, `logo`, `category`, `tags`) and the avatar asset are dropped.
- Output is a self-contained HTML file (inline CSS/JS, no CDN, works from `file://`, light/dark aware) instead of a Cursor Canvas. The "read `~/.cursor/skills-cursor/canvas/SKILL.md` and the canvas SDK `.d.ts` files" prerequisite is replaced by an inline set of HTML output rules (location, escaping, primitives, self-check).
- Canvas components map to plain HTML: cards → `<section>`, DAG/mermaid diagrams → inline SVG or CSS boxes, collapsibles → `<details>`.
- Like upstream, the skill body is an initial outline.

## License

MIT
