import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  HelpCircle,
  ArrowRight,
  Layers,
  Activity,
  Compass,
} from 'lucide-react';
import {
  Correspondence,
  PhysicalVerificationResponse,
  GateCatalogResponse,
  GateCatalogEntry,
} from '../types';
import { api } from '../services/api';

interface PhysicalVerificationPageProps {
  correspondences: Correspondence[];
  onSelectCorrespondence?: (id: string) => void;
}

export const PhysicalVerificationPage: React.FC<PhysicalVerificationPageProps> = ({
  correspondences,
}) => {
  const [selectedCorrId, setSelectedCorrId] = useState<string>(
    correspondences[0]?.id || ''
  );
  const [catalog, setCatalog] = useState<Record<string, GateCatalogEntry>>({});
  const [verificationData, setVerificationData] = useState<PhysicalVerificationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load catalog and initial correspondence verification
  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        const catRes = await api.getPhysicalGates();
        if (catRes?.gates) {
          setCatalog(catRes.gates);
        }
      } catch (err) {
        console.error('Failed to load physical gates catalog', err);
      }
    };
    fetchCatalog();
  }, []);

  useEffect(() => {
    if (!selectedCorrId && correspondences.length > 0) {
      // Prefer real negative control if available
      const realCorr = correspondences.find((c) => !c.is_synthetic);
      setSelectedCorrId(realCorr ? realCorr.id : correspondences[0].id);
    }
  }, [correspondences, selectedCorrId]);

  useEffect(() => {
    if (!selectedCorrId) return;

    const loadVerification = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await api.getPhysicalVerification(selectedCorrId);
        setVerificationData(data);
      } catch (err: any) {
        console.error('Failed to load physical verification', err);
        setError(err?.message || 'Physical verification service unavailable.');
      } finally {
        setIsLoading(false);
      }
    };

    loadVerification();
  }, [selectedCorrId]);

  const gateKeys = ['GATE1', 'GATE2', 'GATE3', 'GATE4', 'GATE5', 'GATE6'];

  const selectedCorr = correspondences.find((c) => c.id === selectedCorrId);
  const isReal = selectedCorr && !selectedCorr.is_synthetic;

  return (
    <div className="space-y-6 font-sans">
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] uppercase font-extrabold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-900 border border-blue-300">
              PHASE 3 RIGID KINEMATIC GATES
            </span>
            <span className="text-xs text-slate-600 font-bold">Deterministic Physical Verification</span>
          </div>
          <h1 className="text-2xl font-extrabold text-[#0d2247] mt-1 flex items-center space-x-2 tracking-tight">
            <ShieldCheck className="w-6 h-6 text-blue-600" />
            <span>Six-Gate Physical Verification Engine</span>
          </h1>
          <p className="text-xs text-slate-700 font-semibold mt-0.5">
            Physical verification cannot be bypassed. Visual similarity without orbital ephemeris, topography, and GroundGrid ray-consistency is rejected.
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

      {/* Provenance & Decision Banner */}
      <div
        className={`p-5 rounded-2xl border shadow-sm transition-all ${
          verificationData?.passed
            ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
            : 'bg-rose-50 border-rose-300 text-rose-950'
        }`}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span
                className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase border ${
                  isReal
                    ? 'bg-amber-100 text-amber-900 border-amber-300'
                    : 'bg-purple-100 text-purple-900 border-purple-300'
                }`}
              >
                {isReal ? 'REAL LUNAR DATA' : 'SYNTHETIC CONTROLLED DATA'}
              </span>
              <span className="text-xs text-slate-700 font-bold">
                Evaluation ID: <strong className="font-mono text-slate-900">{selectedCorrId}</strong>
              </span>
            </div>
            <div className="text-lg font-extrabold text-[#0d2247]">
              PHYSICAL STATUS:{' '}
              <span
                className={
                  verificationData?.passed ? 'text-emerald-700 font-extrabold' : 'text-rose-700 font-extrabold'
                }
              >
                {verificationData?.status || (isLoading ? 'EVALUATING...' : 'UNKNOWN')}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4 text-xs">
            <div className="text-right">
              <span className="text-slate-500 text-[10px] font-extrabold block uppercase">EMPIRICAL ACCURACY</span>
              <span className="font-extrabold text-slate-900">
                {isReal ? 'N/A (Empirical)' : 'SYNTHETIC BENCHMARK ONLY'}
              </span>
            </div>
            <div className="text-right">
              <span className="text-slate-500 text-[10px] font-extrabold block uppercase">PHYSICAL VALIDATION</span>
              <span
                className={`font-extrabold ${
                  verificationData?.passed ? 'text-emerald-700' : 'text-rose-700'
                }`}
              >
                {verificationData?.passed ? 'VALIDATED (SYNTHETIC)' : 'NOT VALIDATED'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Visual Match -> Physics -> Decision Flowchart */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-xs font-extrabold uppercase text-[#0d2247] tracking-wider flex items-center space-x-2">
          <Activity className="w-4 h-4 text-blue-600" />
          <span>VISUAL MATCH ➔ PHYSICS ➔ DECISION ARCHITECTURE</span>
        </h3>

        <div className="flex flex-col md:flex-row items-center justify-between gap-3 text-xs">
          <div className="w-full md:w-1/4 p-4 rounded-xl bg-amber-50 border border-amber-200 text-center">
            <span className="text-[10px] text-amber-900 font-extrabold block uppercase">1. VISUAL HYPOTHESIS</span>
            <span className="text-slate-900 font-bold block mt-1">Feature Extraction</span>
            <span className="text-[10px] text-slate-600 font-semibold block mt-0.5">
              Candidate Keypoints: {selectedCorr?.candidate_count ?? selectedCorr?.num_candidate_matches ?? 'N/A'}
            </span>
          </div>

          <ArrowRight className="w-5 h-5 text-slate-400 shrink-0 hidden md:block" />

          <div className="w-full md:w-2/4 p-4 rounded-xl bg-blue-50 border border-blue-200 text-center">
            <span className="text-[10px] text-blue-900 font-extrabold block uppercase">2. SIX RIGID PHYSICAL GATES</span>
            <span className="text-slate-900 font-bold block mt-1">GroundGrid, DEM Topography, Pushbroom Ray-Casting</span>
            <span className="text-[10px] text-blue-800 font-semibold block mt-0.5">
              Zero tolerance for out-of-bounds, boundary clamping, or excessive residual
            </span>
          </div>

          <ArrowRight className="w-5 h-5 text-slate-400 shrink-0 hidden md:block" />

          <div
            className={`w-full md:w-1/4 p-4 rounded-xl border text-center ${
              verificationData?.passed
                ? 'bg-emerald-50 border-emerald-300'
                : 'bg-rose-50 border-rose-300'
            }`}
          >
            <span
              className={`text-[10px] font-extrabold block uppercase ${
                verificationData?.passed ? 'text-emerald-900' : 'text-rose-900'
              }`}
            >
              3. FINAL OUTCOME
            </span>
            <span
              className={`font-extrabold block mt-1 text-sm ${
                verificationData?.passed ? 'text-emerald-800' : 'text-rose-800'
              }`}
            >
              {verificationData?.status || 'EVALUATING'}
            </span>
            <span className="text-[10px] text-slate-700 font-semibold block mt-0.5">
              {verificationData?.passed
                ? 'Passes All Six Kinematic Gates'
                : 'Physically Rejected'}
            </span>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="p-8 text-center text-xs text-slate-700 font-bold flex items-center justify-center space-x-2 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
          <span>Loading physical verification data from backend...</span>
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="p-5 rounded-2xl bg-rose-50 border border-rose-300 text-xs text-rose-950 flex items-center space-x-3 shadow-sm">
          <XCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <div>
            <div className="font-extrabold">Physical verification service unavailable</div>
            <div className="text-[11px] text-rose-800 font-semibold">{error}</div>
          </div>
        </div>
      )}

      {/* Six Physical Gates Detailed Cards */}
      {!isLoading && verificationData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {gateKeys.map((gateKey) => {
            const gateResult = verificationData.gates?.[gateKey];
            const catEntry = catalog[gateKey];

            const status = gateResult?.status || 'NOT_EVALUATED';
            const isPass = status === 'PASS';
            const isRejected = status === 'REJECTED';

            const gateName = gateResult?.gate_name || catEntry?.gate_name || gateKey;
            const threshold = gateResult?.threshold || catEntry?.threshold || 'N/A';
            const observed = gateResult?.observed_value || (isPass ? 'PASS' : isRejected ? 'FAIL' : 'N/A');
            const reason = gateResult?.reason || catEntry?.description || 'Evaluation complete.';

            return (
              <div
                key={gateKey}
                className={`bg-white p-5 rounded-2xl border flex flex-col justify-between space-y-3 shadow-sm transition-all ${
                  isRejected
                    ? 'border-rose-300 bg-rose-50/50'
                    : isPass
                    ? 'border-emerald-300 bg-emerald-50/50'
                    : 'border-slate-200'
                }`}
              >
                <div>
                  {/* Gate Title & Status Badge */}
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-800 border border-slate-300">
                      {gateKey}
                    </span>
                    <span
                      className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full flex items-center space-x-1 border ${
                        isRejected
                          ? 'bg-rose-100 text-rose-900 border-rose-300'
                          : isPass
                          ? 'bg-emerald-100 text-emerald-900 border-emerald-300'
                          : 'bg-slate-100 text-slate-800 border-slate-300'
                      }`}
                    >
                      {isRejected && <XCircle className="w-3.5 h-3.5 text-rose-600" />}
                      {isPass && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
                      <span>{status}</span>
                    </span>
                  </div>

                  <h4 className="text-xs font-extrabold text-[#0d2247] uppercase tracking-tight">
                    {gateName}
                  </h4>
                  <p className="text-[11px] text-slate-700 mt-1 leading-relaxed font-semibold">
                    {catEntry?.description || reason}
                  </p>
                </div>

                {/* Quantitative Threshold & Observed Evaluation */}
                <div className="space-y-2 pt-3 border-t border-slate-200 text-[11px]">
                  <div className="flex justify-between font-semibold">
                    <span className="text-slate-500 font-bold">Threshold:</span>
                    <span className="text-slate-900 font-extrabold text-right max-w-[170px] truncate" title={threshold}>
                      {threshold}
                    </span>
                  </div>
                  <div className="flex justify-between font-semibold">
                    <span className="text-slate-500 font-bold">Observed:</span>
                    <span
                      className={`font-extrabold ${
                        isRejected
                          ? 'text-rose-700'
                          : isPass
                          ? 'text-emerald-700'
                          : 'text-slate-900'
                      }`}
                    >
                      {observed}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-[10px] text-slate-800 font-semibold">
                    <span className="font-extrabold text-slate-900">Outcome: </span>
                    {reason}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Rejection Reasons & Preserved Limitations */}
      {!isLoading && verificationData && verificationData.rejection_reasons?.length > 0 && (
        <div className="bg-rose-50 p-5 rounded-2xl border border-rose-300 space-y-3 shadow-sm">
          <div className="flex items-center space-x-2 text-rose-900 text-xs font-extrabold uppercase">
            <AlertTriangle className="w-4 h-4 text-rose-600" />
            <span>Preserved Rejection Reasons ({verificationData.rejection_reasons.length})</span>
          </div>
          <div className="space-y-2 text-xs text-rose-950 font-semibold">
            {verificationData.rejection_reasons.map((r, i) => (
              <div
                key={i}
                className="p-3 rounded-xl bg-white border border-rose-200 text-rose-900 flex items-start space-x-2 shadow-sm"
              >
                <XCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{r}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

