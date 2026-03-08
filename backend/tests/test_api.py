"""Tests for API endpoints."""
import json
from unittest.mock import patch, AsyncMock
import pytest

from app import storage


class TestHealthEndpoint:
    def test_health_check(self, test_client):
        response = test_client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestProjectsEndpoints:
    def test_list_projects_empty(self, test_client, tmp_data_dir):
        response = test_client.get("/api/projects")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_projects_with_data(self, test_client, sample_project, tmp_data_dir):
        response = test_client.get("/api/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Docs"

    def test_get_project_detail(self, test_client, sample_project, tmp_data_dir):
        response = test_client.get("/api/projects/test123")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Docs"
        assert len(data["pages"]) == 2

    def test_get_project_not_found(self, test_client, tmp_data_dir):
        response = test_client.get("/api/projects/nonexistent")
        assert response.status_code == 404

    def test_get_page_content(self, test_client, sample_project, tmp_data_dir):
        response = test_client.get("/api/projects/test123/pages/page1")
        assert response.status_code == 200
        data = response.json()
        assert "Getting Started" in data["content"]

    def test_get_page_not_found(self, test_client, tmp_data_dir):
        response = test_client.get("/api/projects/test123/pages/missing")
        assert response.status_code == 404

    def test_export_project(self, test_client, sample_project, tmp_data_dir):
        response = test_client.get("/api/projects/test123/export")
        assert response.status_code == 200
        assert "Getting Started" in response.text
        assert "API Guide" in response.text
        assert "content-disposition" in response.headers

    def test_export_not_found(self, test_client, tmp_data_dir):
        response = test_client.get("/api/projects/nonexistent/export")
        assert response.status_code == 404

    def test_delete_project(self, test_client, sample_project, tmp_data_dir):
        response = test_client.delete("/api/projects/test123")
        assert response.status_code == 200
        # Verify it's gone
        response = test_client.get("/api/projects/test123")
        assert response.status_code == 404

    def test_delete_not_found(self, test_client, tmp_data_dir):
        response = test_client.delete("/api/projects/nonexistent")
        assert response.status_code == 404


class TestScrapeEndpoint:
    def test_scrape_with_mocked_scraper(self, test_client, tmp_data_dir):
        """Test POST /api/scrape with mocked scraper to avoid real HTTP calls."""
        mock_pages = [
            {
                "id": "abc123",
                "url": "https://example.com/docs",
                "title": "Example Docs",
                "html": "<h1>Hello</h1><p>World</p>",
            }
        ]

        with patch("app.routers.scrape.scrape_site", new_callable=AsyncMock, return_value=mock_pages):
            response = test_client.post("/api/scrape", json={
                "url": "https://example.com/docs",
                "name": "Example",
            })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Example"
        assert data["page_count"] == 1
        assert "id" in data

    def test_scrape_auto_names_from_url(self, test_client, tmp_data_dir):
        mock_pages = [
            {
                "id": "abc123",
                "url": "https://docs.example.com/getting-started",
                "title": "Getting Started",
                "html": "<h1>Hello</h1>",
            }
        ]

        with patch("app.routers.scrape.scrape_site", new_callable=AsyncMock, return_value=mock_pages):
            response = test_client.post("/api/scrape", json={
                "url": "https://docs.example.com/getting-started",
            })

        assert response.status_code == 200
        assert response.json()["name"] == "docs.example.com"

    def test_scrape_with_playwright_flag(self, test_client, tmp_data_dir):
        """Test POST /api/scrape correctly passes use_playwright flag."""
        with patch("app.routers.scrape.scrape_site", new_callable=AsyncMock, return_value=[{"id": "1", "url": "x", "title": "x", "html": "x"}]) as mock_scrape:
            response = test_client.post("/api/scrape", json={
                "url": "https://example.com",
                "use_playwright": True,
            })
            
        assert response.status_code == 200
        # Verify the kwarg was passed True
        mock_scrape.assert_called_once()
        _, kwargs = mock_scrape.call_args
        assert kwargs["use_playwright"] is True

    def test_scrape_no_pages_returns_400(self, test_client, tmp_data_dir):
        with patch("app.routers.scrape.scrape_site", new_callable=AsyncMock, return_value=[]):
            response = test_client.post("/api/scrape", json={
                "url": "https://example.com/empty",
            })

        assert response.status_code == 400

    def test_stop_scrape(self, test_client):
        response = test_client.post("/api/scrape/stop", json={"job_id": "test-id-123"})
        assert response.status_code == 200
        assert response.json() == {"status": "stopping"}
        
        from app.routers.scrape import CANCELLED_JOBS
        assert "test-id-123" in CANCELLED_JOBS
        
        # cleanup
        CANCELLED_JOBS.remove("test-id-123")
