import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, Cell, CartesianGrid } from 'recharts';
import type { Risque } from '../../types';

interface RiskMatrixProps {
  risks: Risque[];
}

export function RiskMatrix({ risks }: RiskMatrixProps) {
  // Group risks by (impact, probabilite)
  // X = Impact (1-5), Y = Probability (1-5)
  // Z = Bubble size (count of risks in that cell)
  
  const matrix: Record<string, any> = {};
  
  // Initialize 5x5 grid
  for (let i = 1; i <= 5; i++) {
    for (let p = 1; p <= 5; p++) {
      matrix[`${i}-${p}`] = { x: i, y: p, z: 0, risks: [] };
    }
  }

  risks.forEach((r) => {
    const key = `${r.impact}-${r.probabilite}`;
    if (matrix[key]) {
      matrix[key].z += 40; // Bubble size multiplier
      matrix[key].risks.push(r.libelle);
    }
  });

  const data = Object.values(matrix).filter((d) => d.z > 0);

  const getCellColor = (x: number, y: number) => {
    const score = x * y;
    if (score >= 20) return '#ef4444'; // CRITICAL
    if (score >= 12) return '#f59e0b'; // HIGH
    if (score >= 6) return '#eab308'; // MEDIUM
    return '#10b981'; // LOW
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const { x, y, risks } = payload[0].payload;
      return (
        <div className="bg-popover text-popover-foreground border p-3 rounded-lg shadow-md w-64">
          <p className="font-bold mb-1 border-b pb-1">Impact: {x} | Probabilité: {y}</p>
          <ul className="text-xs list-disc pl-4 space-y-1">
            {risks.slice(0, 3).map((r: string, i: number) => <li key={i}>{r}</li>)}
            {risks.length > 3 && <li>... +{risks.length - 3} autres</li>}
          </ul>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-[400px] w-full p-4 bg-card rounded-xl border flex flex-col items-center">
      <h3 className="font-semibold text-sm text-muted-foreground w-full mb-4">Matrice des Risques</h3>
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" dataKey="x" name="Impact" domain={[0, 6]} ticks={[1,2,3,4,5]} label={{ value: 'Impact', position: 'insideBottom', offset: -10 }} />
          <YAxis type="number" dataKey="y" name="Probabilité" domain={[0, 6]} ticks={[1,2,3,4,5]} label={{ value: 'Probabilité', angle: -90, position: 'insideLeft' }} />
          <ZAxis type="number" dataKey="z" range={[50, 400]} name="Nombre de risques" />
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
          <Scatter name="Risques" data={data}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getCellColor(entry.x, entry.y)} opacity={0.8} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
