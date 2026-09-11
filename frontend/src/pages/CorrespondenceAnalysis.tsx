import React, { useState } from 'react';
import { Correspondence, Observation } from '../types';
import { Zap, ShieldCheck, Filter, RefreshCw, Eye, EyeOff, Layers } from 'lucide-react';
import { EvidenceRadar } from '../components/EvidenceRadar';
import { UncertaintyGauge } from '../components/UncertaintyGauge';
import { api } from '../services/api';

interface CorrespondenceAnalysisProps {
  correspondences: Correspondence[];
  observations: Observation[];
  onRefresh: () => void;
}

export const CorrespondenceAnalysis: React.FC<CorrespondenceAnalysisProps> = ({
  correspondences,
  observations,
  onRefresh,
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
      <div className="p-8 text-center font-mono text-xs text-lunar-400">
        No correspondence tasks evaluated yet. Run the demo mission to start matching.
      </div>
    );
  }

  // Filter matches based on verified toggle
  const activeMatches = showOnlyVerified
    ? currentCorr.matches.filter((m) => m.is_inlier)
    : currentCorr.matches;

  return (
    <div className="space-y-6 font-mono">
      {/* Top Controls Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-lunar-50">Correspondence Analysis</h1>
          <p className="text-xs text-lunar-400">
            Multi-modal keypoint matching with physics-grounded geometric, solar, and terrain gating.
          </p>
        </div>

        {/* Task Selector & Re-run Toolbar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Select Correspondence Task */}
          <select
            value={currentCorr.id}
            onChange={(e) => setSelectedCorrId(e.target.value)}
            className="bg-lunar-900 border border-lunar-700 text-xs text-lunar-200 px-3 py-1.5 rounded-lg focus:outline-none focus:border-space-cyan"
          >
            {correspondences.map((c) => (
              <option key={c.id} value={c.id}>
                {c.id} ({c.source_observation_id} ➔ {c.target_observation_id}) — {c.status}
              </option>
            ))}
          </select>

          {/* Matcher Algorithm */}
          <select
            value={matcherAlgo}
            onChange={(e) => setMatcherAlgo(e.target.value)}
            className="bg-lunar-900 border border-lunar-700 text-xs text-lunar-200 px-3 py-1.5 rounded-lg focus:outline-none focus:border-space-cyan"
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
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-lunar-800 hover:bg-lunar-700 text-xs text-space-cyan border border-lunar-700 font-semibold"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
            <span>Re-Analyze</span>
          </button>

          {/* CRITICAL TOGGLE: Raw Matches vs Physics-Verified Matches */}
          <button
            onClick={() => setShowOnlyVerified(!showOnlyVerified)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              showOnlyVerified
                ? 'bg-space-emerald/20 text-space-emerald border border-space-emerald/40'
                : 'bg-space-amber/20 text-space-amber border border-space-amber/40'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>
              {showOnlyVerified ? 'PHYSICS-VERIFIED MATCHES' : 'RAW VISUAL MATCHES'}
            </span>
          </button>
        </div>
      </div>

      {/* Side-by-Side Match Visualizer */}
      <div className="telemetry-panel p-5 rounded-xl border border-lunar-700/60 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 text-xs">
            <span className="text-lunar-300 font-bold">
              {srcObs.sensor_type} ({srcObs.id})
            </span>
            <span className="text-lunar-500">➔</span>
            <span className="text-lunar-300 font-bold">
              {tgtObs.sensor_type} ({tgtObs.id})
            </span>
          </div>

          <div className="flex items-center space-x-4 text-xs">
            <span>
              Candidate Matches:{' '}
              <strong className="text-lunar-100">{currentCorr.num_candidate_matches}</strong>
            </span>
            <span>
              Verified Inliers:{' '}
              <strong className="text-space-emerald">{currentCorr.num_inliers}</strong>
            </span>
            <span>
              Inlier Ratio:{' '}
              <strong className="text-space-cyan">
                {Math.round(currentCorr.inlier_ratio * 100)}%
              </strong>
            </span>
          </div>
        </div>

        {/* Dual Canvas Viewport with SVG overlay */}
        <div className="relative w-full aspect-[2/1] rounded-xl overflow-hidden bg-lunar-950 border border-lunar-800 flex">
          {/* Source Image View */}
          <div className="w-1/2 h-full relative border-r border-lunar-800">
            <img
              src={srcObs.image_url}
              alt="Source Observation"
              className="w-full h-full object-cover"
            />
            <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-lunar-950/80 border border-lunar-700 text-[10px] text-space-cyan">
              SRC: {srcObs.sensor_type} ({srcObs.spatial_resolution_m}m)
            </div>
          </div>

          {/* Target Image View */}
          <div className="w-1/2 h-full relative">
            <img
              src={tgtObs.image_url}
              alt="Target Observation"
              className="w-full h-full object-cover"
            />
            <div className="absolute top-2 right-2 px-2 py-0.5 rounded bg-lunar-950/80 border border-lunar-700 text-[10px] text-space-cyan">
              TGT: {tgtObs.sensor_type} ({tgtObs.spatial_resolution_m}m)
            </div>
          </div>

          {/* Connecting Match Lines SVG Overlay */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            {activeMatches.map((m, idx) => {
              // Normalized coords (assuming 512x512 resolution mapped to width/2 and height)
              const x1 = (m.src_x / 512) * 50; // 0 to 50%
              const y1 = (m.src_y / 512) * 100; // 0 to 100%
              const x2 = 50 + (m.tgt_x / 512) * 50; // 50 to 100%
              const y2 = (m.tgt_y / 512) * 100;

              const stroke = m.is_inlier ? '#10b981' : '#f43f5e';
              const opacity = m.is_inlier ? 0.75 : 0.45;

              return (
                <g key={idx}>
                  <line
                    x1={`${x1}%`}
                    y1={`${y1}%`}
                    x2={`${x2}%`}
                    y2={`${y2}%`}
                    stroke={stroke}
                    strokeWidth={m.is_inlier ? 1.5 : 1}
                    strokeOpacity={opacity}
                  />
                  <circle cx={`${x1}%`} cy={`${y1}%`} r={m.is_inlier ? 3 : 2} fill={stroke} />
                  <circle cx={`${x2}%`} cy={`${y2}%`} r={m.is_inlier ? 3 : 2} fill={stroke} />
                </g>
              );
            })}
          </svg>

          {/* Mode Indicator Overlay */}
          <div className="absolute bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-lunar-950/90 border border-lunar-700 text-[11px] font-bold text-lunar-200">
            {showOnlyVerified
              ? `Displaying ${activeMatches.length} Physics-Verified Inliers (Green)`
              : `Displaying ${activeMatches.length} Raw Matches (Red: Rejected, Green: Inliers)`}
          </div>
        </div>
      </div>

      {/* Physics Evidence Profile & Uncertainty Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="telemetry-panel p-5 rounded-xl border border-lunar-700/60">
          <EvidenceRadar evidence={currentCorr.evidence_profile} />
        </div>
        <div className="telemetry-panel p-5 rounded-xl border border-lunar-700/60">
          <UncertaintyGauge uncertainty={currentCorr.uncertainty_breakdown} />
        </div>
      </div>
    </div>
  );
};
