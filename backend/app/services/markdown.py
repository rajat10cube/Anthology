"""HTML to Markdown conversion service."""
from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from markdownify import markdownify as md


def convert_to_markdown(
    html: str,
    title: str = "Untitled",
    source_url: str = "",
    base_url: str = "",
) -> str:
    """Convert HTML content to well-structured Markdown.

    Args:
        html: HTML string to convert.
        title: Page title for frontmatter.
        source_url: Original URL of the page.
        base_url: Base URL for resolving relative links.

    Returns:
        Markdown string with YAML frontmatter.
    """
    # Resolve relative URLs to absolute before conversion
    if source_url:
        html = _resolve_relative_urls(html, source_url)

    # Convert HTML to Markdown
    markdown = md(
        html,
        heading_style="ATX",
        code_language_callback=_detect_language,
        escape_underscores=False,
        escape_asterisks=False,
    )

    # Clean up excessive whitespace
    markdown = _clean_markdown(markdown)

    # Add frontmatter
    frontmatter = _build_frontmatter(title, source_url)

    return f"{frontmatter}\n{markdown}"


def _resolve_relative_urls(html: str, page_url: str) -> str:
    """Resolve relative src/href attributes in HTML to absolute URLs.

    This ensures images and links in the exported Markdown point to valid
    absolute URLs rather than broken relative paths.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Resolve image sources
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if not src.startswith(("data:", "mailto:")):
            img["src"] = urljoin(page_url, src)

    # Resolve link hrefs
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith(("data:", "mailto:", "javascript:", "#")):
            a["href"] = urljoin(page_url, href)

    # Resolve source elements (picture tags)
    for source in soup.find_all("source", srcset=True):
        source["srcset"] = urljoin(page_url, source["srcset"])

    return str(soup)


def _detect_language(el) -> str | None:
    """Try to detect the programming language from a code element's classes."""
    if el is None:
        return None

    classes = el.get("class", [])
    if isinstance(classes, str):
        classes = classes.split()

    for cls in classes:
        cls_lower = cls.lower()
        # Common patterns: "language-python", "lang-js", "highlight-javascript"
        for prefix in ("language-", "lang-", "highlight-"):
            if cls_lower.startswith(prefix):
                return cls_lower[len(prefix):]

    return None


def _clean_markdown(text: str) -> str:
    """Clean up common markdown conversion artifacts."""
    import re

    # Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove trailing whitespace on each line
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Ensure single trailing newline
    text = text.strip() + "\n"

    return text


def _build_frontmatter(title: str, source_url: str) -> str:
    """Build YAML frontmatter block."""
    scrape_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "---",
        f"title: \"{title}\"",
    ]
    if source_url:
        lines.append(f"source: \"{source_url}\"")
    lines.append(f"scraped_at: \"{scrape_date}\"")
    lines.append("---")
    return "\n".join(lines)
