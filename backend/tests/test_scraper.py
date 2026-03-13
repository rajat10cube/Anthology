"""Tests for the scraper service."""
import gzip
import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.scraper import (
    _normalize_url,
    _is_same_domain,
    _is_doc_link,
    _extract_links,
    _extract_content,
    _extract_content,
    _extract_title,
    _make_page_id,
    _parse_sitemap_xml,
    _discover_sitemap_urls,
    scrape_site_stream,
    scrape_site_stream_playwright,
    scrape_site_stream_playwright_parallel,
)


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


class TestParseSitemapXml:
    def test_standard_urlset(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/docs/page1</loc></url>
          <url><loc>https://example.com/docs/page2</loc></url>
        </urlset>"""
        pages, sitemaps = _parse_sitemap_xml(xml)
        assert pages == ["https://example.com/docs/page1", "https://example.com/docs/page2"]
        assert sitemaps == []

    def test_sitemap_index(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sitemap><loc>https://example.com/sitemap-docs.xml</loc></sitemap>
          <sitemap><loc>https://example.com/sitemap-blog.xml</loc></sitemap>
        </sitemapindex>"""
        pages, sitemaps = _parse_sitemap_xml(xml)
        assert pages == []
        assert sitemaps == ["https://example.com/sitemap-docs.xml", "https://example.com/sitemap-blog.xml"]

    def test_urlset_without_namespace(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset>
          <url><loc>https://example.com/docs/guide</loc></url>
        </urlset>"""
        pages, sitemaps = _parse_sitemap_xml(xml)
        assert pages == ["https://example.com/docs/guide"]

    def test_malformed_xml_returns_empty(self):
        pages, sitemaps = _parse_sitemap_xml("this is not xml <><>")
        assert pages == []
        assert sitemaps == []

    def test_strips_whitespace_from_urls(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>  https://example.com/docs/page1  </loc></url>
        </urlset>"""
        pages, _ = _parse_sitemap_xml(xml)
        assert pages == ["https://example.com/docs/page1"]


class TestDiscoverSitemapUrls:
    @pytest.mark.asyncio
    async def test_discovers_urls_from_standard_sitemap(self):
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/docs/page1</loc></url>
          <url><loc>https://example.com/docs/page2</loc></url>
        </urlset>"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = sitemap_xml

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        urls = await _discover_sitemap_urls("https://example.com/docs", mock_client)
        assert "https://example.com/docs/page1" in urls
        assert "https://example.com/docs/page2" in urls

    @pytest.mark.asyncio
    async def test_handles_sitemap_index(self):
        index_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sitemap><loc>https://example.com/sitemap-docs.xml</loc></sitemap>
        </sitemapindex>"""
        child_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/docs/deep-page</loc></url>
        </urlset>"""

        mock_index = MagicMock()
        mock_index.status_code = 200
        mock_index.text = index_xml

        mock_child = MagicMock()
        mock_child.status_code = 200
        mock_child.text = child_xml

        mock_client = AsyncMock()
        mock_client.get.side_effect = [mock_index, mock_child]

        urls = await _discover_sitemap_urls("https://example.com/docs", mock_client)
        assert "https://example.com/docs/deep-page" in urls

    @pytest.mark.asyncio
    async def test_handles_gzip_sitemap(self):
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/docs/compressed</loc></url>
        </urlset>"""
        compressed = gzip.compress(sitemap_xml.encode("utf-8"))

        index_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sitemap><loc>https://example.com/sitemap-docs.xml.gz</loc></sitemap>
        </sitemapindex>"""

        mock_index = MagicMock()
        mock_index.status_code = 200
        mock_index.text = index_xml

        mock_gz = MagicMock()
        mock_gz.status_code = 200
        mock_gz.content = compressed

        mock_client = AsyncMock()
        mock_client.get.side_effect = [mock_index, mock_gz]

        urls = await _discover_sitemap_urls("https://example.com/docs", mock_client)
        assert "https://example.com/docs/compressed" in urls

    @pytest.mark.asyncio
    async def test_returns_empty_on_404(self):
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        urls = await _discover_sitemap_urls("https://example.com/docs", mock_client)
        assert urls == []

    @pytest.mark.asyncio
    async def test_filters_non_doc_urls(self):
        """URLs outside the base path or with asset extensions should be filtered out."""
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/docs/page1</loc></url>
          <url><loc>https://example.com/blog/post1</loc></url>
          <url><loc>https://example.com/docs/image.png</loc></url>
        </urlset>"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = sitemap_xml

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        urls = await _discover_sitemap_urls("https://example.com/docs", mock_client)
        assert "https://example.com/docs/page1" in urls
        assert "https://example.com/blog/post1" not in urls
        assert "https://example.com/docs/image.png" not in urls

    @pytest.mark.asyncio
    async def test_deduplicates_urls(self):
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/docs/page1</loc></url>
          <url><loc>https://example.com/docs/page1</loc></url>
        </urlset>"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = sitemap_xml

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        urls = await _discover_sitemap_urls("https://example.com/docs", mock_client)
        assert urls.count("https://example.com/docs/page1") == 1


class TestSitemapStreamEvent:
    @pytest.mark.asyncio
    async def test_emits_sitemap_discovered_event(self):
        """The stream should yield a sitemap_discovered event when a sitemap is found."""
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://example.com/docs/from-sitemap</loc></url>
        </urlset>"""

        # Mock the httpx client for both sitemap and page fetching
        mock_sitemap_response = MagicMock()
        mock_sitemap_response.status_code = 200
        mock_sitemap_response.text = sitemap_xml

        mock_page_response = MagicMock()
        mock_page_response.status_code = 200
        mock_page_response.headers = {"content-type": "text/html"}
        mock_page_response.text = "<html><body><main><h1>Test</h1><p>Content</p></main></body></html>"
        mock_page_response.raise_for_status = MagicMock()

        call_count = 0
        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if "sitemap" in url:
                return mock_sitemap_response
            return mock_page_response

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.scraper._build_client", return_value=mock_client):
            events = []
            async for event in scrape_site_stream(
                "https://example.com/docs",
                max_pages=5,
                use_sitemap=True,
            ):
                events.append(event)

            sitemap_events = [e for e in events if e["type"] == "sitemap_discovered"]
            assert len(sitemap_events) == 1
            assert sitemap_events[0]["urls_found"] == 1

