import { useEffect, useState } from 'react';
import { FileText, CheckCircle, ShieldAlert, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import type { Rapport } from '../types';
import { KPICard } from '../components/dashboard/KPICard';
import { ScoreGauge } from '../components/dashboard/ScoreGauge';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

interface ConformiteScore {
  referentiel: string;
  taux_conformite: number;
}

interface AnalyseResult {
  conformites?: ConformiteScore[];
  risques?: { severite: string }[];
}

export function Dashboard() {
  const navigate = useNavigate();
  const [reports, setReports] = useState<Rapport[]>([]);
  const [loading, setLoading] = useState(true);
  const [avgIso, setAvgIso] = useState<number | null>(null);
  const [avgRgpd, setAvgRgpd] = useState<number | null>(null);
  const [avgLoi, setAvgLoi] = useState<number | null>(null);
  const [criticalRisks, setCriticalRisks] = useState(0);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await api.get<{ data: Rapport[] }>('/rapports');
        const fetchedReports: Rapport[] = response.data.data ?? [];
        setReports(fetchedReports);

        // Fetch analyses for completed reports to compute real averages
        const completedReports = fetchedReports.filter(r => r.statut === 'termine');

        if (completedReports.length === 0) {
          // No data yet — leave gauges null (will show placeholder)
          return;
        }

        const analysesData: AnalyseResult[] = await Promise.all(
          completedReports.map(async (r) => {
            try {
              // Get the analysis ID for this report
              const analysesList = await api.get<{ data: any[] }>(`/analyses/rapport/${r.id}`);
              const analyses = analysesList.data.data;
              if (analyses.length > 0) {
                const analyseId = analyses[0].id;
                const [confRes, riskRes] = await Promise.all([
                  api.get<{ data: ConformiteScore[] }>(`/analyses/${analyseId}/conformite`).catch(() => ({ data: { data: [] } })),
                  api.get<{ data: { severite: string }[] }>(`/analyses/${analyseId}/risks`).catch(() => ({ data: { data: [] } }))
                ]);
                
                return {
                  conformites: confRes.data.data,
                  risques: riskRes.data.data
                };
              }
              return {};
            } catch (err) {
              console.error(err);
              return {};
            }
          })
        );

        // Compute average compliance scores per framework
        const isoScores: number[] = [];
        const rgpdScores: number[] = [];
        const loiScores: number[] = [];
        let critical = 0;

        for (const analyse of analysesData) {
          if (analyse.conformites) {
            for (const c of analyse.conformites) {
              const fw = c.referentiel?.toUpperCase() ?? '';
              if (fw.includes('ISO')) isoScores.push(c.taux_conformite);
              if (fw.includes('RGPD') || fw.includes('GDPR')) rgpdScores.push(c.taux_conformite);
              if (fw.includes('LOI') || fw.includes('09')) loiScores.push(c.taux_conformite);
            }
          }
          if (analyse.risques) {
            critical += analyse.risques.filter(
              r => r.severite?.toUpperCase() === 'CRITIQUE' || r.severite?.toUpperCase() === 'CRITICAL'
            ).length;
          }
        }

        const avg = (arr: number[]) => arr.length > 0 ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : null;

        setAvgIso(avg(isoScores));
        setAvgRgpd(avg(rgpdScores));
        setAvgLoi(avg(loiScores));
        setCriticalRisks(critical);

      } catch (error) {
        console.error('Failed to fetch reports:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

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

  const completed = reports.filter(r => r.statut === 'termine').length;
  const pending = reports.filter(r => r.statut === 'en_cours' || r.statut === 'en_attente').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Activity className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const noData = reports.length === 0;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Tableau de bord</h2>
        <p className="text-muted-foreground mt-2">
          Vue d'ensemble de vos analyses de conformité et risques GRC.
        </p>
      </div>

      {/* KPIs */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Rapports"
          value={reports.length}
          icon={<FileText />}
          description="Rapports uploadés"
        />
        <KPICard
          title="Analyses Terminées"
          value={completed}
          icon={<CheckCircle className="text-emerald-500" />}
        />
        <KPICard
          title="En Cours"
          value={pending}
          icon={<Activity className="text-amber-500 animate-pulse" />}
        />
        <KPICard
          title="Risques Critiques"
          value={criticalRisks}
          icon={<ShieldAlert className="text-destructive" />}
          description={criticalRisks > 0 ? "Nécessitant une action immédiate" : "Aucun risque critique"}
        />
      </div>

      {/* Charts / Gauges */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 col-span-3">
          <h3 className="font-semibold mb-6">Moyenne de Conformité Globale</h3>
          {noData ? (
            <p className="text-sm text-center text-muted-foreground py-8">
              Importez et analysez un rapport pour voir les scores de conformité.
            </p>
          ) : (
            <div className="flex flex-col md:flex-row justify-around items-center gap-8">
              <ScoreGauge score={avgIso ?? 0} title="ISO 27001" />
              <ScoreGauge score={avgRgpd ?? 0} title="RGPD" />
              <ScoreGauge score={avgLoi ?? 0} title="Loi 09-08" />
            </div>
          )}
        </div>
      </div>

      {/* Recent activity */}
      <div className="rounded-xl border bg-card text-card-foreground shadow-sm">
        <div className="p-6 border-b">
          <h3 className="font-semibold">Activité Récente</h3>
        </div>
        <div className="p-6">
          {reports.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground/40 mb-3" />
              <p className="text-sm text-muted-foreground">
                Aucun rapport trouvé. Commencez par importer un document GRC.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {reports.slice(0, 5).map((report) => (
                <div key={report.id} className="flex items-center justify-between p-4 rounded-lg border bg-muted/20">
                  <div className="flex items-center gap-4">
                    <FileText className="h-8 w-8 text-primary/70" />
                    <div>
                      <p className="font-medium">{report.nom}</p>
                      <p className="text-xs text-muted-foreground">
                        {format(new Date(report.created_at), 'dd MMM yyyy HH:mm', { locale: fr })}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2 items-center">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      report.statut === 'termine' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400' :
                      report.statut === 'en_cours' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
                      report.statut === 'erreur' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                      'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-400'
                    }`}>
                      {report.statut.toUpperCase()}
                    </span>
                    {report.statut === 'termine' && (
                      <button
                        onClick={() => goToAnalysis(report.id)}
                        className="inline-flex h-8 items-center justify-center rounded-md border text-foreground hover:bg-muted px-3 text-xs font-medium"
                      >
                        Voir
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
