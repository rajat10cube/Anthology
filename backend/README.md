# anthology-mcp

**MCP server for [Anthology](https://github.com/rajat10cube/Anthology)** — scrape any documentation website into AI-ready Markdown, directly from your AI coding assistant.

## Install

```bash
pip install anthology-mcp
```

## Usage with Claude Code

```bash
claude mcp add anthology -- anthology-mcp
```

Then ask Claude:

- *"Scrape the Supabase auth docs via Anthology, then write the login code for me."*
- *"What scraped docs do you have in Anthology right now?"*

## What it does

Anthology's MCP server exposes three tools to AI agents:

| Tool | Description |
|------|-------------|
| `scrape_new_docs` | Crawl a documentation site and convert it to Markdown |
| `read_scraped_docs` | Read previously scraped documentation |
| `list_scraped_docs` | List all saved documentation projects |

The scraper uses BFS crawling with sitemap discovery, configurable depth/page limits, and optional headless browser support for JS-heavy sites.

## Optional: Headless Browser

For JavaScript-rendered sites (Docusaurus, Mintlify, etc.):

```bash
pip install anthology-mcp[playwright]
playwright install chromium
```

## Links

- **GitHub**: [github.com/rajat10cube/Anthology](https://github.com/rajat10cube/Anthology)
- **License**: [AGPL-3.0](https://github.com/rajat10cube/Anthology/blob/main/LICENSE)
