import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Globe, Settings2, Zap, FileText, Loader2, CheckCircle2, ArrowRight, Gauge } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { useScrapeStore } from "@/stores/useScrapeStore";

export function ScrapeForm() {
  const [url, setUrl] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [maxPages, setMaxPages] = useState(50);
  const [maxDepth, setMaxDepth] = useState(3);
  const [parallel, setParallel] = useState(true);
  const {
    isLoading, error, result, phase,
    scrapedPages, scrapedCount, queuedCount, siteName,
    startScrape, stopScrape, reset,
  } = useScrapeStore();
  const navigate = useNavigate();


  // ------- COMPLETE STATE -------
  if (phase === "complete" && result) {
    setTimeout(() => {
      reset();
      navigate(`/library/${result.id}`);
    }, 2000);

    return (
      <div className="w-full max-w-2xl mx-auto animate-fade-in" id="scrape-success">
        <div className="glass p-6 rounded-xl min-h-[360px] flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/20 flex items-center justify-center animate-pulse-glow" style={{ "--tw-shadow-color": "rgba(16,185,129,0.3)" } as React.CSSProperties}>
            <CheckCircle2 className="w-8 h-8 text-emerald-400" />
          </div>
          <h3 className="text-xl font-semibold text-emerald-400 mb-1">Crawling Complete!</h3>
          <p className="text-muted-foreground">
            Crawled <span className="text-foreground font-medium">{result.page_count}</span> pages from{" "}
            <span className="text-foreground font-medium">{result.name}</span>
          </p>
          <div className="mt-4 flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="w-4 h-4 animate-spin" />
            Redirecting to project...
          </div>
        </div>
      </div>
    );
  }

  // ------- PROGRESS STATE (scraping/converting) -------
  if (phase === "scraping" || phase === "converting") {
    const visiblePages = scrapedPages.slice(-4);

    return (
      <div className="w-full max-w-2xl mx-auto animate-fade-in" id="scrape-progress">
        <div className="glass p-6 rounded-xl min-h-[360px] flex flex-col">
          {/* Header */}
          <div className="flex items-start justify-between gap-2 mb-4">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500/30 to-violet-500/30 flex items-center justify-center shrink-0">
                <Zap className="w-5 h-5 text-primary animate-pulse" />
              </div>
              <div className="min-w-0">
                <h3 className="font-semibold text-foreground text-sm sm:text-base">
                  {phase === "converting" ? "Converting..." : "Crawling..."}
                </h3>
                <p className="text-xs sm:text-sm text-muted-foreground truncate">
                  {siteName || url}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {phase === "scraping" && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => stopScrape()}
                  className="text-destructive hover:text-destructive hover:bg-destructive/10 border-destructive/20 bg-destructive/5 px-2 sm:px-3"
                >
                  <span className="hidden sm:inline">Stop &amp; Save</span>
                  <span className="sm:hidden text-xs">Stop</span>
                </Button>
              )}
              <div className="text-right">
                <div className="text-xl sm:text-2xl font-bold text-primary tabular-nums">
                  {scrapedCount}
                </div>
                <div className="text-xs text-muted-foreground">pages</div>
              </div>
            </div>
          </div>

          {/* Progress bar */}
          <div className="h-1.5 bg-muted rounded-full overflow-hidden mb-4">
            {phase === "converting" ? (
              <div className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full w-full animate-pulse" />
            ) : (
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${Math.min((scrapedCount / maxPages) * 100, 95)}%` }}
              />
            )}
          </div>

          {/* Status line */}
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-4">
            <span className="flex items-center gap-1.5">
              {phase === "converting" ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Converting {scrapedCount} pages to Markdown...
                </>
              ) : (
                <>
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  {queuedCount > 0 ? `${queuedCount} pages queued` : "Discovering pages..."}
                </>
              )}
            </span>
            {phase === "scraping" && (
              <span className="tabular-nums">{scrapedCount} / {maxPages} max</span>
            )}
          </div>

          {/* Live page list — fixed height, 4 items max, no overflow */}
          <div className="flex-1 overflow-hidden">
            <div className="space-y-1.5">
              {visiblePages.map((page, i) => {
                const isLatest = i === visiblePages.length - 1;
                return (
                  <div
                    key={page.url}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all duration-300 ${isLatest
                      ? "bg-primary/10 border border-primary/20 text-foreground animate-fade-in"
                      : "text-muted-foreground"
                      }`}
                  >
                    <FileText className={`w-3.5 h-3.5 shrink-0 ${isLatest ? "text-primary" : ""}`} />
                    <span className="truncate">{page.title}</span>
                    {isLatest && phase === "scraping" && (
                      <ArrowRight className="w-3 h-3 ml-auto text-primary shrink-0 animate-pulse" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const isValidUrl = (string: string) => {
    const trimmed = string.trim();
    if (!trimmed) return false;
    // Simple check: at least one dot and no spaces
    return trimmed.includes(".") && !trimmed.includes(" ");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    let finalUrl = url.trim();
    if (!finalUrl.startsWith("http://") && !finalUrl.startsWith("https://")) {
      finalUrl = `https://${finalUrl}`;
    }

    await startScrape({
      url: finalUrl,
      max_pages: maxPages,
      max_depth: maxDepth,
      parallel,
    });
  };

  // ------- DEFAULT FORM STATE -------
  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto" id="scrape-form">
      <div className="relative flex items-center gap-3">
        <div className="relative flex-1">
          <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground z-10" />
          <Input
            type="text"
            placeholder="https://docs.example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="pl-11 pr-12 sm:pr-4 h-12 text-base w-full"
            disabled={isLoading}
            required
            id="scrape-url-input"
          />
          {/* Mobile-only icon button inside input */}
          <Button
            type="submit"
            size="icon"
            disabled={isLoading || !isValidUrl(url)}
            className="absolute right-1 top-1/2 -translate-y-1/2 sm:hidden h-10 w-10"
            id="scrape-submit-btn-mobile"
          >
            <Zap className="w-4 h-4" />
          </Button>
        </div>

        {/* Desktop-only button */}
        <Button
          type="submit"
          size="lg"
          disabled={isLoading || !isValidUrl(url)}
          id="scrape-submit-btn"
          className="hidden sm:flex h-12"
        >
          <Zap className="w-5 h-5" />
          Crawl
        </Button>
      </div>

      <div className="mt-3 flex items-center justify-between">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1.5 cursor-pointer"
        >
          <Settings2 className="w-3.5 h-3.5" />
          Advanced Settings
        </button>
      </div>

      <div className={`mt-3 glass p-4 rounded-lg flex gap-4 transition-opacity duration-200 ${showAdvanced ? "visible opacity-100" : "invisible opacity-0 pointer-events-none"}`}>
        <div className="flex-1">
          <label className="text-sm text-muted-foreground mb-1 block">Max Pages</label>
          <Input
            type="number"
            min={1}
            max={200}
            value={maxPages}
            onChange={(e) => setMaxPages(Number(e.target.value))}
            disabled={isLoading || !showAdvanced}
          />
        </div>
        <div className="flex-1">
          <label className="text-sm text-muted-foreground mb-1 block">Max Depth</label>
          <Input
            type="number"
            min={1}
            max={10}
            value={maxDepth}
            onChange={(e) => setMaxDepth(Number(e.target.value))}
            disabled={isLoading || !showAdvanced}
          />
        </div>
        {/* Parallel toggle */}
        <div className="flex flex-col justify-between gap-1">
          <label className="text-sm text-muted-foreground block">Parallel Crawl</label>
          <div className="flex items-center gap-2 py-2">
            <Switch
              id="parallel-toggle"
              checked={parallel}
              onCheckedChange={setParallel}
              disabled={isLoading || !showAdvanced}
            />
            <span className={`w-24 text-sm font-medium flex items-center gap-1 ${
              parallel ? "text-primary" : "text-muted-foreground"
            }`}>
              {parallel
                ? <><Gauge className="w-3.5 h-3.5" />Parallel</>
                : <><Zap className="w-3.5 h-3.5" />Sequential</>}
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className="mt-3 p-3 rounded-lg bg-destructive/10 border border-destructive/30 text-destructive text-sm animate-fade-in" id="scrape-error">
          {error}
        </div>
      )}
    </form>
  );
}
