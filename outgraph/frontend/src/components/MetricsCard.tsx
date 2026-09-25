import React from 'react';
import { LucideIcon, Info } from 'lucide-react';

interface MetricsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'cyan' | 'emerald' | 'amber' | 'rose' | 'indigo';
  tooltip?: string;
}

export const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'cyan',
  tooltip,
}) => {
  const colorStyles = {
    cyan: 'text-blue-600 bg-blue-50 border-blue-200',
    emerald: 'text-emerald-600 bg-emerald-50 border-emerald-200',
    amber: 'text-amber-600 bg-amber-50 border-amber-200',
    rose: 'text-rose-600 bg-rose-50 border-rose-200',
    indigo: 'text-indigo-600 bg-indigo-50 border-indigo-200',
  };

  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all duration-200">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-1.5">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            {title}
          </span>
          {tooltip && (
            <div className="group relative cursor-pointer">
              <Info className="w-3.5 h-3.5 text-slate-400 hover:text-slate-600" />
              <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block w-48 p-2.5 bg-slate-900 text-white text-[11px] rounded-lg shadow-xl z-50 pointer-events-none leading-tight font-normal">
                {tooltip}
              </div>
            </div>
          )}
        </div>
        <div className={`p-2 rounded-xl border ${colorStyles[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="text-3xl font-extrabold text-[#0d2247] tracking-tight">{value}</div>
      {subtitle && <p className="text-xs text-slate-500 mt-1 font-medium">{subtitle}</p>}
    </div>
  );
};
