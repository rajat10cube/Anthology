import { Route, Routes, BrowserRouter, Link } from "react-router-dom";
import { BookOpen, Menu } from "lucide-react";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Sidebar } from "@/components/Sidebar";
import { Home } from "@/pages/Home";
import { Library } from "@/pages/Library";
import { ProjectDetail } from "@/pages/ProjectDetail";
import { useSidebarStore } from "@/stores/useSidebarStore";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

function TopNavbar({ isCollapsed }: { isCollapsed: boolean }) {
  const setMobileOpen = useSidebarStore(state => state.setMobileOpen);

  return (
    <header className={cn(
      "fixed top-0 right-0 h-16 glass !border-none z-[100] flex items-center justify-between px-4 md:px-8 transition-all duration-300",
      "left-0",
      isCollapsed ? "md:left-20" : "md:left-64"
    )}>
      <Link to="/" className="flex items-center gap-3 group">
        <span className="text-xl md:text-2xl font-bold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent select-none">
          Anthology
        </span>
      </Link>

      <div className="md:hidden">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setMobileOpen(true)}
          className="text-muted-foreground"
        >
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle Menu</span>
        </Button>
      </div>
    </header>
  );
}

function AppContent() {
  const isCollapsed = useSidebarStore(state => state.isCollapsed);

  return (
    <>
      <div className="gradient-bg" />
      <TopNavbar isCollapsed={isCollapsed} />
      <Sidebar />
      <main className={cn(
        "min-h-screen flex flex-col w-full transition-all duration-300 pt-16",
        isCollapsed ? "md:pl-20" : "md:pl-64"
      )}>
        <div className="relative flex-1 flex flex-col w-full h-full">
          <div className="flex-1 flex flex-col relative w-full overflow-hidden">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/library" element={<Library />} />
              <Route path="/library/:id" element={<ProjectDetail />} />
            </Routes>
          </div>
        </div>
      </main>
    </>
  );
}

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="anthology-theme">
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
