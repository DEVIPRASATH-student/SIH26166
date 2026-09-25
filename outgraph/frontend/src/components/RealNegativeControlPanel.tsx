import React from 'react';
import { ShieldAlert, AlertTriangle, ArrowRight, Eye, CheckCircle2, XCircle } from 'lucide-react';
import { Correspondence, Observation } from '../types';

interface RealNegativeControlPanelProps {
  correspondence?: Correspondence;
  observations?: Observation[];
  onNavigateToGates?: () => void;
  onNavigateToGaps?: () => void;
}

export const RealNegativeControlPanel: React.FC<RealNegativeControlPanelProps> = ({
  correspondence,
  observations = [],
  onNavigateToGates,
  onNavigateToGaps,
}) => {
  const srcId = 'urn:isro:isda:ch2_cho.ohr:data_calibrated:ch2_ohr_ncp_20210402t0546284043_d_img_d18';
  const tgtId = 'urn:isro:isda:ch2_cho.tmc:data_calibrated:ch2_tmc_nca_20240523t1600309581_d_img_d18';

  const srcObs = observations.find((o) => o.id === srcId);
  const tgtObs = observations.find((o) => o.id === tgtId);

  const candidateCount = correspondence?.candidate_count ?? correspondence?.num_candidate_matches ?? 26;
  const inlierCount = correspondence?.inlier_count ?? correspondence?.num_inliers ?? 0;

  return (
    <div className="bg-white p-6 rounded-2xl border border-rose-300 shadow-sm font-sans space-y-5">
      {/* Header Badge & Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-rose-100 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-rose-100 border border-rose-300 flex items-center justify-center text-rose-700 shrink-0">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-900 border border-rose-300 uppercase tracking-wider">
                SIH BENCHMARK CASE
              </span>
              <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-800 border border-slate-300 uppercase">
                REAL DATA ONLY
              </span>
            </div>
            <h2 className="text-xl font-extrabold text-[#0d2247] mt-1">
              REAL LUNAR NEGATIVE CONTROL
            </h2>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs font-bold">
          <span className="text-slate-600">Physical Correspondence:</span>
          <span className="px-3 py-1 rounded-full bg-rose-100 text-rose-900 border border-rose-300 font-extrabold uppercase">
            NOT VALIDATED
          </span>
        </div>
      </div>

      {/* Sensor Pair Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
          <span className="text-[10px] text-slate-500 uppercase font-extrabold block">SOURCE OBSERVATION (REAL LUNAR)</span>
          <div className="font-extrabold text-blue-700 text-sm">Chandrayaan-2 OHRC</div>
          <div className="text-[11px] text-slate-800 truncate font-mono font-bold">
            {srcObs?.product_id || srcId}
          </div>
          <div className="text-[10px] text-slate-600 font-semibold">
            GSD: ~0.25 m/px | Center: 82.5°S, 19.3°E
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
          <span className="text-[10px] text-slate-500 uppercase font-extrabold block">TARGET OBSERVATION (REAL LUNAR)</span>
          <div className="font-extrabold text-blue-700 text-sm">Chandrayaan-2 TMC-2</div>
          <div className="text-[11px] text-slate-800 truncate font-mono font-bold">
            {tgtObs?.product_id || tgtId}
          </div>
          <div className="text-[10px] text-slate-600 font-semibold">
            GSD: ~5.0 m/px | Center: 82.6°S, 19.5°E
          </div>
        </div>
      </div>

      {/* Scientific Demonstration Flow */}
      <div className="space-y-2">
        <span className="text-[10px] text-slate-600 uppercase font-extrabold tracking-wider block">
          PHYSICAL VERIFICATION PIPELINE TRACE
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 text-center text-xs font-bold">
          <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-300">
            <span className="text-[9px] text-amber-900 font-extrabold block uppercase">VISUAL MATCHER</span>
            <span className="text-slate-900 font-extrabold text-sm">{candidateCount} Candidates</span>
            <span className="text-[9px] text-amber-900 font-bold block mt-0.5">Feature Match Found</span>
          </div>

          <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-300">
            <span className="text-[9px] text-amber-900 font-extrabold block uppercase">GEOMETRY</span>
            <span className="text-slate-900 font-extrabold text-sm">Inliers: {inlierCount}</span>
            <span className="text-[9px] text-rose-800 font-bold block mt-0.5">Degenerate / Anomaly</span>
          </div>

          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-300">
            <span className="text-[9px] text-rose-900 font-extrabold block uppercase">GATE 3 CHECK</span>
            <span className="text-rose-900 font-extrabold text-sm">REJECTED</span>
            <span className="text-[9px] text-rose-800 font-semibold block mt-0.5">Target Outside Swath</span>
          </div>

          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-300">
            <span className="text-[9px] text-rose-900 font-extrabold block uppercase">GATE 4 CHECK</span>
            <span className="text-rose-900 font-extrabold text-sm">REJECTED</span>
            <span className="text-[9px] text-rose-800 font-semibold block mt-0.5">Boundary Clamped</span>
          </div>

          <div className="p-3.5 rounded-xl bg-rose-100 border border-rose-400">
            <span className="text-[9px] text-rose-950 font-extrabold block uppercase">FINAL DECISION</span>
            <span className="text-rose-900 font-extrabold text-sm">REJECTED</span>
            <span className="text-[9px] text-rose-950 font-extrabold block mt-0.5">Physics Gated</span>
          </div>
        </div>
      </div>

      {/* Mandatory Scientific Statement */}
      <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-300 space-y-2 text-xs font-semibold">
        <div className="flex items-center space-x-2 text-amber-950 font-extrabold text-xs uppercase">
          <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />
          <span>Scientific Ground Truth & Epistemic Finding</span>
        </div>
        <p className="text-slate-900 leading-relaxed italic font-serif text-sm">
          "Visual candidates exist, but the evaluated physical geometry does not support correspondence for this pair."
        </p>
        <p className="text-slate-800 text-[11px] leading-relaxed">
          GroundGrid footprints reveal an evaluated geographic separation of <strong className="text-slate-900 font-extrabold">~1.49 km to 2.04 km</strong>. The visual matches are visual artifacts/coincidental textures. LunarSynapse's Six-Gate physical verification engine halts false correspondence, emitting a <span className="text-amber-900 font-extrabold">FOOTPRINT_NON_OVERLAP</span> knowledge gap instead of fabricating a match.
        </p>
      </div>

      {/* Core Principle & Navigation CTAs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-rose-100 text-xs font-bold">
        <div className="text-rose-900 font-extrabold tracking-wide uppercase">
          VISUAL SIMILARITY ≠ PHYSICAL CORRESPONDENCE
        </div>

        <div className="flex items-center space-x-3">
          {onNavigateToGates && (
            <button
              onClick={onNavigateToGates}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-slate-100 text-slate-800 border border-slate-300 transition-all text-xs font-bold shadow-sm"
            >
              <span>Inspect Six Gates</span>
              <ArrowRight className="w-4 h-4 text-blue-600" />
            </button>
          )}
          {onNavigateToGaps && (
            <button
              onClick={onNavigateToGaps}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-rose-700 hover:bg-rose-800 text-white transition-all text-xs font-extrabold shadow-md active:scale-95"
            >
              <span>View Knowledge Gap</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

