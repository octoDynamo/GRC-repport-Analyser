import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Cpu } from 'lucide-react';
import { cn } from '../../lib/utils';

const navItems = [
  { title: "Tableau de Bord", icon: LayoutDashboard, href: "/dashboard" },
  { title: "Rapports", icon: FileText, href: "/reports" },
];

export function Sidebar() {
  return (
    <div className="flex w-64 flex-col border-r bg-muted/30 min-h-screen">
      <div className="flex h-16 items-center border-b px-6">
        <Cpu className="h-6 w-6 text-primary mr-2" />
        <span className="text-xl font-bold tracking-tight text-foreground">
          GRC <span className="text-primary">AI</span> Analyzer
        </span>
      </div>
      <div className="flex-1 overflow-auto py-6 flex flex-col gap-1 px-4">
        {navItems.map((item) => (
          <NavLink
            key={item.href}
            to={item.href}
            className={({ isActive }: { isActive: boolean }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.title}
          </NavLink>
        ))}
      </div>
      <div className="p-4 border-t text-xs text-muted-foreground text-center">
        PFE GRC Analyzer © {new Date().getFullYear()}
      </div>
    </div>
  );
}
