"""Scrape endpoint — triggers scraping and saves results."""
import json
from urllib.parse import urlparse

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.services.scraper import (
    scrape_site,
    scrape_site_stream,
    scrape_site_stream_parallel,
    scrape_site_stream_playwright,
    scrape_site_stream_playwright_parallel,
)
from app.services.markdown import convert_to_markdown
from app.storage import save_project

router = APIRouter()

# In-memory registry for tracking cancelled scrape streams
CANCELLED_JOBS: set[str] = set()


class ScrapeRequest(BaseModel):
    url: str
    name: str | None = None
    max_pages: int = 50
    max_depth: int = 3
    job_id: str | None = None
    parallel: bool = False
    concurrency: int = 8
    use_playwright: bool = False

class StopScrapeRequest(BaseModel):
    job_id: str


class ScrapeResponse(BaseModel):
    id: str
    name: str
    url: str
    page_count: int
    scraped_at: str


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_docs(request: ScrapeRequest):
    """Scrape a documentation website and save as markdown."""
    url = str(request.url)

    if request.name:
        name = request.name
    else:
        parsed = urlparse(url)
        name = parsed.netloc.replace("www.", "")

    try:
        raw_pages = await scrape_site(
            url=url,
            max_pages=request.max_pages,
            max_depth=request.max_depth,
            parallel=request.parallel,
            concurrency=request.concurrency,
            use_playwright=request.use_playwright,
        )

        if not raw_pages:
            raise HTTPException(
                status_code=400,
                detail="No pages could be scraped from the provided URL. "
                       "Check that the URL is accessible and contains documentation.",
            )

        pages = []
        for page in raw_pages:
            markdown = convert_to_markdown(
                html=page["html"],
                title=page["title"],
                source_url=page["url"],
                base_url=url,
            )
            pages.append({
                "id": page["id"],
                "title": page["title"],
                "url": page["url"],
                "markdown": markdown,
            })

        manifest = save_project(name=name, url=url, pages=pages)

        return ScrapeResponse(
            id=manifest["id"],
            name=manifest["name"],
            url=manifest["url"],
            page_count=manifest["page_count"],
            scraped_at=manifest["scraped_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}",
        )


@router.post("/scrape/stop")
async def stop_scrape(request: StopScrapeRequest):
    """Signal an ongoing scraping stream to stop."""
    CANCELLED_JOBS.add(request.job_id)
    return {"status": "stopping"}

@router.post("/scrape/stream")
async def scrape_docs_stream(request: ScrapeRequest):
    """Scrape with SSE progress events.

    Event types sent:
        - started:       {"url": ..., "name": ..., "max_pages": ...}
        - page_scraped:  {"title": ..., "url": ..., "scraped": N, "queued": M}
        - converting:    {"scraped": N}
        - complete:      {"id": ..., "name": ..., "page_count": ..., "scraped_at": ...}
        - error:         {"message": ...}
    """
    url = str(request.url)
    if request.name:
        name = request.name
    else:
        parsed = urlparse(url)
        name = parsed.netloc.replace("www.", "")

    async def event_generator():
        try:
            # Send start event
            yield _sse("started", {
                "url": url,
                "name": name,
                "max_pages": request.max_pages,
            })

            # Stream scraping progress
            raw_pages = []
            if request.use_playwright:
                stream = (
                    scrape_site_stream_playwright_parallel(
                        url=url,
                        max_pages=request.max_pages,
                        max_depth=request.max_depth,
                        concurrency=request.concurrency,
                    )
                    if request.parallel
                    else scrape_site_stream_playwright(
                        url=url,
                        max_pages=request.max_pages,
                        max_depth=request.max_depth,
                    )
                )
            else:
                stream = (
                    scrape_site_stream_parallel(
                        url=url,
                        max_pages=request.max_pages,
                        max_depth=request.max_depth,
                        concurrency=request.concurrency,
                    )
                    if request.parallel
                    else scrape_site_stream(
                        url=url,
                        max_pages=request.max_pages,
                        max_depth=request.max_depth,
                    )
                )
            async for event in stream:
                # Check for cancellation before processing event
                if request.job_id and request.job_id in CANCELLED_JOBS:
                    break

                if event["type"] == "page_scraped":
                    raw_pages.append(event["page"])
                    yield _sse("page_scraped", {
                        "title": event["page"]["title"],
                        "url": event["page"]["url"],
                        "scraped": event["scraped"],
                        "queued": event["queued"],
                    })

            if not raw_pages:
                yield _sse("error", {
                    "message": "No pages could be scraped from the provided URL.",
                })
                return

            # Send converting event
            yield _sse("converting", {"scraped": len(raw_pages)})

            # Convert to markdown
            pages = []
            for page in raw_pages:
                markdown = convert_to_markdown(
                    html=page["html"],
                    title=page["title"],
                    source_url=page["url"],
                    base_url=url,
                )
                pages.append({
                    "id": page["id"],
                    "title": page["title"],
                    "url": page["url"],
                    "markdown": markdown,
                })

            # Save project
            manifest = save_project(name=name, url=url, pages=pages)

            yield _sse("complete", {
                "id": manifest["id"],
                "name": manifest["name"],
                "url": manifest["url"],
                "page_count": manifest["page_count"],
                "scraped_at": manifest["scraped_at"],
            })

        except Exception as e:
            yield _sse("error", {"message": str(e)})
        finally:
            if request.job_id:
                CANCELLED_JOBS.discard(request.job_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(event: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
