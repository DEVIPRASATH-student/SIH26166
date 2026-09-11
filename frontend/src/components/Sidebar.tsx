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
} from 'lucide-react';

export type PageId =
  | 'overview'
  | 'observations'
  | 'correspondence'
  | 'registration'
  | 'entities'
  | 'graph'
  | 'knowledge'
  | 'recommendations'
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
  const navItems = [
    { id: 'overview' as PageId, label: 'Mission Overview', icon: Compass },
    { id: 'observations' as PageId, label: 'Observations', icon: Layers },
    { id: 'correspondence' as PageId, label: 'Correspondence', icon: Zap },
    { id: 'registration' as PageId, label: 'Registration Lab', icon: Sliders },
    {
      id: 'entities' as PageId,
      label: 'Lunar Entities',
      icon: Globe,
      badge: entityCount > 0 ? entityCount : undefined,
    },
    { id: 'graph' as PageId, label: 'Entity Graph', icon: Network },
    {
      id: 'knowledge' as PageId,
      label: 'Knowledge Gaps',
      icon: AlertCircle,
      badge: gapCount > 0 ? gapCount : undefined,
      badgeColor: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
    },
    { id: 'recommendations' as PageId, label: 'Next Observation', icon: Target },
    { id: 'stress' as PageId, label: 'Stress Lab', icon: Flame },
    { id: 'redteam' as PageId, label: 'Red Team Lab', icon: ShieldAlert },
  ];

  return (
    <aside className="w-64 bg-lunar-900 border-r border-lunar-700/50 flex flex-col justify-between p-4 min-h-[calc(100vh-4rem)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-mono uppercase tracking-wider text-lunar-400 font-semibold">
          Scientific Intelligence
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectPage(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-mono font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-space-cyan/15 text-space-cyan border border-space-cyan/30 shadow-sm'
                    : 'text-lunar-300 hover:bg-lunar-800 hover:text-lunar-100'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon
                    className={`w-4 h-4 ${
                      isActive ? 'text-space-cyan' : 'text-lunar-400'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && (
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold ${
                      item.badgeColor ||
                      'bg-space-cyan/20 text-space-cyan border border-space-cyan/30'
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

      {/* Mission Footer Quote */}
      <div className="p-3 rounded-lg bg-lunar-950 border border-lunar-800 text-[11px] text-lunar-400 leading-relaxed font-mono">
        <p className="text-lunar-300 font-semibold mb-1">Mission Philosophy:</p>
        <p className="italic">
          "Others register images. LunarSynapse builds a memory and reasoning layer for the Moon."
        </p>
      </div>
    </aside>
  );
};
