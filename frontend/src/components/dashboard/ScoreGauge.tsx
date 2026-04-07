import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface ScoreGaugeProps {
  score: number;
  title: string;
}

export function ScoreGauge({ score, title }: ScoreGaugeProps) {
  const data = [
    { name: 'Score', value: score },
    { name: 'Restant', value: 100 - score },
  ];

  const getColor = (val: number) => {
    if (val >= 80) return '#10b981'; // emerald
    if (val >= 50) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  const COLORS = [getColor(score), '#e2e8f0'];

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <h4 className="text-sm font-medium text-muted-foreground mb-4">{title}</h4>
      <div className="relative h-40 w-40">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              startAngle={180}
              endAngle={0}
              dataKey="value"
              stroke="none"
              cornerRadius={5}
            >
              {data.map((_entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value: number | undefined) => [`${value}%`]} />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center mt-6">
          <span className="text-3xl font-bold" style={{ color: getColor(score) }}>
            {score}%
          </span>
        </div>
      </div>
    </div>
  );
}
