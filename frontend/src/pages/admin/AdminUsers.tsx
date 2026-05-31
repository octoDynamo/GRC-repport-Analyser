import { useEffect, useState } from 'react';
import { Users, Plus, Pencil, Trash2, X, Check, Shield, UserCheck } from 'lucide-react';
import { adminApi } from '../../services/api';
import type { AdminUser } from '../../types';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

const ROLE_BADGE: Record<string, string> = {
  ADMIN: 'bg-purple-100 text-purple-700',
  ANALYSTE: 'bg-blue-100 text-blue-700',
};

interface CreateForm {
  nom: string;
  email: string;
  password: string;
  role: string;
}

export function AdminUsers() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [editRole, setEditRole] = useState('');
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [form, setForm] = useState<CreateForm>({ nom: '', email: '', password: '', role: 'ANALYSTE' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      setUsers(await adminApi.getUsers());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await adminApi.createUser(form);
      setShowCreate(false);
      setForm({ nom: '', email: '', password: '', role: 'ANALYSTE' });
      await load();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la création');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateRole = async (id: string) => {
    setSaving(true);
    try {
      await adminApi.updateUser(id, { role: editRole });
      setEditId(null);
      await load();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    setSaving(true);
    try {
      await adminApi.deleteUser(deleteId);
      setDeleteId(null);
      await load();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la suppression');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-purple-100 p-2">
            <Users className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Gestion des utilisateurs</h1>
            <p className="text-sm text-muted-foreground">{users.length} utilisateur{users.length > 1 ? 's' : ''} enregistré{users.length > 1 ? 's' : ''}</p>
          </div>
        </div>
        <button
          onClick={() => { setShowCreate(true); setError(''); }}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" /> Nouvel utilisateur
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-center justify-between">
          {error}
          <button onClick={() => setError('')}><X className="h-4 w-4" /></button>
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-xl bg-background border shadow-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Créer un utilisateur</h2>
              <button onClick={() => setShowCreate(false)}><X className="h-5 w-5 text-muted-foreground" /></button>
            </div>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">Nom complet</label>
                <input required value={form.nom} onChange={e => setForm({ ...form, nom: e.target.value })}
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Jean Dupont" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input required type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="jean@entreprise.com" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Mot de passe</label>
                <input required type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="••••••••" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Rôle</label>
                <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}
                  className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-background">
                  <option value="ANALYSTE">ANALYSTE</option>
                  <option value="ADMIN">ADMIN</option>
                </select>
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <div className="flex gap-2 pt-1">
                <button type="button" onClick={() => setShowCreate(false)}
                  className="flex-1 rounded-lg border px-4 py-2 text-sm hover:bg-muted transition-colors">
                  Annuler
                </button>
                <button type="submit" disabled={saving}
                  className="flex-1 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors">
                  {saving ? 'Création…' : 'Créer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirmation */}
      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-xl bg-background border shadow-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-red-600">Confirmer la suppression</h2>
            <p className="text-sm text-muted-foreground">Cette action est irréversible. L'utilisateur et tous ses rapports seront supprimés.</p>
            <div className="flex gap-2">
              <button onClick={() => setDeleteId(null)}
                className="flex-1 rounded-lg border px-4 py-2 text-sm hover:bg-muted transition-colors">
                Annuler
              </button>
              <button onClick={handleDelete} disabled={saving}
                className="flex-1 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50 transition-colors">
                {saving ? 'Suppression…' : 'Supprimer'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16 text-muted-foreground text-sm">Chargement…</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/40">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Utilisateur</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Rôle</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Créé le</th>
                <th className="px-4 py-3 text-center font-medium text-muted-foreground">Rapports</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b last:border-0 hover:bg-muted/20 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-semibold text-xs">
                        {u.nom.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-foreground">{u.nom}</p>
                        <p className="text-xs text-muted-foreground">{u.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {editId === u.id ? (
                      <div className="flex items-center gap-1">
                        <select value={editRole} onChange={e => setEditRole(e.target.value)}
                          className="rounded border px-2 py-1 text-xs bg-background focus:outline-none focus:ring-1 focus:ring-primary">
                          <option value="ANALYSTE">ANALYSTE</option>
                          <option value="ADMIN">ADMIN</option>
                        </select>
                        <button onClick={() => handleUpdateRole(u.id)} className="p-1 text-green-600 hover:text-green-700">
                          <Check className="h-4 w-4" />
                        </button>
                        <button onClick={() => setEditId(null)} className="p-1 text-muted-foreground hover:text-foreground">
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${ROLE_BADGE[u.role]}`}>
                        {u.role === 'ADMIN' ? <Shield className="h-3 w-3" /> : <UserCheck className="h-3 w-3" />}
                        {u.role}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {format(new Date(u.created_at), 'dd MMM yyyy', { locale: fr })}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-medium">
                      {u.nb_rapports}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => { setEditId(u.id); setEditRole(u.role); }}
                        className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                        title="Modifier le rôle"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => setDeleteId(u.id)}
                        className="rounded p-1.5 text-muted-foreground hover:bg-red-50 hover:text-red-600 transition-colors"
                        title="Supprimer"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
