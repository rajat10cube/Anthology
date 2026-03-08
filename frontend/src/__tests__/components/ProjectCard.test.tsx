import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ProjectCard } from "@/components/ProjectCard";
import type { Project } from "@/lib/api";

const mockProject: Project = {
  id: "test123",
  name: "Test Docs",
  url: "https://example.com/docs",
  pages: [
    { id: "p1", title: "Page 1", url: "https://example.com/docs/p1" },
    { id: "p2", title: "Page 2", url: "https://example.com/docs/p2" },
  ],
  page_count: 2,
  scraped_at: "2024-06-15T10:30:00Z",
};

const renderCard = (overrides = {}) => {
  const onExport = vi.fn();
  const onDelete = vi.fn();
  render(
    <MemoryRouter>
      <ProjectCard project={{ ...mockProject, ...overrides }} onExport={onExport} onDelete={onDelete} />
    </MemoryRouter>
  );
  return { onExport, onDelete };
};

describe("ProjectCard", () => {
  it("renders project name", () => {
    renderCard();
    expect(screen.getByText("Test Docs")).toBeInTheDocument();
  });

  it("renders page count badge", () => {
    renderCard();
    expect(screen.getByText("2 pages")).toBeInTheDocument();
  });

  it("renders formatted date", () => {
    renderCard();
    expect(screen.getByText(/Jun 15, 2024/)).toBeInTheDocument();
  });

  it("calls onExport when export button is clicked", () => {
    const { onExport } = renderCard();
    // Click the export toggle button via its ID
    const exportToggleBtn = document.getElementById("export-btn-test123")!;
    fireEvent.click(exportToggleBtn);
    
    // Click the "Single .md" option inside the dropdown
    const singleExportBtn = screen.getByText("Single .md");
    fireEvent.click(singleExportBtn);
    
    expect(onExport).toHaveBeenCalledWith("test123", "single");
  });

  it("calls onDelete when delete button is clicked", () => {
    const { onDelete } = renderCard();
    const buttons = screen.getAllByRole("button");
    // buttons: [View, Export Toggle, Single, Multi, Delete]
    // Note: single and multi might be rendered as buttons depending on how we structured it, 
    // but looking at ProjectCard.tsx, they are <button> elements.
    // However, they only appear AFTER the export toggle is clicked.
    // So if the menu is closed, buttons = [View, Export Toggle, Delete]
    fireEvent.click(buttons[2]);
    expect(onDelete).toHaveBeenCalledWith("test123");
  });
});
