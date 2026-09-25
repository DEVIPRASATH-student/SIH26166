import React from 'react';
import { AlertCircle, ShieldAlert } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <div className="bg-amber-500/10 border-b border-amber-500/25 px-6 py-2 flex flex-col md:flex-row items-start md:items-center justify-between text-xs font-mono text-amber-300 gap-2">
      <div className="flex items-center space-x-2">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
        <span>
          <strong className="font-bold">SCIENTIFIC INTEGRITY GUARDRAILS:</strong>{' '}
          Physical Correspondence:{' '}
          <span className="font-bold underline text-amber-200">NOT VALIDATED</span> | Real-Data Accuracy:{' '}
          <span className="font-bold underline text-amber-200">N/A</span> | Empirical Calibration:{' '}
          <span className="font-bold underline text-amber-200">NOT ESTABLISHED</span> | Axiom:{' '}
          <span className="font-bold underline text-amber-200">UNKNOWN ≠ NEGATIVE</span>
        </span>
      </div>
      <div className="flex items-center space-x-3 text-[10px] text-amber-400/90 uppercase tracking-widest shrink-0">
        <span>RAW DATA: 0 BYTES MODIFIED</span>
        <span className="hidden lg:inline">•</span>
        <span className="hidden lg:inline">SIH 26166</span>
      </div>
    </div>
  );
};
