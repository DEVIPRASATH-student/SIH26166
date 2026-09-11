import React, { useState, useEffect } from 'react';
import { LunarEntity, Recommendation } from '../types';
import { Target, Sparkles, Sliders, CheckCircle2, ArrowUpRight, Zap, Info } from 'lucide-react';
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

  const fetchRecommendation = async (entityId: string, question: string) => {
    if (!entityId) return;
    setIsLoading(true);
    try {
      const rec = await api.getNextObservation(entityId, question);
      setRecommendation(rec);
    } catch (err) {
      console.error('Failed to compute recommendation', err);
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
      <div className="p-8 text-center font-mono text-xs text-lunar-400">
        No entities available for recommendation. Run the demo mission first.
      </div>
    );
  }

  return (
    <div className="space-y-6 font-mono">
      {/* Top Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-space-emerald/20 text-space-emerald border border-space-emerald/30">
              AUTONOMOUS OBSERVATION SCHEDULER
            </span>
            <span className="text-xs text-lunar-400">Information Gain Maximizer</span>
          </div>
          <h1 className="text-xl font-bold text-lunar-50 mt-1">Next-Best Observation Engine</h1>
          <p className="text-xs text-lunar-400">
            Calculates Expected Information Gain across payload sensors to optimize lunar observation targeting.
          </p>
        </div>

        {/* Target Entity & Question Selectors */}
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <label className="text-[10px] text-lunar-400 uppercase block mb-1">Target Entity</label>
            <select
              value={selectedEntityId}
              onChange={(e) => setSelectedEntityId(e.target.value)}
              className="bg-lunar-900 border border-lunar-700 text-xs text-lunar-200 px-3 py-1.5 rounded-lg focus:outline-none focus:border-space-cyan"
            >
              {entities.map((e) => (
                <option key={e.entity_id} value={e.entity_id}>
                  {e.entity_id} ({e.entity_type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[10px] text-lunar-400 uppercase block mb-1">Scientific Inquiry</label>
            <select
              value={scientificQuestion}
              onChange={(e) => setScientificQuestion(e.target.value)}
              className="bg-lunar-900 border border-lunar-700 text-xs text-lunar-200 px-3 py-1.5 rounded-lg focus:outline-none focus:border-space-cyan"
            >
              <option value="spectral analysis">Spectral / Mineralogy Analysis</option>
              <option value="fine morphology">Fine Morphology & Crater Rims</option>
              <option value="terrain analysis">Terrain Topography & Slope</option>
              <option value="elevation analysis">Elevation Depth Profile</option>
              <option value="water ice prospecting">Water Ice Absorption Prospecting</option>
              <option value="boulder hazard">Boulder Hazard Assessment</option>
            </select>
          </div>
        </div>
      </div>

      {/* Information Gain Formulation Card */}
      <div className="telemetry-panel p-4 rounded-xl border border-lunar-700/60 bg-lunar-950/60">
        <div className="flex items-center space-x-2 text-xs font-bold text-space-cyan uppercase mb-1">
          <Info className="w-4 h-4" />
          <span>Expected Information Gain Formula</span>
        </div>
        <p className="text-xs text-lunar-300 font-mono">
          {"E[ΔI] = Current Uncertainty × Sensor Relevance × Missing Info Factor × Measurement Quality × Feasibility"}
        </p>
      </div>

      {/* Ranked Recommendations List */}
      <div className="space-y-4">
        {recommendation?.ranked_sensors?.map((sensorRec, idx) => {
          const isTop = idx === 0;
          const gainPct = Math.round(sensorRec.expected_information_gain * 100);

          return (
            <div
              key={idx}
              className={`p-5 rounded-xl border transition-all duration-200 ${
                isTop
                  ? 'bg-space-cyan/10 border-space-cyan shadow-lg glow-cyan'
                  : 'telemetry-panel border-lunar-700/60'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3">
                <div className="flex items-center space-x-3">
                  <span
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                      isTop
                        ? 'bg-space-cyan text-lunar-950'
                        : 'bg-lunar-800 text-lunar-300'
                    }`}
                  >
                    #{idx + 1}
                  </span>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-base font-bold text-lunar-50">
                        {sensorRec.sensor} Payload
                      </span>
                      {isTop && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-space-emerald/20 text-space-emerald border border-space-emerald/30">
                          RECOMMENDED NEXT TARGET
                        </span>
                      )}
                      {sensorRec.is_new_modality && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                          NEW MODALITY
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-lunar-400">{sensorRec.description}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-4 text-xs">
                  <div>
                    <span className="text-lunar-400 text-[10px] block">EXPECTED GAIN</span>
                    <span className="text-base font-bold text-space-emerald">
                      {sensorRec.expected_information_gain}
                    </span>
                  </div>
                  <div>
                    <span className="text-lunar-400 text-[10px] block">UNCERTAINTY REDUCTION</span>
                    <span className="text-base font-bold text-space-cyan">
                      {Math.round(sensorRec.uncertainty_reduction * 100)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Progress Gain Bar */}
              <div className="w-full bg-lunar-950 h-2 rounded-full overflow-hidden mb-3 border border-lunar-800">
                <div
                  className={`h-full rounded-full ${
                    isTop ? 'bg-space-cyan' : 'bg-lunar-600'
                  }`}
                  style={{ width: `${gainPct}%` }}
                />
              </div>

              {/* Justification Explanation */}
              <p className="text-xs text-lunar-300 leading-relaxed bg-lunar-950/70 p-3 rounded-lg border border-lunar-800">
                {sensorRec.explanation}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
