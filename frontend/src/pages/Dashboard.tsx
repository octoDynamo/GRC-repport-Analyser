import { useEffect, useState } from 'react';
import { FileText, CheckCircle, ShieldAlert, Activity } from 'lucide-react';
import { api } from '../services/api';
import type { Rapport } from '../types';
import { KPICard } from '../components/dashboard/KPICard';
import { ScoreGauge } from '../components/dashboard/ScoreGauge';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

export function Dashboard() {
  const [reports, setReports] = useState<Rapport[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await api.get<{ data: Rapport[] }>('/rapports');
        setReports(response.data.data);
      } catch (error) {
        console.error('Failed to fetch reports:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  const completed = reports.filter(r => r.statut === 'termine').length;
  const pending = reports.filter(r => r.statut === 'en_cours' || r.statut === 'en_attente').length;
  
  // Mock average scores for the dashboard overview
  const avgIso = 78;
  const avgRgpd = 65;
  const avgLoi = 82;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Activity className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

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
          trend={{ value: 12, positive: true, label: "ce mois" }}
        />
        <KPICard
          title="En Cours"
          value={pending}
          icon={<Activity className="text-amber-500 animate-pulse" />}
        />
        <KPICard
          title="Risques Critiques"
          value={14}
          icon={<ShieldAlert className="text-destructive" />}
          description="Nécessitant une action immédiate"
        />
      </div>

      {/* Charts / Gauges */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border bg-card text-card-foreground shadow-sm p-6 col-span-3">
          <h3 className="font-semibold mb-6">Moyenne de Conformité Globale</h3>
          <div className="flex flex-col md:flex-row justify-around items-center gap-8">
            <ScoreGauge score={avgIso} title="ISO 27001" />
            <ScoreGauge score={avgRgpd} title="RGPD" />
            <ScoreGauge score={avgLoi} title="Loi 09-08" />
          </div>
        </div>
      </div>

      {/* Recent activity */}
      <div className="rounded-xl border bg-card text-card-foreground shadow-sm">
        <div className="p-6 border-b">
          <h3 className="font-semibold">Activité Récente</h3>
        </div>
        <div className="p-6">
          {reports.length === 0 ? (
            <p className="text-sm text-center text-muted-foreground py-8">Aucun rapport trouvé.</p>
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
                  <div>
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      report.statut === 'termine' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400' :
                      report.statut === 'en_cours' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
                      report.statut === 'erreur' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                      'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-400'
                    }`}>
                      {report.statut.toUpperCase()}
                    </span>
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
