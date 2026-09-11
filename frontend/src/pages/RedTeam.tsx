import React, { useState, useEffect } from 'react';
import { RedTeamTest } from '../types';
import { ShieldAlert, ShieldCheck, AlertTriangle, CheckCircle2, Play, RefreshCw, XCircle } from 'lucide-react';
import { api } from '../services/api';

export const RedTeam: React.FC = () => {
  const [tests, setTests] = useState<RedTeamTest[]>([]);
  const [preventionRate, setPreventionRate] = useState<number>(1.0);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  const runRedTeamSuite = async () => {
    setIsRunning(true);
    try {
      const data = await api.runRedTeam();
      setTests(data.tests);
      setPreventionRate(data.prevention_rate);
    } catch (err) {
      console.error('Failed to run red team suite', err);
    } finally {
      setIsRunning(false);
    }
  };

  useEffect(() => {
    runRedTeamSuite();
  }, []);

  return (
    <div className="space-y-6 font-mono">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-space-rose/20 text-space-rose border border-space-rose/30">
              ADVERSARIAL STRESS CHALLENGE
            </span>
            <span className="text-xs text-lunar-400">Anti-Hallucination Gating</span>
          </div>
          <h1 className="text-xl font-bold text-lunar-50 mt-1 flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-space-rose" />
            <span>Adversarial Correspondence Red Team</span>
          </h1>
          <p className="text-xs text-lunar-400">
            Showcases deceptive false matches that fool standard visual descriptors but are strictly rejected by LunarSynapse multi-physics verification.
          </p>
        </div>

        <button
          onClick={runRedTeamSuite}
          disabled={isRunning}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-space-rose to-rose-700 hover:from-rose-500 hover:to-rose-600 text-lunar-50 font-bold text-xs shadow-md transition-all shrink-0"
        >
          <RefreshCw className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
          <span>{isRunning ? 'Running Red Team...' : 'Re-Run Attack Traps'}</span>
        </button>
      </div>

      {/* Defense Telemetry Summary */}
      <div className="telemetry-panel p-5 rounded-xl border border-space-rose/30 bg-gradient-to-r from-space-rose/5 to-lunar-900 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-space-rose uppercase block mb-1">
            Red Team Gating Defense Rate
          </span>
          <div className="text-3xl font-bold text-lunar-50 font-mono">
            {Math.round(preventionRate * 100)}% Prevention of False Correspondences
          </div>
          <p className="text-xs text-lunar-300 mt-1 max-w-xl">
            Raw visual similarity alone is never accepted as proof. All candidate correspondences must satisfy geometric projective consistency, ephemeris illumination, and topographic slope profiles.
          </p>
        </div>
        <div className="p-3 rounded-lg bg-lunar-950 border border-lunar-800 text-center shrink-0">
          <span className="text-[10px] text-lunar-400 block uppercase">DECEPTIVE TRAPS</span>
          <span className="text-xl font-bold text-space-emerald">{tests.length} / {tests.length} Blocked</span>
        </div>
      </div>

      {/* Deceptive Traps Showcase Grid */}
      <div className="space-y-4">
        {tests.map((test) => (
          <div
            key={test.test_id}
            className="telemetry-panel p-5 rounded-xl border border-lunar-700/60 space-y-4 hover:border-lunar-600 transition-all"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-lunar-800 pb-3">
              <div className="flex items-center space-x-3">
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-space-rose/20 text-space-rose border border-space-rose/30">
                  {test.test_id}
                </span>
                <h3 className="text-sm font-bold text-lunar-100">{test.name}</h3>
              </div>
              <span className="text-xs font-bold px-3 py-1 rounded-full bg-space-emerald/20 text-space-emerald border border-space-emerald/30 flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4" />
                <span>{test.final_decision}</span>
              </span>
            </div>

            {/* Attack Vector Description */}
            <p className="text-xs text-lunar-300 leading-relaxed bg-lunar-950 p-3 rounded-lg border border-lunar-800">
              <strong className="text-space-cyan">Attack Vector: </strong>
              {test.attack_vector}
            </p>

            {/* Contrast Comparison Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              {/* Left: Raw Matcher Result */}
              <div className="p-4 rounded-xl bg-space-rose/10 border border-space-rose/30 space-y-1.5">
                <div className="flex items-center space-x-2 text-space-rose font-bold text-xs uppercase">
                  <XCircle className="w-4 h-4" />
                  <span>Raw Visual Matcher (Deceived)</span>
                </div>
                <div className="text-lunar-200 font-semibold">{test.raw_matcher_result}</div>
                <p className="text-[11px] text-lunar-400 pt-1">
                  Naive visual matchers get fooled by circular crater symmetry or high local texture contrast.
                </p>
              </div>

              {/* Right: LunarSynapse Physics Verification Result */}
              <div className="p-4 rounded-xl bg-space-emerald/10 border border-space-emerald/30 space-y-1.5">
                <div className="flex items-center space-x-2 text-space-emerald font-bold text-xs uppercase">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>LunarSynapse Multi-Physics Gating</span>
                </div>
                <div className="text-lunar-50 font-bold">{test.physics_verification_result}</div>
                <p className="text-[11px] text-lunar-300 pt-1 font-medium">
                  {test.explanation}
                </p>
              </div>
            </div>

            {/* Physics Rejection Reasons Breakdown */}
            <div className="p-3 rounded-lg bg-lunar-950 border border-lunar-800 space-y-1 text-xs">
              <span className="text-[10px] uppercase font-bold text-space-rose block">
                PHYSICS REJECTION LOG:
              </span>
              <ul className="list-disc list-inside text-lunar-300 space-y-0.5 text-[11px]">
                {test.rejection_reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
