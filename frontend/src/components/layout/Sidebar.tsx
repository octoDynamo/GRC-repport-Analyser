import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Cpu, Users, ShieldCheck } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuthStore } from '../../store/authStore';

const analystNav = [
  { title: 'Tableau de Bord', icon: LayoutDashboard, href: '/dashboard' },
  { title: 'Rapports', icon: FileText, href: '/reports' },
];

const adminNav = [
  { title: 'Tableau de Bord', icon: LayoutDashboard, href: '/dashboard' },
  { title: 'Rapports', icon: FileText, href: '/reports' },
];

const adminOnlyNav = [
  { title: 'Utilisateurs', icon: Users, href: '/admin/users' },
  { title: 'Référentiels', icon: ShieldCheck, href: '/admin/referentiels' },
];

function NavItem({ href, icon: Icon, title }: { href: string; icon: React.ElementType; title: string }) {
  return (
    <NavLink
      to={href}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all',
          isActive
            ? 'bg-primary text-primary-foreground shadow-sm'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        )
      }
    >
      <Icon className="h-4 w-4" />
      {title}
    </NavLink>
  );
}

export function Sidebar() {
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role === 'ADMIN';
  const navItems = isAdmin ? adminNav : analystNav;

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
          <NavItem key={item.href} {...item} />
        ))}

        {isAdmin && (
          <>
            <div className="mx-1 my-3 border-t" />
            <p className="px-3 pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Administration
            </p>
            {adminOnlyNav.map((item) => (
              <NavItem key={item.href} {...item} />
            ))}
          </>
        )}
      </div>

      <div className="p-4 border-t">
        {user && (
          <div className="mb-2 rounded-lg bg-muted px-3 py-2">
            <p className="text-xs font-medium text-foreground truncate">{user.nom}</p>
            <p className="text-xs text-muted-foreground truncate">{user.email}</p>
            <span className={cn(
              'mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium',
              isAdmin ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
            )}>
              {user.role}
            </span>
          </div>
        )}
        <p className="text-xs text-muted-foreground text-center">PFE GRC Analyzer © {new Date().getFullYear()}</p>
      </div>
    </div>
  );
}
