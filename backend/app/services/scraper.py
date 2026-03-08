"""Web scraper service — crawls documentation sites and extracts content."""
import asyncio
import hashlib
import re
from urllib.parse import urljoin, urlparse, urldefrag
from typing import Any, AsyncIterator

import httpx
from bs4 import BeautifulSoup, Tag


# Elements to remove before extracting content
STRIP_TAGS = [
    "nav", "footer", "header", "aside", "script", "style", "noscript",
    "svg", "iframe", "form", ".sidebar", ".nav", ".footer", ".header",
    ".menu", ".toc", ".table-of-contents", ".breadcrumb", ".pagination",
    "[role='navigation']", "[role='banner']", "[role='contentinfo']",
]

# Selectors to find main content area, tried in order
CONTENT_SELECTORS = [
    "main",
    "article",
    "[role='main']",
    ".main-content",
    ".content",
    ".markdown-body",
    ".documentation",
    ".docs-content",
    "#content",
    "#main-content",
    "#docs",
]


def _normalize_url(url: str) -> str:
    """Normalize a URL by removing fragment and trailing slash."""
    url, _ = urldefrag(url)
    if url.endswith("/") and len(urlparse(url).path) > 1:
        url = url.rstrip("/")
    return url


def _is_same_domain(url: str, base_url: str) -> bool:
    """Check if a URL belongs to the same domain as the base URL."""
    return urlparse(url).netloc == urlparse(base_url).netloc


def _is_doc_link(url: str, base_url: str) -> bool:
    """Check if a URL is likely a documentation page (not an asset)."""
    parsed = urlparse(url)
    path = parsed.path.lower()

    # Skip common non-doc extensions
    skip_extensions = {
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
        ".css", ".js", ".json", ".xml", ".zip", ".tar", ".gz",
        ".pdf", ".mp4", ".mp3", ".woff", ".woff2", ".ttf", ".eot",
    }
    for ext in skip_extensions:
        if path.endswith(ext):
            return False

    # Must be same domain
    if not _is_same_domain(url, base_url):
        return False

    # Must share the same path prefix (stay within the docs section)
    base_path = urlparse(base_url).path
    if base_path and not path.startswith(base_path.rstrip("/")):
        return False

    return True


def _extract_links(soup: BeautifulSoup, current_url: str, base_url: str) -> list[str]:
    """Extract internal documentation links from a page."""
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        absolute = _normalize_url(urljoin(current_url, href))
        if _is_doc_link(absolute, base_url):
            links.append(absolute)
    return links


