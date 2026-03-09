import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import Mark from "mark.js";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface MarkdownRendererProps {
  content: string;
  searchTerm?: string;
}

export function MarkdownRenderer({ content, searchTerm }: MarkdownRendererProps) {
  const contentRef = useRef<HTMLDivElement>(null);
  const markInstance = useRef<Mark | null>(null);

  // Initialize mark.js
  useEffect(() => {
    if (contentRef.current) {
      markInstance.current = new Mark(contentRef.current);
    }
  }, [content]);

  // Apply highlights when search term changes or content changes
  useEffect(() => {
    if (!markInstance.current) return;

    // First unmark previous highlights
    markInstance.current.unmark({
      done: () => {
        // Then apply new highlights if there's a search term
        if (searchTerm && searchTerm.trim() !== "") {
          markInstance.current?.mark(searchTerm.trim(), {
            element: "span",
            className: "search-highlight bg-yellow-500/50 text-yellow-900 dark:text-yellow-100 rounded-sm px-0.5",
            separateWordSearch: false,
            done: () => {
              // Scroll the first highlight into view
              if (contentRef.current) {
                const firstHighlight = contentRef.current.querySelector(".search-highlight");
                if (firstHighlight) {
                  firstHighlight.scrollIntoView({ behavior: "smooth", block: "center" });
                }
              }
            }
          });
        }
      }
    });
  }, [searchTerm, content]);
  if (!content) {
    return (
      <div className="text-center text-muted-foreground py-12">
        <p>Select a page to view its content</p>
      </div>
    );
  }

  // Strip frontmatter
  const cleanContent = content.replace(/^---[\s\S]*?---\n*/m, "");

  return (
    <div className="markdown-body" id="markdown-content" ref={contentRef}>
      <ReactMarkdown
        components={{
          code(props) {
            const { children, className, ...rest } = props;
            const match = /language-(\w+)/.exec(className || "");
            const codeString = String(children).replace(/\n$/, "");

            if (match) {
              return (
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="div"
                  customStyle={{
                    background: "rgba(10, 10, 30, 0.8)",
                    borderRadius: "0.75rem",
                    border: "1px solid rgba(99, 102, 241, 0.15)",
                    margin: "1rem 0",
                    fontSize: "0.875rem",
                  }}
                >
                  {codeString}
                </SyntaxHighlighter>
              );
            }

            return (
              <code className={className} {...rest}>
                {children}
              </code>
            );
          },
        }}
      >
        {cleanContent}
      </ReactMarkdown>
    </div>
  );
}
