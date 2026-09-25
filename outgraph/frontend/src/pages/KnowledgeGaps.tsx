import React, { useState, useEffect } from 'react';
import { KnowledgeGap } from '../types';
import { AlertCircle, Target, ArrowRight, ShieldAlert, CheckCircle2, RefreshCw, XCircle, Info } from 'lucide-react';
import { api } from '../services/api';

interface KnowledgeGapsProps {
  gaps: KnowledgeGap[];
  onNavigateToRecommendation: () => void;
}

export const KnowledgeGaps: React.FC<KnowledgeGapsProps> = ({
  gaps: initialGaps,
  onNavigateToRecommendation,
}) => {
  const [gaps, setGaps] = useState<KnowledgeGap[]>(initialGaps);
  const [supportedTypes, setSupportedTypes] = useState<string[]>([]);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchGaps = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const g = await api.getKnowledgeGaps();
      setGaps(g);
      const typesRes = await api.getKnowledgeGapTypes();
      if (typesRes?.supported_gap_types) {
        setSupportedTypes(typesRes.supported_gap_types);
      }
    } catch (err: any) {
      console.error('Failed to load knowledge gaps', err);
      setError(err?.message || 'Knowledge gap service unavailable.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (initialGaps.length === 0) {
      fetchGaps();
    }
  }, []);

  const getSeverityStyle = (sev: string): string => {
    const s = sev.toUpperCase();
    if (s === 'HIGH') return 'bg-rose-100 text-rose-800 border-rose-300 font-extrabold';
    if (s === 'MEDIUM') return 'bg-amber-100 text-amber-800 border-amber-300 font-extrabold';
    return 'bg-blue-100 text-blue-800 border-blue-300 font-extrabold';
  };

  const filteredGaps = filterType === 'ALL'
    ? gaps
    : gaps.filter((g) => g.gap_type === filterType);

  const gapDescriptions: Record<string, string> = {
    MISSING_MODALITY: 'Critical spectral or elevation sensor data missing for cross-modal fusion.',
    MISSING_TEMPORAL_OBSERVATION: 'Single-epoch observation lacks multi-temporal baseline under different solar illumination.',
    MISSING_GEOMETRIC_VALIDATION: 'Insufficient pushbroom GroundGrid inliers to establish homographic transformation.',
    MISSING_TERRAIN_VALIDATION: 'Topographic slope corridor in DEM SLDEM2015 unverified.',
    MISSING_SPECTRAL_VALIDATION: 'Hyperspectral band alignment (IIRS 0.8-5.0um) unconfirmed.',
    INSUFFICIENT_CORRESPONDENCE: 'Fewer than minimum required geometric tie points across image footprints.',
    FOOTPRINT_NON_OVERLAP: 'GroundGrid spatial polygons do not intersect. Observed separation prevents direct registration.',
    UNCERTAINTY_TOO_HIGH: 'Epistemic uncertainty or feature dispersion saturates beyond acceptable decision threshold.',
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] uppercase font-extrabold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300">
              EPISTEMIC STATE TRACKER
            </span>
            <span className="text-xs text-slate-600 font-bold">8 Supported Epistemic Taxonomies</span>
          </div>
          <h1 className="text-2xl font-extrabold text-[#0d2247] mt-1 flex items-center space-x-2 tracking-tight">
            <AlertCircle className="w-6 h-6 text-amber-500" />
            <span>Autonomous Knowledge Gap Engine</span>
          </h1>
          <p className="text-xs text-slate-700 font-semibold mt-0.5">
            Systematic detection of unobserved modalities, physical non-overlap, and high epistemic uncertainty.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchGaps}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-white hover:bg-slate-100 text-xs font-bold text-slate-800 border border-slate-300 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-blue-600 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Gaps</span>
          </button>
          <button
            onClick={onNavigateToRecommendation}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-blue-700 hover:bg-blue-800 text-white font-bold text-xs shadow-md transition-all shrink-0 active:scale-95"
          >
            <Target className="w-4 h-4" />
            <span>Next-Best Observation Targeting</span>
          </button>
        </div>
      </div>

      {/* Mandatory Scientific Explanation Card */}
      <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 flex items-start space-x-3 text-xs shadow-sm">
        <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-extrabold text-amber-900 uppercase text-[11px]">
            SCIENTIFIC PRINCIPLE: KNOWLEDGE GAP IS MISSING INFORMATION, NOT A FAILED ENTITY
          </span>
          <p className="text-slate-800 leading-relaxed font-semibold">
            A knowledge gap signifies an unobserved parameter or geometric constraint (e.g. lack of multi-solar angle baseline, unacquired spectral bands, or footprint non-overlap). It directs future orbital collection rather than invalidating a physical lunar crater or boulder entity.
          </p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-700 font-extrabold mr-2">Filter Taxonomy:</span>
        <button
          onClick={() => setFilterType('ALL')}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-bold border transition-all ${
            filterType === 'ALL'
              ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
              : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
          }`}
        >
          ALL ({gaps.length})
        </button>
        {supportedTypes.map((t) => {
          const count = gaps.filter((g) => g.gap_type === t).length;
          return (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                filterType === t
                  ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                  : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
              }`}
            >
              {t} {count > 0 && `(${count})`}
            </button>
          );
        })}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="p-8 text-center text-xs text-slate-700 font-bold flex items-center justify-center space-x-2 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
          <span>Scanning World Model for active epistemic knowledge gaps...</span>
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="p-5 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center space-x-3 shadow-sm">
          <XCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <div>
            <div className="font-extrabold">Knowledge Gap Engine Unavailable</div>
            <div className="text-[11px] text-rose-700 font-medium">{error}</div>
          </div>
        </div>
      )}

      {/* Prioritized Gaps List - Ultra High-Contrast Clean Cards */}
      {!isLoading && (
        <div className="space-y-4">
          {filteredGaps.map((gap) => (
            <div
              key={gap.id}
              className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-slate-300 transition-all"
            >
              <div className="space-y-2 max-w-3xl">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`text-[10px] uppercase font-extrabold px-2.5 py-0.5 rounded-full border ${getSeverityStyle(
                      gap.severity
                    )}`}
                  >
                    {gap.severity} SEVERITY
                  </span>
                  <span className="text-sm font-extrabold text-[#0d2247]">{gap.gap_type}</span>
                  <span className="text-xs text-slate-700 font-bold">Target Entity: <strong className="text-slate-900 font-mono">{gap.entity_id}</strong></span>
                  {gap.is_synthetic && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 font-extrabold border border-purple-200">
                      SYNTHETIC
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-900 font-bold leading-relaxed">{gap.reason}</p>
                <div className="text-[11px] text-slate-600 font-semibold italic">
                  {gapDescriptions[gap.gap_type] || 'Epistemic uncertainty identified in observation graph.'}
                </div>
              </div>

              {/* Recommended Target Action */}
              <div className="flex items-center space-x-4 shrink-0">
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 font-extrabold block uppercase">RECOMMENDED TARGET SENSOR</span>
                  <span className="text-xs font-extrabold text-blue-700 bg-blue-50 px-3 py-1 rounded-xl border border-blue-200 inline-block mt-0.5">
                    {gap.recommended_sensor} Payload
                  </span>
                </div>
                <button
                  onClick={onNavigateToRecommendation}
                  className="p-3 rounded-xl bg-blue-700 hover:bg-blue-800 text-white shadow-md transition-all"
                  title="Target Next Observation"
                >
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}

          {filteredGaps.length === 0 && (
            <div className="p-12 text-center text-xs text-slate-600 font-bold bg-white rounded-2xl border border-slate-200 shadow-sm">
              No knowledge gaps matching current filter. Run demo mission to evaluate observations.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
