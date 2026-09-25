import React, { useState } from 'react';
import {
  X,
  HelpCircle,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Layers,
  ChevronDown,
  ChevronUp,
  Info,
  Clock,
  Compass,
  ArrowRight,
  ExternalLink,
  Target,
  FileText,
  Activity,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { ScenarioExplanation, PhysicalGateDetail, ExplainabilityTraceStep } from '../types';

interface ExplainabilityModalProps {
  explanation: ScenarioExplanation;
  onClose: () => void;
}

export const ExplainabilityModal: React.FC<ExplainabilityModalProps> = ({
  explanation,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<
    'JUDGE' | 'GATES' | 'EVIDENCE' | 'UNCERTAINTY' | 'TRACE' | 'PROVENANCE'
  >('JUDGE');
  const [traceExpanded, setTraceExpanded] = useState<boolean>(true);

  const isReal = !explanation.provenance.is_synthetic;
  const isRejected = explanation.decision === 'REJECTED';
  const isAccepted = explanation.decision === 'ACCEPTED';
  const isUnknown = explanation.decision === 'UNKNOWN';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-lunar-950/80 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-5xl bg-lunar-900 border border-space-cyan/40 rounded-2xl shadow-2xl overflow-hidden my-auto max-h-[92vh] flex flex-col font-mono">
        {/* Modal Top Bar */}
        <div className="px-6 py-4 border-b border-lunar-800 bg-gradient-to-r from-lunar-950 via-lunar-900 to-lunar-950 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3">
            <span className="p-1.5 rounded-lg bg-space-cyan/20 text-space-cyan border border-space-cyan/30">
              <HelpCircle className="w-5 h-5" />
            </span>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] uppercase font-bold tracking-wider text-space-cyan">
                  SCIENTIFIC EXPLAINABILITY & PROVENANCE ENGINE
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[9px] uppercase font-bold border ${
                    isReal
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                      : 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                  }`}
                >
                  {isReal ? 'REAL LUNAR DATA' : 'SYNTHETIC CONTROLLED DATA'}
                </span>
              </div>
              <h2 className="text-lg font-bold text-lunar-50 mt-0.5">
                Explain Decision: {explanation.scenario_name}
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-lunar-800 text-lunar-300 hover:text-white hover:bg-lunar-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="px-6 border-b border-lunar-800 bg-lunar-950/60 flex items-center space-x-2 overflow-x-auto shrink-0 text-xs">
          {[
            { id: 'JUDGE', label: 'Judge Card & Verdict' },
            { id: 'GATES', label: 'Physical Gates & Illumination' },
            { id: 'EVIDENCE', label: '11D Evidence Fusion' },
            { id: 'UNCERTAINTY', label: 'Uncertainty & Gaps' },
            { id: 'TRACE', label: 'Decision Trace' },
            { id: 'PROVENANCE', label: 'Full Provenance' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-3 px-3.5 font-bold transition-all border-b-2 whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-space-cyan text-space-cyan bg-space-cyan/5'
                  : 'border-transparent text-lunar-400 hover:text-lunar-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs flex-1">
          {/* TAB 1: JUDGE CARD & HIGH LEVEL VERDICT */}
          {activeTab === 'JUDGE' && (
            <div className="space-y-6">
              {/* Highlight Card: WHY DID LUNARSYNAPSE MAKE THIS DECISION? */}
              <div
                className={`p-6 rounded-2xl border ${
                  isRejected
                    ? 'bg-rose-950/30 border-rose-500/50'
                    : isAccepted
                    ? 'bg-emerald-950/30 border-emerald-500/50'
                    : 'bg-amber-950/30 border-amber-500/50'
                } space-y-4`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {isRejected ? (
                      <ShieldAlert className="w-6 h-6 text-rose-400" />
                    ) : isAccepted ? (
                      <ShieldCheck className="w-6 h-6 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="w-6 h-6 text-amber-400" />
                    )}
                    <span className="text-sm font-bold text-lunar-100 uppercase tracking-wide">
                      {explanation.judge_card.question}
                    </span>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold uppercase border ${
                      isRejected
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                        : isAccepted
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    }`}
                  >
                    DECISION: {explanation.decision}
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-lunar-950/80 border border-lunar-800 text-sm leading-relaxed text-lunar-100 font-sans">
                  {explanation.judge_card.high_level_verdict}
                </div>

                {/* Clarification: Does this mean images are unrelated? */}
                <div className="p-3.5 rounded-xl bg-lunar-950/90 border border-lunar-800/80 space-y-1">
                  <span className="text-[11px] font-bold text-space-cyan uppercase tracking-wide block">
                    Important Scientific Distinction:
                  </span>
                  <p className="text-xs text-lunar-300 leading-relaxed">
                    {explanation.judge_card.does_this_mean_images_are_unrelated}
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                  <div className="p-3 rounded-xl bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 uppercase font-bold block">
                      Physical Gates Verdict
                    </span>
                    <span className="text-xs font-bold text-lunar-200 mt-0.5 block truncate">
                      {explanation.judge_card.physical_gates_verdict}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 uppercase font-bold block">
                      Uncertainty Impact
                    </span>
                    <span className="text-xs font-bold text-amber-300 mt-0.5 block truncate">
                      {explanation.judge_card.uncertainty_impact}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 uppercase font-bold block">
                      Provenance Class
                    </span>
                    <span className="text-xs font-bold text-space-cyan mt-0.5 block truncate">
                      {explanation.judge_card.is_real_or_synthetic}
                    </span>
                  </div>
                </div>
              </div>

              {/* Summary and Candidate Generation Comparison */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-lunar-950 border border-lunar-800 space-y-2">
                  <span className="text-[10px] uppercase font-bold text-space-cyan block">
                    Executive Summary
                  </span>
                  <p className="text-xs text-lunar-300 leading-relaxed">{explanation.summary}</p>
                  <div className="pt-2 border-t border-lunar-800/80">
                    <span className="text-[10px] text-lunar-400">Primary Decisive Reason:</span>
                    <div className="text-xs font-bold text-rose-300 mt-0.5">
                      {explanation.primary_reason}
                    </div>
                  </div>
                </div>

                {/* Candidate Generation Distinction */}
                <div className="p-4 rounded-xl bg-lunar-950 border border-lunar-800 space-y-2">
                  <span className="text-[10px] uppercase font-bold text-space-cyan block">
                    Candidate Generation vs Benchmark
                  </span>
                  <div className="space-y-1.5">
                    <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                      <div className="text-[10px] text-lunar-400 font-bold">
                        CURRENT DEMONSTRATION INSTANCE:
                      </div>
                      <div className="text-xs text-lunar-200 mt-0.5">
                        <span className="text-space-cyan font-bold">
                          {explanation.candidate_generation.current_demonstration_instance.candidate_count} candidates
                        </span>{' '}
                        ({explanation.candidate_generation.current_demonstration_instance.matcher_used})
                      </div>
                      <div className="text-[10px] text-lunar-400 mt-0.5">
                        {explanation.candidate_generation.current_demonstration_instance.candidate_description}
                      </div>
                    </div>

                    {explanation.candidate_generation.historical_phase7_benchmark && (
                      <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                        <div className="text-[10px] text-lunar-400 font-bold">
                          HISTORICAL PHASE 7 BENCHMARK:
                        </div>
                        <div className="text-xs text-lunar-200 mt-0.5">
                          {explanation.candidate_generation.historical_phase7_benchmark.candidate_count} candidates /{' '}
                          {explanation.candidate_generation.historical_phase7_benchmark.geometric_inliers} geometric inliers (
                          {explanation.candidate_generation.historical_phase7_benchmark.inlier_ratio_pct}%)
                        </div>
                        <div className="text-[10px] text-amber-300/80 mt-0.5">
                          *{explanation.candidate_generation.historical_phase7_benchmark.note}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Geometric Verification Section */}
              <div className="p-4 rounded-xl bg-lunar-950 border border-lunar-800 space-y-3">
                <span className="text-[10px] uppercase font-bold text-space-cyan block">
                  Geometric Verification Evidence
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Method</span>
                    <span className="text-xs font-bold text-lunar-200">
                      {explanation.geometric_evidence.transformation_model}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Inliers</span>
                    <span className="text-xs font-bold text-space-cyan">
                      {explanation.geometric_evidence.inlier_count}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Residual</span>
                    <span className="text-xs font-bold text-lunar-200">
                      {explanation.geometric_evidence.reprojection_residual_px !== null &&
                      explanation.geometric_evidence.reprojection_residual_px !== undefined
                        ? `${explanation.geometric_evidence.reprojection_residual_px} px`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Decision</span>
                    <span className="text-xs font-bold text-amber-300">
                      {explanation.geometric_evidence.geometric_decision}
                    </span>
                  </div>
                </div>
                {explanation.geometric_evidence.scientific_distinction && (
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800 text-[11px] text-lunar-300">
                    <span className="text-amber-400 font-bold">Rule: </span>
                    {explanation.geometric_evidence.scientific_distinction}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: PHYSICAL GATES & ILLUMINATION */}
          {activeTab === 'GATES' && (
            <div className="space-y-6">
              {/* Six Physical Gates Table */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-lunar-100 flex items-center space-x-2">
                      <Layers className="w-4 h-4 text-space-cyan" />
                      <span>The Six Strict Physical Validation Gates</span>
                    </h3>
                    <p className="text-[11px] text-lunar-400 mt-0.5">
                      Deterministic verification using calibrated GroundGrids and DEM topography.
                    </p>
                  </div>
                  <span
                    className={`px-2.5 py-1 rounded text-xs font-bold uppercase border ${
                      explanation.physical_gates.overall_result === 'PASS'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                    }`}
                  >
                    Result: {explanation.physical_gates.overall_result}
                  </span>
                </div>

                <div className="overflow-x-auto rounded-xl border border-lunar-800 bg-lunar-950">
                  <table className="w-full text-xs text-left border-collapse">
                    <thead>
                      <tr className="border-b border-lunar-800 bg-lunar-900/60 text-lunar-400 text-[10px] uppercase font-bold">
                        <th className="p-3">Gate</th>
                        <th className="p-3">Gate Name</th>
                        <th className="p-3">Result</th>
                        <th className="p-3">Reason / Evaluation</th>
                        <th className="p-3">Metric / Threshold</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-lunar-850">
                      {explanation.physical_gates.gates.map((g) => {
                        const isPass = g.result === 'PASS';
                        const isFail = g.result === 'REJECTED';
                        return (
                          <tr key={g.gate_id} className="hover:bg-lunar-900/40 transition-colors">
                            <td className="p-3 font-bold text-space-cyan">GATE {g.gate_id}</td>
                            <td className="p-3 font-bold text-lunar-200">
                              <div>{g.gate_name}</div>
                              {g.gate_id === 5 && (
                                <span className="text-[9px] text-amber-300 font-normal">
                                  Corridor Elevation Check (Not Illumination)
                                </span>
                              )}
                            </td>
                            <td className="p-3">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                                  isPass
                                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                                    : isFail
                                    ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                                    : 'bg-lunar-800 text-lunar-400 border-lunar-700'
                                }`}
                              >
                                {g.result}
                              </span>
                            </td>
                            <td className="p-3 text-lunar-300 max-w-xs">{g.reason}</td>
                            <td className="p-3 text-lunar-400">
                              <div>
                                <span className="text-lunar-500">Threshold:</span> {g.threshold}
                              </div>
                              {g.actual_value && (
                                <div className="text-rose-300 font-bold">
                                  <span className="text-lunar-500 font-normal">Actual:</span> {g.actual_value}
                                </div>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                <div className="p-3 rounded-xl bg-lunar-950 border border-lunar-800 text-[11px] text-lunar-400 space-y-1">
                  <div className="text-amber-400 font-bold">Scientific Gate Invariant:</div>
                  <p>
                    Gate 5 is strictly <span className="text-lunar-200 font-mono">TARGET_OUTSIDE_ELEVATION_CORRIDOR</span>.
                    Illumination verification is NOT Gate 5; it operates as an independent radiometric evidence check.
                  </p>
                </div>
              </div>

              {/* Illumination Verification Section (Separately Exposed) */}
              <div className="p-4 rounded-xl bg-lunar-950 border border-purple-500/40 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Compass className="w-4 h-4 text-purple-400" />
                    <span className="text-xs font-bold text-purple-300 uppercase tracking-wide">
                      {explanation.illumination_evidence.section_title}
                    </span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                      explanation.illumination_evidence.status === 'SUPPORTED'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : explanation.illumination_evidence.status === 'REJECTED'
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                        : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    }`}
                  >
                    {explanation.illumination_evidence.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Solar Azimuth Delta</span>
                    <span className="text-xs font-bold text-lunar-200">
                      {explanation.illumination_evidence.solar_azimuth_difference_deg !== undefined
                        ? `${explanation.illumination_evidence.solar_azimuth_difference_deg.toFixed(1)}°`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Elevation Delta</span>
                    <span className="text-xs font-bold text-lunar-200">
                      {explanation.illumination_evidence.solar_elevation_difference_deg !== undefined
                        ? `${explanation.illumination_evidence.solar_elevation_difference_deg.toFixed(1)}°`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Incidence Divergence</span>
                    <span className="text-xs font-bold text-lunar-200">
                      {explanation.illumination_evidence.incidence_angle_divergence_deg !== undefined
                        ? `${explanation.illumination_evidence.incidence_angle_divergence_deg.toFixed(1)}°`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Rejection Threshold</span>
                    <span className="text-xs font-bold text-purple-300">&gt; 60.0°</span>
                  </div>
                </div>

                <p className="text-xs text-lunar-300 leading-relaxed bg-lunar-900/60 p-3 rounded-lg border border-lunar-850">
                  {explanation.illumination_evidence.explanation}
                </p>

                <div className="text-[10px] text-purple-300/80 italic">
                  *{explanation.illumination_evidence.gate_distinction_note}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: 11D EVIDENCE FUSION MATRIX */}
          {activeTab === 'EVIDENCE' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-lunar-100 flex items-center space-x-2">
                    <Activity className="w-4 h-4 text-space-cyan" />
                    <span>11-Dimensional Evidence Fusion Matrix</span>
                  </h3>
                  <p className="text-[11px] text-lunar-400 mt-0.5">
                    Scientific Ledger across physical, geometric, terrain, and sensor modalities.
                  </p>
                </div>
                <div className="px-2.5 py-1 rounded bg-lunar-950 border border-amber-500/40 text-[10px] text-amber-300 font-bold">
                  AXIOM: MISSING != NEGATIVE
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries(explanation.evidence_dimensions).map(([dim, data]) => {
                  const isSupported = data.status === 'SUPPORTED';
                  const isContradicted = data.status === 'CONTRADICTED';
                  const isMissing = data.status === 'MISSING' || data.status === 'UNKNOWN';

                  return (
                    <div
                      key={dim}
                      className={`p-3 rounded-xl border space-y-2 ${
                        isContradicted
                          ? 'bg-rose-950/20 border-rose-500/40 text-rose-300'
                          : isSupported
                          ? 'bg-space-cyan/10 border-space-cyan/30 text-space-cyan'
                          : 'bg-lunar-950 border-lunar-800 text-lunar-400'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs">{dim}</span>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase border ${
                            isSupported
                              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                              : isContradicted
                              ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                              : 'bg-lunar-800 text-lunar-400 border-lunar-700'
                          }`}
                        >
                          {data.status}
                        </span>
                      </div>

                      <div className="space-y-1 text-[11px]">
                        <div>
                          <span className="text-lunar-500">Present:</span>{' '}
                          <span className="text-lunar-200">{data.evidence_present}</span>
                        </div>
                        <div>
                          <span className="text-lunar-500">Missing:</span>{' '}
                          <span className="text-lunar-400">{data.evidence_missing}</span>
                        </div>
                        <div className="text-[10px] text-lunar-500 pt-1 border-t border-lunar-850">
                          Source: {data.evidence_source} | Conf: {(data.confidence * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 4: UNCERTAINTY & KNOWLEDGE GAPS */}
          {activeTab === 'UNCERTAINTY' && (
            <div className="space-y-6">
              {/* Uncertainty Decomposition */}
              <div className="p-4 rounded-xl bg-lunar-950 border border-lunar-800 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs uppercase font-bold text-space-cyan">
                    Uncertainty Decomposition & Risk Modeling
                  </h3>
                  <span className="text-[10px] text-amber-400 font-bold">
                    {explanation.uncertainty.calibration_statement}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                  <div className="p-3 rounded-xl bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Scalar UQ</span>
                    <span className="text-lg font-bold text-space-cyan mt-1 block">
                      {explanation.uncertainty.scalar_uncertainty.toFixed(2)}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Epistemic UQ</span>
                    <span className="text-lg font-bold text-amber-300 mt-1 block">
                      {explanation.uncertainty.epistemic_uncertainty !== undefined
                        ? explanation.uncertainty.epistemic_uncertainty.toFixed(2)
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Aleatoric UQ</span>
                    <span className="text-lg font-bold text-lunar-200 mt-1 block">
                      {explanation.uncertainty.aleatoric_uncertainty !== undefined
                        ? explanation.uncertainty.aleatoric_uncertainty.toFixed(2)
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Risk Category</span>
                    <span className="text-xs font-bold text-rose-300 mt-1.5 block">
                      {explanation.uncertainty.qualitative_risk}
                    </span>
                  </div>
                </div>

                {explanation.uncertainty.decomposition && (
                  <div className="space-y-2 pt-2 border-t border-lunar-850">
                    <span className="text-[11px] font-bold text-lunar-300 block">
                      Why is uncertainty at this level? (4-Factor Analysis):
                    </span>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                      <div className="p-2.5 rounded bg-lunar-900 border border-lunar-800">
                        <span className="text-amber-400 font-bold">Evidence Disagreement: </span>
                        <span className="text-lunar-300">
                          {explanation.uncertainty.decomposition.evidence_disagreement}
                        </span>
                      </div>
                      <div className="p-2.5 rounded bg-lunar-900 border border-lunar-800">
                        <span className="text-amber-400 font-bold">Geometric Instability: </span>
                        <span className="text-lunar-300">
                          {explanation.uncertainty.decomposition.geometric_instability}
                        </span>
                      </div>
                      <div className="p-2.5 rounded bg-lunar-900 border border-lunar-800">
                        <span className="text-amber-400 font-bold">Feature Ambiguity: </span>
                        <span className="text-lunar-300">
                          {explanation.uncertainty.decomposition.feature_ambiguity}
                        </span>
                      </div>
                      <div className="p-2.5 rounded bg-lunar-900 border border-lunar-800">
                        <span className="text-amber-400 font-bold">Spatial Sparsity: </span>
                        <span className="text-lunar-300">
                          {explanation.uncertainty.decomposition.spatial_sparsity}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {explanation.uncertainty.saturation_note && (
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800 text-[10px] text-amber-300/80">
                    *{explanation.uncertainty.saturation_note}
                  </div>
                )}
              </div>

              {/* Knowledge Gap & Next-Best Observation */}
              {explanation.knowledge_gap && (
                <div className="p-4 rounded-xl bg-lunar-950 border border-amber-500/40 space-y-3">
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    <span className="text-xs font-bold text-amber-300 uppercase tracking-wide">
                      Epistemic Knowledge Gap: {explanation.knowledge_gap.gap_type}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                    <div className="p-2.5 rounded bg-lunar-900 border border-lunar-800">
                      <span className="text-space-cyan font-bold block">What is known?</span>
                      <span className="text-lunar-300">{explanation.knowledge_gap.what_is_known}</span>
                    </div>
                    <div className="p-2.5 rounded bg-lunar-900 border border-lunar-800">
                      <span className="text-amber-300 font-bold block">What is unknown?</span>
                      <span className="text-lunar-300">{explanation.knowledge_gap.what_is_unknown}</span>
                    </div>
                    <div className="p-2.5 rounded bg-lunar-900 border border-lunar-800">
                      <span className="text-rose-300 font-bold block">Why is it unknown?</span>
                      <span className="text-lunar-300">{explanation.knowledge_gap.why_is_it_unknown}</span>
                    </div>
                    <div className="p-2.5 rounded bg-lunar-900 border border-lunar-800">
                      <span className="text-purple-300 font-bold block">What evidence is missing?</span>
                      <span className="text-lunar-300">{explanation.knowledge_gap.what_evidence_is_missing}</span>
                    </div>
                  </div>

                  {explanation.recommendation && (
                    <div className="p-3.5 rounded-xl bg-space-cyan/10 border border-space-cyan/30 space-y-2 mt-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-space-cyan flex items-center space-x-1.5">
                          <Target className="w-3.5 h-3.5" />
                          <span>Candidate Next Observation Proposal</span>
                        </span>
                        <span className="px-2 py-0.5 rounded bg-space-cyan/20 text-space-cyan font-bold text-[10px]">
                          Expected Gain: +{(explanation.recommendation.expected_uncertainty_reduction * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="text-xs text-lunar-200">
                        <span className="text-lunar-400">Target Sensor:</span>{' '}
                        <span className="font-bold text-space-cyan">
                          {explanation.recommendation.candidate_observation}
                        </span>
                      </div>
                      {explanation.recommendation.operational_requirements && (
                        <p className="text-[11px] text-lunar-300">
                          {explanation.recommendation.operational_requirements}
                        </p>
                      )}
                      {explanation.recommendation.disclaimer && (
                        <div className="text-[10px] text-amber-300/80 italic">
                          *{explanation.recommendation.disclaimer}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* TAB 5: STEP-BY-STEP DECISION TRACE */}
          {activeTab === 'TRACE' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-lunar-100 flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-space-cyan" />
                    <span>Step-by-Step Decision Trace</span>
                  </h3>
                  <p className="text-[11px] text-lunar-400 mt-0.5">
                    Chronological reasoning execution path through the LunarSynapse World Model.
                  </p>
                </div>
                <button
                  onClick={() => setTraceExpanded(!traceExpanded)}
                  className="px-2.5 py-1 rounded bg-lunar-800 text-lunar-300 hover:text-white flex items-center space-x-1 text-[11px]"
                >
                  <span>{traceExpanded ? 'Collapse All' : 'Expand All'}</span>
                  {traceExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              </div>

              <div className="space-y-2">
                {explanation.explainability_trace.map((step) => {
                  const isPass = step.status === 'PASS' || step.status === 'COMPLETED' || step.status === 'ACCEPTED';
                  const isRejected = step.status === 'REJECTED';
                  return (
                    <div
                      key={step.step}
                      className="p-3 rounded-xl bg-lunar-950 border border-lunar-800 flex items-start space-x-3 text-xs"
                    >
                      <div className="w-6 h-6 rounded-full bg-space-cyan/20 border border-space-cyan/40 text-space-cyan flex items-center justify-center font-bold shrink-0 text-[10px]">
                        {step.step}
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-lunar-100">{step.name}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase border ${
                              isRejected
                                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                                : isPass
                                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                                : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                            }`}
                          >
                            {step.status}
                          </span>
                        </div>
                        <p className="text-lunar-300 text-[11px]">{step.reason}</p>
                        <div className="flex items-center space-x-4 text-[10px] text-lunar-500 pt-0.5">
                          <span>Source: {step.source}</span>
                          {step.metric && <span>Metric: {step.metric}</span>}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 6: FULL PROVENANCE */}
          {activeTab === 'PROVENANCE' && (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-lunar-100 flex items-center space-x-2">
                <FileText className="w-4 h-4 text-space-cyan" />
                <span>Full Telemetry Provenance Inspection</span>
              </h3>

              <div className="p-4 rounded-xl bg-lunar-950 border border-lunar-800 space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-lunar-900 border border-lunar-800 space-y-1">
                    <span className="text-[10px] text-lunar-400 font-bold block">SOURCE PRODUCT</span>
                    <div className="text-lunar-200 break-all">{explanation.provenance.source_observation}</div>
                    <div className="text-[10px] text-lunar-400 pt-1">
                      Sensor: {explanation.provenance.sensor_source} | GSD: {explanation.provenance.source_gsd_m} m
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-lunar-900 border border-lunar-800 space-y-1">
                    <span className="text-[10px] text-lunar-400 font-bold block">TARGET PRODUCT</span>
                    <div className="text-lunar-200 break-all">{explanation.provenance.target_observation}</div>
                    <div className="text-[10px] text-lunar-400 pt-1">
                      Sensor: {explanation.provenance.sensor_target} | GSD: {explanation.provenance.target_gsd_m} m
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">DEM Source</span>
                    <span className="text-xs font-bold text-lunar-200">{explanation.provenance.dem_source}</span>
                  </div>
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Matcher</span>
                    <span className="text-xs font-bold text-space-cyan">{explanation.provenance.matcher}</span>
                  </div>
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Processing Stage</span>
                    <span className="text-xs font-bold text-lunar-200">{explanation.provenance.processing_stage}</span>
                  </div>
                  <div className="p-2 rounded bg-lunar-900 border border-lunar-800">
                    <span className="text-[10px] text-lunar-400 block">Derived Status</span>
                    <span className="text-xs font-bold text-amber-300">{explanation.provenance.derived_status}</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-lunar-900/60 border border-lunar-800 text-[11px] text-lunar-300 leading-relaxed">
                  <span className="font-bold text-space-cyan">Provenance Class: </span>
                  {explanation.provenance.data_provenance}
                </div>
              </div>
            </div>
          )}

          {/* Persistent Limitations Footer */}
          <div className="p-4 rounded-xl bg-lunar-950 border border-lunar-800 space-y-1.5 shrink-0">
            <span className="text-[10px] uppercase font-bold text-lunar-400 flex items-center space-x-1.5">
              <Info className="w-3.5 h-3.5" />
              <span>Scientific Limitations & Ground Truth Disclaimers</span>
            </span>
            <ul className="text-[10px] text-lunar-400 list-disc list-inside space-y-0.5">
              {explanation.limitations.map((lim, idx) => (
                <li key={idx}>{lim}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
