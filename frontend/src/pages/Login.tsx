import type { FormEvent } from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Cpu, Lock, Mail, Loader2, ShieldCheck } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { api } from '../services/api';
import type { AuthResponse } from '../types';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post<{ data: AuthResponse; message: string; success: boolean }>('/auth/login', {
        email,
        password,
      });
      
      const { user, access_token } = response.data.data;
      setAuth(user, access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Une erreur est survenue lors de la connexion.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left side - Branding/Hero */}
      <div className="hidden w-1/2 flex-col justify-between bg-primary p-12 text-primary-foreground lg:flex relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80')] opacity-10 bg-cover bg-center mix-blend-overlay" />
        <div className="absolute inset-0 bg-gradient-to-t from-primary/90 to-primary/40" />
        
        <div className="relative z-10 flex items-center text-2xl font-bold tracking-tight">
          <Cpu className="mr-3 h-8 w-8 text-primary-foreground" />
          GRC AI Analyzer
        </div>
        
        <div className="relative z-10 space-y-4">
          <h1 className="text-4xl font-extrabold tracking-tight">Plateforme d'Analyse GRC Augmentée</h1>
          <p className="text-lg text-primary-foreground/80 max-w-md">
            Automatisez l'analyse de vos rapports de conformité, extrayez les risques, vérifiez l'alignement ISO 27001, RGPD et Loi 09-08 avec la puissance de Mistral AI.
          </p>
        </div>
        
        <div className="relative z-10 text-sm opacity-70">
          Projet de Fin d'Études © {new Date().getFullYear()}
        </div>
      </div>

      {/* Right side - Login Form */}
      <div className="flex w-full flex-col justify-center px-4 sm:px-12 lg:w-1/2 xl:px-24">
        <div className="mx-auto w-full max-w-md space-y-8">
          <div className="text-center lg:text-left">
            <div className="flex items-center justify-center lg:justify-start mb-6">
              <ShieldCheck className="h-10 w-10 text-primary" />
            </div>
            <h2 className="text-3xl font-bold tracking-tight">Connexion</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Veuillez saisir vos identifiants pour accéder à votre espace
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-md bg-destructive/15 p-4 text-sm text-destructive font-medium border border-destructive/20 animate-in fade-in slide-in-from-top-2">
                {error}
              </div>
            )}
            
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium leading-none" htmlFor="email">
                  Email professionnel
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="flex h-11 w-full rounded-md border border-input bg-transparent px-3 py-1 pl-10 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                    placeholder="analyste@entreprise.com"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium leading-none" htmlFor="password">
                  Mot de passe
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="flex h-11 w-full rounded-md border border-input bg-transparent px-3 py-1 pl-10 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    placeholder="••••••••"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="inline-flex w-full h-11 items-center justify-center rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Connexion en cours...
                </>
              ) : (
                'Se connecter'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
