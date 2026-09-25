import React, { useState } from 'react';
import { Observation } from '../types';
import { Layers } from 'lucide-react';

interface ObservationWorkspaceProps {
  observations: Observation[];
}

export const ObservationWorkspace: React.FC<ObservationWorkspaceProps> = ({ observations }) => {
  const [dataFilter, setDataFilter] = useState<'ALL' | 'REAL' | 'SYNTHETIC'>('ALL');
  const [selectedId, setSelectedId] = useState<string>('');

  const filteredObservations = observations.filter((obs) => {
    if (dataFilter === 'REAL') return !obs.is_synthetic;
    if (dataFilter === 'SYNTHETIC') return obs.is_synthetic;
    return true;
  });

  const currentObs =
    filteredObservations.find((o) => o.id === selectedId) ||
    filteredObservations[0] ||
    observations[0];

  if (!currentObs) {
    return (
      <div className="p-12 text-center font-sans text-xs text-slate-500 bg-white border border-slate-200 rounded-2xl shadow-sm">
        No observation records available matching the filter '{dataFilter}'.
      </div>
    );
  }

  const isReal = !currentObs.is_synthetic;
  const sensorName = currentObs.sensor_type || currentObs.sensor || 'OHRC';

  return (
    <div className="space-y-6 font-sans">
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 border border-blue-200">
              REMOTE SENSING CATALOG
            </span>
            <span className="text-xs text-slate-500 font-medium">PDS4 Compliant Telemetry</span>
          </div>
          <h1 className="text-2xl font-extrabold text-[#0d2247] mt-1 flex items-center space-x-2 tracking-tight">
            <Layers className="w-6 h-6 text-blue-600" />
            <span>Observation Telemetry Workspace</span>
          </h1>
          <p className="text-xs text-slate-600 font-medium">
            Inspect heterogeneous remote sensing streams (Chandrayaan-2 OHRC, TMC-2, IIRS) and ephemeris illumination geometry.
          </p>
        </div>

        {/* Real / Synthetic Data Mode Filter */}
        <div className="flex items-center space-x-2 bg-white p-1 rounded-xl border border-slate-200 shadow-sm">
          <button
            onClick={() => setDataFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              dataFilter === 'ALL'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            ALL ({observations.length})
          </button>
          <button
            onClick={() => setDataFilter('REAL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              dataFilter === 'REAL'
                ? 'bg-amber-500 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            REAL FLIGHT
          </button>
          <button
            onClick={() => setDataFilter('SYNTHETIC')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              dataFilter === 'SYNTHETIC'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            SYNTHETIC
          </button>
        </div>
      </div>

      {/* Main Grid View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Observation List Selector */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-xs font-bold text-slate-700 uppercase border-b border-slate-100 pb-3">
            <span>Observation Streams</span>
            <span className="text-[10px] text-slate-400">{filteredObservations.length} Available</span>
          </div>
          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {filteredObservations.map((obs) => {
              const isSelected = obs.id === currentObs.id;
              const isRealObs = !obs.is_synthetic;
              return (
                <div
                  key={obs.id}
                  onClick={() => setSelectedId(obs.id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-blue-50 border-blue-500 shadow-sm ring-1 ring-blue-500/20'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-bold mb-1">
                    <span className="text-blue-700 font-extrabold uppercase">{obs.sensor_type || obs.sensor}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${
                        isRealObs
                          ? 'bg-amber-100 text-amber-800 border-amber-200'
                          : 'bg-purple-100 text-purple-800 border-purple-200'
                      }`}
                    >
                      {isRealObs ? 'REAL' : 'SYNTHETIC'}
                    </span>
                  </div>
                  <div className="text-xs font-bold text-slate-800 truncate">{obs.id}</div>
                  <div className="text-[11px] text-slate-500 mt-1 font-medium">
                    Res: {obs.spatial_resolution_m} m/px • Solar Az: {obs.sun_azimuth_deg}°
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Active Observation Metadata & Preview Card */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold uppercase text-blue-700">{sensorName} INSTRUMENT FRAME</span>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                    isReal
                      ? 'bg-amber-100 text-amber-800 border-amber-200'
                      : 'bg-purple-100 text-purple-800 border-purple-200'
                  }`}
                >
                  {isReal ? 'REAL LUNAR FLIGHT DATA' : 'SYNTHETIC CONTROL'}
                </span>
              </div>
              <h2 className="text-lg font-extrabold text-[#0d2247] mt-1 break-all font-mono">
                {currentObs.id}
              </h2>
            </div>
          </div>

          {/* Ephemeris & Sensor Telemetry Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 font-bold uppercase block">SPATIAL RESOLUTION</span>
              <div className="text-sm font-extrabold text-slate-900 mt-0.5">
                {currentObs.spatial_resolution_m} m/px
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 font-bold uppercase block">SOLAR ELEVATION / AZIMUTH</span>
              <div className="text-sm font-extrabold text-slate-900 mt-0.5">
                {currentObs.sun_elevation_deg}° / {currentObs.sun_azimuth_deg}°
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 font-bold uppercase block">INCIDENCE / PHASE ANGLE</span>
              <div className="text-sm font-extrabold text-slate-900 mt-0.5">
                {currentObs.incidence_angle_deg}° / {currentObs.phase_angle_deg}°
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[10px] text-slate-500 font-bold uppercase block">EMISSION ANGLE</span>
              <div className="text-sm font-extrabold text-blue-700 mt-0.5">
                {currentObs.emission_angle_deg}°
              </div>
            </div>
          </div>

          {/* Footprint Bounds & Geodetic Coordinates */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs font-mono">
            <span className="text-[10px] text-slate-500 font-bold uppercase block font-sans">
              GEODETIC FOOTPRINT BOUNDING BOX
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-slate-800 font-bold text-[11px]">
              <div>Min Lat: {currentObs.lat_min.toFixed(4)}°</div>
              <div>Max Lat: {currentObs.lat_max.toFixed(4)}°</div>
              <div>Min Lon: {currentObs.lon_min.toFixed(4)}°</div>
              <div>Max Lon: {currentObs.lon_max.toFixed(4)}°</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
