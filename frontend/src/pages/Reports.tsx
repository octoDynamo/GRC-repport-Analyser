import type { ChangeEvent, FormEvent } from 'react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileUp, FileText, Loader2, Play, AlertCircle, Trash2 } from 'lucide-react';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { api } from '../services/api';
import type { Rapport } from '../types';
import { useReportStore } from '../store/reportStore';

export function Reports() {
  const navigate = useNavigate();
  const { reportList, setReports } = useReportStore();
  
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');

  const fetchReports = async () => {
    try {
      const response = await api.get<{ data: Rapport[] }>('/rapports');
      setReports(response.data.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;

    // Use extension-based validation because MIME can be empty/inconsistent across browsers/OS.
    const extension = file.name.split('.').pop()?.toLowerCase();
    const allowedExtensions = ['pdf', 'docx', 'xlsx'];
    if (!extension || !allowedExtensions.includes(extension)) {
      setError('Format invalide. PDF, DOCX ou XLSX uniquement.');
      return;
    }

    setUploading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post<{ data: Rapport }>('/rapports/upload', formData);
      await fetchReports();
      setFile(null);
      // Reset input
      const input = document.getElementById('file-upload') as HTMLInputElement;
      if (input) input.value = '';
    } catch (err: any) {
      const backendDetail =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        (Array.isArray(err.response?.data?.detail) ? err.response.data.detail[0]?.msg : null);
      setError(backendDetail || 'Erreur lors de l\'upload');
    } finally {
      setUploading(false);
    }
  };

  const goToAnalysis = async (rapportId: string) => {
    try {
      const analysesList = await api.get<{ data: any[] }>(`/analyses/rapport/${rapportId}`);
      const analyses = analysesList.data.data;
      if (analyses && analyses.length > 0) {
        navigate(`/analysis/${analyses[0].id}`);
      } else {
        alert("Aucune analyse trouvée pour ce rapport.");
      }
    } catch (err) {
      console.error(err);
      alert("Erreur lors de la récupération de l'analyse.");
    }
  };

  const launchAnalysis = async (rapportId: string) => {
    try {
      const response = await api.post<{ data: { analyse_id: string } }>(`/analyses/lancer/${rapportId}`);
      // Optimistically fetch reports to show "en_cours"
      fetchReports();
      // Navigate to analysis page
      navigate(`/analysis/${response.data.data.analyse_id}`);
    } catch (err) {
      console.error(err);
      alert('Erreur lors du lancement de l\'analyse');
    }
  };

  const handleDeleteReport = async (rapportId: string) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce rapport et toutes ses analyses ?')) return;
    try {
      await api.delete(`/rapports/${rapportId}`);
      fetchReports();
    } catch (err) {
      console.error(err);
      alert('Erreur lors de la suppression du rapport');
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Rapports</h2>
          <p className="text-muted-foreground mt-2">
            Gérez vos documents GRC et lancez de nouvelles analyses via Mistral AI.
          </p>
        </div>
      </div>

      {/* Upload Section */}
      <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4">Nouveau Rapport</h3>
        <form onSubmit={handleUpload} className="flex flex-col md:flex-row items-end gap-4">
          <div className="flex-1 w-full space-y-2">
            <label htmlFor="file-upload" className="text-sm font-medium">Sélectionnez un fichier (PDF, DOCX, XLSX)</label>
            <input
              id="file-upload"
              type="file"
              onChange={handleFileChange}
              accept=".pdf,.docx,.xlsx"
              className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm text-foreground file:border-0 file:bg-transparent file:text-foreground file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
          <button
            type="submit"
            disabled={!file || uploading}
            className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-8 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
          >
            {uploading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileUp className="mr-2 h-4 w-4" />}
            Uploader
          </button>
        </form>
        {error && <p className="text-destructive text-sm flex items-center mt-3"><AlertCircle className="w-4 h-4 mr-1"/>{error}</p>}
      </div>

      {/* Reports List */}
      <div className="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
        <div className="p-6 border-b">
          <h3 className="font-semibold text-lg">Vos Documents</h3>
        </div>
        {loading ? (
          <div className="p-8 flex justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
        ) : reportList.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-4 opacity-20" />
            <p>Aucun rapport uploadé pour le moment.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-muted/50">
                <tr>
                  <th className="px-6 py-3">Nom du fichier</th>
                  <th className="px-6 py-3">Format</th>
                  <th className="px-6 py-3">Date</th>
                  <th className="px-6 py-3">Statut</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {reportList.map((r) => (
                  <tr key={r.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-6 py-4 font-medium flex items-center gap-3">
                      <FileText className="h-5 w-5 text-primary/60" />
                      {r.nom}
                    </td>
                    <td className="px-6 py-4 uppercase text-xs font-semibold">{r.format}</td>
                    <td className="px-6 py-4 text-muted-foreground">
                      {format(new Date(r.created_at), 'dd MMM yyyy', { locale: fr })}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        r.statut === 'termine' ? 'bg-emerald-100 text-emerald-800' :
                        r.statut === 'en_cours' ? 'bg-amber-100 text-amber-800' :
                        r.statut === 'erreur' ? 'bg-red-100 text-red-800' :
                        'bg-slate-100 text-slate-800'
                      }`}>
                        {r.statut.toUpperCase().replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right flex items-center justify-end gap-2">
                      {r.statut === 'en_attente' || r.statut === 'erreur' ? (
                        <button
                          onClick={() => launchAnalysis(r.id)}
                          className="inline-flex h-8 items-center justify-center rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 px-3 text-xs font-medium"
                        >
                          <Play className="h-3 w-3 mr-1" /> Analyser
                        </button>
                      ) : r.statut === 'termine' ? (
                        <button
                          onClick={() => goToAnalysis(r.id)}
                          className="inline-flex h-8 items-center justify-center rounded-md border text-foreground hover:bg-muted px-3 text-xs font-medium"
                        >
                          Voir l'Analyse
                        </button>
                      ) : (
                        <span className="text-xs text-muted-foreground flex items-center justify-end"><Loader2 className="h-3 w-3 animate-spin mr-1"/> En cours</span>
                      )}
                      <button
                        onClick={() => handleDeleteReport(r.id)}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md text-destructive hover:bg-destructive/10 transition-colors"
                        title="Supprimer ce rapport"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
