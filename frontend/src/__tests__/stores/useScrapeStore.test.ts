import { describe, it, expect, vi, beforeEach } from "vitest";
import { useScrapeStore } from "@/stores/useScrapeStore";

describe("useScrapeStore", () => {
  beforeEach(() => {
    useScrapeStore.setState({
      isLoading: false,
      error: null,
      result: null,
      phase: "idle",
      scrapedPages: [],
      scrapedCount: 0,
      queuedCount: 0,
      siteName: null,
    });
  });

  it("has correct initial state", () => {
    const state = useScrapeStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
    expect(state.result).toBeNull();
    expect(state.phase).toBe("idle");
    expect(state.scrapedPages).toEqual([]);
    expect(state.scrapedCount).toBe(0);
  });

  it("reset clears all state", () => {
    useScrapeStore.setState({
      isLoading: true,
      error: "Some error",
      phase: "scraping",
      scrapedCount: 5,
      scrapedPages: [{ title: "Test", url: "https://example.com" }],
      result: { id: "x", name: "X", url: "", page_count: 0, scraped_at: "" },
    });

    useScrapeStore.getState().reset();

    const state = useScrapeStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
    expect(state.result).toBeNull();
    expect(state.phase).toBe("idle");
    expect(state.scrapedPages).toEqual([]);
    expect(state.scrapedCount).toBe(0);
  });

  it("startScrape sets loading and scraping phase", async () => {
    // Mock fetch to return a stream that ends immediately
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      body: {
        getReader: () => ({
          read: vi.fn().mockResolvedValueOnce({ done: true, value: undefined }),
        }),
      },
    });
    global.fetch = mockFetch;

    const promise = useScrapeStore.getState().startScrape({ url: "https://example.com" });

    // Should be loading immediately after calling
    expect(useScrapeStore.getState().isLoading).toBe(true);
    expect(useScrapeStore.getState().phase).toBe("scraping");

    await promise;
  });

  it("startScrape sets error on non-ok response", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "Scraping failed" }),
    });
    global.fetch = mockFetch;

    await useScrapeStore.getState().startScrape({ url: "https://bad.com" });

    expect(useScrapeStore.getState().error).toBe("Scraping failed");
    expect(useScrapeStore.getState().isLoading).toBe(false);
    expect(useScrapeStore.getState().phase).toBe("error");
  });

  it("stopScrape sends request to cancel active job", async () => {
    useScrapeStore.setState({
      phase: "scraping",
      jobId: "test-job-123",
    });

    const mockFetch = vi.fn().mockResolvedValue({ ok: true });
    global.fetch = mockFetch;

    await useScrapeStore.getState().stopScrape();

    expect(mockFetch).toHaveBeenCalledWith("/api/scrape/stop", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ job_id: "test-job-123" }),
    }));
  });

  it("stopScrape does nothing if not scraping", async () => {
    useScrapeStore.setState({
      phase: "idle",
      jobId: "test-job-123",
    });

    const mockFetch = vi.fn();
    global.fetch = mockFetch;

    await useScrapeStore.getState().stopScrape();

    expect(mockFetch).not.toHaveBeenCalled();
  });
});
