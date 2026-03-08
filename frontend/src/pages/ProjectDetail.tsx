import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Download, Trash2, FileText, ExternalLink, ChevronDown, FileArchive, LayoutList, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { useProjectStore } from "@/stores/useProjectStore";
import { cn } from "@/lib/utils";

type MobileTab = "pages" | "content";

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [mobileTab, setMobileTab] = useState<MobileTab>("pages");
  const exportRef = useRef<HTMLDivElement>(null);
  const {
    selectedProject,
    selectedPageContent,
    selectedPageId,
    isLoading,
    loadProject,
    loadPage,
    removeProject,
    downloadExport,
  } = useProjectStore();

  useEffect(() => {
    if (id) {
      loadProject(id);
    }
  }, [id, loadProject]);

  // Auto-select first page when project loads
  useEffect(() => {
    if (selectedProject && selectedProject.pages.length > 0 && !selectedPageId) {
      loadPage(selectedProject.id, selectedProject.pages[0].id);
    }
  }, [selectedProject, selectedPageId, loadPage]);

  // Close export menu on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (exportRef.current && !exportRef.current.contains(e.target as Node)) {
        setShowExportMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  if (isLoading && !selectedProject) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }

  if (!selectedProject) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-muted-foreground">Project not found</p>
      </div>
    );
  }

  const handleDelete = async () => {
    await removeProject(selectedProject.id);
    navigate("/library");
  };

  const handleExport = (format: "single" | "multi") => {
    downloadExport(selectedProject.id, format);
    setShowExportMenu(false);
  };

  const handlePageSelect = (projectId: string, pageId: string) => {
    loadPage(projectId, pageId);
    setMobileTab("content");
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden" id="project-detail">
      {/* Top bar */}
      <div className="sticky top-0 z-10 flex items-center justify-between px-2 sm:px-6 py-3 border-b border-border/50 glass animate-fade-in shrink-0">
        <div className="flex items-center gap-1 sm:gap-3 min-w-0">
          <Button variant="ghost" size="icon" onClick={() => navigate("/library")}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="min-w-0">
            <h1 className="text-lg font-semibold truncate">{selectedProject.name}</h1>
            <div className="hidden sm:flex items-center gap-2 text-sm text-muted-foreground">
              <ExternalLink className="w-3 h-3 shrink-0" />
              <span className="truncate">{selectedProject.url}</span>
              <Badge className="shrink-0">{selectedProject.page_count} pages</Badge>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {/* Export dropdown */}
          <div className="relative" ref={exportRef}>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowExportMenu(!showExportMenu)}
              id="export-btn"
            >
              <Download className="w-4 h-4" />
              <span className="hidden sm:inline">Download</span>
              <ChevronDown className="w-3 h-3 ml-1" />
            </Button>
            {showExportMenu && (
              <div className="absolute right-0 top-full mt-1 w-56 glass rounded-lg border border-border/50 shadow-xl z-50 animate-fade-in overflow-hidden">
                <button
                  onClick={() => handleExport("single")}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-left hover:bg-accent transition-colors cursor-pointer"
                  id="export-single"
                >
                  <FileText className="w-4 h-4 text-primary shrink-0" />
                  <div>
                    <div className="font-medium text-foreground">Single .md file</div>
                    <div className="text-xs text-muted-foreground">All pages combined</div>
                  </div>
                </button>
                <div className="border-t border-border/30" />
                <button
                  onClick={() => handleExport("multi")}
                  className="w-full flex items-center gap-3 px-4 py-3 text-sm text-left hover:bg-accent transition-colors cursor-pointer"
                  id="export-multi"
                >
                  <FileArchive className="w-4 h-4 text-primary shrink-0" />
                  <div>
                    <div className="font-medium text-foreground">Multiple .md files</div>
                    <div className="text-xs text-muted-foreground">Zip with individual files</div>
                  </div>
                </button>
              </div>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDelete}
            className="hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30"
          >
            <Trash2 className="w-4 h-4" />
            <span className="hidden sm:inline">Delete</span>
          </Button>
        </div>
      </div>

      {/* Mobile tab bar — hidden on sm+ */}
      <div className="flex sm:hidden shrink-0 border-b border-border/50">
        <button
          onClick={() => setMobileTab("pages")}
          className={cn(
            "flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors",
            mobileTab === "pages"
              ? "text-primary border-b-2 border-primary"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <LayoutList className="w-4 h-4" />
          Pages
        </button>
        <button
          onClick={() => setMobileTab("content")}
          className={cn(
            "flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors",
            mobileTab === "content"
              ? "text-primary border-b-2 border-primary"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <BookOpen className="w-4 h-4" />
          Content
        </button>
      </div>

      {/* Content area */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Sidebar — full width on mobile (pages tab), fixed width on desktop */}
        <aside
          className={cn(
            "border-r border-border/50 overflow-y-auto bg-sidebar-background shrink-0 animate-slide-in relative",
            // Mobile: full width, shown only on pages tab
            "w-full sm:w-72",
            mobileTab === "pages" ? "flex sm:flex flex-col" : "hidden sm:flex sm:flex-col"
          )}
          id="page-sidebar"
        >
          <div className="p-4 absolute inset-0 overflow-y-auto">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
              Pages ({selectedProject.pages.length})
            </h2>
            <div className="space-y-1">
              {selectedProject.pages.map((page) => (
                <button
                  key={page.id}
                  onClick={() => handlePageSelect(selectedProject.id, page.id)}
                  className={cn(
                    "w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-200 flex items-center gap-2 cursor-pointer",
                    selectedPageId === page.id
                      ? "bg-primary/15 text-primary border border-primary/20"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent"
                  )}
                >
                  <FileText className="w-4 h-4 shrink-0" />
                  <span className="truncate">{page.title}</span>
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Main content — full width on mobile (content tab), flex-1 on desktop */}
        <main
          className={cn(
            "flex-1 overflow-y-auto relative p-8",
            mobileTab === "content" ? "flex sm:flex flex-col" : "hidden sm:flex sm:flex-col"
          )}
        >
          <div className="absolute inset-0 p-8 overflow-y-auto">
            {isLoading && !selectedPageContent ? (
              <div className="flex items-center justify-center h-full">
                <div className="spinner" />
              </div>
            ) : (
              <div className="max-w-3xl mx-auto animate-fade-in">
                <MarkdownRenderer content={selectedPageContent || ""} />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
