import React from 'react';
import {
  Layers,
  Zap,
  Globe,
  AlertCircle,
  Target,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  ShieldCheck,
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
  const verifiedCount = correspondences.filter((c) => c.status === 'VERIFIED').length;
  const uncertainCount = correspondences.filter((c) => c.status === 'UNCERTAIN').length;

  return (
    <div className="space-y-6">
      {/* Top Welcome Banner */}
      <div className="telemetry-panel p-6 rounded-2xl border border-lunar-700/60 bg-gradient-to-r from-lunar-900 via-lunar-850 to-lunar-900">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-space-cyan/20 text-space-cyan border border-space-cyan/30">
                ACTIVE MULTI-MODAL CAMPAIGN
              </span>
              <span className="text-xs font-mono text-lunar-400">Lunar South Pole Region</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-lunar-50 mt-1 font-mono">
              LunarSynapse World Model
            </h1>
            <p className="text-xs text-lunar-300 font-mono mt-1 max-w-2xl leading-relaxed">
              Fusing heterogeneous OHRC, TMC-2, and IIRS remote sensing streams into persistent physical entities, quantified beliefs, and autonomous next-best observation targeting.
            </p>
          </div>
          <button
            onClick={onRunDemo}
            disabled={isRunningDemo}
            className="flex items-center justify-center space-x-2 px-5 py-3 rounded-xl bg-gradient-to-r from-space-cyan to-blue-600 hover:from-sky-400 hover:to-blue-500 text-lunar-950 font-mono font-bold text-xs uppercase tracking-wider shadow-lg shadow-space-cyan/20 transition-all shrink-0"
          >
            <Sparkles className="w-4 h-4" />
            <span>{isRunningDemo ? 'Executing...' : 'Run Demo Mission'}</span>
          </button>
        </div>
      </div>

      {/* Primary Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricsCard
          title="Total Observations"
          value={observations.length}
          subtitle="OHRC, TMC-2, IIRS payloads"
          icon={Layers}
          color="cyan"
          tooltip="Total registered remote sensing observation frames."
        />
        <MetricsCard
          title="Verified Correspondences"
          value={verifiedCount}
          subtitle={`${uncertainCount} flagged uncertain`}
          icon={Zap}
          color="emerald"
          tooltip="Pairs verified via geometric, solar ephemeris, and terrain physics constraints."
        />
        <MetricsCard
          title="Persistent Entities"
          value={entities.length}
          subtitle="Physical lunar features"
          icon={Globe}
          color="indigo"
          tooltip="Resolved physical craters, boulders, and terrain regions with persistent identity."
        />
        <MetricsCard
          title="Active Knowledge Gaps"
          value={gaps.length}
          subtitle="Scientific blind spots"
          icon={AlertCircle}
          color="amber"
          tooltip="Prioritized missing modalities, high illumination uncertainty, or resolution bounds."
        />
      </div>

      {/* Core Concept Flowchart */}
      <div className="telemetry-panel p-5 rounded-xl border border-lunar-700/60">
        <h2 className="text-xs font-mono font-bold uppercase text-lunar-300 mb-3 tracking-wider flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-space-cyan" />
          <span>Scientific Intelligence Pipeline Architecture</span>
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2 text-center text-xs font-mono">
          <div className="p-3 rounded-lg bg-lunar-850 border border-lunar-700">
            <span className="text-[10px] text-space-cyan font-bold block mb-1">STAGE 1</span>
            <span className="text-lunar-200">Sensor-Aware Ingestion</span>
          </div>
          <div className="p-3 rounded-lg bg-lunar-850 border border-lunar-700">
            <span className="text-[10px] text-space-cyan font-bold block mb-1">STAGE 2</span>
            <span className="text-lunar-200">Cross-Modal Matching</span>
          </div>
          <div className="p-3 rounded-lg bg-lunar-850 border border-space-cyan/40 bg-space-cyan/5">
            <span className="text-[10px] text-space-emerald font-bold block mb-1">STAGE 3 (CORE)</span>
            <span className="text-lunar-50 font-bold">Physics Verification</span>
          </div>
          <div className="p-3 rounded-lg bg-lunar-850 border border-lunar-700">
            <span className="text-[10px] text-space-cyan font-bold block mb-1">STAGE 4</span>
            <span className="text-lunar-200">Sub-Pixel Refinement</span>
          </div>
          <div className="p-3 rounded-lg bg-lunar-850 border border-lunar-700">
            <span className="text-[10px] text-space-cyan font-bold block mb-1">STAGE 5</span>
            <span className="text-lunar-200">Entity Resolution</span>
          </div>
          <div className="p-3 rounded-lg bg-lunar-850 border border-lunar-700">
            <span className="text-[10px] text-space-cyan font-bold block mb-1">STAGE 6</span>
            <span className="text-lunar-200">Knowledge Gap Detection</span>
          </div>
          <div className="p-3 rounded-lg bg-lunar-850 border border-space-emerald/40 bg-space-emerald/5">
            <span className="text-[10px] text-space-emerald font-bold block mb-1">STAGE 7 (TARGET)</span>
            <span className="text-space-emerald font-bold">Next-Best Observation</span>
          </div>
        </div>
      </div>

      {/* Actionable Split: Top Recommendation & Active Entities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Recommendation Card */}
        <div className="telemetry-panel p-5 rounded-xl border border-lunar-700/60 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono font-bold uppercase text-space-cyan flex items-center space-x-1.5">
                <Target className="w-4 h-4" />
                <span>Priority Target Recommendation</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-space-emerald/20 text-space-emerald border border-space-emerald/30">
                MAX INFORMATION GAIN
              </span>
            </div>
            {topRec ? (
              <div className="space-y-3 font-mono">
                <div className="flex items-center justify-between p-3 rounded-lg bg-lunar-950 border border-lunar-800">
                  <div>
                    <span className="text-[11px] text-lunar-400 block">TARGET ENTITY</span>
                    <span className="text-sm font-bold text-lunar-100">{topRec.entity_id}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] text-lunar-400 block">RECOMMENDED SENSOR</span>
                    <span className="text-sm font-bold text-space-cyan">{topRec.recommended_sensor}</span>
                  </div>
                </div>
                <p className="text-xs text-lunar-300 leading-relaxed">{topRec.explanation}</p>
                <div className="flex items-center space-x-4 text-xs">
                  <div>
                    <span className="text-lunar-400 text-[10px] block">EXPECTED GAIN:</span>
                    <span className="text-space-emerald font-bold">{topRec.expected_information_gain}</span>
                  </div>
                  <div>
                    <span className="text-lunar-400 text-[10px] block">UNCERTAINTY REDUCTION:</span>
                    <span className="text-space-cyan font-bold">{Math.round(topRec.uncertainty_reduction * 100)}%</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-6 text-center text-xs font-mono text-lunar-400">
                Run the demo mission to calculate initial target recommendations.
              </div>
            )}
          </div>
          <button
            onClick={() => onNavigate('recommendations')}
            className="mt-4 w-full py-2 rounded-lg bg-lunar-800 hover:bg-lunar-700 text-xs font-mono font-medium text-lunar-200 flex items-center justify-center space-x-2 transition-all"
          >
            <span>Explore All Recommendations</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Persistent Lunar Entities Preview */}
        <div className="telemetry-panel p-5 rounded-xl border border-lunar-700/60 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono font-bold uppercase text-lunar-300 flex items-center space-x-1.5">
                <Globe className="w-4 h-4 text-space-cyan" />
                <span>Persistent Lunar Entities ({entities.length})</span>
              </span>
              <span className="text-xs font-mono text-lunar-400">World Model Memory</span>
            </div>
            <div className="space-y-2">
              {entities.slice(0, 3).map((e) => (
                <div
                  key={e.entity_id}
                  className="p-3 rounded-lg bg-lunar-950 border border-lunar-800 flex items-center justify-between text-xs font-mono"
                >
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-lunar-100">{e.entity_id}</span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-lunar-800 text-lunar-300 uppercase">
                        {e.entity_type}
                      </span>
                    </div>
                    <span className="text-[11px] text-lunar-400">
                      Coords: {e.latitude.toFixed(3)}°S, {e.longitude.toFixed(3)}°E
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-lunar-400 block">OBSERVATIONS</span>
                    <span className="font-bold text-space-cyan">{e.associated_observations_count} attached</span>
                  </div>
                </div>
              ))}
              {entities.length === 0 && (
                <div className="p-6 text-center text-xs font-mono text-lunar-400">
                  No entities resolved yet. Run demo mission to populate world model.
                </div>
              )}
            </div>
          </div>
          <button
            onClick={() => onNavigate('entities')}
            className="mt-4 w-full py-2 rounded-lg bg-lunar-800 hover:bg-lunar-700 text-xs font-mono font-medium text-lunar-200 flex items-center justify-center space-x-2 transition-all"
          >
            <span>View All Entities & Hypotheses</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
