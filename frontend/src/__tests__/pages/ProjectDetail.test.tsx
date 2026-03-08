import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProjectDetail } from "@/pages/ProjectDetail";
import { useProjectStore } from "@/stores/useProjectStore";

vi.mock("@/stores/useProjectStore", () => ({
  useProjectStore: vi.fn(),
}));

const mockProject = {
  id: "test123",
  name: "Test Docs",
  url: "https://example.com/docs",
  pages: [
    { id: "p1", title: "Getting Started", url: "https://example.com/docs" },
    { id: "p2", title: "API Reference", url: "https://example.com/docs/api" },
  ],
  page_count: 2,
  scraped_at: "2024-01-01T00:00:00Z",
};

const baseMock = {
  selectedProject: mockProject,
  selectedPageContent: "# Getting Started\n\nWelcome!",
  selectedPageId: "p1",
  isLoading: false,
  error: null,
  loadProject: vi.fn(),
  loadPage: vi.fn(),
  removeProject: vi.fn(),
  downloadExport: vi.fn(),
};

const renderDetail = () =>
  render(
    <MemoryRouter initialEntries={["/library/test123"]}>
      <Routes>
        <Route path="/library/:id" element={<ProjectDetail />} />
        <Route path="/library" element={<div>Library</div>} />
      </Routes>
    </MemoryRouter>
  );

describe("ProjectDetail", () => {
  beforeEach(() => {
    vi.mocked(useProjectStore).mockReturnValue(baseMock);
  });

  it("renders project name", () => {
    renderDetail();
    expect(screen.getByText("Test Docs")).toBeInTheDocument();
  });

  it("renders sidebar with page list", () => {
    renderDetail();
    // "Getting Started" appears in both sidebar and content
    expect(screen.getAllByText("Getting Started").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("API Reference")).toBeInTheDocument();
  });

  it("renders markdown content", () => {
    renderDetail();
    expect(screen.getByText("Welcome!")).toBeInTheDocument();
  });

  it("clicking a page calls loadPage", () => {
    renderDetail();
    fireEvent.click(screen.getByText("API Reference"));
    expect(baseMock.loadPage).toHaveBeenCalledWith("test123", "p2");
  });

  it("calls loadProject on mount", () => {
    renderDetail();
    expect(baseMock.loadProject).toHaveBeenCalledWith("test123");
  });

  it("shows page count badge", () => {
    renderDetail();
    expect(screen.getByText("2 pages")).toBeInTheDocument();
  });
});
