import React from 'react';
import { EvidenceProfile } from '../types';

interface EvidenceRadarProps {
  evidence?: EvidenceProfile;
}

export const EvidenceRadar: React.FC<EvidenceRadarProps> = ({ evidence }) => {
  if (!evidence) {
    return (
      <div className="p-4 rounded-lg bg-lunar-900 border border-lunar-800 text-xs text-lunar-400 font-mono">
        No physics evidence profile calculated yet.
      </div>
    );
  }

  const items = [
    { label: 'Geometry (RANSAC & Reproj)', score: evidence.geometry_score, weight: '30%', desc: 'Inlier ratio & projective error' },
    { label: 'Solar Illumination', score: evidence.illumination_score, weight: '20%', desc: 'Ephemeris azimuth & shadow vector' },
    { label: 'Raw Visual Match', score: evidence.visual_score, weight: '20%', desc: 'Feature distance & descriptor similarity' },
    { label: 'Terrain Topography', score: evidence.terrain_score, weight: '15%', desc: 'DEM slope & roughness correlation' },
    { label: 'Scale Ratio', score: evidence.scale_score, weight: '8%', desc: 'Estimated vs physical sensor GSD' },
    { label: 'Spatial Dispersion', score: evidence.spatial_score, weight: '7%', desc: 'Convex hull coverage & entropy' },
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono font-semibold uppercase text-lunar-300">
          Multi-Pillar Evidence Breakdown
        </span>
        <span
          className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
            evidence.status === 'VERIFIED'
              ? 'bg-space-emerald/20 text-space-emerald border border-space-emerald/30'
              : evidence.status === 'REJECTED'
              ? 'bg-space-rose/20 text-space-rose border border-space-rose/30'
              : 'bg-space-amber/20 text-space-amber border border-space-amber/30'
          }`}
        >
          {evidence.status} ({Math.round(evidence.overall_confidence * 100)}%)
        </span>
      </div>

      <div className="space-y-2.5">
        {items.map((item, idx) => {
          const pct = Math.round(item.score * 100);
          const barColor =
            item.score >= 0.75
              ? 'bg-space-emerald'
              : item.score >= 0.45
              ? 'bg-space-amber'
              : 'bg-space-rose';

          return (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-lunar-300">{item.label}</span>
                <span className="text-lunar-100 font-semibold">{pct}%</span>
              </div>
              <div className="w-full bg-lunar-800 h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {evidence.rejection_reasons && evidence.rejection_reasons.length > 0 && (
        <div className="mt-4 p-3 rounded-lg bg-space-rose/10 border border-space-rose/30 space-y-1">
          <div className="text-xs font-mono font-bold text-space-rose flex items-center space-x-1">
            <span>PHYSICS VETO & REJECTION REASONS:</span>
          </div>
          <ul className="list-disc list-inside text-[11px] text-lunar-300 font-mono space-y-0.5">
            {evidence.rejection_reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
