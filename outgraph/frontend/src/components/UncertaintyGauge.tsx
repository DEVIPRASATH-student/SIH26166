import React from 'react';
import { UncertaintyBreakdown } from '../types';
import { Shield, AlertTriangle, CheckCircle } from 'lucide-react';

interface UncertaintyGaugeProps {
  uncertainty?: UncertaintyBreakdown;
}

export const UncertaintyGauge: React.FC<UncertaintyGaugeProps> = ({ uncertainty }) => {
  if (!uncertainty) {
    return (
      <div className="p-4 rounded-lg bg-lunar-900 border border-lunar-800 text-xs text-lunar-400 font-mono">
        Uncertainty not quantified yet.
      </div>
    );
  }

  const uncPct = Math.round(uncertainty.total_uncertainty * 100);
  const isHighRisk = uncertainty.total_uncertainty > 0.45;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono font-semibold uppercase text-lunar-300">
          Uncertainty Quantification
        </span>
        <span
          className={`text-xs font-mono font-bold px-2 py-0.5 rounded flex items-center space-x-1 ${
            isHighRisk
              ? 'bg-space-rose/20 text-space-rose border border-space-rose/30'
              : 'bg-space-cyan/20 text-space-cyan border border-space-cyan/30'
          }`}
        >
          {isHighRisk ? <AlertTriangle className="w-3 h-3 mr-1" /> : <Shield className="w-3 h-3 mr-1" />}
          <span>{uncertainty.calibration_status} ({uncPct}%)</span>
        </span>
      </div>

      {/* Primary Gauge */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs font-mono text-lunar-400">
          <span>Composite Epistemic & Aleatoric Risk</span>
          <span className="font-bold text-lunar-100">{uncPct}%</span>
        </div>
        <div className="w-full bg-lunar-800 h-2.5 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              uncPct < 25 ? 'bg-space-emerald' : uncPct < 50 ? 'bg-space-amber' : 'bg-space-rose'
            }`}
            style={{ width: `${uncPct}%` }}
          />
        </div>
      </div>

      {/* Decomposition Grid */}
      <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
        <div className="p-2 rounded bg-lunar-850 border border-lunar-700/60">
          <span className="text-lunar-400 text-[10px] block">EVIDENCE DISAGREEMENT</span>
          <span className="text-lunar-100 font-bold">
            {Math.round(uncertainty.evidence_disagreement * 100)}%
          </span>
        </div>
        <div className="p-2 rounded bg-lunar-850 border border-lunar-700/60">
          <span className="text-lunar-400 text-[10px] block">GEOMETRIC INSTABILITY</span>
          <span className="text-lunar-100 font-bold">
            {Math.round(uncertainty.geometric_instability * 100)}%
          </span>
        </div>
        <div className="p-2 rounded bg-lunar-850 border border-lunar-700/60">
          <span className="text-lunar-400 text-[10px] block">FEATURE AMBIGUITY</span>
          <span className="text-lunar-100 font-bold">
            {Math.round(uncertainty.feature_ambiguity * 100)}%
          </span>
        </div>
        <div className="p-2 rounded bg-lunar-850 border border-lunar-700/60">
          <span className="text-lunar-400 text-[10px] block">SPATIAL SPARSITY</span>
          <span className="text-lunar-100 font-bold">
            {Math.round(uncertainty.spatial_sparsity * 100)}%
          </span>
        </div>
      </div>
    </div>
  );
};
