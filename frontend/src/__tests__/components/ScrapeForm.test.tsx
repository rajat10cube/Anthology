import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ScrapeForm } from "@/components/ScrapeForm";
import { useScrapeStore } from "@/stores/useScrapeStore";

// Mock the store
vi.mock("@/stores/useScrapeStore", () => ({
  useScrapeStore: vi.fn(),
}));

const mockStore = {
  isLoading: false,
  error: null,
  result: null,
  phase: "idle" as const,
  scrapedPages: [],
  scrapedCount: 0,
  queuedCount: 0,
  siteName: null,
  startScrape: vi.fn(),
  reset: vi.fn(),
};

const renderForm = () =>
  render(
    <MemoryRouter>
      <ScrapeForm />
    </MemoryRouter>
  );

describe("ScrapeForm", () => {
  beforeEach(() => {
    vi.mocked(useScrapeStore).mockReturnValue(mockStore);
    mockStore.startScrape.mockClear();
  });

  it("renders URL input and submit button", () => {
    renderForm();
    expect(screen.getByPlaceholderText("https://docs.example.com")).toBeInTheDocument();
    expect(screen.getByText("Crawl")).toBeInTheDocument();
  });

  it("submits with the entered URL", async () => {
    renderForm();
    const input = screen.getByPlaceholderText("https://docs.example.com");
    fireEvent.change(input, { target: { value: "https://example.com/docs" } });
    fireEvent.submit(input.closest("form")!);
    expect(mockStore.startScrape).toHaveBeenCalledWith(
      expect.objectContaining({ url: "https://example.com/docs" })
    );
  });

  it("shows progress state when scraping", () => {
    vi.mocked(useScrapeStore).mockReturnValue({
      ...mockStore,
      isLoading: true,
      phase: "scraping",
      scrapedCount: 3,
      scrapedPages: [
        { title: "Getting Started", url: "https://example.com/start" },
        { title: "API Reference", url: "https://example.com/api" },
        { title: "Configuration", url: "https://example.com/config" },
      ],
      siteName: "example.com",
    });
    renderForm();
    expect(screen.getByText("Crawling...")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("Configuration")).toBeInTheDocument();
  });

  it("shows converting phase", () => {
    vi.mocked(useScrapeStore).mockReturnValue({
      ...mockStore,
      isLoading: true,
      phase: "converting",
      scrapedCount: 5,
      scrapedPages: [],
      siteName: "example.com",
    });
    renderForm();
    expect(screen.getByText("Converting...")).toBeInTheDocument();
  });

  it("shows error message", () => {
    vi.mocked(useScrapeStore).mockReturnValue({ ...mockStore, error: "Connection failed" });
    renderForm();
    expect(screen.getByText("Connection failed")).toBeInTheDocument();
  });

  it("shows success state", () => {
    vi.mocked(useScrapeStore).mockReturnValue({
      ...mockStore,
      phase: "complete",
      result: { id: "abc", name: "Example", url: "https://example.com", page_count: 5, scraped_at: "2024-01-01" },
    });
    renderForm();
    expect(screen.getByText("Crawling Complete!")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });
});
