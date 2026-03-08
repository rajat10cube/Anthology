"""Tests for the scraper service."""
import pytest
from bs4 import BeautifulSoup

from app.services.scraper import (
    _normalize_url,
    _is_same_domain,
    _is_doc_link,
    _extract_links,
    _extract_content,
    _extract_title,
    _make_page_id,
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
