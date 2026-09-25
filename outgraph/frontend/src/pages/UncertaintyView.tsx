import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  HelpCircle,
  ShieldAlert,
  Info,
  RefreshCw,
  XCircle,
  Sliders,
  TrendingDown,
  Layers,
} from 'lucide-react';
import { Correspondence, UncertaintyResponse, UncertaintySummaryResponse } from '../types';
import { api } from '../services/api';

interface UncertaintyViewProps {
  correspondences: Correspondence[];
}

export const UncertaintyView: React.FC<UncertaintyViewProps> = ({ correspondences }) => {
  const [selectedCorrId, setSelectedCorrId] = useState<string>(
    correspondences[0]?.id || ''
  );
  const [uncertaintyData, setUncertaintyData] = useState<UncertaintyResponse | null>(null);
  const [summaryData, setSummaryData] = useState<UncertaintySummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const s = await api.getUncertaintySummary();
        setSummaryData(s);
      } catch (err) {
        console.error('Failed to load uncertainty summary', err);
      }
    };
    fetchSummary();
  }, []);

  useEffect(() => {
    if (!selectedCorrId && correspondences.length > 0) {
      const realCorr = correspondences.find((c) => !c.is_synthetic);
      setSelectedCorrId(realCorr ? realCorr.id : correspondences[0].id);
    }
  }, [correspondences, selectedCorrId]);

  useEffect(() => {
    if (!selectedCorrId) return;

    const loadUncertainty = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await api.getUncertainty(selectedCorrId);
        setUncertaintyData(data);
      } catch (err: any) {
        console.error('Failed to load uncertainty detail', err);
        setError(err?.message || 'Uncertainty service unavailable.');
      } finally {
        setIsLoading(false);
      }
    };

    loadUncertainty();
  }, [selectedCorrId]);

  const selectedCorr = correspondences.find((c) => c.id === selectedCorrId);
  const isReal = selectedCorr && !selectedCorr.is_synthetic;

  return (
    <div className="space-y-6 font-sans">
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] uppercase font-extrabold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
              BAYESIAN & EPISTEMIC UQ
            </span>
            <span className="text-xs text-slate-600 font-bold">Multi-Factor Uncertainty Decomposition</span>
          </div>
          <h1 className="text-2xl font-extrabold text-[#0d2247] mt-1 flex items-center space-x-2 tracking-tight">
            <Activity className="w-6 h-6 text-amber-600" />
            <span>Uncertainty Quantification Dashboard</span>
          </h1>
          <p className="text-xs text-slate-700 font-semibold mt-0.5">
            Decomposed scalar, 95% confidence interval, covariance proxy, and qualitative epistemic risk metrics.
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

      {/* Mandatory Calibration & Saturation Disclaimers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-amber-50/70 p-5 rounded-2xl border border-amber-300 space-y-2 shadow-sm">
          <div className="flex items-center space-x-2 text-xs font-extrabold text-amber-900 uppercase">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>MANDATORY CALIBRATION LIMITATION</span>
          </div>
          <p className="text-xs text-amber-950 font-extrabold uppercase tracking-wide">
            REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED
          </p>
          <p className="text-[11px] text-slate-800 font-semibold leading-relaxed">
            Current mathematical values represent computational bayesian proxies and evidence variances. They are not to be interpreted as empirically ground-truthed real-lunar probabilities.
          </p>
        </div>

        <div className="bg-blue-50/70 p-5 rounded-2xl border border-blue-300 space-y-2 shadow-sm">
          <div className="flex items-center space-x-2 text-xs font-extrabold text-blue-900 uppercase">
            <Info className="w-4 h-4 text-blue-600 shrink-0" />
            <span>SATURATION LIMITATION PRESERVATION</span>
          </div>
          <p className="text-xs text-slate-900 font-extrabold">
            Feature-dispersion uncertainty saturates above 4 px.
          </p>
          <p className="text-[11px] text-slate-800 font-semibold leading-relaxed">
            To prevent unbounded divergent variance estimators, sub-pixel reprojection dispersion saturates deterministically at the &gt;4.0 px threshold.
          </p>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="p-8 text-center text-xs text-slate-700 font-bold flex items-center justify-center space-x-2 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
          <span>Computing uncertainty decomposition from backend...</span>
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="p-5 rounded-2xl bg-rose-50 border border-rose-300 text-xs text-rose-950 flex items-center space-x-3 shadow-sm">
          <XCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <div>
            <div className="font-extrabold">Uncertainty service unavailable</div>
            <div className="text-[11px] text-rose-800 font-semibold">{error}</div>
          </div>
        </div>
      )}

      {/* Detailed Uncertainty Breakdown */}
      {!isLoading && uncertaintyData && (
        <div className="space-y-6">
          {/* Main 4 UQ Modalities Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* SCALAR */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-extrabold block">
                  1. SCALAR UNCERTAINTY
                </span>
                <div className="text-3xl font-extrabold text-[#0d2247] mt-1 font-mono">
                  {uncertaintyData.scalar.toFixed(4)}
                </div>
                <span className="text-[10px] text-slate-600 font-bold block mt-1">
                  Normalized [0.0 - 1.0] scale
                </span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mt-4 border border-slate-200">
                <div
                  className="h-full rounded-full bg-amber-500"
                  style={{ width: `${Math.round(uncertaintyData.scalar * 100)}%` }}
                />
              </div>
            </div>

            {/* INTERVAL */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-extrabold block">
                  2. 95% CONFIDENCE INTERVAL
                </span>
                <div className="text-xl font-extrabold text-blue-700 mt-1 font-mono">
                  [{uncertaintyData.interval.lower.toFixed(3)}, {uncertaintyData.interval.upper.toFixed(3)}]
                </div>
                <span className="text-[10px] text-slate-600 font-bold block mt-1">
                  Confidence level: {(uncertaintyData.interval.confidence_level * 100).toFixed(0)}%
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-[10px] text-slate-800 font-extrabold mt-3 font-mono">
                Spread: {(uncertaintyData.interval.upper - uncertaintyData.interval.lower).toFixed(3)}
              </div>
            </div>

            {/* QUALITATIVE */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-extrabold block">
                  3. QUALITATIVE SEMANTICS
                </span>
                <div
                  className={`text-xl font-extrabold mt-1 ${
                    uncertaintyData.qualitative === 'LOW'
                      ? 'text-emerald-700'
                      : uncertaintyData.qualitative === 'MODERATE'
                      ? 'text-amber-700'
                      : 'text-rose-700'
                  }`}
                >
                  {uncertaintyData.qualitative}
                </div>
                <span className="text-[10px] text-slate-600 font-bold block mt-1">
                  Epistemic classification
                </span>
              </div>
              <div className="text-[10px] text-slate-800 font-extrabold p-2.5 rounded-xl bg-slate-50 border border-slate-200 mt-3">
                Status: {uncertaintyData.calibration_status}
              </div>
            </div>

            {/* UNKNOWN != NEGATIVE PRESERVATION */}
            <div className="bg-blue-50/80 p-5 rounded-2xl border border-blue-200 shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-[10px] text-blue-900 uppercase font-extrabold block">
                  4. EPISTEMIC STATUS
                </span>
                <div className="text-sm font-extrabold text-blue-900 mt-1">
                  UNKNOWN ≠ NEGATIVE
                </div>
                <span className="text-[10px] text-slate-700 font-semibold block mt-1">
                  Unobserved values preserved
                </span>
              </div>
              <div className="text-[10px] text-blue-950 font-extrabold p-2.5 rounded-xl bg-white border border-blue-200 mt-3">
                Missing data ≠ Negative proof
              </div>
            </div>
          </div>

          {/* Covariance Matrix Proxy & Decomposition */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Covariance Proxy Matrix */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-extrabold uppercase text-[#0d2247]">
                  Covariance Proxy Matrix (2x2)
                </span>
                <span className="text-[10px] text-slate-500 font-bold">
                  Dispersion × Disagreement
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="grid grid-cols-2 gap-3 text-center">
                  <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-sm">
                    <span className="text-[10px] text-slate-500 font-bold block">Var(X)</span>
                    <span className="text-base font-extrabold text-slate-900 font-mono">
                      {uncertaintyData.covariance_proxy[0]?.[0]?.toFixed(4) ?? '0.0000'}
                    </span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-sm">
                    <span className="text-[10px] text-slate-500 font-bold block">Cov(X, Y)</span>
                    <span className="text-base font-extrabold text-blue-700 font-mono">
                      {uncertaintyData.covariance_proxy[0]?.[1]?.toFixed(4) ?? '0.0000'}
                    </span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-sm">
                    <span className="text-[10px] text-slate-500 font-bold block">Cov(Y, X)</span>
                    <span className="text-base font-extrabold text-blue-700 font-mono">
                      {uncertaintyData.covariance_proxy[1]?.[0]?.toFixed(4) ?? '0.0000'}
                    </span>
                  </div>
                  <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-sm">
                    <span className="text-[10px] text-slate-500 font-bold block">Var(Y)</span>
                    <span className="text-base font-extrabold text-slate-900 font-mono">
                      {uncertaintyData.covariance_proxy[1]?.[1]?.toFixed(4) ?? '0.0000'}
                    </span>
                  </div>
                </div>
              </div>
              <p className="text-[11px] text-slate-600 font-semibold leading-relaxed">
                Represents joint uncertainty across feature space alignment and multi-pillar evidence disagreement.
              </p>
            </div>

            {/* Epistemic Decomposition Factors */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <span className="text-xs font-extrabold uppercase text-[#0d2247] block">
                Epistemic Decomposition Factors
              </span>

              <div className="space-y-4 text-xs font-bold">
                <div>
                  <div className="flex justify-between text-slate-800 mb-1.5">
                    <span>Evidence Disagreement:</span>
                    <span className="font-extrabold text-amber-700 font-mono">
                      {uncertaintyData.decomposition.evidence_disagreement.toFixed(4)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200">
                    <div
                      className="h-full bg-amber-500 rounded-full"
                      style={{
                        width: `${Math.round(
                          uncertaintyData.decomposition.evidence_disagreement * 100
                        )}%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-800 mb-1.5">
                    <span>Geometric Instability:</span>
                    <span className="font-extrabold text-rose-700 font-mono">
                      {uncertaintyData.decomposition.geometric_instability.toFixed(4)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200">
                    <div
                      className="h-full bg-rose-500 rounded-full"
                      style={{
                        width: `${Math.round(
                          uncertaintyData.decomposition.geometric_instability * 100
                        )}%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-800 mb-1.5">
                    <span>Feature Ambiguity:</span>
                    <span className="font-extrabold text-blue-700 font-mono">
                      {uncertaintyData.decomposition.feature_ambiguity.toFixed(4)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200">
                    <div
                      className="h-full bg-blue-600 rounded-full"
                      style={{
                        width: `${Math.round(
                          uncertaintyData.decomposition.feature_ambiguity * 100
                        )}%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-slate-800 mb-1.5">
                    <span>Spatial Sparsity:</span>
                    <span className="font-extrabold text-indigo-700 font-mono">
                      {uncertaintyData.decomposition.spatial_sparsity.toFixed(4)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200">
                    <div
                      className="h-full bg-indigo-600 rounded-full"
                      style={{
                        width: `${Math.round(
                          uncertaintyData.decomposition.spatial_sparsity * 100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

