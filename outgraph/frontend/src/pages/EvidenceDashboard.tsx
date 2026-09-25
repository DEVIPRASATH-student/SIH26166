import React, { useState, useEffect } from 'react';
import {
  Layers,
  HelpCircle,
  AlertCircle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Info,
  ShieldCheck,
  Eye,
} from 'lucide-react';
import { Correspondence, EvidenceDetailResponse } from '../types';
import { api } from '../services/api';

interface EvidenceDashboardProps {
  correspondences: Correspondence[];
}

export const EvidenceDashboard: React.FC<EvidenceDashboardProps> = ({
  correspondences,
}) => {
  const [selectedCorrId, setSelectedCorrId] = useState<string>(
    correspondences[0]?.id || ''
  );
  const [evidenceData, setEvidenceData] = useState<EvidenceDetailResponse | null>(null);
  const [availableDimensions, setAvailableDimensions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDims = async () => {
      try {
        const res = await api.getEvidenceDimensions();
        if (res?.dimensions) {
          setAvailableDimensions(res.dimensions);
        }
      } catch (err) {
        console.error('Failed to load dimensions', err);
      }
    };
    fetchDims();
  }, []);

  useEffect(() => {
    if (!selectedCorrId && correspondences.length > 0) {
      const realCorr = correspondences.find((c) => !c.is_synthetic);
      setSelectedCorrId(realCorr ? realCorr.id : correspondences[0].id);
    }
  }, [correspondences, selectedCorrId]);

  useEffect(() => {
    if (!selectedCorrId) return;

    const loadEvidence = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await api.getEvidence(selectedCorrId);
        setEvidenceData(data);
      } catch (err: any) {
        console.error('Failed to load evidence', err);
        setError(err?.message || 'Evidence service unavailable.');
      } finally {
        setIsLoading(false);
      }
    };

    loadEvidence();
  }, [selectedCorrId]);

  const default11Dimensions = [
    'GEOMETRIC',
    'TERRAIN',
    'ILLUMINATION',
    'SPECTRAL',
    'SCALE',
    'TEMPORAL',
    'TEXTURE',
    'REGISTRATION',
    'PHYSICAL',
    'MANUAL',
    'SYNTHETIC',
  ];

  const dimensionsToDisplay =
    availableDimensions.length > 0 ? availableDimensions : default11Dimensions;

  const selectedCorr = correspondences.find((c) => c.id === selectedCorrId);
  const isReal = selectedCorr && !selectedCorr.is_synthetic;

  return (
    <div className="space-y-6 font-sans">
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] uppercase font-extrabold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-900 border border-blue-300">
              MULTI-PILLAR EPISTEMIC FRAMEWORK
            </span>
            <span className="text-xs text-slate-600 font-bold">11 Orthogonal Evidence Dimensions</span>
          </div>
          <h1 className="text-2xl font-extrabold text-[#0d2247] mt-1 flex items-center space-x-2 tracking-tight">
            <Layers className="w-6 h-6 text-blue-600" />
            <span>Evidence Verification Dashboard</span>
          </h1>
          <p className="text-xs text-slate-700 font-semibold mt-0.5">
            Multi-modal remote sensing verification spanning geometry, shadow physics, topographic slopes, and spectral coherence.
          </p>
        </div>

        {/* Task Selector */}
        <div className="flex items-center space-x-3">
          <label className="text-xs text-slate-700 font-extrabold">Target Correspondence:</label>
          <select
            value={selectedCorrId}
            onChange={(e) => setSelectedCorrId(e.target.value)}
            className="bg-white border border-slate-300 text-xs text-slate-900 font-bold px-3 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600 shadow-sm max-w-xs truncate"
          >
            {correspondences.map((c) => (
              <option key={c.id} value={c.id}>
                {c.is_synthetic ? '[SYNTH]' : '[REAL]'} {c.id.substring(0, 38)}... — {c.status}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Mandatory Scientific Guardrail: UNKNOWN != NEGATIVE */}
      <div className="p-5 rounded-2xl border border-blue-200 bg-blue-50/60 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-blue-100 border border-blue-300 flex items-center justify-center text-blue-700 shrink-0">
            <HelpCircle className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-extrabold text-blue-900 tracking-wide uppercase">
                MANDATORY AXIOM: UNKNOWN ≠ NEGATIVE
              </span>
              <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-900 font-extrabold border border-blue-300">
                PRESERVED
              </span>
            </div>
            <p className="text-xs text-slate-800 font-semibold mt-1 leading-relaxed max-w-3xl">
              "Missing evidence is represented as unknown rather than interpreted as negative evidence." Unobserved sensors (e.g. unacquired IIRS hyperspectral bands or uncalibrated illumination) create epistemic knowledge gaps, not negative physical proof.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0 text-xs font-bold">
          <span className="text-slate-600">Provenience Mode:</span>
          <span
            className={`font-extrabold px-3 py-1 rounded-full text-[11px] uppercase border ${
              isReal
                ? 'bg-amber-100 text-amber-900 border-amber-300'
                : 'bg-purple-100 text-purple-900 border-purple-300'
            }`}
          >
            {isReal ? 'REAL LUNAR OBSERVATION' : 'SYNTHETIC CONTROLLED'}
          </span>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="p-8 text-center text-xs text-slate-700 font-bold flex items-center justify-center space-x-2 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
          <span>Retrieving multi-dimensional evidence profile...</span>
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="p-5 rounded-2xl bg-rose-50 border border-rose-300 text-xs text-rose-950 flex items-center space-x-3 shadow-sm">
          <XCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <div>
            <div className="font-extrabold">Evidence service unavailable</div>
            <div className="text-[11px] text-rose-800 font-semibold">{error}</div>
          </div>
        </div>
      )}

      {/* 11 Evidence Dimensions Grid */}
      {!isLoading && evidenceData && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold uppercase text-[#0d2247]">
              11 Scientific Evidence Dimensions Profile
            </span>
            <span className="text-[11px] text-slate-600 font-extrabold">
              Confidence: {Math.round(evidenceData.overall_confidence * 100)}% | Uncertainty: {evidenceData.total_uncertainty.toFixed(3)}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {dimensionsToDisplay.map((dim) => {
              const score = evidenceData.dimensions[dim] ?? 0.0;
              const isMissing = score === 0.0 && !['MANUAL', 'SYNTHETIC'].includes(dim);
              const isHigh = score >= 0.7;
              const isModerate = score > 0.3 && score < 0.7;

              let statusText = 'ACTIVE';
              let badgeStyle = 'bg-blue-100 text-blue-900 border-blue-300';

              if (isMissing) {
                statusText = 'UNKNOWN (MISSING)';
                badgeStyle = 'bg-amber-100 text-amber-900 border-amber-300';
              } else if (isHigh) {
                statusText = 'STRONGLY SUPPORTING';
                badgeStyle = 'bg-emerald-100 text-emerald-900 border-emerald-300';
              } else if (isModerate) {
                statusText = 'MODERATE EVIDENCE';
                badgeStyle = 'bg-blue-100 text-blue-900 border-blue-300';
              } else {
                statusText = 'LOW / INSUFFICIENT';
                badgeStyle = 'bg-rose-100 text-rose-900 border-rose-300';
              }

              return (
                <div
                  key={dim}
                  className={`bg-white p-4 rounded-2xl border flex flex-col justify-between space-y-3 shadow-sm transition-all ${
                    isMissing
                      ? 'border-amber-300 bg-amber-50/40'
                      : isHigh
                      ? 'border-emerald-300 bg-emerald-50/40'
                      : 'border-slate-200'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-extrabold text-[#0d2247]">{dim}</span>
                      <span className={`text-[9px] font-extrabold px-2 py-0.5 rounded-full border ${badgeStyle}`}>
                        {statusText}
                      </span>
                    </div>

                    <div className="flex items-baseline space-x-2 mt-1">
                      <span className="text-xl font-extrabold font-mono text-slate-900">
                        {isMissing ? 'N/A' : score.toFixed(3)}
                      </span>
                      <span className="text-[10px] text-slate-500 font-semibold">
                        {isMissing ? '(Unobserved dimension)' : 'normalized [0.0 - 1.0]'}
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mt-3 border border-slate-200">
                      <div
                        className={`h-full rounded-full ${
                          isMissing
                            ? 'bg-amber-500'
                            : isHigh
                            ? 'bg-emerald-600'
                            : isModerate
                            ? 'bg-blue-600'
                            : 'bg-rose-500'
                        }`}
                        style={{ width: `${Math.round(score * 100)}%` }}
                      />
                    </div>
                  </div>

                  <div className="text-[10px] text-slate-600 font-medium pt-2 border-t border-slate-100">
                    {isMissing ? (
                      <span className="text-amber-800 font-semibold italic">
                        Missing evidence is preserved as unknown, never penalized as negative proof.
                      </span>
                    ) : (
                      <span>Empirical pillar score evaluated from sensor ephemeris & physics.</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Supporting vs Missing Evidence Split Panels */}
      {!isLoading && evidenceData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Supporting Evidence */}
          <div className="bg-white p-5 rounded-2xl border border-emerald-300 shadow-sm space-y-3">
            <div className="flex items-center space-x-2 text-xs font-extrabold text-emerald-800 uppercase">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Supporting Evidence Dimensions ({evidenceData.supporting_evidence.length})</span>
            </div>
            {evidenceData.supporting_evidence.length > 0 ? (
              <div className="space-y-2 text-xs font-bold">
                {evidenceData.supporting_evidence.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900"
                  >
                    {item}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-500 font-medium italic p-4 rounded-xl bg-slate-50 border border-slate-200">
                No dimensions currently cross the high-confidence supporting threshold (&gt;0.60).
              </div>
            )}
          </div>

          {/* Missing Evidence (Explicitly Preserved, Never Hidden) */}
          <div className="bg-white p-5 rounded-2xl border border-amber-300 shadow-sm space-y-3">
            <div className="flex items-center space-x-2 text-xs font-extrabold text-amber-800 uppercase">
              <HelpCircle className="w-4 h-4 text-amber-600" />
              <span>Missing Evidence Dimensions ({evidenceData.missing_evidence.length})</span>
            </div>
            {evidenceData.missing_evidence.length > 0 ? (
              <div className="space-y-2 text-xs font-bold">
                {evidenceData.missing_evidence.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-center justify-between"
                  >
                    <span>{item}</span>
                    <span className="text-[10px] text-amber-800 font-extrabold uppercase px-2 py-0.5 rounded-full bg-amber-100 border border-amber-300">
                      Preserved As Unknown
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-slate-500 font-medium italic p-4 rounded-xl bg-slate-50 border border-slate-200">
                All 11 evidence dimensions active in current evaluation.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

