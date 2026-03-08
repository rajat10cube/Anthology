import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Library } from "@/pages/Library";
import { useProjectStore } from "@/stores/useProjectStore";

vi.mock("@/stores/useProjectStore", () => ({
  useProjectStore: vi.fn(),
}));

const baseMock = {
  projects: [],
  isLoading: false,
  error: null,
  loadProjects: vi.fn(),
  removeProject: vi.fn(),
  downloadExport: vi.fn(),
};

describe("Library", () => {
  beforeEach(() => {
    vi.mocked(useProjectStore).mockReturnValue(baseMock);
  });

  it("shows empty state when no projects", () => {
    render(
      <MemoryRouter>
        <Library />
      </MemoryRouter>
    );
    expect(screen.getByText("No documentation yet")).toBeInTheDocument();
  });

  it("renders project cards", () => {
    vi.mocked(useProjectStore).mockReturnValue({
      ...baseMock,
      projects: [
        { id: "1", name: "React Docs", url: "https://react.dev", pages: [], page_count: 10, scraped_at: "2024-01-01" },
        { id: "2", name: "Vue Docs", url: "https://vuejs.org", pages: [], page_count: 5, scraped_at: "2024-01-02" },
      ],
    });
    render(
      <MemoryRouter>
        <Library />
      </MemoryRouter>
    );
    expect(screen.getByText("React Docs")).toBeInTheDocument();
    expect(screen.getByText("Vue Docs")).toBeInTheDocument();
  });

  it("shows loading spinner", () => {
    vi.mocked(useProjectStore).mockReturnValue({
      ...baseMock,
      isLoading: true,
    });
    const { container } = render(
      <MemoryRouter>
        <Library />
      </MemoryRouter>
    );
    expect(container.querySelector(".spinner")).toBeInTheDocument();
  });

  it("calls loadProjects on mount", () => {
    render(
      <MemoryRouter>
        <Library />
      </MemoryRouter>
    );
    expect(baseMock.loadProjects).toHaveBeenCalled();
  });
});
