import React, { useState } from 'react';
import { Observation, SensorType } from '../types';
import { Layers, Sun, Compass, Sliders, Info, ZoomIn } from 'lucide-react';

interface ObservationWorkspaceProps {
  observations: Observation[];
}

export const ObservationWorkspace: React.FC<ObservationWorkspaceProps> = ({ observations }) => {
  const [selectedId, setSelectedId] = useState<string>(
    observations[0]?.id || 'OBS-OHRC-001'
  );

  const currentObs = observations.find((o) => o.id === selectedId) || observations[0];

  if (!currentObs) {
    return (
      <div className="p-8 text-center font-mono text-xs text-lunar-400">
        No observation records available. Run the demo mission to generate multi-modal observations.
      </div>
    );
  }

  return (
    <div className="space-y-6 font-mono">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-lunar-50">Observation Workspace</h1>
          <p className="text-xs text-lunar-400">
            Inspect heterogeneous remote sensing modalities (OHRC, TMC-2, IIRS) and solar ephemeris geometry.
          </p>
        </div>

        {/* Sensor Observation Selector Tabs */}
        <div className="flex items-center space-x-2 bg-lunar-900 p-1 rounded-lg border border-lunar-700">
          {observations.map((obs) => {
            const isSelected = obs.id === currentObs.id;
            return (
              <button
                key={obs.id}
                onClick={() => setSelectedId(obs.id)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  isSelected
                    ? 'bg-space-cyan text-lunar-950 shadow-md'
                    : 'text-lunar-400 hover:text-lunar-100 hover:bg-lunar-800'
                }`}
              >
                {obs.sensor_type} ({obs.id})
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Visualizer & Metadata */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 7 Columns: Image Viewport */}
        <div className="lg:col-span-7 telemetry-panel p-5 rounded-xl border border-lunar-700/60 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold uppercase text-space-cyan">
                  {currentObs.sensor_type} Payload Imagery
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-lunar-800 text-lunar-300">
                  {currentObs.spatial_resolution_m} m/px GSD
                </span>
              </div>
              <span className="text-[10px] text-lunar-400">Resolution: 512 x 512 px</span>
            </div>

            {/* Image Canvas Container */}
            <div className="relative aspect-square w-full rounded-lg overflow-hidden bg-lunar-950 border border-lunar-800 flex items-center justify-center group">
              <img
                src={currentObs.image_url}
                alt={currentObs.id}
                className="w-full h-full object-cover select-none transition-transform duration-300 group-hover:scale-105"
              />
              <div className="absolute top-3 left-3 px-2 py-1 rounded bg-lunar-950/80 backdrop-blur-md border border-lunar-700 text-[10px] text-lunar-200">
                {currentObs.id}
              </div>
              <div className="absolute bottom-3 right-3 px-2 py-1 rounded bg-lunar-950/80 backdrop-blur-md border border-lunar-700 text-[10px] text-amber-400">
                SYNTHETIC / DEMO DATA
              </div>
            </div>
          </div>

          <div className="mt-4 text-[11px] text-lunar-400 flex items-center justify-between">
            <span>Center Lat/Lon: {((currentObs.lat_min + currentObs.lat_max) / 2).toFixed(3)}°S, {((currentObs.lon_min + currentObs.lon_max) / 2).toFixed(3)}°E</span>
            <span>Sensor Mode: Calibrated Reflectance</span>
          </div>
        </div>

        {/* Right 5 Columns: Solar Geometry & Payload Telemetry */}
        <div className="lg:col-span-5 space-y-4">
          {/* Solar Geometry Panel */}
          <div className="telemetry-panel p-5 rounded-xl border border-lunar-700/60 space-y-3">
            <h2 className="text-xs font-bold uppercase text-lunar-300 flex items-center space-x-1.5">
              <Sun className="w-4 h-4 text-amber-400" />
              <span>Astronomical Ephemeris & Illumination</span>
            </h2>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-lunar-950 border border-lunar-800">
                <span className="text-[10px] text-lunar-400 block">SUN AZIMUTH</span>
                <span className="text-sm font-bold text-amber-300">{currentObs.sun_azimuth_deg.toFixed(1)}°</span>
                <span className="text-[10px] text-lunar-500 block mt-0.5">Clockwise from North</span>
              </div>
              <div className="p-3 rounded-lg bg-lunar-950 border border-lunar-800">
                <span className="text-[10px] text-lunar-400 block">SUN ELEVATION</span>
                <span className="text-sm font-bold text-amber-300">{currentObs.sun_elevation_deg.toFixed(1)}°</span>
                <span className="text-[10px] text-lunar-500 block mt-0.5">Angle above horizon</span>
              </div>
              <div className="p-3 rounded-lg bg-lunar-950 border border-lunar-800">
                <span className="text-[10px] text-lunar-400 block">INCIDENCE ANGLE</span>
                <span className="text-sm font-bold text-lunar-200">{currentObs.incidence_angle_deg.toFixed(1)}°</span>
              </div>
              <div className="p-3 rounded-lg bg-lunar-950 border border-lunar-800">
                <span className="text-[10px] text-lunar-400 block">PHASE ANGLE</span>
                <span className="text-sm font-bold text-space-cyan">{currentObs.phase_angle_deg.toFixed(1)}°</span>
              </div>
            </div>

            {/* Expected Shadow Orientation */}
            <div className="p-3 rounded-lg bg-lunar-850 border border-lunar-700 text-xs">
              <span className="text-lunar-400 text-[10px] block">EXPECTED SHADOW VECTOR</span>
              <span className="text-lunar-100 font-bold">
                {((currentObs.sun_azimuth_deg + 180) % 360).toFixed(1)}° (Anti-solar azimuth direction)
              </span>
            </div>
          </div>

          {/* Instrument Metadata Details */}
          <div className="telemetry-panel p-5 rounded-xl border border-lunar-700/60 space-y-3">
            <h2 className="text-xs font-bold uppercase text-lunar-300 flex items-center space-x-1.5">
              <Sliders className="w-4 h-4 text-space-cyan" />
              <span>Payload Characteristics</span>
            </h2>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-lunar-800">
                <span className="text-lunar-400">Sensor Class</span>
                <span className="text-lunar-100 font-semibold">{currentObs.metadata.sensor_name || currentObs.sensor_type}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-lunar-800">
                <span className="text-lunar-400">Ground Sampling Distance</span>
                <span className="text-space-cyan font-bold">{currentObs.spatial_resolution_m} meters / pixel</span>
              </div>
              <div className="flex justify-between py-1 border-b border-lunar-800">
                <span className="text-lunar-400">Spectral Band</span>
                <span className="text-lunar-200">{currentObs.metadata.spectral_band || currentObs.metadata.spectral_range_um || 'Broadband'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-lunar-800">
                <span className="text-lunar-400">Geodetic Extent (Lat)</span>
                <span className="text-lunar-200">{currentObs.lat_min.toFixed(3)}° to {currentObs.lat_max.toFixed(3)}°</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-lunar-400">Geodetic Extent (Lon)</span>
                <span className="text-lunar-200">{currentObs.lon_min.toFixed(3)}° to {currentObs.lon_max.toFixed(3)}°</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
