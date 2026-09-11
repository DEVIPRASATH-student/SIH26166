import React from 'react';
import { AlertCircle } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2 flex items-center justify-between text-xs font-mono text-amber-300">
      <div className="flex items-center space-x-2">
        <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
        <span>
          <strong className="font-bold">SCIENTIFIC INTEGRITY NOTICE:</strong> All active observations are{' '}
          <span className="underline font-bold">SYNTHETIC / DEMO DATA</span> derived from physical Lunar-Lambertian reflectance and procedural digital elevation models. Not official Chandrayaan-2 planetary release data.
        </span>
      </div>
      <span className="text-[10px] text-amber-400/80 uppercase tracking-widest hidden md:inline">
        SIH 26166 PROTOTYPE
      </span>
    </div>
  );
};
