import React, { useState, useEffect } from 'react';
import { LunarEntity, Recommendation } from '../types';
import { Target, Sparkles, Sliders, CheckCircle2, ArrowUpRight, Zap, Info, AlertTriangle, RefreshCw, XCircle } from 'lucide-react';
import { api } from '../services/api';

interface NextObservationProps {
  entities: LunarEntity[];
}

export const NextObservation: React.FC<NextObservationProps> = ({ entities }) => {
  const [selectedEntityId, setSelectedEntityId] = useState<string>(
    entities[0]?.entity_id || ''
  );
  const [scientificQuestion, setScientificQuestion] = useState<string>('spectral analysis');
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRecommendation = async (entityId: string, question: string) => {
    if (!entityId) return;
    setIsLoading(true);
    setError(null);
    try {
      const rec = await api.getNextObservation(entityId, question);
      setRecommendation(rec);
    } catch (err: any) {
      console.error('Failed to compute recommendation', err);
      setError(err?.message || 'Recommendation service unavailable.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedEntityId) {
      fetchRecommendation(selectedEntityId, scientificQuestion);
    }
  }, [selectedEntityId, scientificQuestion]);

  if (entities.length === 0) {
    return (
      <div className="p-8 text-center font-sans text-xs text-slate-500 bg-white border border-slate-200 rounded-2xl shadow-sm">
        No entities available for next-best observation targeting. Run the demo mission first to populate the world model.
      </div>
    );
  }

  const isPayloadUnavailable =
    recommendation?.payload_status === 'PAYLOAD_UNAVAILABLE';

  return (
    <div className="space-y-6 font-sans">
      {/* Top Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
              INFORMATION GAIN SCHEDULER
            </span>
            <span className="text-xs text-slate-500 font-medium">Target Epistemic Reduction</span>
          </div>
          <h1 className="text-2xl font-extrabold text-[#0d2247] mt-1 flex items-center space-x-2 tracking-tight">
            <Target className="w-6 h-6 text-blue-600" />
            <span>Next-Best Observation Engine</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Calculates Expected Information Gain across payload sensors to prioritize uncertainty-reducing orbital observations.
          </p>
        </div>

        {/* Target Entity & Question Selectors */}
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <label className="text-[10px] text-slate-500 font-bold uppercase block mb-1">Target Entity</label>
            <select
              value={selectedEntityId}
              onChange={(e) => setSelectedEntityId(e.target.value)}
              className="bg-white border border-slate-300 text-xs text-slate-800 font-bold px-3 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600 shadow-sm"
            >
              {entities.map((e) => (
                <option key={e.entity_id} value={e.entity_id}>
                  {e.entity_id} ({e.entity_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[10px] text-slate-500 font-bold uppercase block mb-1">Scientific Inquiry</label>
            <select
              value={scientificQuestion}
              onChange={(e) => setScientificQuestion(e.target.value)}
              className="bg-white border border-slate-300 text-xs text-slate-800 font-bold px-3 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600 shadow-sm"
            >
              <option value="spectral analysis">Spectral / Mineralogy Analysis</option>
              <option value="fine morphology">Fine Morphology & Crater Rims</option>
              <option value="terrain analysis">Terrain Topography & Slope</option>
              <option value="elevation analysis">Elevation Depth Profile</option>
              <option value="water ice prospecting">Water Ice Absorption Prospecting</option>
              <option value="boulder hazard">Boulder Hazard Assessment</option>
              <option value="offline sensor test">Simulate Payload Offline / Unavailable</option>
            </select>
          </div>
        </div>
      </div>

      {/* Language Policy Banner */}
      <div className="p-4 rounded-2xl bg-blue-50 border border-blue-200 flex items-start space-x-3 text-xs shadow-sm">
        <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-bold text-blue-900 uppercase text-[11px]">
            EPISTEMIC POLICY: POTENTIALLY_REDUCES_UNCERTAINTY
          </span>
          <p className="text-slate-700 leading-relaxed font-normal">
            Observation planning uses strictly epistemic probabilistic reduction terminology (<strong className="text-blue-800">POTENTIALLY_REDUCES_UNCERTAINTY</strong>). The system never claims future observations "WILL_RESOLVE" or are "GUARANTEED".
          </p>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="p-8 text-center text-xs text-slate-500 flex items-center justify-center space-x-2 bg-white rounded-2xl border border-slate-200">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
          <span>Computing Expected Information Gain E[ΔI] across lunar payload fleet...</span>
        </div>
      )}

      {/* Active Recommendation Overview */}
      {!isLoading && recommendation && !isPayloadUnavailable && (
        <div className="space-y-5">
          {/* Hero Recommendation Summary Card */}
          <div className="bg-[#0d2247] p-7 rounded-3xl text-white shadow-xl space-y-5 relative overflow-hidden border border-blue-900">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-blue-900/80 pb-4">
              <div>
                <span className="text-[10px] uppercase font-bold text-orange-400 tracking-wider">TOP OPTIMIZED TARGET</span>
                <h2 className="text-xl font-extrabold text-white mt-0.5 tracking-tight">
                  Target Entity: {recommendation.entity_id}
                </h2>
              </div>
              <div className="flex items-center space-x-2 text-xs">
                <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 font-bold uppercase text-[10px]">
                  {recommendation.payload_status || 'AVAILABLE'}
                </span>
                <span className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30 font-bold uppercase text-[10px]">
                  POTENTIALLY_REDUCES_UNCERTAINTY
                </span>
              </div>
            </div>

            {/* Core Scientific Requirements */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-1 backdrop-blur-md">
                <span className="text-[10px] text-blue-200 uppercase font-bold block">RECOMMENDED SENSOR</span>
                <div className="text-base font-extrabold text-orange-400">
                  {recommendation.recommended_sensor} Payload
                </div>
                <div className="text-[11px] text-blue-200/80 font-normal">
                  {recommendation.sensor_requirement || 'Multi-modal payload specification'}
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-1 backdrop-blur-md">
                <span className="text-[10px] text-blue-200 uppercase font-bold block">SPATIAL REQUIREMENT</span>
                <div className="text-xs font-bold text-white">
                  {recommendation.spatial_requirement || 'Sub-kilometer spatial resolution'}
                </div>
                <div className="text-[11px] text-blue-200/80 font-normal">
                  Matched to entity geodetic envelope
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-1 backdrop-blur-md">
                <span className="text-[10px] text-blue-200 uppercase font-bold block">TEMPORAL & SOLAR</span>
                <div className="text-xs font-bold text-amber-300">
                  {recommendation.temporal_requirement || 'Orthogonal solar azimuth recommended'}
                </div>
                <div className="text-[11px] text-blue-200/80 font-normal">
                  Optimized incidence & phase angles
                </div>
              </div>
            </div>

            {/* Rationale & Uncertainty Reduction */}
            <div className="p-5 rounded-2xl bg-white/5 border border-white/10 space-y-2 text-xs backdrop-blur-md">
              <span className="text-[10px] text-orange-400 font-bold block uppercase tracking-wider">
                SCIENTIFIC RATIONALE & UNCERTAINTY BASIS
              </span>
              <p className="text-blue-100 leading-relaxed font-normal">
                {recommendation.rationale || recommendation.explanation}
              </p>
              <div className="flex flex-wrap items-center gap-6 pt-2 text-xs">
                <div>
                  <span className="text-blue-300 text-[10px] block font-medium">EXPECTED INFORMATION GAIN:</span>
                  <span className="text-emerald-400 font-extrabold text-sm">{recommendation.expected_information_gain.toFixed(3)}</span>
                </div>
                <div>
                  <span className="text-blue-300 text-[10px] block font-medium">UNCERTAINTY REDUCTION:</span>
                  <span className="text-orange-400 font-extrabold text-sm">{Math.round(recommendation.uncertainty_reduction * 100)}%</span>
                </div>
                <div>
                  <span className="text-blue-300 text-[10px] block font-medium">FEASIBILITY SCORE:</span>
                  <span className="text-white font-extrabold text-sm">{recommendation.feasibility.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Ranked Sensor Alternatives */}
          {recommendation.ranked_sensors?.length > 0 && (
            <div className="space-y-3">
              <span className="text-xs font-bold uppercase text-slate-700 block tracking-wider">
                Ranked Fleet Sensor Alternatives
              </span>

              <div className="space-y-3">
                {recommendation.ranked_sensors.map((s, idx) => {
                  const isTop = idx === 0;
                  return (
                    <div
                      key={idx}
                      className={`p-5 rounded-2xl border flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs transition-all ${
                        isTop
                          ? 'bg-white border-blue-500 shadow-md ring-1 ring-blue-500/20'
                          : 'bg-white border-slate-200 shadow-sm hover:border-slate-300'
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-extrabold text-slate-800 text-sm">{s.sensor} Payload</span>
                          {isTop && (
                            <span className="text-[9px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold uppercase">
                              RANK #1
                            </span>
                          )}
                          {s.is_new_modality && (
                            <span className="text-[9px] px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 font-bold uppercase">
                              NEW MODALITY
                            </span>
                          )}
                        </div>
                        <p className="text-slate-600 text-xs leading-relaxed font-normal">{s.explanation}</p>
                      </div>

                      <div className="flex items-center space-x-6 shrink-0 text-right">
                        <div>
                          <span className="text-[10px] text-slate-400 font-bold block uppercase">GAIN</span>
                          <span className="font-extrabold text-emerald-600 text-sm">{s.expected_information_gain.toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-400 font-bold block uppercase">REDUCTION</span>
                          <span className="font-extrabold text-blue-600 text-sm">{Math.round(s.uncertainty_reduction * 100)}%</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
