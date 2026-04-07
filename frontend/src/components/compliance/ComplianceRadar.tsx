import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';
import type { Conformite } from '../../types';

interface ComplianceRadarProps {
  conformites: Conformite[];
  referentiel: string;
}

export function ComplianceRadar({ conformites, referentiel }: ComplianceRadarProps) {
  const filtered = conformites.filter(c => c.referentiel === referentiel);
  if (filtered.length === 0) return null;

  const data = filtered.map(c => ({
    domaine: c.domaine?.slice(0, 15) + (c.domaine && c.domaine.length > 15 ? '...' : '') || 'Global',
    taux: c.taux_conformite,
    full_name: c.domaine || 'Global'
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-popover text-popover-foreground border px-3 py-2 rounded-lg shadow-sm">
          <p className="font-semibold text-sm mb-1">{payload[0].payload.full_name}</p>
          <p className="text-primary text-xs font-bold">{payload[0].value}% conforme</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-[300px] w-full mt-4 bg-muted/20 rounded-xl p-2">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="domaine" tick={{ fontSize: 10, fill: '#64748b' }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} />
          <Tooltip content={<CustomTooltip />} />
          <Radar name={referentiel} dataKey="taux" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
