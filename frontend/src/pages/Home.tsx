import { BookOpen, FileText, Zap, FolderOpen, Download, Sparkles } from "lucide-react";
import { ScrapeForm } from "@/components/ScrapeForm";
import { useScrapeStore } from "@/stores/useScrapeStore";

const features = [
  {
    icon: Zap,
    title: "Instant Crawling",
    description: "Enter a documentation URL and get clean, structured Markdown files in seconds.",
  },
  {
    icon: FileText,
    title: "AI-Ready Markdown",
    description: "Generated Markdown is optimized for LLM context windows with proper formatting.",
  },
  {
    icon: FolderOpen,
    title: "Organized Library",
    description: "Manage all your crawled documentation collections in one centralized library.",
  },
  {
    icon: Download,
    title: "Easy Export",
    description: "Export ready-to-use .md files for seamless integration with any LLM workflow.",
  },
];

export function Home() {
  const phase = useScrapeStore((s) => s.phase);
  const isActive = phase === "scraping" || phase === "converting" || phase === "complete";

  return (
    <div className="flex-1">
      {/* Hero Section */}
      <section className="relative pt-8 pb-20 md:py-24 px-6 overflow-hidden" id="hero">
        <div className="max-w-4xl mx-auto text-center animate-fade-in">

          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-8 text-sm text-muted-foreground">
            <Sparkles className="w-4 h-4 text-primary" />
            Documentation for the AI era
          </div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent">
              Turn any docs
            </span>
            <br />
            into LLM context
          </h1>

          {/* Subtitle — fades out and collapses when crawling starts */}
          <div
            className="overflow-hidden transition-all duration-500 ease-in-out"
            style={{
              maxHeight: isActive ? "0px" : "120px",
              opacity: isActive ? 0 : 1,
              marginBottom: isActive ? "0px" : "3rem",
            }}
          >
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Crawl documentation websites and convert them to well-structured Markdown files.
              Keep your AI&apos;s knowledge current with up-to-date context.
            </p>
          </div>

          <ScrapeForm />
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6" id="features">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-4">
            <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
              How it works
            </span>
          </h2>
          <p className="text-center text-muted-foreground mb-12 max-w-lg mx-auto">
            From URL to AI-ready documentation in three simple steps
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, i) => (
              <div
                key={feature.title}
                className="glass glass-hover p-6 rounded-xl animate-fade-in"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-indigo-500/20 to-violet-500/20 flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-semibold text-lg mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
