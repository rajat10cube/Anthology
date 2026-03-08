import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";

describe("MarkdownRenderer", () => {
  it("renders headings from markdown", () => {
    render(<MarkdownRenderer content="# Hello World" />);
    expect(screen.getByText("Hello World")).toBeInTheDocument();
  });

  it("renders paragraphs from markdown", () => {
    render(<MarkdownRenderer content="This is a paragraph." />);
    expect(screen.getByText("This is a paragraph.")).toBeInTheDocument();
  });

  it("renders code blocks", () => {
    const md = '```python\nprint("hello")\n```';
    render(<MarkdownRenderer content={md} />);
    expect(screen.getByText(/print/)).toBeInTheDocument();
  });

  it("strips YAML frontmatter", () => {
    const md = '---\ntitle: "Test"\nsource: "https://example.com"\n---\n\n# Actual Content';
    render(<MarkdownRenderer content={md} />);
    expect(screen.getByText("Actual Content")).toBeInTheDocument();
    expect(screen.queryByText("title:")).not.toBeInTheDocument();
  });

  it("handles empty content", () => {
    render(<MarkdownRenderer content="" />);
    expect(screen.getByText("Select a page to view its content")).toBeInTheDocument();
  });
});
