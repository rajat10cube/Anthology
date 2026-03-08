import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ExternalLink, FileText, Download, Trash2, Calendar, FileArchive } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Project } from "@/lib/api";

interface ProjectCardProps {
  project: Project;
  onExport: (id: string, format: "single" | "multi") => void;
  onDelete: (id: string) => void;
}

export function ProjectCard({ project, onExport, onDelete }: ProjectCardProps) {
  const navigate = useNavigate();
  const [showExportMenu, setShowExportMenu] = useState(false);
  const exportRef = useRef<HTMLDivElement>(null);

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

  const handleExport = (format: "single" | "multi") => {
    onExport(project.id, format);
    setShowExportMenu(false);
  };

  const formattedDate = new Date(project.scraped_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <Card className="group animate-fade-in" id={`project-card-${project.id}`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className="truncate">{project.name}</CardTitle>
            <CardDescription className="flex items-center gap-1.5 mt-1 truncate">
              <ExternalLink className="w-3.5 h-3.5 shrink-0" />
              <a 
                href={project.url} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="truncate hover:underline"
              >
                {project.url}
              </a>
            </CardDescription>
          </div>
          <Badge>{project.page_count} pages</Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <Calendar className="w-3.5 h-3.5" />
          {formattedDate}
        </div>
      </CardContent>

      <CardFooter className="gap-2">
        <Button
          variant="default"
          size="sm"
          onClick={() => navigate(`/library/${project.id}`)}
          className="flex-1"
        >
          <FileText className="w-4 h-4" />
          View
        </Button>
        {/* Export dropdown */}
        <div className="relative" ref={exportRef}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowExportMenu(!showExportMenu)}
            id={`export-btn-${project.id}`}
          >
            <Download className="w-4 h-4" />
          </Button>
          {showExportMenu && (
            <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 w-48 glass rounded-lg border border-border/50 shadow-xl z-50 animate-fade-in overflow-hidden">
              <button
                onClick={() => handleExport("single")}
                className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-left hover:bg-accent transition-colors cursor-pointer"
              >
                <FileText className="w-4 h-4 text-primary shrink-0" />
                <div>
                  <div className="font-medium text-foreground">Single .md</div>
                </div>
              </button>
              <div className="border-t border-border/30" />
              <button
                onClick={() => handleExport("multi")}
                className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-left hover:bg-accent transition-colors cursor-pointer"
              >
                <FileArchive className="w-4 h-4 text-primary shrink-0" />
                <div>
                  <div className="font-medium text-foreground">Multiple (.zip)</div>
                </div>
              </button>
            </div>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onDelete(project.id)}
          className="hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}
