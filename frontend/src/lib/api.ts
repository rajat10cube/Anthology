const API_BASE = import.meta.env.VITE_API_URL || "/api";

interface Project {
  id: string;
  name: string;
  url: string;
  pages: { id: string; title: string; url: string }[];
  page_count: number;
  scraped_at: string;
}

interface PageContent {
  id: string;
  content: string;
}

export type { Project, PageContent };

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/projects`);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function fetchProject(id: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects/${id}`);
  if (!res.ok) throw new Error("Project not found");
  return res.json();
}

export async function fetchPage(projectId: string, pageId: string): Promise<PageContent> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/pages/${pageId}`);
  if (!res.ok) throw new Error("Page not found");
  return res.json();
}

export async function deleteProjectApi(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/projects/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete project");
}

export async function exportProjectApi(id: string, format: "single" | "multi" = "single"): Promise<Blob> {
  const res = await fetch(`${API_BASE}/projects/${id}/export?format=${format}`);
  if (!res.ok) throw new Error("Failed to export project");
  return res.blob();
}

export interface ScrapeRequest {
  url: string;
  name?: string;
  max_pages?: number;
  max_depth?: number;
  job_id?: string;
  parallel?: boolean;
}

export interface ScrapeResponse {
  id: string;
  name: string;
  url: string;
  page_count: number;
  scraped_at: string;
}

export async function scrapeApi(request: ScrapeRequest): Promise<ScrapeResponse> {
  const res = await fetch(`${API_BASE}/scrape`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "Scraping failed" }));
    throw new Error(data.detail || "Scraping failed");
  }
  return res.json();
}
