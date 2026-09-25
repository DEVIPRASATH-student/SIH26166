import React from 'react';
import {
  Compass,
  Layers,
  Zap,
  Sliders,
  Globe,
  Network,
  AlertCircle,
  Target,
  Flame,
  ShieldAlert,
  ShieldCheck,
  Activity,
  Play,
  HelpCircle,
} from 'lucide-react';

export type PageId =
  | 'overview'
  | 'scenarios'
  | 'observations'
  | 'correspondence'
  | 'physical-verification'
  | 'evidence'
  | 'uncertainty'
  | 'graph'
  | 'knowledge'
  | 'recommendations'
  | 'system-status'
  | 'presentation'
  | 'registration'
  | 'entities'
  | 'stress'
  | 'redteam';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
  entityCount: number;
  gapCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  entityCount,
  gapCount,
}) => {
  const primaryNavItems = [
    { id: 'overview' as PageId, label: 'Dashboard', icon: Compass },
    { id: 'scenarios' as PageId, label: 'Demo Scenarios', icon: Target },
    { id: 'presentation' as PageId, label: 'Presentation Mode', icon: Play, badge: 'DEMO' },
    { id: 'observations' as PageId, label: 'Observations', icon: Layers },
    { id: 'correspondence' as PageId, label: 'Correspondence', icon: Zap },
    { id: 'physical-verification' as PageId, label: 'Physical Verification', icon: ShieldCheck },
    { id: 'evidence' as PageId, label: 'Evidence Dashboard', icon: Layers },
    { id: 'uncertainty' as PageId, label: 'Uncertainty View', icon: Activity },
    { id: 'graph' as PageId, label: 'World Model Graph', icon: Network },
    {
      id: 'knowledge' as PageId,
      label: 'Knowledge Gaps',
      icon: AlertCircle,
      badge: gapCount > 0 ? gapCount : undefined,
      badgeColor: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
    },
    { id: 'recommendations' as PageId, label: 'Next Observation', icon: Target },
    { id: 'system-status' as PageId, label: 'System Status', icon: Activity },
  ];

  const secondaryNavItems = [
    { id: 'registration' as PageId, label: 'Registration Lab', icon: Sliders },
    {
      id: 'entities' as PageId,
      label: 'Lunar Entities',
      icon: Globe,
      badge: entityCount > 0 ? entityCount : undefined,
    },
    { id: 'stress' as PageId, label: 'Stress Lab', icon: Flame },
    { id: 'redteam' as PageId, label: 'Red Team Lab', icon: ShieldAlert },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between p-4 min-h-[calc(100vh-4.25rem)] font-sans shadow-sm">
      <div className="space-y-4">
        <div>
          <div className="px-3 py-1.5 text-[10px] uppercase tracking-wider text-slate-500 font-bold">
            Scientific Pipeline
          </div>
          <nav className="space-y-1">
            {primaryNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectPage(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150 ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-slate-600 hover:bg-slate-200/70 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon
                      className={`w-4 h-4 ${
                        isActive ? 'text-white' : 'text-slate-500'
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== undefined && (
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold ${
                        isActive 
                          ? 'bg-blue-500 text-white' 
                          : item.badgeColor || 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        <div>
          <div className="px-3 py-1.5 text-[10px] uppercase tracking-wider text-slate-500 font-bold">
            Research Labs
          </div>
          <nav className="space-y-1">
            {secondaryNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectPage(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-slate-600 hover:bg-slate-200/70 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== undefined && (
                    <span className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold ${
                      isActive ? 'bg-blue-500 text-white' : 'bg-slate-200 text-slate-700'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Mission Footer Quote */}
      <div className="p-3 rounded-xl bg-white border border-slate-200 text-[11px] text-slate-600 leading-relaxed font-sans mt-4 shadow-sm">
        <p className="text-[#0d2247] font-bold mb-0.5">ISRO Mission Paradigm:</p>
        <p className="italic text-slate-500">
          "Visual correspondence is a hypothesis. Physical verification is mandatory."
        </p>
      </div>
    </aside>
  );
};
