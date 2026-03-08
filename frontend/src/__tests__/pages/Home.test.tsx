import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Home } from "@/pages/Home";

// Mock ScrapeForm since it's tested separately
vi.mock("@/components/ScrapeForm", () => ({
  ScrapeForm: () => <div data-testid="scrape-form">ScrapeForm</div>,
}));

describe("Home", () => {
  it("renders hero tagline", () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    );
    expect(screen.getByText(/Turn any docs/)).toBeInTheDocument();
    expect(screen.getByText(/into LLM context/)).toBeInTheDocument();
  });

  it("renders the scrape form", () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    );
    expect(screen.getByTestId("scrape-form")).toBeInTheDocument();
  });

  it("renders feature cards", () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    );
    expect(screen.getByText("Instant Crawling")).toBeInTheDocument();
    expect(screen.getByText("AI-Ready Markdown")).toBeInTheDocument();
    expect(screen.getByText("Organized Library")).toBeInTheDocument();
    expect(screen.getByText("Easy Export")).toBeInTheDocument();
  });
});
