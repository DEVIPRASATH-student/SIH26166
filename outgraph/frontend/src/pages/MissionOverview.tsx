import React from 'react';
import {
  Layers,
  Zap,
  Globe,
  AlertCircle,
  Target,
  ArrowRight,
  Sparkles,
  ShieldAlert,
  Activity,
  AlertTriangle,
} from 'lucide-react';
import { MetricsCard } from '../components/MetricsCard';
import { Observation, Correspondence, LunarEntity, KnowledgeGap, Recommendation } from '../types';
import { PageId } from '../components/Sidebar';

interface MissionOverviewProps {
  observations: Observation[];
  correspondences: Correspondence[];
  entities: LunarEntity[];
  gaps: KnowledgeGap[];
  topRec: Recommendation | null;
  onNavigate: (page: PageId) => void;
  onRunDemo: () => void;
  isRunningDemo: boolean;
}

export const MissionOverview: React.FC<MissionOverviewProps> = ({
  observations,
  correspondences,
  entities,
  gaps,
  topRec,
  onNavigate,
  onRunDemo,
  isRunningDemo,
}) => {
  const verifiedCount = correspondences.filter((c) => c.status === 'VERIFIED' || c.status === 'ACCEPTED').length;
  const rejectedCount = correspondences.filter((c) => c.status === 'REJECTED' || c.status === 'GEOMETRICALLY_DEGENERATE').length;

  const realObsCount = observations.filter((o) => !o.is_synthetic).length;
  const synthObsCount = observations.filter((o) => o.is_synthetic).length;

  return (
    <div className="space-y-6 font-sans">
      {/* Premium Hero Mission Control Banner */}
      <div className="bg-gradient-to-br from-[#0d2247] via-[#112d5e] to-[#0a1a36] p-8 rounded-3xl text-white shadow-xl relative overflow-hidden border border-blue-900/50">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-3 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="px-3 py-1 rounded-full text-[10px] font-bold bg-orange-500/20 text-orange-300 border border-orange-400/30 uppercase tracking-wider">
                ISRO CHANDRAYAAN-2 MISSION CONTROL
              </span>
              <span className="text-xs text-blue-200 font-medium">OHRC • TMC-2 • IIRS</span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                REAL: {realObsCount}
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-400/30">
                SYNTHETIC: {synthObsCount}
              </span>
            </div>
            
            <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-white leading-tight">
              LunarSynapse Mission Control
            </h1>
            
            <p className="text-sm text-blue-100/90 leading-relaxed font-normal">
              Physics-Aware, Self-Evolving Multi-Modal Lunar World Model fusing heterogeneous remote sensing streams into persistent physical entities, quantified beliefs, and autonomous next-best observation targeting.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
            <button
              onClick={() => onNavigate('presentation')}
              className="flex items-center justify-center space-x-2 px-5 py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white border border-white/20 font-bold text-xs uppercase tracking-wider transition-all backdrop-blur-md"
            >
              <span>Presentation Mode</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            
            <button
              onClick={onRunDemo}
              disabled={isRunningDemo}
              className="flex items-center justify-center space-x-2 px-5 py-3 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-orange-500/20 transition-all active:scale-95"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isRunningDemo ? 'Executing...' : 'Run Demo Mission'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Disclaimers Strip */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2.5">
            <ShieldAlert className="w-4 h-4 text-rose-500 shrink-0" />
            <span className="text-slate-600 font-medium">Physical Correspondence Validation:</span>
          </div>
          <span className="font-bold text-rose-600 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200 uppercase text-[10px]">
            NOT VALIDATED
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
            <span className="text-slate-600 font-medium">Real-Data Ground Truth:</span>
          </div>
          <span className="font-bold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200 uppercase text-[10px]">
            N/A (GROUND TRUTH NOT ESTABLISHED)
          </span>
        </div>
      </div>

      {/* Primary Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricsCard
          title="Observations"
          value={observations.length}
          subtitle={`${realObsCount} real flight / ${synthObsCount} synthetic`}
          icon={Layers}
          color="cyan"
          tooltip="Total registered remote sensing observation frames."
        />
        <MetricsCard
          title="Correspondences"
          value={correspondences.length}
          subtitle={`${verifiedCount} supported, ${rejectedCount} rejected`}
          icon={Zap}
          color="emerald"
          tooltip="Pairs verified via geometric and Six-Gate physical constraints."
        />
        <MetricsCard
          title="Persistent Entities"
          value={entities.length}
          subtitle="Physical craters / boulders"
          icon={Globe}
          color="indigo"
          tooltip="Resolved physical craters, boulders, and terrain regions with persistent identity."
        />
        <MetricsCard
          title="Knowledge Gaps"
          value={gaps.length}
          subtitle="Epistemic blind spots"
          icon={AlertCircle}
          color="amber"
          tooltip="Prioritized missing modalities, high illumination uncertainty, or resolution bounds."
        />
      </div>

      {/* Pipeline Execution Architecture */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <h2 className="text-xs font-bold uppercase text-slate-700 tracking-wider flex items-center space-x-2">
            <Activity className="w-4 h-4 text-blue-600" />
            <span>End-to-End Scientific Pipeline Architecture</span>
          </h2>
          <span className="text-[10px] text-slate-400 font-medium">
            States: READY | SUPPORTED | AMBIGUOUS | REJECTED | UNKNOWN
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-9 gap-2.5 text-center text-xs">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[9px] text-blue-600 font-bold block mb-0.5">1. OBSERVATION</span>
            <span className="text-slate-800 font-extrabold block text-xs">Sensor Stream</span>
            <span className="text-[9px] font-bold text-emerald-600 block mt-1">READY</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[9px] text-blue-600 font-bold block mb-0.5">2. CORRESPONDENCE</span>
            <span className="text-slate-800 font-extrabold block text-xs">Visual Matcher</span>
            <span className="text-[9px] font-bold text-amber-600 block mt-1">HYPOTHESIS</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[9px] text-blue-600 font-bold block mb-0.5">3. GEOMETRY</span>
            <span className="text-slate-800 font-extrabold block text-xs">Homography</span>
            <span className="text-[9px] font-bold text-slate-500 block mt-1">EVALUATED</span>
          </div>

          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200">
            <span className="text-[9px] text-rose-700 font-bold block mb-0.5">4. SIX GATES</span>
            <span className="text-rose-900 font-extrabold block text-xs">Physics Gate</span>
            <span className="text-[9px] font-bold text-rose-600 block mt-1">REJECT / PASS</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[9px] text-blue-600 font-bold block mb-0.5">5. EVIDENCE</span>
            <span className="text-slate-800 font-extrabold block text-xs">11 Dimensions</span>
            <span className="text-[9px] font-bold text-blue-600 block mt-1">UNKNOWN≠NEG</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[9px] text-blue-600 font-bold block mb-0.5">6. UNCERTAINTY</span>
            <span className="text-slate-800 font-extrabold block text-xs">Interval</span>
            <span className="text-[9px] font-bold text-amber-600 block mt-1">&gt;4px SATURATE</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[9px] text-blue-600 font-bold block mb-0.5">7. WORLD MODEL</span>
            <span className="text-slate-800 font-extrabold block text-xs">Belief Memory</span>
            <span className="text-[9px] font-bold text-blue-600 block mt-1">UPDATED</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
            <span className="text-[9px] text-blue-600 font-bold block mb-0.5">8. KNOWLEDGE GAP</span>
            <span className="text-slate-800 font-extrabold block text-xs">8 Taxonomies</span>
            <span className="text-[9px] font-bold text-amber-600 block mt-1">DETECTED</span>
          </div>

          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200">
            <span className="text-[9px] text-emerald-700 font-bold block mb-0.5">9. NEXT TARGET</span>
            <span className="text-emerald-900 font-extrabold block text-xs">Info Gain E[ΔI]</span>
            <span className="text-[9px] font-bold text-emerald-600 block mt-1">POTENTIALLY</span>
          </div>
        </div>
      </div>

      {/* Demo Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Real Negative Control */}
        <div className="bg-white p-6 rounded-2xl border border-rose-200 shadow-sm flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 uppercase">
                DEMO SCENARIO A
              </span>
              <span className="text-xs text-slate-500 font-medium">Real Flight Benchmark</span>
            </div>
            <h3 className="text-sm font-bold text-slate-800 mt-2">
              REAL LUNAR NEGATIVE CONTROL (OHRC vs TMC-2)
            </h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              26 candidate visual matches found. Six-Gate physics halts correspondence at Gate 3 due to spatial swath separation.
            </p>
          </div>
          <button
            onClick={() => onNavigate('correspondence')}
            className="flex items-center justify-between px-4 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-bold transition-all"
          >
            <span>Inspect Real Negative Control</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Synthetic Positive Control */}
        <div className="bg-white p-6 rounded-2xl border border-emerald-200 shadow-sm flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 uppercase">
                DEMO SCENARIO B-E
              </span>
              <span className="text-xs text-slate-500 font-medium">Controlled Testbed</span>
            </div>
            <h3 className="text-sm font-bold text-slate-800 mt-2">
              SYNTHETIC CONTROLLED POSITIVE CASES
            </h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Controlled synthetic warps validate algorithmic convergence and full pipeline pass under known ground-truth conditions.
            </p>
          </div>
          <button
            onClick={() => onNavigate('correspondence')}
            className="flex items-center justify-between px-4 py-2.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs font-bold transition-all"
          >
            <span>Inspect Synthetic Positive Control</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
