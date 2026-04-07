import type { ReactNode } from 'react';
import { cn } from '../../lib/utils';

interface KPICardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  description?: string;
  trend?: {
    value: number;
    label: string;
    positive: boolean;
  };
  className?: string;
}

export function KPICard({ title, value, icon, description, trend, className }: KPICardProps) {
  return (
    <div className={cn("rounded-xl border bg-card text-card-foreground shadow-sm p-6 flex flex-col justify-between", className)}>
      <div className="flex items-center justify-between pb-2">
        <h3 className="tracking-tight text-sm font-medium text-muted-foreground">{title}</h3>
        <div className="h-4 w-4 text-muted-foreground">{icon}</div>
      </div>
      <div>
        <div className="text-3xl font-bold">{value}</div>
        {(description || trend) && (
          <p className="text-xs text-muted-foreground mt-1 flex items-center">
            {trend && (
              <span className={cn("mr-1 font-medium", trend.positive ? "text-emerald-500" : "text-destructive")}>
                {trend.positive ? '+' : ''}{trend.value}%
              </span>
            )}
            {description}
          </p>
        )}
      </div>
    </div>
  );
}
