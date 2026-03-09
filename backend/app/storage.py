"""File-system storage layer for scraped projects."""
import io
import json
import os
import re
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

load_dotenv()

# Use env var or default to backend/data
custom_data_dir = os.getenv("DATA_DIR")
if custom_data_dir:
    DATA_DIR = Path(custom_data_dir)
else:
    DATA_DIR = Path(__file__).parent.parent / "data"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:80] or "untitled"


def save_project(
    name: str,
    url: str,
    pages: list[dict[str, str]],
) -> dict[str, Any]:
    """Save a scraped project to disk.

    Args:
        name: Project display name.
        url: The root URL that was scraped.
        pages: List of dicts with keys: id, title, url, markdown.

    Returns:
        The project manifest dict.
    """
    _ensure_data_dir()
    project_id = uuid.uuid4().hex[:12]
    project_dir = DATA_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    # Write individual markdown files
    page_manifests: list[dict[str, str]] = []
    for page in pages:
        page_id = page["id"]
        md_path = project_dir / f"{page_id}.md"
        md_path.write_text(page["markdown"], encoding="utf-8")
        page_manifests.append({
            "id": page_id,
            "title": page["title"],
            "url": page["url"],
        })

    manifest = {
        "id": project_id,
        "name": name,
        "url": url,
        "pages": page_manifests,
        "page_count": len(page_manifests),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }

    manifest_path = project_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return manifest


def list_projects() -> list[dict[str, Any]]:
    """List all saved projects."""
    _ensure_data_dir()
    projects = []
    for entry in sorted(DATA_DIR.iterdir()):
        manifest_path = entry / "manifest.json"
        if entry.is_dir() and manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            projects.append(manifest)
    return projects


def get_project(project_id: str) -> dict[str, Any] | None:
    """Get a single project manifest by ID."""
    manifest_path = DATA_DIR / project_id / "manifest.json"
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def get_page(project_id: str, page_id: str) -> str | None:
    """Get the markdown content of a single page."""
    md_path = DATA_DIR / project_id / f"{page_id}.md"
    if not md_path.exists():
        return None
    return md_path.read_text(encoding="utf-8")


def delete_project(project_id: str) -> bool:
    """Delete a project directory. Returns True if it existed."""
    project_dir = DATA_DIR / project_id
    if not project_dir.exists():
        return False
    shutil.rmtree(project_dir)
    return True


def export_project(project_id: str) -> str | None:
    """Concatenate all markdown files for a project into a single string."""
    manifest = get_project(project_id)
    if manifest is None:
        return None

    parts: list[str] = []
    for page in manifest["pages"]:
        content = get_page(project_id, page["id"])
        if content:
            parts.append(content)

    return "\n\n---\n\n".join(parts)


def export_project_zip(project_id: str) -> tuple[bytes, str] | None:
    """Export all markdown files as a zip archive.

    Returns:
        Tuple of (zip_bytes, project_name) or None if project not found.
    """
    manifest = get_project(project_id)
    if manifest is None:
        return None

    project_name = _slugify(manifest["name"])
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        seen_names: dict[str, int] = {}
        for i, page in enumerate(manifest["pages"], 1):
            content = get_page(project_id, page["id"])
            if not content:
                continue

            # Create a readable filename from the page title
            slug = _slugify(page["title"])
            if slug in seen_names:
                seen_names[slug] += 1
                slug = f"{slug}-{seen_names[slug]}"
            else:
                seen_names[slug] = 1

            filename = f"{project_name}/{str(i).zfill(2)}-{slug}.md"
            zf.writestr(filename, content)

    return buf.getvalue(), project_name


def search_project(project_id: str, query: str) -> list[str]:
    """Search for a text query across all pages in a project.

    Returns:
        A list of page IDs that contain the query (case-insensitive).
    """
    manifest = get_project(project_id)
    if manifest is None:
        return []

    query_lower = query.lower()
    matches = []

    for page in manifest["pages"]:
        content = get_page(project_id, page["id"])
        if content and query_lower in content.lower():
            matches.append(page["id"])

    return matches

