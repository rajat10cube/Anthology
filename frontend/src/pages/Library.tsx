import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Plus, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProjectCard } from "@/components/ProjectCard";
import { useProjectStore } from "@/stores/useProjectStore";

export function Library() {
  const { projects, isLoading, loadProjects, removeProject, downloadExport } = useProjectStore();

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  if (isLoading && projects.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="flex-1 py-8 px-6" id="library-page">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8 animate-fade-in">
          <div>
            <h1 className="text-3xl font-bold">
              <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
                Your Library
              </span>
            </h1>
            <p className="text-muted-foreground mt-1">
              {projects.length} documentation {projects.length === 1 ? "collection" : "collections"}
            </p>
          </div>
          <Link to="/">
            <Button>
              <Plus className="w-4 h-4" />
              Crawl New
            </Button>
          </Link>
        </div>

        {projects.length === 0 ? (
          <div className="text-center py-24 animate-fade-in" id="library-empty">
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-indigo-500/10 to-violet-500/10 flex items-center justify-center">
              <BookOpen className="w-10 h-10 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No documentation yet</h3>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              Start by crawling your first documentation site. Your collections will appear here.
            </p>
            <Link to="/">
              <Button size="lg">
                <Plus className="w-5 h-5" />
                Crawl Your First Docs
              </Button>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onExport={downloadExport}
                onDelete={removeProject}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
