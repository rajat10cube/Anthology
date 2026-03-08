import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { BookOpen, Home, Library, Menu, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ModeToggle } from "@/components/ModeToggle";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { useSidebarStore } from "@/stores/useSidebarStore";

const navLinks = [
  { to: "/", label: "Home", icon: Home },
  { to: "/library", label: "Library", icon: Library },
];

function SidebarContent({ 
  isCollapsed = false, 
  showToggle = false
}: { 
  isCollapsed?: boolean; 
  showToggle?: boolean; 
}) {
  const location = useLocation();
  const toggleCollapse = useSidebarStore(state => state.toggleCollapse);

  return (
    <>
      <div className={cn("p-4 flex items-center transition-all", isCollapsed ? "justify-center" : "justify-between")}>
        {isCollapsed && showToggle ? (
          <button 
            onClick={toggleCollapse}
            className="w-10 h-10 flex items-center justify-center transition-all shrink-0 group relative cursor-pointer text-muted-foreground hover:bg-primary/5 rounded-lg"
            title="Expand sidebar"
          >
            <BookOpen className="w-4 h-4 absolute transition-all duration-200 opacity-100 group-hover:opacity-0 group-hover:scale-75" />
            <PanelLeftOpen className="w-4 h-4 absolute transition-all duration-200 opacity-0 scale-75 group-hover:opacity-100 group-hover:scale-100" />
          </button>
        ) : (
          <Link 
            to="/" 
            className="flex items-center justify-center w-10 h-10 group shrink-0 transition-all rounded-lg hover:bg-primary/5"
          >
            <div className="flex items-center justify-center text-muted-foreground transition-colors group-hover:text-primary">
              <BookOpen className="w-4 h-4" />
            </div>
          </Link>
        )}
        
        {!isCollapsed && showToggle && (
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={toggleCollapse}
            className="text-muted-foreground hover:text-muted-foreground shrink-0"
            title="Collapse sidebar"
          >
            <PanelLeftClose className="w-4 h-4" />
          </Button>
        )}
      </div>

      <nav className="flex-1 px-4 space-y-2 overflow-y-auto">
        {navLinks.map(({ to, label, icon: Icon }) => {
          const isActive = location.pathname === to ||
            (to === "/library" && location.pathname.startsWith("/library"));
            
          return (
            <Link key={to} to={to} className="block">
              <Button
                variant="ghost"
                className={cn(
                  "w-full h-11 transition-all",
                  isCollapsed ? "justify-center px-0" : "justify-start gap-3 px-4",
                  isActive ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-muted-foreground hover:bg-primary/5"
                )}
                title={isCollapsed ? label : undefined}
              >
                <Icon className={cn("w-4 h-4 shrink-0 transition-colors", isActive && "text-primary")} />
                {!isCollapsed && <span className="text-base font-medium">{label}</span>}
              </Button>
            </Link>
          );
        })}
      </nav>

      <div className={cn("p-4 mt-auto border-t border-border/50 flex items-center", isCollapsed ? "justify-center" : "justify-between")}>
        {!isCollapsed && <span className="text-sm font-medium text-muted-foreground">Theme</span>}
        <ModeToggle />
      </div>
    </>
  );
}

export function Sidebar() {
  const location = useLocation();
  const isCollapsed = useSidebarStore(state => state.isCollapsed);
  const isMobileOpen = useSidebarStore(state => state.isMobileOpen);
  const setMobileOpen = useSidebarStore(state => state.setMobileOpen);

  // Close sheet on navigation
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname, setMobileOpen]);

  return (
    <>
      {/* Desktop Sidebar - back to full height */}
      <aside className={cn(
        "hidden md:flex fixed top-0 bottom-0 left-0 glass !rounded-none border-r border-border/50 flex-col z-[60] transition-all duration-300",
        isCollapsed ? "w-20" : "w-64"
      )}>
        <SidebarContent isCollapsed={isCollapsed} showToggle={true} />
      </aside>

      {/* Mobile Drawer (controlled by TopNavbar hamburger) */}
      <Sheet open={isMobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-64 p-0 glass !rounded-none border-r border-border/50 flex flex-col gap-0 sm:max-w-xs">
          <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
          <SidebarContent isCollapsed={false} showToggle={false} />
        </SheetContent>
      </Sheet>
    </>
  );
}
