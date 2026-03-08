import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
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
    <div className="markdown-body" id="markdown-content">
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
