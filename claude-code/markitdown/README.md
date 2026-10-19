# markitdown

Registers Microsoft's [markitdown-mcp](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-mcp) server with Claude Code. It exposes one tool, `convert_to_markdown(uri)`, which takes an `http:`, `https:`, `file:` or `data:` URI (PDF, DOCX, XLSX, PPTX, HTML, CSV, JSON, images, audio, ZIP, YouTube) and returns Markdown.

Requires [uv](https://docs.astral.sh/uv/) on `PATH`; the server runs with `uvx markitdown-mcp`, so there is nothing else to install. The repository's `install.sh` / `install.ps1` install uv if it is missing.

Ask Claude things like "convert ~/Downloads/spec.pdf to markdown and summarize the API section".

## Install

```
/plugin install markitdown --marketplace newwwbe/plugins
```
