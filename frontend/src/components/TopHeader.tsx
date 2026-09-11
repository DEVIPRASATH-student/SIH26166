import React from 'react';
import { Play, Activity, Sparkles, Database, CheckCircle2, AlertTriangle } from 'lucide-react';
import { SystemHealth } from '../types';

interface TopHeaderProps {
  health: SystemHealth | null;
  isRunningDemo: boolean;
  onRunDemo: () => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({ health, isRunningDemo, onRunDemo }) => {
  return (
    <header className="h-16 bg-lunar-900/90 border-b border-lunar-700/50 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-50">
      {/* Brand & Project Identity */}
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-space-cyan/20 to-lunar-800 border border-space-cyan/40 flex items-center justify-center shadow-inner glow-cyan">
          <div className="w-4 h-4 rounded-full bg-space-cyan/80 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-lg text-lunar-50 tracking-wide">LunarSynapse</span>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-space-cyan/15 text-space-cyan border border-space-cyan/30">
              v1.0 MVP
            </span>
          </div>
          <p className="text-xs text-lunar-400 font-mono tracking-tight">
            Physics-Aware, Self-Evolving Multi-Modal Lunar World Model
          </p>
        </div>
      </div>

      {/* System Status Indicators & Action CTA */}
      <div className="flex items-center space-x-4">
        {/* Synthetic Data Badge */}
        <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-lunar-850 border border-lunar-700 text-xs font-mono text-lunar-300">
          <span className="w-2 h-2 rounded-full bg-amber-400" />
          <span>SYNTHETIC / DEMO DATA</span>
        </div>

        {/* Telemetry Status */}
        <div className="flex items-center space-x-2 px-3 py-1 rounded-md bg-lunar-850 border border-lunar-700 text-xs font-mono">
          <Activity className="w-3.5 h-3.5 text-space-emerald" />
          <span className="text-lunar-300">TELEMETRY:</span>
          <span className={health?.database_connected ? "text-space-emerald font-semibold" : "text-lunar-400"}>
            {health?.status || "CONNECTED"}
          </span>
        </div>

        {/* Primary Demo Mission Button */}
        <button
          onClick={onRunDemo}
          disabled={isRunningDemo}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-mono text-xs font-semibold uppercase tracking-wider transition-all duration-200 ${
            isRunningDemo
              ? "bg-lunar-700 text-lunar-400 cursor-not-allowed"
              : "bg-gradient-to-r from-space-cyan to-blue-600 hover:from-sky-400 hover:to-blue-500 text-lunar-950 font-bold shadow-lg shadow-space-cyan/20 active:scale-95"
          }`}
        >
          {isRunningDemo ? (
            <>
              <div className="w-4 h-4 border-2 border-lunar-400 border-t-transparent rounded-full animate-spin" />
              <span>EXECUTING MISSION...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>RUN COMPLETE DEMO MISSION</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
};
