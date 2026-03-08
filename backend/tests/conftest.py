"""Shared test fixtures."""
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app import storage


@pytest.fixture
def test_client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """Override the storage DATA_DIR with a temp directory."""
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <html>
    <head><title>Test Page - Docs</title></head>
    <body>
        <nav><a href="/other">Other</a></nav>
        <main>
            <h1>Getting Started</h1>
            <p>Welcome to the documentation.</p>
            <pre><code class="language-python">print("hello")</code></pre>
            <h2>Installation</h2>
            <p>Run <code>pip install mylib</code> to install.</p>
            <a href="/docs/guide">Guide</a>
            <a href="/docs/api">API Reference</a>
        </main>
        <footer>Copyright 2024</footer>
    </body>
    </html>
    """


@pytest.fixture
def sample_project(tmp_data_dir):
    """Create a sample project on disk for testing."""
    project_dir = tmp_data_dir / "test123"
    project_dir.mkdir()

    manifest = {
        "id": "test123",
        "name": "Test Docs",
        "url": "https://example.com/docs",
        "pages": [
            {"id": "page1", "title": "Getting Started", "url": "https://example.com/docs"},
            {"id": "page2", "title": "API Guide", "url": "https://example.com/docs/api"},
        ],
        "page_count": 2,
        "scraped_at": "2024-01-01T00:00:00+00:00",
    }
    (project_dir / "manifest.json").write_text(json.dumps(manifest))
    (project_dir / "page1.md").write_text("# Getting Started\n\nWelcome!\n")
    (project_dir / "page2.md").write_text("# API Guide\n\nEndpoints here.\n")

    return manifest
