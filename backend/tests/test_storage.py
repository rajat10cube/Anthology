"""Tests for file-system storage layer."""
import json
import pytest

from app.storage import (
    save_project,
    list_projects,
    get_project,
    get_page,
    delete_project,
    export_project,
)


class TestSaveProject:
    def test_creates_manifest_and_files(self, tmp_data_dir):
        pages = [
            {"id": "p1", "title": "Page 1", "url": "https://example.com/1", "markdown": "# Page 1\n"},
            {"id": "p2", "title": "Page 2", "url": "https://example.com/2", "markdown": "# Page 2\n"},
        ]
        manifest = save_project(name="Test Project", url="https://example.com", pages=pages)

        assert manifest["name"] == "Test Project"
        assert manifest["url"] == "https://example.com"
        assert manifest["page_count"] == 2
        assert "id" in manifest
        assert "scraped_at" in manifest

        # Check files exist
        project_dir = tmp_data_dir / manifest["id"]
        assert (project_dir / "manifest.json").exists()
        assert (project_dir / "p1.md").exists()
        assert (project_dir / "p2.md").exists()

    def test_markdown_content_saved_correctly(self, tmp_data_dir):
        pages = [{"id": "p1", "title": "T", "url": "https://example.com", "markdown": "# Hello World\n"}]
        manifest = save_project(name="Test", url="https://example.com", pages=pages)

        content = (tmp_data_dir / manifest["id"] / "p1.md").read_text()
        assert content == "# Hello World\n"


class TestListProjects:
    def test_empty_initially(self, tmp_data_dir):
        assert list_projects() == []

    def test_lists_saved_projects(self, sample_project, tmp_data_dir):
        projects = list_projects()
        assert len(projects) == 1
        assert projects[0]["name"] == "Test Docs"

    def test_lists_multiple_projects(self, tmp_data_dir):
        pages = [{"id": "p1", "title": "T", "url": "https://example.com", "markdown": "# T\n"}]
        save_project(name="Project A", url="https://a.com", pages=pages)
        save_project(name="Project B", url="https://b.com", pages=pages)
        assert len(list_projects()) == 2


class TestGetProject:
    def test_returns_project(self, sample_project, tmp_data_dir):
        project = get_project("test123")
        assert project is not None
        assert project["name"] == "Test Docs"
        assert len(project["pages"]) == 2

    def test_returns_none_for_missing(self, tmp_data_dir):
        assert get_project("nonexistent") is None


class TestGetPage:
    def test_returns_content(self, sample_project, tmp_data_dir):
        content = get_page("test123", "page1")
        assert content is not None
        assert "Getting Started" in content

    def test_returns_none_for_missing(self, tmp_data_dir):
        assert get_page("test123", "missing") is None


class TestDeleteProject:
    def test_deletes_project(self, sample_project, tmp_data_dir):
        assert delete_project("test123") is True
        assert get_project("test123") is None

    def test_returns_false_for_missing(self, tmp_data_dir):
        assert delete_project("nonexistent") is False


class TestExportProject:
    def test_combines_pages(self, sample_project, tmp_data_dir):
        content = export_project("test123")
        assert content is not None
        assert "Getting Started" in content
        assert "API Guide" in content
        assert "---" in content  # separator

    def test_returns_none_for_missing(self, tmp_data_dir):
        assert export_project("nonexistent") is None
