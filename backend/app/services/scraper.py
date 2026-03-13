"""Web scraper service — crawls documentation sites and extracts content."""
import asyncio
import gzip
import hashlib
import re
import xml.etree.ElementTree as ET
from io import BytesIO
from urllib.parse import urljoin, urlparse, urldefrag
from typing import Any, AsyncIterator

import httpx
from bs4 import BeautifulSoup, Tag

try:
    from playwright.async_api import async_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False


# Elements to remove before extracting content
STRIP_TAGS = [
    # HTML elements
    "nav", "footer", "header", "aside", "script", "style", "noscript",
    "svg", "iframe", "form",
    # Layout / navigation classes
    ".sidebar", ".nav", ".footer", ".header",
    ".menu", ".toc", ".table-of-contents", ".breadcrumb", ".breadcrumbs",
    ".pagination",
    # ARIA roles
    "[role='navigation']", "[role='banner']", "[role='contentinfo']",
    # Modals & overlays
    ".modal", ".popup", "#modal", ".overlay",
    # Ads
    ".ad", ".ads", ".advert", "#ad",
    # Cookie / consent banners
    ".cookie", "#cookie", ".cookie-banner", ".consent",
    # Language selectors
    ".lang-selector", ".language", "#language-selector",
    # Social & share widgets
    ".social", ".social-media", ".social-links", "#social",
    ".share", "#share",
    # Generic widgets
    ".widget", "#widget",
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


# ── Sitemap discovery ──────────────────────────────────────────────────

_SITEMAP_NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
}


