"""Projects endpoints — CRUD for scraped documentation projects."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response

from app.storage import (
    list_projects,
    get_project,
    get_page,
    delete_project,
    export_project,
    export_project,
    export_project_zip,
    search_project,
)

router = APIRouter()


@router.get("/projects")
async def get_all_projects():
    """List all saved projects."""
    return list_projects()


@router.get("/projects/{project_id}")
async def get_project_detail(project_id: str):
    """Get a single project with its page list."""
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/projects/{project_id}/pages/{page_id}")
async def get_page_content(project_id: str, page_id: str):
    """Get the markdown content of a single page."""
    content = get_page(project_id, page_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"id": page_id, "content": content}


@router.get("/projects/{project_id}/search")
async def search_project_pages(project_id: str, q: str = Query(..., description="Search query")):
    """Search all markdown pages in a project for a specific term.
    
    Returns:
        JSON object with a list of page IDs where matches were found.
    """
    matches = search_project(project_id, q)
    return {"matches": matches}


@router.get("/projects/{project_id}/export")
async def export_project_markdown(
    project_id: str,
    format: str = Query("single", pattern="^(single|multi)$"),
):
    """Export documentation as a single .md file or a .zip of multiple .md files.

    Query params:
        format: "single" (default) — one combined .md file
                "multi" — .zip archive with individual .md files
    """
    if format == "multi":
        result = export_project_zip(project_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Project not found")

        zip_bytes, project_name = result
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{project_name}_docs.zip"',
            },
        )
    else:
        content = export_project(project_id)
        if content is None:
            raise HTTPException(status_code=404, detail="Project not found")

        project = get_project(project_id)
        filename = f"{project['name'].replace(' ', '_')}_docs.md"

        return PlainTextResponse(
            content=content,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
            media_type="text/markdown",
        )


@router.delete("/projects/{project_id}")
async def remove_project(project_id: str):
    """Delete a project and all its files."""
    deleted = delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}
