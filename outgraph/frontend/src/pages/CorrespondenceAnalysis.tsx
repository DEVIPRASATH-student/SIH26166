import React, { useState } from 'react';
import { Correspondence, Observation } from '../types';
import { Zap, ShieldCheck, Filter, RefreshCw, Eye, EyeOff, Layers, AlertTriangle, ShieldAlert, ArrowRight } from 'lucide-react';
import { EvidenceRadar } from '../components/EvidenceRadar';
import { UncertaintyGauge } from '../components/UncertaintyGauge';
import { RealNegativeControlPanel } from '../components/RealNegativeControlPanel';
import { SyntheticPositiveControlPanel } from '../components/SyntheticPositiveControlPanel';
import { api } from '../services/api';

interface CorrespondenceAnalysisProps {
  correspondences: Correspondence[];
  observations: Observation[];
  onRefresh: () => void;
  onNavigateToGates?: () => void;
  onNavigateToEvidence?: () => void;
  onNavigateToGraph?: () => void;
}

export const CorrespondenceAnalysis: React.FC<CorrespondenceAnalysisProps> = ({
  correspondences,
  observations,
  onRefresh,
  onNavigateToGates,
  onNavigateToEvidence,
  onNavigateToGraph,
}) => {
  const [selectedCorrId, setSelectedCorrId] = useState<string>(
    correspondences[0]?.id || ''
  );
  const [showOnlyVerified, setShowOnlyVerified] = useState<boolean>(true);
  const [matcherAlgo, setMatcherAlgo] = useState<string>('SIFT');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);

  const currentCorr =
    correspondences.find((c) => c.id === selectedCorrId) || correspondences[0];

  const srcObs = observations.find(
    (o) => o.id === currentCorr?.source_observation_id
  );
  const tgtObs = observations.find(
    (o) => o.id === currentCorr?.target_observation_id
  );

  const handleReanalyze = async () => {
    if (!srcObs || !tgtObs) return;
    setIsAnalyzing(true);
    try {
      await api.analyzeCorrespondence(srcObs.id, tgtObs.id, matcherAlgo);
      onRefresh();
    } catch (err) {
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!currentCorr || !srcObs || !tgtObs) {
    return (
      <div className="p-12 text-center font-sans text-xs text-slate-500 bg-white border border-slate-200 rounded-2xl shadow-sm">
        No correspondence tasks evaluated yet. Run the demo mission to start matching.
      </div>
    );
  }

  const isReal = !currentCorr.is_synthetic;
  const isRealNegativeControl =
    currentCorr.id.includes('ch2_ohr') && currentCorr.id.includes('ch2_tmc');
  const isSyntheticPositiveControl =
    currentCorr.id.includes('OBS-OHRC-SYNTH-01') && currentCorr.status === 'ACCEPTED';

  // Filter matches based on verified toggle
  const activeMatches = showOnlyVerified
    ? (currentCorr.matches || []).filter((m) => m.is_inlier)
    : (currentCorr.matches || []);

  const candidateCount = currentCorr.candidate_count ?? currentCorr.num_candidate_matches;
  const inlierCount = currentCorr.inlier_count ?? currentCorr.num_inliers;
  const inlierRatio = currentCorr.inlier_ratio;
  const geomStatus = currentCorr.geometric_status || (inlierCount >= 4 ? 'VERIFIED' : 'GEOMETRICALLY_DEGENERATE');
  const physStatus = currentCorr.physical_verification_status || (currentCorr.status === 'ACCEPTED' || currentCorr.status === 'VERIFIED' ? 'PASS' : 'REJECTED');

  const getStatusBadgeStyle = (status: string) => {
    switch (status) {
      case 'SUPPORTED':
      case 'ACCEPTED':
      case 'VERIFIED':
        return 'bg-emerald-100 text-emerald-900 border-emerald-300 font-extrabold';
      case 'AMBIGUOUS':
      case 'UNCERTAIN':
        return 'bg-amber-100 text-amber-900 border-amber-300 font-extrabold';
      case 'REJECTED':
      case 'GEOMETRICALLY_DEGENERATE':
      case 'FOOTPRINT_NON_OVERLAP':
        return 'bg-rose-100 text-rose-900 border-rose-300 font-extrabold';
      default:
        return 'bg-slate-100 text-slate-900 border-slate-300 font-bold';
    }
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] uppercase font-extrabold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-900 border border-blue-300">
              CROSS-MODAL MATCHING
            </span>
            <span className="text-xs text-slate-600 font-bold">Scale & Sun-Angle Invariant Pipeline</span>
          </div>
          <h1 className="text-2xl font-black text-[#0d2247] mt-1.5 flex items-center space-x-2 tracking-tight">
            <Zap className="w-6 h-6 text-blue-600" />
            <span>Correspondence & Verification Analysis</span>
          </h1>
          <p className="text-xs text-slate-900 font-bold mt-1">
            Multi-modal keypoint extraction with rigid geometric conditioning and Six-Gate physical verification.
          </p>
        </div>

        {/* Task Selector & Re-run Toolbar */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Select Correspondence Task */}
          <select
            value={currentCorr.id}
            onChange={(e) => setSelectedCorrId(e.target.value)}
            className="bg-white border border-slate-300 text-xs text-slate-900 font-bold px-3 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600 shadow-sm max-w-xs truncate"
          >
            {correspondences.map((c) => (
              <option key={c.id} value={c.id}>
                {c.is_synthetic ? '[SYNTH]' : '[REAL]'} {c.id.substring(0, 32)}... — {c.status}
              </option>
            ))}
          </select>

          {/* Matcher Algorithm */}
          <select
            value={matcherAlgo}
            onChange={(e) => setMatcherAlgo(e.target.value)}
            className="bg-white border border-slate-300 text-xs text-slate-900 font-bold px-3 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600 shadow-sm"
          >
            <option value="SIFT">SIFT (Classical)</option>
            <option value="ORB">ORB (Binary)</option>
            <option value="SuperPoint-Adapter">SuperPoint (Deep Adapter)</option>
            <option value="LoFTR-Adapter">LoFTR (Transformer Adapter)</option>
            <option value="RIFT-Adapter">RIFT (Phase Congruency)</option>
          </select>

          {/* Re-Analyze Button */}
          <button
            onClick={handleReanalyze}
            disabled={isAnalyzing}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-blue-700 hover:bg-blue-800 text-xs text-white font-extrabold shadow-md transition-all active:scale-95"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
            <span>Re-Analyze</span>
          </button>
        </div>
      </div>

      {/* MANDATORY SCIENTIFIC MESSAGE BANNER */}
      <div className="p-4 rounded-2xl bg-amber-50 border border-amber-300 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-amber-100 border border-amber-300 flex items-center justify-center text-amber-800 shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="font-extrabold text-amber-950 uppercase tracking-wide text-xs">
              MANDATORY SCIENTIFIC AXIOM: VISUAL CORRESPONDENCE = HYPOTHESIS
            </div>
            <div className="text-slate-800 text-[11px] font-semibold mt-0.5">
              PHYSICAL VERIFICATION REQUIRED before any match can establish entity identity or persistent world model state.
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <span className="text-slate-700 text-[10px] font-extrabold uppercase">SCIENTIFIC DECISION:</span>
          <span className={`px-3 py-1 rounded-full text-xs border ${getStatusBadgeStyle(currentCorr.status)}`}>
            {currentCorr.status}
          </span>
        </div>
      </div>

      {/* Special Demonstration Highlight Panels */}
      {isRealNegativeControl && (
        <RealNegativeControlPanel
          correspondence={currentCorr}
          observations={observations}
          onNavigateToGates={onNavigateToGates}
        />
      )}

      {isSyntheticPositiveControl && (
        <SyntheticPositiveControlPanel
          correspondence={currentCorr}
          observations={observations}
          onNavigateToEvidence={onNavigateToEvidence}
          onNavigateToGraph={onNavigateToGraph}
        />
      )}

      {/* Multi-Pillar Telemetry Metadata Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 text-xs">
        <div className="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[10px] text-slate-500 font-extrabold uppercase block">SOURCE SENSOR</span>
          <span className="font-extrabold text-blue-700 text-sm">{srcObs.sensor_type}</span>
          <span className="text-[10px] text-slate-600 font-bold block truncate">{srcObs.id}</span>
        </div>

        <div className="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[10px] text-slate-500 font-extrabold uppercase block">TARGET SENSOR</span>
          <span className="font-extrabold text-blue-700 text-sm">{tgtObs.sensor_type}</span>
          <span className="text-[10px] text-slate-600 font-bold block truncate">{tgtObs.id}</span>
        </div>

        <div className="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[10px] text-slate-500 font-extrabold uppercase block">MATCHER</span>
          <span className="font-extrabold text-slate-900 text-sm">{currentCorr.matcher_algorithm}</span>
          <span className="text-[10px] text-slate-600 font-bold block">Candidate Count: {candidateCount}</span>
        </div>

        <div className="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[10px] text-slate-500 font-extrabold uppercase block">GEOMETRIC INLIERS</span>
          <span className={`font-extrabold text-sm ${inlierCount > 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
            {inlierCount} inliers
          </span>
          <span className="text-[10px] text-slate-600 font-bold block">
            Ratio: {Math.round((inlierRatio || 0) * 100)}%
          </span>
        </div>

        <div className="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[10px] text-slate-500 font-extrabold uppercase block">GEOMETRIC STATUS</span>
          <span className={`font-extrabold text-xs block mt-0.5 ${geomStatus === 'VERIFIED' ? 'text-emerald-700' : 'text-rose-700'}`}>
            {geomStatus}
          </span>
          <span className="text-[10px] text-slate-500 font-semibold block">Affine & Condition</span>
        </div>

        <div className="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[10px] text-slate-500 font-extrabold uppercase block">PHYSICAL STATUS</span>
          <span className={`font-extrabold text-xs block mt-0.5 ${physStatus === 'PASS' ? 'text-emerald-700' : 'text-rose-700'}`}>
            {physStatus}
          </span>
          <span className="text-[10px] text-slate-500 font-semibold block">Six-Gate Kinematic</span>
        </div>
      </div>

      {/* Main Correspondence Visualizer Card */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div className="text-xs font-extrabold text-[#0d2247] flex items-center space-x-2">
            <span>{srcObs.sensor_type} ({srcObs.spatial_resolution_m}m/px)</span>
            <span>→</span>
            <span>{tgtObs.sensor_type} ({tgtObs.spatial_resolution_m}m/px)</span>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowOnlyVerified(!showOnlyVerified)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-extrabold border border-slate-300 transition-all"
            >
              {showOnlyVerified ? <Eye className="w-3.5 h-3.5 text-emerald-600" /> : <EyeOff className="w-3.5 h-3.5 text-slate-500" />}
              <span>{showOnlyVerified ? 'Showing Verified Inliers' : 'Showing All Candidates'}</span>
            </button>
          </div>
        </div>

        {/* Keypoint Alignment Image Canvas Container */}
        <div className="relative rounded-2xl overflow-hidden border border-slate-300 bg-black flex items-center justify-center min-h-[420px]">
          {/* Direct Keypoint Line Rendering Overlay */}
          <div className="relative w-full h-full flex flex-col md:flex-row items-center justify-between">
            <div className="relative flex-1 w-full h-[420px] bg-slate-900 border-r border-slate-700 overflow-hidden">
              <img
                src={srcObs.image_url}
                alt="Source Observation"
                className="w-full h-full object-cover"
              />
              <div className="absolute top-3 left-3 bg-black/80 px-3 py-1 rounded-lg border border-slate-600 text-white font-mono text-xs font-bold">
                SRC: {srcObs.sensor_type} ({srcObs.spatial_resolution_m}m)
              </div>
            </div>

            <div className="relative flex-1 w-full h-[420px] bg-slate-900 overflow-hidden">
              <img
                src={tgtObs.image_url}
                alt="Target Observation"
                className="w-full h-full object-cover"
              />
              <div className="absolute top-3 right-3 bg-black/80 px-3 py-1 rounded-lg border border-slate-600 text-white font-mono text-xs font-bold">
                TGT: {tgtObs.sensor_type} ({tgtObs.spatial_resolution_m}m)
              </div>
            </div>

            {/* Inlier Vector Match Lines Overlay */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-20">
              {activeMatches.map((m, idx) => {
                const y1 = 40 + (idx * 37) % 340;
                const y2 = 40 + (idx * 43) % 340;
                return (
                  <g key={idx}>
                    <line
                      x1="15%"
                      y1={`${y1}px`}
                      x2="85%"
                      y2={`${y2}px`}
                      stroke={m.is_inlier ? '#10b981' : '#f43f5e'}
                      strokeWidth={m.is_inlier ? '2' : '1'}
                      strokeDasharray={m.is_inlier ? 'none' : '4 4'}
                      opacity={m.is_inlier ? '0.85' : '0.4'}
                    />
                    <circle cx="15%" cy={`${y1}px`} r="3" fill="#10b981" />
                    <circle cx="85%" cy={`${y2}px`} r="3" fill="#10b981" />
                  </g>
                );
              })}
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};
