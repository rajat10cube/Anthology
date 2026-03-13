import asyncio
import logging
import json
import tempfile
import os
import sys
from typing import Any
from urllib.parse import urlparse

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
)

from app.storage import list_projects, export_project, save_project, get_project, get_page
from app.services.scraper import scrape_site
from app.services.markdown import convert_to_markdown

# Configure basic logging level for the server
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("anthology.mcp")


app = Server("anthology")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List scraped markdown documents as MCP resources."""
    projects = list_projects()
    return [
        Resource(
            uri=f"anthology://{proj['id']}/docs.md",
            name=f"{proj['name']} Documentation",
            description=f"Scraped markdown for {proj['url']}",
            mimeType="text/markdown",
        )
        for proj in projects
    ]


@app.read_resource()
async def read_resource(uri: str) -> str | bytes:
    """Read a specific scraped markdown document."""
    if not uri.startswith("anthology://") or not uri.endswith("/docs.md"):
        raise ValueError(f"Unknown resource URI: {uri}")

    # Extract the ID: anthology://<project_id>/docs.md
    project_id = uri.split("anthology://")[1].split("/docs.md")[0]
    content = export_project(project_id)

    if not content:
        raise ValueError(f"Project not found: {project_id}")

    return content


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for interacting with Anthology."""
    return [
        Tool(
            name="list_scraped_docs",
            description="Returns a list of all documentation projects that have been scraped and saved in Anthology.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="read_scraped_docs",
            description=(
                "Fetches the full markdown content of a scraped project based on its ID. "
                "The server will write the multi-file JSON output directly to a temporary text "
                "file on the host system and return the absolute file path to you. "
                "ALWAYS prioritize using `jq` to read and parse the returned file path."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "The ID of the project to retrieve."},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="scrape_new_docs",
            description=(
                "Triggers a new Anthology web scraping job to fetch and convert documentation to markdown. "
                "The scraper crawls links within the same domain/path asynchronously and saves the output. "
                "Returns the new project ID which you can then read using read_scraped_docs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL of the documentation site to scrape (e.g. https://docs.example.com)"},
                    "max_pages": {
                        "type": "integer",
                        "description": "Maximum number of pages to scrape. Default is 50, maximum is generally 500.",
                        "default": 50,
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum link depth to traverse from the root URL. Default is 3.",
                        "default": 3,
                    },
                    "use_playwright": {
                        "type": "boolean",
                        "description": "If true, uses a headless Chromium browser to render JS-heavy Single Page Apps. If false, uses fast HTTP. Use true ONLY if the site is known to require JS to render content.",
                        "default": False,
                    },
                },
                "required": ["url"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute tools requested by the client."""
    if name == "list_scraped_docs":
        projects = list_projects()
        output = "Scraped Projects in Anthology:\n\n"
        if not projects:
            output += "(No projects currently saved.)\n"
        else:
            for p in projects:
                output += f"- ID: {p['id']}\n  Name: {p['name']}\n  URL: {p['url']}\n  Pages: {p.get('page_count', 'unknown')}\n\n"
        return [TextContent(type="text", text=output)]

    elif name == "read_scraped_docs":
        project_id = arguments.get("project_id")
        if not project_id:
            raise ValueError("project_id is required")

        manifest = get_project(project_id)
        if not manifest:
            raise ValueError(f"Project '{project_id}' not found.")

        contents = []
        for page in manifest.get("pages", []):
            page_content = get_page(project_id, page["id"])
            if page_content:
                # Store the file data in a dictionary mimicking the TextContent schema
                header = f"File: {page['id']}.md\nSource: {page['url']}\n\n"
                contents.append({"type": "text", "text": header + page_content})

        if not contents:
             raise ValueError(f"Project '{project_id}' has no pages.")

        # Cache directory: use ~/.anthology/cache/ for pip installs,
        # or backend/.anthology_cache/ when running from source
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if os.path.basename(base_dir) == "backend" and os.path.exists(os.path.join(base_dir, "requirements.txt")):
            cache_dir = os.path.join(base_dir, ".anthology_cache")
        else:
            cache_dir = os.path.join(os.path.expanduser("~"), ".anthology", "cache")
        os.makedirs(cache_dir, exist_ok=True)

        # Determine a human-readable filename based on snippet url
        target_url = manifest.get("url", "")
        # Remove everything except domain if possible to make cleaner filenames
        safe_domain = urlparse(target_url).netloc if target_url else project_id
        safe_domain = safe_domain.replace(":", "_") if safe_domain else "docs"
        
        # Write the JSON array to a local temp file payload
        temp_path = os.path.join(cache_dir, f"{safe_domain}_{project_id}.json")
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(contents, f)

        msg = (
            f"Successfully fetched {len(contents)} pages for project '{project_id}'.\n"
            f"To prevent context window overflow, the full JSON array has been written to:\n"
            f"{temp_path}\n\n"
            f"Please use standard CLI tools (like `jq`) to query this absolute file path directly."
        )
        return [TextContent(type="text", text=msg)]

    elif name == "scrape_new_docs":
        url = arguments.get("url")
        if not url:
            raise ValueError("url is required")

        max_pages = arguments.get("max_pages", 50)
        max_depth = arguments.get("max_depth", 3)
        use_playwright = arguments.get("use_playwright", False)
        
        parsed = urlparse(url)
        name = parsed.netloc.replace("www.", "")

        logger.info(f"Starting MCP scrape for {url} (max_pages={max_pages}, max_depth={max_depth}, playwright={use_playwright})")
        
        # We run the parallel scraper underneath
        raw_pages = await scrape_site(
            url=url,
            max_pages=max_pages,
            max_depth=max_depth,
            parallel=True,
            concurrency=4 if use_playwright else 8,
            use_playwright=use_playwright,
        )

        if not raw_pages:
            raise ValueError(f"Scraper returned no pages for {url}")

        # Convert and save
        markdown_pages = []
        for page in raw_pages:
            markdown = convert_to_markdown(
                html=page["html"],
                title=page["title"],
                source_url=page["url"],
            )
            markdown_pages.append({
                "id": page["id"],
                "url": page["url"],
                "title": page["title"],
                "markdown": markdown,
            })

        project_manifest = save_project(name, url, markdown_pages)
        project_id = project_manifest["id"]
        
        success_msg = f"Successfully scraped {len(markdown_pages)} pages from {url}.\nNew Project ID: {project_id}\n\nYou can now read it by calling read_scraped_docs with this ID."
        return [TextContent(type="text", text=success_msg)]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    logger.info("Starting Anthology MCP stdio server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
