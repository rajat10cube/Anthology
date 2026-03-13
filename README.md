<div align="center">

# ⚡ Anthology

**Turn any documentation website into AI-ready Markdown — in seconds.**

[![AGPL-3.0 License](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![PyPI](https://img.shields.io/pypi/v/anthology-mcp.svg)](https://pypi.org/project/anthology-mcp/)

</div>

---

## The Problem

LLMs don't know about libraries released after their training cutoff. Copy-pasting docs or building RAG systems isn't practical for most developers.

On top of that, AI coding agents like Claude Code charge a premium for internet search — so every time your agent looks up a docs page, it costs extra. Feeding docs as context yourself is both cheaper and faster.

## The Solution

Anthology scrapes any documentation website and converts it to well-structured Markdown files that you can feed directly into your LLM as context.

**Paste a URL → Get AI-ready Markdown → Load into your LLM**

---

## ✨ Features

- 🕷️ **Parallel Scraper** — Asynchronous BFS crawl with configurable depth and concurrency
- 🗺️ **Sitemap Discovery** — Automatically fetches `sitemap.xml` to find all pages before crawling, including sitemap index files and gzip-compressed sitemaps
- 📝 **Clean Markdown** — Strips nav, sidebars, footers; adds YAML frontmatter
- 🔍 **Global Multi-Page Search** — Instantly scan the contents of all documents in a library simultaneously
- 📊 **Real-time Progress** — SSE-powered live updates during scraping
- 📚 **Library Management** — Browse, view, search, and delete scraped collections
- 📦 **Flexible Export** — Single combined `.md` or `.zip` of individual files
- 🌙 **Dark UI** — Glassmorphism design with smooth animations

---

## 🚀 Quick Start

### Prerequisites

- **Docker** (recommended) — or Node.js ≥ 18 + Python ≥ 3.11 for manual setup

### Option A: Docker (recommended)

```bash
git clone https://github.com/rajat10cube/anthology.git
cd anthology
docker compose up --build
```

Open **http://localhost:3000** and start scraping!

### Option B: Manual Setup

#### Prerequisites

- Node.js ≥ 18
- Python ≥ 3.11

#### 1. Clone

```bash
git clone https://github.com/rajat10cube/anthology.git
cd anthology
```

#### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** and start scraping!

---

## 🤖 AI Agent Integration (MCP)

Anthology includes a native [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server, allowing AI coding assistants like **Claude Code** to autonomously scrape updated documentation and read it directly into their context window.

### Option A: Install from [PyPI](https://pypi.org/project/anthology-mcp/) (recommended)

```bash
pipx install anthology-mcp
claude mcp add anthology -- anthology-mcp
```

That's it — two commands. Start asking Claude to scrape docs!

### Option B: From source

If you already cloned the repo:

```bash
claude mcp add anthology "/absolute/path/to/anthology/backend/.venv/bin/python" "/absolute/path/to/anthology/backend/run_mcp.py"
```

### Example Prompts

- *"Scrape the Supabase auth docs via Anthology, then write the login code for me."*
- *"Use Anthology to scrape https://docs.openclaw.ai/ with max_pages=50 and max_depth=3, then tell me where config is stored."*
- *"What scraped docs do you have in Anthology right now?"*

> **Note:** When installed via pipx, scraped data is stored in `~/.anthology/data/` and cache in `~/.anthology/cache/`. When running from source, data stays in `backend/data/`.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scrape` | Scrape a URL and save to library |
| `POST` | `/api/scrape/stream` | Scrape with SSE progress events |
| `GET` | `/api/projects` | List all projects |
| `GET` | `/api/projects/:id` | Project detail with page list |
| `GET` | `/api/projects/:id/pages/:pid` | Single page markdown |
| `GET` | `/api/projects/:id/export?format=single\|multi` | Export as `.md` or `.zip` |
| `DELETE` | `/api/projects/:id` | Delete a project |

---

## 🧪 Testing

```bash
# Backend (77 tests)
cd backend && source .venv/bin/activate
python -m pytest tests/ -v

# Frontend (42 tests)
cd frontend && npm test
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite, Tailwind CSS v4, shadcn/ui, Zustand, mark.js |
| **Backend** | Python 3.13, FastAPI, BeautifulSoup4, markdownify, httpx, Playwright, MCP |
| **Infra** | Docker, nginx |
| **Testing** | pytest, Vitest, React Testing Library |

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

[AGPL-3.0](LICENSE) — any public SaaS implementation must share its source code.
