import React from 'react';
import { KnowledgeGap } from '../types';
import { AlertCircle, Target, ArrowRight, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { PageId } from '../components/Sidebar';

interface KnowledgeGapsProps {
  gaps: KnowledgeGap[];
  onNavigateToRecommendation: () => void;
}

export const KnowledgeGaps: React.FC<KnowledgeGapsProps> = ({
  gaps,
  onNavigateToRecommendation,
}) => {
  const severityStyles = {
    HIGH: 'bg-space-rose/20 text-space-rose border-space-rose/40',
    MEDIUM: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
    LOW: 'bg-space-cyan/20 text-space-cyan border-space-cyan/40',
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-lunar-50 flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-amber-400" />
            <span>Autonomous Knowledge-Gap Detection</span>
          </h1>
          <p className="text-xs text-lunar-400">
            Systematic identification of missing modalities, high epistemic uncertainty, and unverified physical structures.
          </p>
        </div>

        <button
          onClick={onNavigateToRecommendation}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-space-cyan to-blue-600 hover:from-sky-400 hover:to-blue-500 text-lunar-950 font-bold text-xs shadow-md transition-all shrink-0"
        >
          <Target className="w-4 h-4" />
          <span>Resolve With Next-Best Observation</span>
        </button>
      </div>

      {/* Prioritized Gaps List */}
      <div className="space-y-4">
        {gaps.map((gap) => (
          <div
            key={gap.id}
            className="telemetry-panel p-5 rounded-xl border border-lunar-700/60 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-lunar-600 transition-all"
          >
            <div className="space-y-2 max-w-3xl">
              <div className="flex items-center space-x-3">
                <span
                  className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                    severityStyles[gap.severity] || severityStyles.MEDIUM
                  }`}
                >
                  {gap.severity} PRIORITY
                </span>
                <span className="text-sm font-bold text-lunar-100">{gap.gap_type}</span>
                <span className="text-xs text-lunar-400">Target: {gap.entity_id}</span>
              </div>
              <p className="text-xs text-lunar-300 leading-relaxed">{gap.reason}</p>
            </div>

            {/* Recommended Target Action */}
            <div className="flex items-center space-x-4 shrink-0">
              <div className="text-right">
                <span className="text-[10px] text-lunar-400 block uppercase">RECOMMENDED PAYLOAD</span>
                <span className="text-xs font-bold text-space-cyan bg-space-cyan/10 px-2 py-1 rounded border border-space-cyan/30">
                  {gap.recommended_sensor} Sensor
                </span>
              </div>
              <button
                onClick={onNavigateToRecommendation}
                className="p-2 rounded-lg bg-lunar-800 hover:bg-lunar-700 text-space-cyan border border-lunar-700"
                title="Calculate Information Gain"
              >
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}

        {gaps.length === 0 && (
          <div className="p-12 text-center text-xs text-lunar-400 telemetry-panel rounded-xl">
            No active knowledge gaps detected. Run the complete demo mission to trigger gap scanning.
          </div>
        )}
      </div>
    </div>
  );
};
