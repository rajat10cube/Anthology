import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useProjectStore } from "@/stores/useProjectStore";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("useProjectStore", () => {
  beforeEach(() => {
    // Reset store state
    useProjectStore.setState({
      projects: [],
      selectedProject: null,
      selectedPageContent: null,
      selectedPageId: null,
      isLoading: false,
      error: null,
    });
    mockFetch.mockClear();
  });

  it("has correct initial state", () => {
    const state = useProjectStore.getState();
    expect(state.projects).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it("loadProjects fetches and sets projects", async () => {
    const mockProjects = [{ id: "1", name: "Test" }];
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockProjects,
    });

    await useProjectStore.getState().loadProjects();

    expect(useProjectStore.getState().projects).toEqual(mockProjects);
    expect(useProjectStore.getState().isLoading).toBe(false);
  });

  it("loadProjects sets error on failure", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });

    await useProjectStore.getState().loadProjects();

    expect(useProjectStore.getState().error).toBeTruthy();
    expect(useProjectStore.getState().isLoading).toBe(false);
  });

  it("removeProject removes from list", async () => {
    useProjectStore.setState({
      projects: [
        { id: "1", name: "A", url: "", pages: [], page_count: 0, scraped_at: "" },
        { id: "2", name: "B", url: "", pages: [], page_count: 0, scraped_at: "" },
      ],
    });
    mockFetch.mockResolvedValueOnce({ ok: true });

    await useProjectStore.getState().removeProject("1");

    expect(useProjectStore.getState().projects).toHaveLength(1);
    expect(useProjectStore.getState().projects[0].id).toBe("2");
  });

  it("clearError resets error", () => {
    useProjectStore.setState({ error: "Some error" });
    useProjectStore.getState().clearError();
    expect(useProjectStore.getState().error).toBeNull();
  });
});
