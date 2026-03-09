import { create } from "zustand";
import {
  fetchProjects,
  fetchProject,
  fetchPage,
  deleteProjectApi,
  exportProjectApi,
  searchProjectApi,
  type Project,
} from "@/lib/api";

interface ProjectState {
  projects: Project[];
  selectedProject: Project | null;
  selectedPageContent: string | null;
  selectedPageId: string | null;
  searchResults: string[] | null;
  isLoading: boolean;
  error: string | null;

  loadProjects: () => Promise<void>;
  loadProject: (id: string) => Promise<void>;
  loadPage: (projectId: string, pageId: string) => Promise<void>;
  removeProject: (id: string) => Promise<void>;
  downloadExport: (id: string, format?: "single" | "multi") => Promise<void>;
  searchProject: (query: string) => Promise<void>;
  clearSearch: () => void;
  clearError: () => void;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  selectedProject: null,
  selectedPageContent: null,
  selectedPageId: null,
  searchResults: null,
  isLoading: false,
  error: null,

  loadProjects: async () => {
    set({ isLoading: true, error: null });
    try {
      const projects = await fetchProjects();
      set({ projects, isLoading: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },

  loadProject: async (id: string) => {
    set({ isLoading: true, error: null, selectedPageContent: null, selectedPageId: null, searchResults: null });
    try {
      const project = await fetchProject(id);
      set({ selectedProject: project, isLoading: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },

  loadPage: async (projectId: string, pageId: string) => {
    set({ isLoading: true, error: null });
    try {
      const page = await fetchPage(projectId, pageId);
      set({ selectedPageContent: page.content, selectedPageId: pageId, isLoading: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },

  removeProject: async (id: string) => {
    try {
      await deleteProjectApi(id);
      const { projects } = get();
      set({ projects: projects.filter((p) => p.id !== id) });
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  downloadExport: async (id: string, format: "single" | "multi" = "single") => {
    try {
      const blob = await exportProjectApi(id, format);
      const project = get().projects.find((p) => p.id === id) || get().selectedProject;
      const ext = format === "multi" ? "zip" : "md";
      const filename = `${(project?.name || "export").replace(/\s+/g, "_")}_docs.${ext}`;

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  searchProject: async (query: string) => {
    const { selectedProject } = get();
    if (!selectedProject || !query.trim()) {
      set({ searchResults: null });
      return;
    }
    
    set({ isLoading: true, error: null });
    try {
      const matches = await searchProjectApi(selectedProject.id, query.trim());
      set({ searchResults: matches, isLoading: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false, searchResults: null });
    }
  },

  clearSearch: () => set({ searchResults: null }),

  clearError: () => set({ error: null }),
}));
