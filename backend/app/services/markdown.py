"""HTML to Markdown conversion service."""
from datetime import datetime, timezone
from urllib.parse import urljoin

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
