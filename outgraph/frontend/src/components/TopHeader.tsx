import React from 'react';
import { Play, Activity, Sparkles, UserCheck, LogOut } from 'lucide-react';
import { SystemHealth, SystemStatus } from '../types';

interface TopHeaderProps {
  health: SystemHealth | null;
  systemStatus: SystemStatus | null;
  dataMode: 'ALL' | 'REAL' | 'SYNTHETIC';
  onChangeDataMode: (mode: 'ALL' | 'REAL' | 'SYNTHETIC') => void;
  isRunningDemo: boolean;
  onRunDemo: () => void;
  onLaunchPresentation: () => void;
  currentUser: { id: string; role: string } | null;
  onLogout: () => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  health,
  systemStatus,
  dataMode,
  onChangeDataMode,
  isRunningDemo,
  onRunDemo,
  onLaunchPresentation,
  currentUser,
  onLogout,
}) => {
  // Determine live system status (not hardcoded)
  const isOnline = systemStatus?.status === 'OPERATIONAL' || health?.status === 'OPERATIONAL';
  const isDegraded = systemStatus?.status === 'DEGRADED';
  const statusLabel = isOnline ? 'Backend Online' : isDegraded ? 'Backend Degraded' : 'Backend Unavailable';

  return (
    <header className="relative bg-white border-b border-slate-200 shadow-sm sticky top-0 z-50 font-sans">
      {/* Top Tricolor India Flag Line Bar */}
      <div className="h-1 w-full flex">
        <div className="h-full w-1/3 bg-[#FF9933]" />
        <div className="h-full w-1/3 bg-white" />
        <div className="h-full w-1/3 bg-[#138808]" />
      </div>

      <div className="h-16 px-6 flex items-center justify-between">
        {/* Brand & Project Identity */}
        <div className="flex items-center space-x-3">
          <div className="w-12 h-9 rounded-lg border border-slate-200 bg-white p-1 flex items-center justify-center shrink-0 shadow-sm">
            <img
              src="/isro_logo.jpg"
              alt="ISRO Logo"
              className="w-full h-full object-contain"
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
          </div>
          <div className="h-7 w-[1px] bg-slate-200" />
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-base text-[#0d2247] tracking-tight">
                LunarSynapse
              </span>
            </div>
            <p className="text-[11px] text-slate-500 tracking-tight hidden sm:block font-medium">
              Physics-Aware, Self-Evolving Multi-Modal Lunar World Model
            </p>
          </div>
        </div>

        {/* System Status Indicators & Action CTA */}
        <div className="flex items-center space-x-3">
          {/* Data Mode Selector Filter */}
          <div className="flex items-center space-x-1 p-0.5 rounded-lg bg-slate-100 border border-slate-200 text-xs">
            <button
              onClick={() => onChangeDataMode('ALL')}
              className={`px-2.5 py-1 rounded text-[11px] font-bold transition-all ${
                dataMode === 'ALL'
                  ? 'bg-white text-slate-800 shadow-sm border border-slate-200'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              ALL
            </button>
            <button
              onClick={() => onChangeDataMode('REAL')}
              className={`px-2.5 py-1 rounded text-[11px] font-bold transition-all ${
                dataMode === 'REAL'
                  ? 'bg-rose-50 text-rose-700 border border-rose-200 shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              REAL
            </button>
            <button
              onClick={() => onChangeDataMode('SYNTHETIC')}
              className={`px-2.5 py-1 rounded text-[11px] font-bold transition-all ${
                dataMode === 'SYNTHETIC'
                  ? 'bg-amber-50 text-amber-700 border border-amber-200 shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              SYNTHETIC
            </button>
          </div>

          {/* Live Subsystem Status */}
          <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-xs">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-bold text-emerald-700 text-[11px]">{statusLabel}</span>
          </div>

          {/* Authorized Official Badge */}
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-xs">
            <UserCheck className="w-3.5 h-3.5 text-blue-700" />
            <span className="text-slate-700 text-[11px] font-medium">
              {currentUser?.id || 'Authorized Official'}
            </span>
            <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
              Authorized Official
            </span>
          </div>

          {/* Logout Button */}
          <button
            onClick={onLogout}
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-semibold transition-all"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </header>
  );
};
