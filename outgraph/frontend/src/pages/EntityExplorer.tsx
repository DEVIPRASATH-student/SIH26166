import React, { useState, useEffect } from 'react';
import { LunarEntity, EntityDetail } from '../types';
import { Activity, Layers } from 'lucide-react';
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
      <div className="p-8 text-center font-sans text-xs font-bold text-slate-600 bg-white rounded-2xl border border-slate-200">
        No persistent lunar entities resolved yet. Run the demo mission to populate the World Model.
      </div>
    );
  }

  return (
    <div className="space-y-6 font-sans">
      {/* Page Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h1 className="text-xl font-black text-[#0d2247]">Persistent Lunar Entity Explorer</h1>
        <p className="text-xs text-slate-900 font-bold mt-1">
          World Model memory layer: physical lunar regions maintaining identity, multi-sensor evidence history, and probabilistic hypotheses.
        </p>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Entity Directory (4 cols) */}
        <div className="lg:col-span-4 space-y-3">
          <div className="text-xs font-black uppercase text-[#0d2247] tracking-wider px-1">
            Registered Lunar Entities ({entities.length})
          </div>
          <div className="space-y-2 max-h-[calc(100vh-14rem)] overflow-y-auto pr-1">
            {entities.map((e) => {
              const isSelected = e.entity_id === selectedEntityId;
              return (
                <div
                  key={e.entity_id}
                  onClick={() => setSelectedEntityId(e.entity_id)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all duration-150 ${
                    isSelected
                      ? 'bg-sky-50 border-sky-400 shadow-sm ring-2 ring-sky-200'
                      : 'bg-white hover:bg-slate-50 border-slate-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-black text-sm text-[#0d2247]">{e.entity_id}</span>
                    <span className="text-[10px] uppercase font-black px-2.5 py-0.5 rounded bg-blue-100 text-blue-950 border border-blue-300">
                      {e.entity_type}
                    </span>
                  </div>
                  <div className="text-xs text-slate-900 font-bold space-y-0.5">
                    <div>Coords: {e.latitude.toFixed(3)}°S, {e.longitude.toFixed(3)}°E</div>
                    <div className="flex justify-between items-center pt-1">
                      <span className="text-slate-700">Extent: ~{e.spatial_extent_m}m</span>
                      <span className="text-emerald-700 font-black">
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
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h2 className="text-lg font-black text-[#0d2247]">{detail.entity_id}</h2>
                      <span className="text-xs px-2.5 py-0.5 rounded bg-blue-100 text-blue-950 border border-blue-300 font-black uppercase">
                        {detail.entity_type}
                      </span>
                    </div>
                    <p className="text-xs text-slate-800 font-bold mt-1">
                      Physical Lunar Region — Created: {new Date(detail.created_at).toLocaleTimeString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-3 text-xs">
                    <div className="p-2.5 rounded-xl bg-slate-900 text-white border border-slate-800 text-center min-w-[90px]">
                      <span className="text-[10px] text-slate-300 block font-extrabold uppercase">BELIEF CONFIDENCE</span>
                      <span className="text-emerald-400 font-black text-sm">{Math.round(detail.confidence * 100)}%</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-900 text-white border border-slate-800 text-center min-w-[90px]">
                      <span className="text-[10px] text-slate-300 block font-extrabold uppercase">UNCERTAINTY</span>
                      <span className="text-sky-300 font-black text-sm">{Math.round(detail.uncertainty * 100)}%</span>
                    </div>
                  </div>
                </div>

                {/* Attached Observations History */}
                <div>
                  <span className="text-xs font-black uppercase text-[#0d2247] block mb-2">
                    Attached Observation Streams ({detail.observations.length})
                  </span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {detail.observations.map((obs, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-slate-900 text-white border border-slate-800 flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center space-x-2.5">
                          <Layers className="w-4 h-4 text-sky-400" />
                          <div>
                            <span className="font-black text-white">{obs.observation_id}</span>
                            <span className="text-[10px] text-slate-300 block font-bold">{obs.sensor_type} Sensor</span>
                          </div>
                        </div>
                        <span className="text-[11px] text-emerald-400 font-black">
                          {Math.round(obs.confidence * 100)}% Match
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Probabilistic World Model Hypotheses */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                <h3 className="text-xs font-black uppercase text-[#0d2247] flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-blue-700" />
                  <span>Probabilistic World Model Hypotheses</span>
                </h3>

                <div className="space-y-3">
                  {detail.hypotheses.map((hyp, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-slate-900 text-white border border-slate-800 space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-black text-sky-300 uppercase tracking-wider text-[11px]">
                          {hyp.property_name.replace('_', ' ')}
                        </span>
                        <div className="flex items-center space-x-3 text-[11px]">
                          <span>
                            Confidence: <strong className="text-emerald-400 font-black">{Math.round(hyp.confidence * 100)}%</strong>
                          </span>
                          <span>
                            Uncertainty: <strong className="text-slate-300 font-bold">{Math.round(hyp.uncertainty * 100)}%</strong>
                          </span>
                        </div>
                      </div>

                      <p className="text-slate-100 leading-relaxed font-bold">{hyp.hypothesis_value}</p>

                      {/* Supporting & Conflicting Evidence */}
                      <div className="pt-2 border-t border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                        <div>
                          <span className="text-emerald-400 font-black block mb-0.5">SUPPORTING EVIDENCE:</span>
                          <ul className="list-disc list-inside text-slate-300 font-bold space-y-0.5">
                            {hyp.supporting_evidence.map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <span className="text-amber-400 font-black block mb-0.5">CONFLICTING / UNCERTAIN:</span>
                          <ul className="list-disc list-inside text-slate-300 font-bold space-y-0.5">
                            {hyp.conflicting_evidence.length > 0 ? (
                              hyp.conflicting_evidence.map((c, i) => <li key={i}>{c}</li>)
                            ) : (
                              <li className="text-slate-400">None detected (high consensus)</li>
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
            <div className="p-8 text-center text-xs text-slate-600 font-bold bg-white rounded-2xl border border-slate-200">
              Loading entity details...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