def _parse_sitemap_xml(content: str) -> tuple[list[str], list[str]]:
    """Parse sitemap XML and return (page_urls, child_sitemap_urls)."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return [], []

    page_urls: list[str] = []
    sitemap_urls: list[str] = []

    # Strip namespace for easier matching
    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag

    if tag == "urlset":
        # Standard sitemap: <urlset> → <url> → <loc>
        for url_el in root.findall("sm:url/sm:loc", _SITEMAP_NS):
            if url_el.text:
                page_urls.append(url_el.text.strip())
        # Fallback: try without namespace
        if not page_urls:
            for url_el in root.iter():
                ltag = url_el.tag.split("}")[-1] if "}" in url_el.tag else url_el.tag
                if ltag == "loc" and url_el.text:
                    page_urls.append(url_el.text.strip())

    elif tag == "sitemapindex":
        # Sitemap index: <sitemapindex> → <sitemap> → <loc>
        for loc_el in root.findall("sm:sitemap/sm:loc", _SITEMAP_NS):
            if loc_el.text:
                sitemap_urls.append(loc_el.text.strip())
        # Fallback: try without namespace
        if not sitemap_urls:
            for el in root.iter():
                ltag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
                if ltag == "loc" and el.text:
                    sitemap_urls.append(el.text.strip())

    return page_urls, sitemap_urls


async def _discover_sitemap_urls(
    base_url: str,
    client: httpx.AsyncClient,
    max_sitemaps: int = 20,
) -> list[str]:
    """Discover page URLs from sitemap.xml.

    Handles standard sitemaps, sitemap index files, and gzip-compressed
    sitemaps.  Returns an empty list when the sitemap is unavailable or
    unparseable — the caller should fall back to regular BFS discovery.
    """
    parsed = urlparse(base_url)
    sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"

    all_urls: list[str] = []
    pending = [sitemap_url]
    visited_sitemaps: set[str] = set()

    while pending and len(visited_sitemaps) < max_sitemaps:
        url = pending.pop(0)
        if url in visited_sitemaps:
            continue
        visited_sitemaps.add(url)

        try:
            resp = await client.get(url, timeout=15.0)
            if resp.status_code != 200:
                continue

            # Handle gzip-compressed sitemaps
            if url.lower().endswith(".gz"):
                try:
                    content = gzip.decompress(resp.content).decode("utf-8")
                except Exception:
                    continue
            else:
                content = resp.text

            page_urls, child_sitemaps = _parse_sitemap_xml(content)
            all_urls.extend(page_urls)
            pending.extend(child_sitemaps)

        except (httpx.HTTPError, Exception):
            continue

    # Filter through _is_doc_link so only relevant doc pages are kept
    return [u for u in dict.fromkeys(all_urls) if _is_doc_link(u, base_url)]


async def scrape_site(
    url: str,
    max_pages: int = 50,
    max_depth: int = 3,
    parallel: bool = False,
    concurrency: int = 8,
    use_playwright: bool = False,
    use_sitemap: bool = True,
) -> list[dict[str, Any]]:
    """Scrape a documentation site.

    Args:
        url: Root documentation URL to start from.
        max_pages: Maximum number of pages to scrape.
        max_depth: Maximum link depth from root.
        parallel: If True, use concurrent fetching.
        concurrency: Max simultaneous requests in parallel mode.
        use_playwright: If True, use headless Chromium instead of httpx.
        use_sitemap: If True, discover URLs from sitemap.xml first.

    Returns:
        List of dicts with keys: id, url, title, html.
    """
    results: list[dict[str, Any]] = []
    if use_playwright:
        stream = (
            scrape_site_stream_playwright_parallel(url, max_pages, max_depth, concurrency, use_sitemap=use_sitemap)
            if parallel
            else scrape_site_stream_playwright(url, max_pages, max_depth, use_sitemap=use_sitemap)
        )
    else:
        stream = (
            scrape_site_stream_parallel(url, max_pages, max_depth, concurrency, use_sitemap=use_sitemap)
            if parallel
            else scrape_site_stream(url, max_pages, max_depth, use_sitemap=use_sitemap)
        )
    async for event in stream:
        if event["type"] == "page_scraped":
            results.append(event["page"])
    return results


async def scrape_site_stream(
    url: str,
    max_pages: int = 50,
    max_depth: int = 3,
    use_sitemap: bool = True,
) -> AsyncIterator[dict[str, Any]]:
    """Scrape a documentation site via sequential BFS crawl, yielding progress events.

    Yields dicts with a "type" key:
        - {"type": "sitemap_discovered", "urls_found": N}
        - {"type": "page_scraped", "page": {...}, "scraped": N, "queued": M}
        - {"type": "page_skipped", "url": ..., "reason": ...}
    """
    base_url = _normalize_url(url)
    visited: set[str] = set()
    scraped_count = 0

    # BFS queue: (url, depth)
    queue: list[tuple[str, int]] = [(base_url, 0)]

    async with _build_client() as client:
        # Seed queue from sitemap if enabled
        if use_sitemap:
            sitemap_urls = await _discover_sitemap_urls(base_url, client)
            if sitemap_urls:
                for surl in sitemap_urls:
                    norm = _normalize_url(surl)
                    if norm not in visited and norm != base_url:
                        queue.append((norm, 0))
                yield {"type": "sitemap_discovered", "urls_found": len(sitemap_urls)}

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
    use_sitemap: bool = True,
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

    # Discover sitemap URLs if enabled
    sitemap_seed_urls: list[str] = []
    if use_sitemap:
        async with _build_client() as sitemap_client:
            sitemap_urls = await _discover_sitemap_urls(base_url, sitemap_client)
        if sitemap_urls:
            for surl in sitemap_urls:
                norm = _normalize_url(surl)
                if norm != base_url:
                    visited.add(norm)
                    sitemap_seed_urls.append(norm)
            yield {"type": "sitemap_discovered", "urls_found": len(sitemap_urls)}

    # Seed with root URL + sitemap-discovered URLs
    visited.add(base_url)
    new_tasks: list[asyncio.Task] = []
    seed_urls = [base_url] + sitemap_seed_urls
    all_tasks: list[asyncio.Task] = [
        asyncio.create_task(fetch_page(u, 0)) for u in seed_urls
    ]

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


async def scrape_site_stream_playwright(
    url: str,
    max_pages: int = 50,
    max_depth: int = 3,
    use_sitemap: bool = True,
) -> AsyncIterator[dict[str, Any]]:
    """Scrape via sequential BFS using a headless Playwright browser.

    Falls back to an error event if Playwright is not installed.
    Yields the same event shapes as scrape_site_stream.
    """
    if not _PLAYWRIGHT_AVAILABLE:
        yield {
            "type": "page_skipped",
            "url": url,
            "reason": "playwright_not_installed",
        }
        return

    base_url = _normalize_url(url)
    visited: set[str] = set()
    scraped_count = 0
    queue: list[tuple[str, int]] = [(base_url, 0)]

    # Seed queue from sitemap if enabled
    if use_sitemap:
        async with _build_client() as client:
            sitemap_urls = await _discover_sitemap_urls(base_url, client)
        if sitemap_urls:
            for surl in sitemap_urls:
                norm = _normalize_url(surl)
                if norm not in visited and norm != base_url:
                    queue.append((norm, 0))
            yield {"type": "sitemap_discovered", "urls_found": len(sitemap_urls)}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Anthology/1.0 (Documentation Scraper)",
        )
        page = await context.new_page()

        try:
            while queue and scraped_count < max_pages:
                current_url, depth = queue.pop(0)

                if current_url in visited:
                    continue
                visited.add(current_url)

                try:
                    response = await page.goto(current_url, wait_until="networkidle", timeout=30_000)

                    if response is None or not response.ok:
                        yield {"type": "page_skipped", "url": current_url, "reason": "error"}
                        continue

                    content_type = response.headers.get("content-type", "")
                    if "text/html" not in content_type:
                        yield {"type": "page_skipped", "url": current_url, "reason": "not_html"}
                        continue

                    html = await page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    title = _extract_title(soup)
                    content = _extract_content(soup)

                    if content:
                        scraped_count += 1
                        yield {
                            "type": "page_scraped",
                            "page": {
                                "id": _make_page_id(current_url),
                                "url": current_url,
                                "title": title,
                                "html": str(content),
                            },
                            "scraped": scraped_count,
                            "queued": len(queue),
                        }

                    if depth < max_depth:
                        new_links = _extract_links(soup, current_url, base_url)
                        for link in new_links:
                            if link not in visited:
                                queue.append((link, depth + 1))

                except Exception:
                    yield {"type": "page_skipped", "url": current_url, "reason": "error"}
                    continue
        finally:
            await browser.close()


async def scrape_site_stream_playwright_parallel(
    url: str,
    max_pages: int = 50,
    max_depth: int = 3,
    concurrency: int = 4,
    use_sitemap: bool = True,
) -> AsyncIterator[dict[str, Any]]:
    """Scrape via parallel BFS using a headless Playwright browser.

    Uses a shared browser context with a semaphore to cap concurrent pages.
    Falls back to an error event if Playwright is not installed.
    Yields the same event shapes as scrape_site_stream.
    """
    if not _PLAYWRIGHT_AVAILABLE:
        yield {
            "type": "page_skipped",
            "url": url,
            "reason": "playwright_not_installed",
        }
        return

    base_url = _normalize_url(url)
    visited: set[str] = set()
    state = {"scraped": 0}
    sem = asyncio.Semaphore(concurrency)
    event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Anthology/1.0 (Documentation Scraper)",
        )

        new_tasks: list[asyncio.Task] = []

        async def fetch_page(page_url: str, depth: int) -> None:
            async with sem:
                page = await context.new_page()
                try:
                    response = await page.goto(page_url, wait_until="networkidle", timeout=30_000)

                    if response is None or not response.ok:
                        await event_queue.put({"type": "page_skipped", "url": page_url, "reason": "error"})
                        return

                    content_type = response.headers.get("content-type", "")
                    if "text/html" not in content_type:
                        await event_queue.put({"type": "page_skipped", "url": page_url, "reason": "not_html"})
                        return

                    html = await page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    title = _extract_title(soup)
                    content = _extract_content(soup)

                    if content and state["scraped"] < max_pages:
                        state["scraped"] += 1
                        await event_queue.put({
                            "type": "page_scraped",
                            "page": {
                                "id": _make_page_id(page_url),
                                "url": page_url,
                                "title": title,
                                "html": str(content),
                            },
                            "scraped": state["scraped"],
                            "queued": 0,
                        })

                    if depth < max_depth and state["scraped"] < max_pages:
                        new_links = _extract_links(soup, page_url, base_url)
                        for link in new_links:
                            if link not in visited:
                                visited.add(link)
                                new_tasks.append(asyncio.create_task(fetch_page(link, depth + 1)))

                except Exception:
                    await event_queue.put({"type": "page_skipped", "url": page_url, "reason": "error"})
                finally:
                    await page.close()

        # Discover sitemap URLs if enabled
        sitemap_seed_urls: list[str] = []
        if use_sitemap:
            async with _build_client() as sitemap_client:
                sitemap_urls = await _discover_sitemap_urls(base_url, sitemap_client)
            if sitemap_urls:
                for surl in sitemap_urls:
                    norm = _normalize_url(surl)
                    if norm != base_url:
                        visited.add(norm)
                        sitemap_seed_urls.append(norm)
                yield {"type": "sitemap_discovered", "urls_found": len(sitemap_urls)}

        # Seed with root URL + sitemap-discovered URLs
        visited.add(base_url)
        seed_urls = [base_url] + sitemap_seed_urls
        all_tasks: list[asyncio.Task] = [
            asyncio.create_task(fetch_page(u, 0)) for u in seed_urls
        ]

        try:
            while all_tasks:
                all_tasks.extend(new_tasks)
                new_tasks.clear()

                if state["scraped"] >= max_pages:
                    for task in all_tasks:
                        task.cancel()
                    await asyncio.gather(*all_tasks, return_exceptions=True)
                    break

                done, pending_set = await asyncio.wait(all_tasks, return_when=asyncio.FIRST_COMPLETED)
                all_tasks = list(pending_set)

                all_tasks.extend(new_tasks)
                new_tasks.clear()

                while not event_queue.empty():
                    yield await event_queue.get()
        finally:
            await browser.close()

        while not event_queue.empty():
            yield await event_queue.get()

