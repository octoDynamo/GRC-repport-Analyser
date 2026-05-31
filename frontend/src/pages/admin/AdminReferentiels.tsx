import { useEffect, useState } from 'react';
import { ShieldCheck, Save, ToggleLeft, ToggleRight, Info } from 'lucide-react';
import { adminApi } from '../../services/api';
import type { ReferentielConfig } from '../../types';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

const REF_META: Record<string, { label: string; color: string; bg: string; border: string }> = {
  ISO27001: { label: 'ISO 27001', color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
  RGPD:     { label: 'RGPD',     color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200' },
  LOI0908:  { label: 'Loi 09-08', color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' },
};

interface Draft {
  actif: boolean;
  seuil_conformite: number;
  description: string;
}

export function AdminReferentiels() {
  const [configs, setConfigs] = useState<ReferentielConfig[]>([]);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const data = await adminApi.getReferentiels();
      setConfigs(data);
      const d: Record<string, Draft> = {};
      data.forEach(c => {
        d[c.referentiel] = { actif: c.actif, seuil_conformite: c.seuil_conformite, description: c.description ?? '' };
      });
      setDrafts(d);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleSave = async (ref: string) => {
    setError('');
    setSaving(ref);
    try {
      await adminApi.updateReferentiel(ref, drafts[ref]);
      setSaved(ref);
      setTimeout(() => setSaved(null), 2000);
      await load();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(null);
    }
  };

  const setDraft = (ref: string, patch: Partial<Draft>) => {
    setDrafts(prev => ({ ...prev, [ref]: { ...prev[ref], ...patch } }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 text-muted-foreground text-sm">
        Chargement…
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-emerald-100 p-2">
          <ShieldCheck className="h-5 w-5 text-emerald-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Configuration des référentiels</h1>
          <p className="text-sm text-muted-foreground">Activez ou désactivez les frameworks de conformité et définissez les seuils.</p>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-5">
        {configs.map((c) => {
          const meta = REF_META[c.referentiel];
          const draft = drafts[c.referentiel];
          if (!draft) return null;
          const isDirty =
            draft.actif !== c.actif ||
            draft.seuil_conformite !== c.seuil_conformite ||
            draft.description !== (c.description ?? '');

          return (
            <div key={c.referentiel} className={`rounded-xl border-2 bg-card shadow-sm overflow-hidden ${draft.actif ? meta.border : 'border-border'}`}>
              {/* Card header */}
              <div className={`flex items-center justify-between px-6 py-4 ${draft.actif ? meta.bg : 'bg-muted/30'}`}>
                <div className="flex items-center gap-3">
                  <span className={`text-lg font-bold ${draft.actif ? meta.color : 'text-muted-foreground'}`}>
                    {meta.label}
                  </span>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${draft.actif ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {draft.actif ? 'Actif' : 'Inactif'}
                  </span>
                </div>
                <button
                  onClick={() => setDraft(c.referentiel, { actif: !draft.actif })}
                  className="transition-colors"
                  title={draft.actif ? 'Désactiver' : 'Activer'}
                >
                  {draft.actif
                    ? <ToggleRight className={`h-8 w-8 ${meta.color}`} />
                    : <ToggleLeft className="h-8 w-8 text-muted-foreground" />
                  }
                </button>
              </div>

              {/* Card body */}
              <div className="px-6 py-5 space-y-4">
                {/* Description */}
                <div>
                  <label className="flex items-center gap-1.5 text-sm font-medium mb-1.5">
                    <Info className="h-3.5 w-3.5 text-muted-foreground" /> Description
                  </label>
                  <textarea
                    value={draft.description}
                    onChange={e => setDraft(c.referentiel, { description: e.target.value })}
                    rows={2}
                    className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary bg-background resize-none"
                  />
                </div>

                {/* Threshold */}
                <div className="flex items-end gap-4">
                  <div className="flex-1">
                    <label className="block text-sm font-medium mb-1.5">
                      Seuil de conformité : <span className={`font-bold ${meta.color}`}>{draft.seuil_conformite}%</span>
                    </label>
                    <input
                      type="range" min={0} max={100} step={5}
                      value={draft.seuil_conformite}
                      onChange={e => setDraft(c.referentiel, { seuil_conformite: Number(e.target.value) })}
                      className="w-full accent-primary"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground mt-0.5">
                      <span>0%</span><span>50%</span><span>100%</span>
                    </div>
                  </div>
                  <div className="text-right text-xs text-muted-foreground pb-5 whitespace-nowrap">
                    Mis à jour le<br />
                    {format(new Date(c.updated_at), 'dd MMM yyyy', { locale: fr })}
                  </div>
                </div>

                {/* Save button */}
                <div className="flex justify-end pt-1">
                  <button
                    onClick={() => handleSave(c.referentiel)}
                    disabled={!isDirty || saving === c.referentiel}
                    className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors
                      ${saved === c.referentiel
                        ? 'bg-green-100 text-green-700'
                        : isDirty
                          ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                          : 'bg-muted text-muted-foreground cursor-not-allowed'
                      }`}
                  >
                    <Save className="h-4 w-4" />
                    {saving === c.referentiel ? 'Sauvegarde…' : saved === c.referentiel ? 'Sauvegardé ✓' : 'Sauvegarder'}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
