"""Tests for the markdown conversion service."""
import pytest
from app.services.markdown import (
    convert_to_markdown,
    _clean_markdown,
    _build_frontmatter,
    _resolve_relative_urls,
)


class TestConvertToMarkdown:
    def test_basic_conversion(self):
        html = "<h1>Hello</h1><p>World</p>"
        result = convert_to_markdown(html, title="Test", source_url="https://example.com")
        assert "# Hello" in result
        assert "World" in result

    def test_includes_frontmatter(self):
        html = "<p>Content</p>"
        result = convert_to_markdown(html, title="My Page", source_url="https://example.com")
        assert "---" in result
        assert 'title: "My Page"' in result
        assert 'source: "https://example.com"' in result
        assert "scraped_at:" in result

    def test_code_blocks(self):
        html = '<pre><code class="language-python">print("hello")</code></pre>'
        result = convert_to_markdown(html, title="Test")
        assert "```python" in result or "```" in result
        assert 'print("hello")' in result

    def test_headings(self):
        html = "<h1>Title</h1><h2>Subtitle</h2><h3>Section</h3>"
        result = convert_to_markdown(html, title="Test")
        assert "# Title" in result
        assert "## Subtitle" in result
        assert "### Section" in result

    def test_lists(self):
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = convert_to_markdown(html, title="Test")
        assert "Item 1" in result
        assert "Item 2" in result

    def test_empty_html(self):
        result = convert_to_markdown("", title="Empty")
        assert 'title: "Empty"' in result

    def test_resolves_relative_image_urls(self):
        html = '<img src="../assets/image.png" alt="screenshot">'
        result = convert_to_markdown(
            html,
            title="Test",
            source_url="https://docs.example.com/starter/page.html",
        )
        assert "https://docs.example.com/assets/image.png" in result
        assert "../assets/image.png" not in result

    def test_preserves_absolute_image_urls(self):
        html = '<img src="https://cdn.example.com/image.png" alt="screenshot">'
        result = convert_to_markdown(
            html,
            title="Test",
            source_url="https://docs.example.com/page.html",
        )
        assert "https://cdn.example.com/image.png" in result


class TestResolveRelativeUrls:
    def test_resolves_relative_image_src(self):
        html = '<img src="../assets/image.png" alt="test">'
        result = _resolve_relative_urls(html, "https://docs.example.com/starter/page.html")
        assert "https://docs.example.com/assets/image.png" in result

    def test_resolves_root_relative_image_src(self):
        html = '<img src="/assets/logo.png" alt="logo">'
        result = _resolve_relative_urls(html, "https://docs.example.com/starter/page.html")
        assert "https://docs.example.com/assets/logo.png" in result

    def test_preserves_absolute_image_src(self):
        html = '<img src="https://cdn.example.com/image.png" alt="test">'
        result = _resolve_relative_urls(html, "https://docs.example.com/page.html")
        assert "https://cdn.example.com/image.png" in result

    def test_preserves_data_uri(self):
        html = '<img src="data:image/svg+xml;base64,PHN2Zz4=" alt="icon">'
        result = _resolve_relative_urls(html, "https://docs.example.com/page.html")
        assert "data:image/svg+xml;base64,PHN2Zz4=" in result

    def test_resolves_link_href(self):
        html = '<a href="../guide.html">Guide</a>'
        result = _resolve_relative_urls(html, "https://docs.example.com/starter/page.html")
        assert "https://docs.example.com/guide.html" in result

    def test_preserves_anchor_links(self):
        html = '<a href="#section">Section</a>'
        result = _resolve_relative_urls(html, "https://docs.example.com/page.html")
        assert '#section' in result

    def test_preserves_javascript_links(self):
        html = '<a href="javascript:void(0)">Click</a>'
        result = _resolve_relative_urls(html, "https://docs.example.com/page.html")
        assert "javascript:void(0)" in result

    def test_resolves_multiple_elements(self):
        html = '''
        <img src="../img1.png" alt="one">
        <a href="other.html">Link</a>
        <img src="../../img2.png" alt="two">
        '''
        result = _resolve_relative_urls(html, "https://docs.example.com/a/b/page.html")
        assert "https://docs.example.com/a/img1.png" in result
        assert "https://docs.example.com/a/b/other.html" in result
        assert "https://docs.example.com/img2.png" in result


class TestCleanMarkdown:
    def test_collapses_newlines(self):
        text = "Line 1\n\n\n\n\nLine 2"
        result = _clean_markdown(text)
        assert "\n\n\n" not in result
        assert "Line 1\n\nLine 2" in result

    def test_strips_trailing_whitespace(self):
        text = "Hello   \nWorld  "
        result = _clean_markdown(text)
        lines = result.split("\n")
        assert lines[0] == "Hello"
        assert lines[1] == "World"


class TestBuildFrontmatter:
    def test_includes_title(self):
        result = _build_frontmatter("My Title", "https://example.com")
        assert '---' in result
        assert 'title: "My Title"' in result

    def test_includes_source_url(self):
        result = _build_frontmatter("Title", "https://example.com/docs")
        assert 'source: "https://example.com/docs"' in result

    def test_no_source_when_empty(self):
        result = _build_frontmatter("Title", "")
        assert "source:" not in result

    def test_includes_date(self):
        result = _build_frontmatter("Title", "")
        assert "scraped_at:" in result
