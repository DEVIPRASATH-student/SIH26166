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
    cyan: 'text-space-cyan bg-space-cyan/10 border-space-cyan/30',
    emerald: 'text-space-emerald bg-space-emerald/10 border-space-emerald/30',
    amber: 'text-space-amber bg-space-amber/10 border-space-amber/30',
    rose: 'text-space-rose bg-space-rose/10 border-space-rose/30',
    indigo: 'text-space-indigo bg-space-indigo/10 border-space-indigo/30',
  };

  return (
    <div className="telemetry-panel p-5 rounded-xl border transition-all duration-200 hover:shadow-lg">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-1.5">
          <span className="text-xs font-mono font-medium text-lunar-400 uppercase tracking-wider">
            {title}
          </span>
          {tooltip && (
            <div className="group relative cursor-pointer">
              <Info className="w-3.5 h-3.5 text-lunar-500 hover:text-lunar-300" />
              <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block w-48 p-2 bg-lunar-900 border border-lunar-700 text-[11px] text-lunar-200 rounded shadow-xl z-50 pointer-events-none">
                {tooltip}
              </div>
            </div>
          )}
        </div>
        <div className={`p-2 rounded-lg border ${colorStyles[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="text-2xl font-bold text-lunar-50 font-mono tracking-tight">{value}</div>
      {subtitle && <p className="text-xs text-lunar-400 mt-1 font-mono">{subtitle}</p>}
    </div>
  );
};
