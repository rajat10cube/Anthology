import { create } from "zustand";
import { type ScrapeRequest, type ScrapeResponse } from "@/lib/api";

interface ScrapedPage {
  title: string;
  url: string;
}

interface ScrapeState {
  isLoading: boolean;
  error: string | null;
  result: ScrapeResponse | null;

  // Progress tracking
  phase: "idle" | "scraping" | "converting" | "complete" | "error";
  scrapedPages: ScrapedPage[];
  scrapedCount: number;
  queuedCount: number;
  sitemapUrlsFound: number;
  siteName: string | null;
  jobId: string | null;

  startScrape: (request: ScrapeRequest) => Promise<void>;
  stopScrape: () => Promise<void>;
  reset: () => void;
}

export const useScrapeStore = create<ScrapeState>((set, get) => ({
  isLoading: false,
  error: null,
  result: null,
  phase: "idle",
  scrapedPages: [],
  scrapedCount: 0,
  queuedCount: 0,
  sitemapUrlsFound: 0,
  siteName: null,
  jobId: null,

  startScrape: async (request: ScrapeRequest) => {
    const jobId = crypto.randomUUID();
    set({
      isLoading: true,
      error: null,
      result: null,
      phase: "scraping",
      scrapedPages: [],
      scrapedCount: 0,
      queuedCount: 0,
      sitemapUrlsFound: 0,
      siteName: null,
      jobId,
    });

    try {
      const response = await fetch("/api/scrape/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...request, job_id: jobId }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({ detail: "Scraping failed" }));
        throw new Error(data.detail || "Scraping failed");
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response stream available");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from the buffer
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // keep incomplete line in buffer

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ") && eventType) {
            try {
              const data = JSON.parse(line.slice(6));
              _handleEvent(set, get, eventType, data);
            } catch {
              // skip malformed JSON
            }
            eventType = "";
          }
        }
      }

      // If we finished reading but never got a complete event, check state
      const { phase } = get();
      if (phase !== "complete" && phase !== "error") {
        set({ phase: "error", error: "Stream ended unexpectedly", isLoading: false });
      }
    } catch (err) {
      set({
        error: (err as Error).message,
        isLoading: false,
        phase: "error",
      });
    }
  },

  stopScrape: async () => {
    const { jobId, phase } = get();
    if (!jobId || phase !== "scraping") return;
    
    try {
      await fetch("/api/scrape/stop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId })
      });
    } catch (err) {
      console.error("Failed to stop scrape:", err);
    }
  },

  reset: () =>
    set({
      isLoading: false,
      error: null,
      result: null,
      phase: "idle",
      scrapedPages: [],
      scrapedCount: 0,
      queuedCount: 0,
      sitemapUrlsFound: 0,
      siteName: null,
      jobId: null,
    }),
}));

function _handleEvent(
  set: (state: Partial<ScrapeState>) => void,
  get: () => ScrapeState,
  eventType: string,
  data: any,
) {
  switch (eventType) {
    case "started":
      set({ siteName: data.name, phase: "scraping" });
      break;

    case "page_scraped": {
      const { scrapedPages } = get();
      set({
        scrapedPages: [...scrapedPages, { title: data.title, url: data.url }],
        scrapedCount: data.scraped,
        queuedCount: data.queued,
      });
      break;
    }

    case "sitemap_discovered":
      set({ sitemapUrlsFound: data.urls_found });
      break;

    case "converting":
      set({ phase: "converting" });
      break;

    case "complete":
      set({
        phase: "complete",
        isLoading: false,
        result: {
          id: data.id,
          name: data.name,
          url: data.url,
          page_count: data.page_count,
          scraped_at: data.scraped_at,
        },
      });
      break;

    case "error":
      set({
        phase: "error",
        error: data.message,
        isLoading: false,
      });
      break;
  }
}