def _extract_content(soup: BeautifulSoup) -> Tag | None:
    """Extract the main content area from a page."""
    # Remove unwanted elements first
    for selector in STRIP_TAGS:
        for el in soup.select(selector):
            el.decompose()

    # Try content selectors in order
    for selector in CONTENT_SELECTORS:
        content = soup.select_one(selector)
        if content:
            return content

    # Fallback to body
    return soup.find("body")


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract the page title."""
    # Try h1 first
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    # Try title tag
    title = soup.find("title")
    if title:
        text = title.get_text(strip=True)
        # Strip common suffixes like " | Docs" or " - Documentation"
        text = re.split(r"\s*[|\-–—]\s*", text)[0].strip()
        return text

    return "Untitled"


def _make_page_id(url: str) -> str:
    """Create a short stable ID from a URL."""
    return hashlib.md5(url.encode()).hexdigest()[:10]


def _build_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        follow_redirects=True,
        timeout=30.0,
        headers={
            "User-Agent": "Anthology/1.0 (Documentation Scraper)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )


async def scrape_site(
    url: str,
    max_pages: int = 50,
    max_depth: int = 3,
    parallel: bool = False,
    concurrency: int = 8,
) -> list[dict[str, Any]]:
    """Scrape a documentation site.

    Args:
        url: Root documentation URL to start from.
        max_pages: Maximum number of pages to scrape.
        max_depth: Maximum link depth from root.
        parallel: If True, use concurrent fetching.
        concurrency: Max simultaneous requests in parallel mode.

    Returns:
        List of dicts with keys: id, url, title, html.
    """
    results: list[dict[str, Any]] = []
    stream = (
        scrape_site_stream_parallel(url, max_pages, max_depth, concurrency)
        if parallel
        else scrape_site_stream(url, max_pages, max_depth)
    )
    async for event in stream:
        if event["type"] == "page_scraped":
            results.append(event["page"])
    return results


async def scrape_site_stream(
    url: str,
    max_pages: int = 50,
    max_depth: int = 3,
) -> AsyncIterator[dict[str, Any]]:
    """Scrape a documentation site via sequential BFS crawl, yielding progress events.

    Yields dicts with a "type" key:
        - {"type": "page_scraped", "page": {...}, "scraped": N, "queued": M}
        - {"type": "page_skipped", "url": ..., "reason": ...}
    """
    base_url = _normalize_url(url)
    visited: set[str] = set()
    scraped_count = 0

    # BFS queue: (url, depth)
    queue: list[tuple[str, int]] = [(base_url, 0)]

    async with _build_client() as client:
        while queue and scraped_count < max_pages:
            current_url, depth = queue.pop(0)

            if current_url in visited:
                continue
            visited.add(current_url)

            try:
                response = await client.get(current_url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    yield {
                        "type": "page_skipped",
                        "url": current_url,
                        "reason": "not_html",
                    }
                    continue

                html = response.text
                soup = BeautifulSoup(html, "html.parser")

                title = _extract_title(soup)
                content = _extract_content(soup)

                if content:
                    page = {
                        "id": _make_page_id(current_url),
                        "url": current_url,
                        "title": title,
                        "html": str(content),
                    }
                    scraped_count += 1
                    yield {
                        "type": "page_scraped",
                        "page": page,
                        "scraped": scraped_count,
                        "queued": len(queue),
                    }

                # Discover more links if within depth limit
                if depth < max_depth:
                    new_links = _extract_links(soup, current_url, base_url)
                    for link in new_links:
                        if link not in visited:
                            queue.append((link, depth + 1))

            except (httpx.HTTPError, Exception):
                yield {
                    "type": "page_skipped",
                    "url": current_url,
                    "reason": "error",
                }
                continue


async def scrape_site_stream_parallel(
    url: str,
    max_pages: int = 50,
    max_depth: int = 3,
    concurrency: int = 8,
) -> AsyncIterator[dict[str, Any]]:
    """Scrape a documentation site with concurrent fetching, yielding progress events.

    Uses asyncio.Semaphore to limit simultaneous HTTP requests to `concurrency`.
    Pages are fetched in parallel; events are yielded as each completes.

    Yields the same event shapes as scrape_site_stream.
    """
    base_url = _normalize_url(url)
    visited: set[str] = set()
    # Use a mutable container so nested coroutines can update shared state
    state = {"scraped": 0}
    sem = asyncio.Semaphore(concurrency)
    event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def fetch_page(page_url: str, depth: int) -> None:
        async with sem:
            try:
                async with _build_client() as client:
                    response = await client.get(page_url)
                    response.raise_for_status()

                    content_type = response.headers.get("content-type", "")
                    if "text/html" not in content_type:
                        await event_queue.put({
                            "type": "page_skipped",
                            "url": page_url,
                            "reason": "not_html",
                        })
                        return

                    html = response.text
                    soup = BeautifulSoup(html, "html.parser")
                    title = _extract_title(soup)
                    content = _extract_content(soup)

                    if content and state["scraped"] < max_pages:
                        state["scraped"] += 1
                        page = {
                            "id": _make_page_id(page_url),
                            "url": page_url,
                            "title": title,
                            "html": str(content),
                        }
                        await event_queue.put({
                            "type": "page_scraped",
                            "page": page,
                            "scraped": state["scraped"],
                            "queued": 0,
                        })

                    # Enqueue newly discovered links
                    if depth < max_depth and state["scraped"] < max_pages:
                        new_links = _extract_links(soup, page_url, base_url)
                        for link in new_links:
                            if link not in visited:
                                visited.add(link)
                                new_tasks.append(
                                    asyncio.create_task(fetch_page(link, depth + 1))
                                )

            except (httpx.HTTPError, Exception):
                await event_queue.put({
                    "type": "page_skipped",
                    "url": page_url,
                    "reason": "error",
                })

    # Seed with root URL
    visited.add(base_url)
    new_tasks: list[asyncio.Task] = []
    root_task = asyncio.create_task(fetch_page(base_url, 0))
    all_tasks: list[asyncio.Task] = [root_task]

    # Drain events as tasks complete
    while all_tasks:
        # Collect any newly created tasks
        all_tasks.extend(new_tasks)
        new_tasks.clear()

        # As soon as we've hit the page limit, cancel everything still running
        if state["scraped"] >= max_pages:
            for task in all_tasks:
                task.cancel()
            await asyncio.gather(*all_tasks, return_exceptions=True)
            break

        # Wait for at least one task to finish
        done, pending_set = await asyncio.wait(
            all_tasks, return_when=asyncio.FIRST_COMPLETED
        )
        all_tasks = list(pending_set)

        # Collect any newly created tasks spawned by completed tasks
        all_tasks.extend(new_tasks)
        new_tasks.clear()

        # Drain all queued events
        while not event_queue.empty():
            yield await event_queue.get()

    # Final drain (any stragglers)
    while not event_queue.empty():
        yield await event_queue.get()

