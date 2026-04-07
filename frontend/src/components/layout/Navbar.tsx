import { LogOut, User as UserIcon } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { useNavigate } from 'react-router-dom';

export function Navbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background px-6 shadow-sm">
      <div className="flex-1" />
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm">
          <UserIcon className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{user?.nom || 'Utilisateur'}</span>
          <span className="ml-1 rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
            {user?.role}
          </span>
        </div>
        <button
          onClick={handleLogout}
          className="flex h-9 w-9 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          title="Déconnexion"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
