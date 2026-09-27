import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export interface KpiCardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: {
    percentage: number;
    isPositive: boolean;
    periodText?: string;
  };
  icon: React.ReactNode;
  accentColor?: 'emerald' | 'teal' | 'indigo' | 'amber' | 'rose' | 'cyan';
  subtitle?: string;
  onClick?: () => void;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  unit,
  trend,
  icon,
  accentColor = 'emerald',
  subtitle,
  onClick,
}) => {
  const accentStyles = {
    emerald: 'border-emerald-500/20 bg-gradient-to-br from-emerald-950/30 via-slate-900 to-slate-950 text-emerald-400',
    teal: 'border-teal-500/20 bg-gradient-to-br from-teal-950/30 via-slate-900 to-slate-950 text-teal-400',
    indigo: 'border-indigo-500/20 bg-gradient-to-br from-indigo-950/30 via-slate-900 to-slate-950 text-indigo-400',
    amber: 'border-amber-500/20 bg-gradient-to-br from-amber-950/30 via-slate-900 to-slate-950 text-amber-400',
    rose: 'border-rose-500/20 bg-gradient-to-br from-rose-950/30 via-slate-900 to-slate-950 text-rose-400',
    cyan: 'border-cyan-500/20 bg-gradient-to-br from-cyan-950/30 via-slate-900 to-slate-950 text-cyan-400',
  };

  const iconBgStyles = {
    emerald: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
    teal: 'bg-teal-500/15 text-teal-400 border border-teal-500/30',
    indigo: 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30',
    amber: 'bg-amber-500/15 text-amber-400 border border-amber-500/30',
    rose: 'bg-rose-500/15 text-rose-400 border border-rose-500/30',
    cyan: 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30',
  };

  return (
    <div
      onClick={onClick}
      className={`glass-panel p-5 rounded-2xl border transition-all duration-200 shadow-xl flex flex-col justify-between ${accentStyles[accentColor]} ${
        onClick ? 'cursor-pointer hover:border-white/30 hover:scale-[1.01]' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">{title}</span>
          <div className="flex items-baseline space-x-1.5 mt-2">
            <span className="text-2xl sm:text-3xl font-black text-white tracking-tight">{value}</span>
            {unit && <span className="text-xs sm:text-sm font-semibold text-slate-400">{unit}</span>}
          </div>
        </div>

        <div className={`p-2.5 rounded-xl shrink-0 ${iconBgStyles[accentColor]}`}>
          {icon}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs">
        {trend ? (
          <div className="flex items-center space-x-1.5">
            <span
              className={`flex items-center font-bold px-1.5 py-0.5 rounded text-[11px] ${
                trend.isPositive ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
              }`}
            >
              {trend.isPositive ? <TrendingUp className="w-3.5 h-3.5 mr-1" /> : <TrendingDown className="w-3.5 h-3.5 mr-1" />}
              {trend.percentage > 0 ? `+${trend.percentage}%` : `${trend.percentage}%`}
            </span>
            <span className="text-slate-400 text-[11px]">{trend.periodText || 'vs last month'}</span>
          </div>
        ) : (
          <span className="text-[11px] text-slate-400">{subtitle || 'Platform telemetry'}</span>
        )}
      </div>
    </div>
  );
};
