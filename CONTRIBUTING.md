# Contributing to Anthology

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

### Prerequisites

- **Node.js** ≥ 18
- **Python** ≥ 3.11
- **npm** (comes with Node.js)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend
cd backend && source .venv/bin/activate && python -m pytest tests/ -v

# Frontend
cd frontend && npm test
```

## Making Changes

1. **Fork** the repo and create a feature branch from `main`
2. Make your changes with clear, descriptive commits
3. Add or update tests for any new functionality
4. Ensure all tests pass before submitting
5. Open a **Pull Request** against `main`

## Code Style

- **Python**: Follow PEP 8. Use type hints.
- **TypeScript/React**: Follow the existing patterns. Use functional components and hooks.

## Reporting Issues

Open a [GitHub Issue](../../issues) with:
- A clear title and description
- Steps to reproduce (if applicable)
- Expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
