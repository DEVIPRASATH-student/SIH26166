import React, { useState, useEffect } from 'react';
import { LunarEntity, EntityDetail } from '../types';
import { Globe, Layers, Activity, Shield, CheckCircle, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

interface EntityExplorerProps {
  entities: LunarEntity[];
}

export const EntityExplorer: React.FC<EntityExplorerProps> = ({ entities }) => {
  const [selectedEntityId, setSelectedEntityId] = useState<string>(
    entities[0]?.entity_id || ''
  );
  const [detail, setDetail] = useState<EntityDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (selectedEntityId) {
      setIsLoading(true);
      api
        .getEntityDetail(selectedEntityId)
        .then((res) => setDetail(res))
        .catch((err) => console.error(err))
        .finally(() => setIsLoading(false));
    }
  }, [selectedEntityId]);

  if (entities.length === 0) {
    return (
      <div className="p-8 text-center font-mono text-xs text-lunar-400">
        No persistent lunar entities resolved yet. Run the demo mission to populate the World Model.
      </div>
    );
  }

  return (
    <div className="space-y-6 font-mono">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-bold text-lunar-50">Persistent Lunar Entity Explorer</h1>
        <p className="text-xs text-lunar-400">
          World Model memory layer: physical lunar regions maintaining identity, multi-sensor evidence history, and probabilistic hypotheses.
        </p>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Entity Directory (4 cols) */}
        <div className="lg:col-span-4 space-y-3">
          <div className="text-xs font-bold uppercase text-lunar-400 tracking-wider px-1">
            Registered Lunar Entities ({entities.length})
          </div>
          <div className="space-y-2 max-h-[calc(100vh-14rem)] overflow-y-auto pr-1">
            {entities.map((e) => {
              const isSelected = e.entity_id === selectedEntityId;
              return (
                <div
                  key={e.entity_id}
                  onClick={() => setSelectedEntityId(e.entity_id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all duration-150 ${
                    isSelected
                      ? 'bg-space-cyan/10 border-space-cyan shadow-md'
                      : 'telemetry-panel hover:bg-lunar-800/80 border-lunar-700/60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-sm text-lunar-100">{e.entity_id}</span>
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-lunar-800 text-space-cyan border border-lunar-700">
                      {e.entity_type}
                    </span>
                  </div>
                  <div className="text-xs text-lunar-400 space-y-0.5">
                    <div>Coords: {e.latitude.toFixed(3)}°S, {e.longitude.toFixed(3)}°E</div>
                    <div className="flex justify-between items-center pt-1">
                      <span>Extent: ~{e.spatial_extent_m}m</span>
                      <span className="text-space-emerald font-semibold">
                        {Math.round(e.confidence * 100)}% Conf
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Entity Physical Profile & Hypotheses (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          {detail ? (
            <>
              {/* Entity Overview Card */}
              <div className="telemetry-panel p-5 rounded-xl border border-lunar-700/60 space-y-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 pb-3 border-b border-lunar-800">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h2 className="text-lg font-bold text-lunar-50">{detail.entity_id}</h2>
                      <span className="text-xs px-2 py-0.5 rounded bg-space-cyan/20 text-space-cyan border border-space-cyan/30 font-bold uppercase">
                        {detail.entity_type}
                      </span>
                    </div>
                    <p className="text-xs text-lunar-400 mt-0.5">
                      Physical Lunar Region — Created: {new Date(detail.created_at).toLocaleTimeString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-3 text-xs">
                    <div className="p-2 rounded bg-lunar-950 border border-lunar-800 text-center">
                      <span className="text-[10px] text-lunar-400 block">BELIEF CONFIDENCE</span>
                      <span className="text-space-emerald font-bold">{Math.round(detail.confidence * 100)}%</span>
                    </div>
                    <div className="p-2 rounded bg-lunar-950 border border-lunar-800 text-center">
                      <span className="text-[10px] text-lunar-400 block">UNCERTAINTY</span>
                      <span className="text-space-cyan font-bold">{Math.round(detail.uncertainty * 100)}%</span>
                    </div>
                  </div>
                </div>

                {/* Attached Observations History */}
                <div>
                  <span className="text-xs font-bold uppercase text-lunar-300 block mb-2">
                    Attached Observation Streams ({detail.observations.length})
                  </span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {detail.observations.map((obs, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg bg-lunar-950 border border-lunar-800 flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center space-x-2">
                          <Layers className="w-4 h-4 text-space-cyan" />
                          <div>
                            <span className="font-bold text-lunar-100">{obs.observation_id}</span>
                            <span className="text-[10px] text-lunar-400 block">{obs.sensor_type} Sensor</span>
                          </div>
                        </div>
                        <span className="text-[10px] text-space-emerald font-bold">
                          {Math.round(obs.confidence * 100)}% Match
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Probabilistic World Model Hypotheses */}
              <div className="telemetry-panel p-5 rounded-xl border border-lunar-700/60 space-y-3">
                <h3 className="text-xs font-bold uppercase text-lunar-300 flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-space-cyan" />
                  <span>Probabilistic World Model Hypotheses</span>
                </h3>

                <div className="space-y-3">
                  {detail.hypotheses.map((hyp, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-lunar-950 border border-lunar-800 space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-space-cyan uppercase tracking-wider text-[11px]">
                          {hyp.property_name.replace('_', ' ')}
                        </span>
                        <div className="flex items-center space-x-3 text-[11px]">
                          <span>
                            Confidence: <strong className="text-space-emerald">{Math.round(hyp.confidence * 100)}%</strong>
                          </span>
                          <span>
                            Uncertainty: <strong className="text-lunar-400">{Math.round(hyp.uncertainty * 100)}%</strong>
                          </span>
                        </div>
                      </div>

                      <p className="text-lunar-200 leading-relaxed font-semibold">{hyp.hypothesis_value}</p>

                      {/* Supporting & Conflicting Evidence */}
                      <div className="pt-2 border-t border-lunar-900 grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                        <div>
                          <span className="text-space-emerald font-bold block mb-0.5">SUPPORTING EVIDENCE:</span>
                          <ul className="list-disc list-inside text-lunar-400 space-y-0.5">
                            {hyp.supporting_evidence.map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <span className="text-amber-400 font-bold block mb-0.5">CONFLICTING / UNCERTAIN:</span>
                          <ul className="list-disc list-inside text-lunar-400 space-y-0.5">
                            {hyp.conflicting_evidence.length > 0 ? (
                              hyp.conflicting_evidence.map((c, i) => <li key={i}>{c}</li>)
                            ) : (
                              <li className="text-lunar-600">None detected (high consensus)</li>
                            )}
                          </ul>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="p-8 text-center text-xs text-lunar-400">Loading entity details...</div>
          )}
        </div>
      </div>
    </div>
  );
};
