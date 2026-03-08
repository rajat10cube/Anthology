"""Tests for the scraper service."""
import pytest
from bs4 import BeautifulSoup

from app.services.scraper import (
    _normalize_url,
    _is_same_domain,
    _is_doc_link,
    _extract_links,
    _extract_content,
    _extract_content,
    _extract_title,
    _make_page_id,
    scrape_site_stream_playwright,
    scrape_site_stream_playwright_parallel,
)
from unittest.mock import patch, AsyncMock, MagicMock


class TestNormalizeUrl:
    def test_removes_fragment(self):
        assert _normalize_url("https://example.com/docs#section") == "https://example.com/docs"

    def test_removes_trailing_slash(self):
        assert _normalize_url("https://example.com/docs/") == "https://example.com/docs"

    def test_keeps_root_slash(self):
        result = _normalize_url("https://example.com/")
        assert result == "https://example.com/"

    def test_no_change_for_clean_url(self):
        assert _normalize_url("https://example.com/docs") == "https://example.com/docs"


class TestIsSameDomain:
    def test_same_domain(self):
        assert _is_same_domain("https://example.com/page", "https://example.com/docs")

    def test_different_domain(self):
        assert not _is_same_domain("https://other.com/page", "https://example.com/docs")


class TestIsDocLink:
    def test_valid_doc_link(self):
        assert _is_doc_link("https://example.com/docs/guide", "https://example.com/docs")

    def test_rejects_image(self):
        assert not _is_doc_link("https://example.com/docs/logo.png", "https://example.com/docs")

    def test_rejects_css(self):
        assert not _is_doc_link("https://example.com/docs/style.css", "https://example.com/docs")

    def test_rejects_external(self):
        assert not _is_doc_link("https://other.com/docs/page", "https://example.com/docs")

    def test_rejects_different_section(self):
        assert not _is_doc_link("https://example.com/blog/post", "https://example.com/docs")


class TestExtractLinks:
    def test_extracts_internal_links(self, sample_html):
        soup = BeautifulSoup(sample_html, "html.parser")
        links = _extract_links(soup, "https://example.com/docs", "https://example.com/docs")
        assert "https://example.com/docs/guide" in links
        assert "https://example.com/docs/api" in links

    def test_ignores_external_links(self):
        html = '<html><body><a href="https://other.com">External</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = _extract_links(soup, "https://example.com/docs", "https://example.com/docs")
        assert len(links) == 0


class TestExtractContent:
    def test_finds_main_element(self, sample_html):
        soup = BeautifulSoup(sample_html, "html.parser")
        content = _extract_content(soup)
        assert content is not None
        assert "Getting Started" in content.get_text()

    def test_strips_nav(self, sample_html):
        soup = BeautifulSoup(sample_html, "html.parser")
        content = _extract_content(soup)
        text = content.get_text()
        # Nav should be stripped before content detection
        assert "Other" not in text or content.name == "main"

    def test_strips_footer(self, sample_html):
        soup = BeautifulSoup(sample_html, "html.parser")
        content = _extract_content(soup)
        text = content.get_text()
        assert "Copyright" not in text


class TestExtractTitle:
    def test_extracts_h1(self, sample_html):
        soup = BeautifulSoup(sample_html, "html.parser")
        title = _extract_title(soup)
        assert title == "Getting Started"

    def test_falls_back_to_title_tag(self):
        html = "<html><head><title>My Page - Docs</title></head><body></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        title = _extract_title(soup)
        assert title == "My Page"

    def test_untitled_fallback(self):
        html = "<html><body><p>No title here</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        title = _extract_title(soup)
        assert title == "Untitled"


class TestMakePageId:
    def test_deterministic(self):
        id1 = _make_page_id("https://example.com/docs")
        id2 = _make_page_id("https://example.com/docs")
        assert id1 == id2

    def test_different_urls_different_ids(self):
        id1 = _make_page_id("https://example.com/docs")
        id2 = _make_page_id("https://example.com/docs/api")
        assert id1 != id2


class TestPlaywrightScrapers:
    @pytest.mark.asyncio
    @patch("app.services.scraper._PLAYWRIGHT_AVAILABLE", False)
    async def test_fails_gracefully_when_not_installed(self):
        stream = scrape_site_stream_playwright("https://example.com/docs", 1)
        events = [e async for e in stream]
        assert len(events) == 1
        assert events[0]["type"] == "page_skipped"
        assert events[0]["reason"] == "playwright_not_installed"

        stream_parallel = scrape_site_stream_playwright_parallel("https://example.com/docs", 1)
        events_parallel = [e async for e in stream_parallel]
        assert len(events_parallel) == 1
        assert events_parallel[0]["type"] == "page_skipped"
        assert events_parallel[0]["reason"] == "playwright_not_installed"

    @pytest.mark.asyncio
    @patch("app.services.scraper._PLAYWRIGHT_AVAILABLE", True)
    @patch("app.services.scraper.async_playwright")
    async def test_successful_scrape_sequential(self, mock_pw, sample_html):
        mock_page = AsyncMock()
        mock_page.content.return_value = sample_html
        mock_page.goto.return_value.ok = True
        mock_page.goto.return_value.headers = {"content-type": "text/html"}

        mock_context = AsyncMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = AsyncMock()
        mock_browser.new_context.return_value = mock_context

        # Set up the context manager mock return values
        mock_pw_context = AsyncMock()
        mock_pw_context.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_pw.return_value = mock_pw_context

        stream = scrape_site_stream_playwright("https://example.com/docs", max_pages=1)
        events = [e async for e in stream]

        scraped = [e for e in events if e["type"] == "page_scraped"]
        assert len(scraped) == 1
        assert scraped[0]["page"]["title"] == "Getting Started"
        assert "Getting Started" in scraped[0]["page"]["html"]
        mock_page.goto.assert_called_with("https://example.com/docs", wait_until="networkidle", timeout=30000)

    @pytest.mark.asyncio
    @patch("app.services.scraper._PLAYWRIGHT_AVAILABLE", True)
    @patch("app.services.scraper.async_playwright")
    async def test_successful_scrape_parallel(self, mock_pw, sample_html):
        mock_page = AsyncMock()
        mock_page.content.return_value = sample_html
        mock_page.goto.return_value.ok = True
        mock_page.goto.return_value.headers = {"content-type": "text/html"}

        mock_context = AsyncMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = AsyncMock()
        mock_browser.new_context.return_value = mock_context

        mock_pw_context = AsyncMock()
        mock_pw_context.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_pw.return_value = mock_pw_context

        stream = scrape_site_stream_playwright_parallel(
            "https://example.com/docs", max_pages=1, concurrency=1
        )
        events = [e async for e in stream]

        scraped = [e for e in events if e["type"] == "page_scraped"]
        assert len(scraped) == 1
        assert scraped[0]["page"]["title"] == "Getting Started"
        mock_page.goto.assert_called_with("https://example.com/docs", wait_until="networkidle", timeout=30000)
