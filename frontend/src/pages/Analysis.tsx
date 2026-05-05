import type { FormEvent } from 'react';
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import * as Tabs from '@radix-ui/react-tabs';
import { 
  Loader2, 
  ShieldAlert, 
  CheckCircle, 
  ListTodo, 
  MessageSquare,
  FileQuestion,
  Download,
  AlertTriangle,
  Send,
  Bot
} from 'lucide-react';
import { api } from '../services/api';
import type { Analyse, Risque, Conformite, Recommandation } from '../types';
import { RiskMatrix } from '../components/risks/RiskMatrix';
import { ComplianceRadar } from '../components/compliance/ComplianceRadar';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function Analysis() {
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [analyse, setAnalyse] = useState<Analyse | null>(null);
  const [risques, setRisques] = useState<Risque[]>([]);
  const [conformites, setConformites] = useState<Conformite[]>([]);
  const [recommandations, setRecommandations] = useState<Recommandation[]>([]);
  
  // Chat state
  const [chatQuestion, setChatQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState<{role: 'user'|'bot', content: string}[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => {
    if (!id) return;

    let pollInterval: ReturnType<typeof setInterval> | null = null;

    const fetchAll = async () => {
      try {
        const aRes = await api.get<{data: Analyse}>(`/analyses/${id}`);
        const currentAnalyse = aRes.data.data;
        setAnalyse(currentAnalyse);

        if (currentAnalyse && (currentAnalyse.statut === 'termine' || currentAnalyse.statut === 'COMPLETED')) {
          // Analysis done — fetch sub-resources and stop polling
          if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
          }
          const [rRes, cRes, recRes] = await Promise.all([
            api.get<{data: Risque[]}>(`/analyses/${id}/risks`),
            api.get<{data: Conformite[]}>(`/analyses/${id}/conformite`),
            api.get<{data: Recommandation[]}>(`/analyses/${id}/recommandations`),
          ]);
          setRisques(rRes.data.data);
          setConformites(cRes.data.data);
          setRecommandations(recRes.data.data);
        } else if (currentAnalyse && currentAnalyse.statut === 'erreur') {
          if (pollInterval) clearInterval(pollInterval);
        }
        // else still in progress — keep polling
      } catch (err) {
        console.error("Failed to load analysis details", err);
        if (pollInterval) clearInterval(pollInterval);
      } finally {
        setLoading(false);
      }
    };

    // First immediate fetch
    fetchAll();

    // Then poll every 4 seconds while the analysis might still be running
    pollInterval = setInterval(fetchAll, 4000);

    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [id]);

  const downloadBlob = async (path: string, filename: string, mimeType: string) => {
    try {
      const resp = await api.get(path, { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([resp.data], { type: mimeType }));
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert('Erreur lors du téléchargement du rapport.');
    }
  };

  const handleExportPdf = () =>
    downloadBlob(`/export/${id}/pdf`, `analyse_${id}.pdf`, 'application/pdf');

  const handleExportExcel = () =>
    downloadBlob(
      `/export/${id}/excel`,
      `analyse_${id}.xlsx`,
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    );

  const handleChat = async (e: FormEvent) => {
    e.preventDefault();
    if (!chatQuestion.trim()) return;

    const q = chatQuestion;
    setChatQuestion('');
    setChatHistory((prev: {role: 'user'|'bot', content: string}[]) => [...prev, { role: 'user', content: q }]);
    setChatLoading(true);

    try {
      const resp = await api.post<{data: {reponse: string, sources: string[]}}>(`/chat/${id}`, { question: q });
      setChatHistory((prev: {role: 'user'|'bot', content: string}[]) => [
        ...prev, 
        { role: 'bot', content: resp.data.data.reponse }
      ]);
    } catch (err) {
      setChatHistory((prev: {role: 'user'|'bot', content: string}[]) => [...prev, { role: 'bot', content: "Désolé, une erreur technique s'est produite." }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Status updates mapping for Recommendations
  const toggleRecStatus = async (recId: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'A_FAIRE' ? 'EN_COURS' : currentStatus === 'EN_COURS' ? 'CLOTURE' : 'A_FAIRE';
    try {
      await api.patch(`/recommandations/${recId}/statut`, { statut: nextStatus });
      setRecommandations((prev: Recommandation[]) => prev.map((r: Recommandation) => r.id === recId ? { ...r, statut: nextStatus as any } : r));
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center space-x-2">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="text-lg font-medium text-muted-foreground">Chargement de l'analyse en cours...</span>
      </div>
    );
  }

  if (!analyse) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-muted-foreground">
        <FileQuestion className="h-16 w-16 mb-4 opacity-50" />
        <h3 className="text-xl font-semibold">Analyse Introuvable</h3>
      </div>
    );
  }

  if (analyse.statut === 'en_cours') {
    return (
      <div className="flex flex-col h-full items-center justify-center text-center p-8">
        <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center mb-6">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight mb-2">Analyse IA en cours</h2>
        <p className="text-muted-foreground max-w-md">
          Mistral est en train d'analyser le document. L'extraction des risques, 
          l'évaluation de conformité et la génération des recommandations 
          peuvent prendre quelques instants.
        </p>
        <button 
          onClick={() => window.location.reload()}
          className="mt-8 rounded-md bg-secondary text-secondary-foreground px-4 py-2 text-sm font-medium hover:bg-secondary/80 transition-colors"
        >
          Rafraîchir la page
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-20">
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Résultats de l'Analyse</h2>
          <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
            Créée le {format(new Date(analyse.created_at), 'dd MMMM yyyy à HH:mm', { locale: fr })}
            <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
              Score Maturité: {analyse.score_maturite || 0}%
            </span>
          </p>
        </div>
        <div className="flex gap-3">
          <button onClick={handleExportExcel} className="inline-flex h-9 items-center justify-center rounded-md border bg-transparent px-4 text-sm font-medium hover:bg-muted transition-colors">
            <Download className="mr-2 h-4 w-4" /> Excel
          </button>
          <button onClick={handleExportPdf} className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors shadow">
            <Download className="mr-2 h-4 w-4" /> PDF
          </button>
        </div>
      </div>

      <Tabs.Root defaultValue="resume" className="w-full">
        <Tabs.List className="flex w-full space-x-2 border-b overflow-x-auto pb-px">
          <Tabs.Trigger value="resume" className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:text-primary text-muted-foreground hover:text-foreground hover:border-muted transition-colors whitespace-nowrap">
            <CheckCircle className="h-4 w-4" /> Résumé Exécutif
          </Tabs.Trigger>
          <Tabs.Trigger value="risques" className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:text-primary text-muted-foreground hover:text-foreground hover:border-muted transition-colors whitespace-nowrap">
            <ShieldAlert className="h-4 w-4" /> Cartographie des Risques ({risques.length})
          </Tabs.Trigger>
          <Tabs.Trigger value="conformite" className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:text-primary text-muted-foreground hover:text-foreground hover:border-muted transition-colors whitespace-nowrap">
            <CheckCircle className="h-4 w-4" /> Conformités ({conformites.length})
          </Tabs.Trigger>
          <Tabs.Trigger value="recommandations" className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:text-primary text-muted-foreground hover:text-foreground hover:border-muted transition-colors whitespace-nowrap">
            <ListTodo className="h-4 w-4" /> Plan d'Action ({recommandations.length})
          </Tabs.Trigger>
          <Tabs.Trigger value="chat" className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:text-primary text-muted-foreground hover:text-foreground hover:border-muted transition-colors whitespace-nowrap">
            <MessageSquare className="h-4 w-4" /> Assistant RAG
          </Tabs.Trigger>
        </Tabs.List>

        <div className="mt-6">
          {/* TAB: Résumé */}
          <Tabs.Content value="resume" className="animate-in fade-in zoom-in-95 duration-200 outline-none">
            <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-8 prose prose-slate dark:prose-invert max-w-none">
              <h3 className="text-xl font-bold mb-6 border-b pb-2">Résumé généré par l'IA</h3>
              {analyse.resume_executif ? (
                <div className="whitespace-pre-wrap leading-relaxed">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {analyse.resume_executif}
                  </ReactMarkdown>
                </div>
              ) : (
                <p className="text-muted-foreground">Aucun résumé disponible.</p>
              )}
            </div>
          </Tabs.Content>

          {/* TAB: Risques */}
          <Tabs.Content value="risques" className="animate-in fade-in zoom-in-95 duration-200 outline-none space-y-6">
            {risques.length > 0 && <RiskMatrix risks={risques} />}
            <div className="rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-muted/50 border-b text-xs uppercase font-semibold text-muted-foreground">
                    <tr>
                      <th className="px-6 py-4">Risque</th>
                      <th className="px-6 py-4">Catégorie</th>
                      <th className="px-6 py-4 text-center">Score (P×I)</th>
                      <th className="px-6 py-4">Sévérité</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y relative">
                    {risques.map((r) => (
                      <tr key={r.id} className="hover:bg-muted/20 transition-colors group">
                        <td className="px-6 py-4">
                          <div className="font-medium">{r.libelle}</div>
                          <div className="text-xs text-muted-foreground mt-1 line-clamp-2 max-w-lg">{r.description}</div>
                        </td>
                        <td className="px-6 py-4 font-medium text-xs">{r.categorie}</td>
                        <td className="px-6 py-4 text-center">
                          <span className="inline-flex font-mono items-center justify-center w-8 h-8 rounded-full bg-secondary text-sm font-bold">
                            {r.score_risque}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold ${
                            r.severite === 'CRITIQUE' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                            r.severite === 'ELEVE' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
                            r.severite === 'MOYEN' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-500' :
                            'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400'
                          }`}>
                            {r.severite === 'CRITIQUE' && <AlertTriangle className="h-3 w-3" />}
                            {r.severite}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {risques.length === 0 && (
                      <tr><td colSpan={4} className="px-6 py-8 text-center text-muted-foreground">Aucun risque extrait.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </Tabs.Content>

          {/* TAB: Conformité */}
          <Tabs.Content value="conformite" className="animate-in fade-in zoom-in-95 duration-200 outline-none">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {['ISO27001', 'RGPD', 'LOI0908'].map((ref) => {
                const cfgs = conformites.filter((c: Conformite) => c.referentiel === ref);
                const avg = cfgs.length ? Math.round(cfgs.reduce((acc: number, c: Conformite) => acc + c.taux_conformite, 0) / cfgs.length) : 0;
                
                return (
                  <div key={ref} className="rounded-xl border bg-card text-card-foreground shadow-sm flex flex-col overflow-hidden">
                    <div className="bg-muted/40 p-5 border-b flex justify-between items-center">
                      <h3 className="font-bold tracking-tight">{ref === 'LOI0908' ? 'Loi 09-08' : ref}</h3>
                      <div className="flex items-center justify-center w-12 h-12 rounded-full border-4 border-primary text-sm font-bold shadow-sm bg-card">
                        {avg}%
                      </div>
                    </div>
                    <div className="p-0 flex-1 flex flex-col divide-y">
                      {cfgs.map((c: Conformite) => (
                        <div key={c.id} className="p-4 flex flex-col gap-2 relative group hover:bg-muted/10 transition-colors">
                          <div className="flex justify-between items-start">
                            <span className="font-medium text-sm line-clamp-1 flex-1 pr-2" title={c.domaine || ''}>
                              {c.domaine || 'Domaine Global'}
                            </span>
                            <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                              c.statut === 'CONFORME' ? 'bg-emerald-100 text-emerald-700' : 
                              c.statut === 'PARTIEL' ? 'bg-amber-100 text-amber-700' : 
                              'bg-red-100 text-red-700'
                            }`}>
                              {c.statut.replace('_', ' ')}
                            </span>
                          </div>
                          {c.ecart && c.statut !== 'CONFORME' && (
                            <p className="text-xs text-muted-foreground line-clamp-2 mt-1 border-l-2 border-red-300 pl-2">
                              {c.ecart}
                            </p>
                          )}
                        </div>
                      ))}
                      {cfgs.length === 0 && <div className="p-6 text-center text-sm text-muted-foreground">Données non disponibles</div>}
                    </div>
                    {cfgs.length > 0 && <ComplianceRadar conformites={conformites} referentiel={ref} />}
                  </div>
                );
              })}
            </div>
          </Tabs.Content>

          {/* TAB: Recommandations */}
          <Tabs.Content value="recommandations" className="animate-in fade-in zoom-in-95 duration-200 outline-none space-y-4">
             <div className="grid gap-4 grid-cols-1">
              {recommandations.map((rec: Recommandation) => (
                <div key={rec.id} className="rounded-xl border bg-card text-card-foreground shadow-sm p-5 flex flex-col md:flex-row md:items-center gap-6 group hover:border-primary/50 transition-colors">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        rec.priorite === 'CRITIQUE' ? 'bg-red-500 text-white' :
                        rec.priorite === 'HAUTE' ? 'bg-orange-500 text-white' :
                        rec.priorite === 'MOYENNE' ? 'bg-amber-500 text-white' : 'bg-emerald-500 text-white'
                      }`}>
                        {rec.priorite}
                      </span>
                      <span className="text-[10px] font-semibold tracking-wider text-muted-foreground uppercase border px-2 py-0.5 rounded">
                        {rec.type_action.replace('_', ' ')}
                      </span>
                      <span className="text-[10px] font-semibold tracking-wider text-muted-foreground uppercase border px-2 py-0.5 rounded">
                        Effort: {rec.effort_estime}
                      </span>
                    </div>
                    <h4 className="font-semibold text-base">{rec.libelle}</h4>
                    <div className="text-sm text-muted-foreground max-w-3xl leading-relaxed prose prose-sm dark:prose-invert">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{rec.description}</ReactMarkdown>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4 shrink-0 border-t md:border-t-0 md:border-l pt-4 md:pt-0 md:pl-6">
                    <button 
                      onClick={() => toggleRecStatus(rec.id, rec.statut)}
                      className={`px-4 py-2 w-32 rounded-md border text-sm font-semibold transition-all shadow-sm ${
                        rec.statut === 'CLOTURE' ? 'bg-emerald-50 border-emerald-200 text-emerald-700 hover:bg-emerald-100' :
                        rec.statut === 'EN_COURS' ? 'bg-amber-50 border-amber-200 text-amber-700 hover:bg-amber-100' :
                        'bg-background hover:bg-muted text-muted-foreground'
                      }`}
                    >
                      {rec.statut.replace('_', ' ')}
                    </button>
                  </div>
                </div>
              ))}
              {recommandations.length === 0 && (
                <div className="rounded-xl border p-12 text-center text-muted-foreground">
                  Aucune recommandation générée.
                </div>
              )}
             </div>
          </Tabs.Content>

          {/* TAB: Chat RAG */}
          <Tabs.Content value="chat" className="animate-in fade-in zoom-in-95 duration-200 outline-none h-[600px] flex flex-col rounded-xl border bg-card text-card-foreground shadow-sm overflow-hidden">
            <div className="bg-primary/5 border-b p-4 flex items-center gap-3">
              <Bot className="h-6 w-6 text-primary" />
              <div>
                <h3 className="font-bold">Assistant RAG Mistral</h3>
                <p className="text-xs text-muted-foreground">Posez vos questions sur le contenu exact de ce rapport.</p>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50 dark:bg-background/50">
              {chatHistory.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground opacity-60">
                  <MessageSquare className="h-12 w-12 mb-4" />
                  <p>Posez-moi une question sur les risques ou la conformité de ce rapport.</p>
                </div>
              ) : (
                chatHistory.map((msg: {role: 'user'|'bot', content: string}, i: number) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-2xl px-5 py-3 ${
                      msg.role === 'user' 
                        ? 'bg-primary text-primary-foreground tabular-nums rounded-tr-sm shadow-sm' 
                        : 'bg-card border text-foreground rounded-tl-sm shadow-sm leading-relaxed prose prose-sm dark:prose-invert max-w-none'
                    }`}>
                      {msg.role === 'user' ? msg.content : (
                        <div className="whitespace-pre-wrap">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
              {chatLoading && (
                <div className="flex justify-start">
                  <div className="bg-card border text-muted-foreground rounded-2xl rounded-tl-sm px-5 py-3 flex items-center gap-2 shadow-sm">
                    <Loader2 className="h-4 w-4 animate-spin" /> Mistral réfléchit...
                  </div>
                </div>
              )}
            </div>
            
            <div className="p-4 bg-background border-t">
              <form onSubmit={handleChat} className="flex gap-2">
                <input 
                  type="text" 
                  value={chatQuestion}
                  onChange={(e) => setChatQuestion(e.target.value)}
                  placeholder="Posez votre question ici..."
                  disabled={chatLoading}
                  className="flex-1 rounded-full border border-input bg-transparent px-4 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary disabled:opacity-50"
                  required
                />
                <button 
                  type="submit" 
                  disabled={chatLoading || !chatQuestion.trim()}
                  className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground hover:bg-primary/90 shadow transition-colors disabled:opacity-50"
                >
                  <Send className="h-4 w-4 ml-0.5" />
                </button>
              </form>
            </div>
          </Tabs.Content>

        </div>
      </Tabs.Root>
    </div>
  );
}
