<div align="center">

# ⚡ Anthology

**Turn any documentation website into AI-ready Markdown — in seconds.**

[![AGPL-3.0 License](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)

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

- 🕷️ **Smart Scraper** — BFS crawl with configurable depth and page limits
- 📝 **Clean Markdown** — Strips nav, sidebars, footers; adds YAML frontmatter
- 📊 **Real-time Progress** — SSE-powered live updates during scraping
- 📚 **Library Management** — Browse, view, search, and delete scraped collections
- 📦 **Flexible Export** — Single combined `.md` or `.zip` of individual files
- 🌙 **Dark UI** — Glassmorphism design with smooth animations

---

## 🚀 Quick Start

### Prerequisites

- Node.js ≥ 18
- Python ≥ 3.11

### 1. Clone

```bash
git clone https://github.com/rajat10cube/anthology.git
cd anthology
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** and start scraping!

---

## 🏗️ Architecture

```
Anthology/
├── backend/                    # Python + FastAPI
│   ├── app/
│   │   ├── main.py             # App entry + CORS + routing
│   │   ├── storage.py          # File-system CRUD
│   │   ├── routers/
│   │   │   ├── scrape.py       # POST /api/scrape (+ SSE stream)
│   │   │   └── projects.py     # CRUD + export endpoints
│   │   └── services/
│   │       ├── scraper.py      # BFS web crawler
│   │       └── markdown.py     # HTML → Markdown converter
│   ├── tests/                  # 60 pytest tests
│   └── requirements.txt
│
└── frontend/                   # React + Vite + Tailwind CSS v4
    ├── src/
    │   ├── components/         # Navbar, ScrapeForm, ProjectCard, MarkdownRenderer
    │   ├── pages/              # Home, Library, ProjectDetail
    │   ├── stores/             # Zustand state (projects, scrape)
    │   ├── lib/                # API client, utils
    │   └── __tests__/          # 42 Vitest tests
    └── vite.config.ts
```

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
# Backend (60 tests)
cd backend && source .venv/bin/activate
python -m pytest tests/ -v

# Frontend (42 tests)
cd frontend && npm test
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite, Tailwind CSS v4, shadcn/ui, Zustand |
| **Backend** | Python 3.13, FastAPI, BeautifulSoup4, markdownify, httpx |
| **Testing** | pytest, Vitest, React Testing Library |

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

[AGPL-3.0](LICENSE) — any public SaaS implementation must share its source code.
