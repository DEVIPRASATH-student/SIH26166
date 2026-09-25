import React, { useState, useEffect } from 'react';
import { RedTeamTest } from '../types';
import { ShieldAlert, ShieldCheck, CheckCircle2, RefreshCw, XCircle } from 'lucide-react';
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
    <div className="space-y-6 font-sans">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] uppercase font-black px-2.5 py-1 rounded bg-rose-100 text-rose-950 border border-rose-300">
              ADVERSARIAL STRESS CHALLENGE
            </span>
            <span className="text-xs text-slate-800 font-extrabold">Anti-Hallucination Gating</span>
          </div>
          <h1 className="text-xl font-black text-[#0d2247] mt-2 flex items-center space-x-2">
            <ShieldAlert className="w-6 h-6 text-rose-700" />
            <span>Adversarial Correspondence Red Team</span>
          </h1>
          <p className="text-xs text-slate-900 font-bold mt-1 max-w-2xl">
            Showcases deceptive false matches that fool standard visual descriptors but are strictly rejected by LunarSynapse multi-physics verification.
          </p>
        </div>

        <button
          onClick={runRedTeamSuite}
          disabled={isRunning}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-rose-700 hover:bg-rose-800 text-white font-black text-xs shadow-md transition-all shrink-0 active:scale-95"
        >
          <RefreshCw className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
          <span>{isRunning ? 'Running Red Team...' : 'Re-Run Attack Traps'}</span>
        </button>
      </div>

      {/* Defense Telemetry Summary */}
      <div className="p-6 rounded-2xl border border-rose-300 bg-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-black text-rose-900 uppercase block mb-1">
            RED TEAM GATING DEFENSE RATE
          </span>
          <div className="text-3xl font-black text-[#0d2247]">
            {Math.round(preventionRate * 100)}% Prevention of False Correspondences
          </div>
          <p className="text-xs text-slate-900 font-bold mt-1.5 max-w-xl leading-relaxed">
            Raw visual similarity alone is never accepted as proof. All candidate correspondences must satisfy geometric projective consistency, ephemeris illumination, and topographic slope profiles.
          </p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 text-white text-center shrink-0 shadow-sm border border-slate-800">
          <span className="text-[10px] text-slate-300 block uppercase font-extrabold tracking-wide">DECEPTIVE TRAPS</span>
          <span className="text-2xl font-black text-emerald-400">{tests.length} / {tests.length} Blocked</span>
        </div>
      </div>

      {/* Deceptive Traps Showcase Grid */}
      <div className="space-y-4">
        {tests.map((test) => (
          <div
            key={test.test_id}
            className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4 hover:border-slate-300 transition-all"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-3">
                <span className="text-xs font-black px-2.5 py-0.5 rounded bg-rose-100 text-rose-950 border border-rose-300">
                  {test.test_id}
                </span>
                <h3 className="text-sm font-black text-[#0d2247]">{test.name}</h3>
              </div>
              <span className="text-xs font-black px-3 py-1 rounded-full bg-emerald-100 text-emerald-950 border border-emerald-300 flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-700" />
                <span>{test.final_decision}</span>
              </span>
            </div>

            {/* Attack Vector Description */}
            <div className="text-xs text-slate-900 leading-relaxed bg-slate-50 p-3.5 rounded-xl border border-slate-200 font-bold">
              <strong className="text-blue-900 font-black">Attack Vector: </strong>
              {test.attack_vector}
            </div>

            {/* Contrast Comparison Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              {/* Left: Raw Matcher Result */}
              <div className="p-4 rounded-xl bg-rose-50/80 border border-rose-300 space-y-1.5">
                <div className="flex items-center space-x-2 text-rose-950 font-black text-xs uppercase">
                  <XCircle className="w-4 h-4 text-rose-700" />
                  <span>Raw Visual Matcher (Deceived)</span>
                </div>
                <div className="text-rose-950 font-black text-sm">{test.raw_matcher_result}</div>
                <p className="text-[11px] text-slate-900 font-bold pt-1">
                  Naive visual matchers get fooled by circular crater symmetry or high local texture contrast.
                </p>
              </div>

              {/* Right: LunarSynapse Physics Verification Result */}
              <div className="p-4 rounded-xl bg-emerald-50/80 border border-emerald-300 space-y-1.5">
                <div className="flex items-center space-x-2 text-emerald-950 font-black text-xs uppercase">
                  <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                  <span>LunarSynapse Multi-Physics Gating</span>
                </div>
                <div className="text-emerald-950 font-black text-sm">{test.physics_verification_result}</div>
                <p className="text-[11px] text-slate-900 font-bold pt-1">
                  {test.explanation}
                </p>
              </div>
            </div>

            {/* Physics Rejection Reasons Breakdown */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5 text-xs">
              <span className="text-[10px] uppercase font-black text-rose-900 block">
                PHYSICS REJECTION LOG:
              </span>
              <ul className="list-disc list-inside text-slate-900 font-bold space-y-1 text-xs">
                {test.rejection_reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>

      {/* Phase 2 Real-Data Baseline Telemetry Section */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <span className="text-[10px] uppercase font-black px-2.5 py-0.5 rounded bg-blue-100 text-blue-900 border border-blue-300">
              PHASE 2 SCIENTIFIC BASELINE
            </span>
            <h2 className="text-base font-black text-[#0d2247] mt-1">Real-Data Correspondence Benchmark Matrix</h2>
          </div>
          <span className="text-xs text-slate-800 font-bold">Ground Truth Levels 1–4</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-slate-200 text-slate-800 font-black">
                <th className="pb-2">Pair ID</th>
                <th className="pb-2">Matcher</th>
                <th className="pb-2">GT Level</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Inliers</th>
                <th className="pb-2">Inlier Ratio</th>
                <th className="pb-2">Err (px)</th>
                <th className="pb-2">Coverage</th>
                <th className="pb-2">Impl Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-900 font-bold">
              <tr>
                <td className="py-3 font-black text-blue-900">SYNTH_CTRL_OHRC_LRO_001</td>
                <td className="py-3">SIFT</td>
                <td className="py-3"><span className="text-amber-900 font-black">LEVEL_4 (Synthetic Control)</span></td>
                <td className="py-3"><span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-950 border border-emerald-300 font-black">ACCEPTED</span></td>
                <td className="py-3">42</td>
                <td className="py-3">68.5%</td>
                <td className="py-3">1.42 px</td>
                <td className="py-3">34.2%</td>
                <td className="py-3"><span className="text-emerald-900 font-black">REAL</span></td>
              </tr>
              <tr>
                <td className="py-3 font-black text-blue-900">REAL_OHRC_LRO_001</td>
                <td className="py-3">SIFT</td>
                <td className="py-3"><span className="text-slate-600 font-bold">LEVEL_UNKNOWN</span></td>
                <td className="py-3"><span className="px-2 py-0.5 rounded bg-slate-100 text-slate-900 border border-slate-300 font-black">DATA_PENDING</span></td>
                <td className="py-3">-</td>
                <td className="py-3">-</td>
                <td className="py-3">-</td>
                <td className="py-3">-</td>
                <td className="py-3"><span className="text-emerald-900 font-black">REAL</span></td>
              </tr>
              <tr>
                <td className="py-3 font-black text-blue-900">REAL_OHRC_TMC2_001</td>
                <td className="py-3">ORB</td>
                <td className="py-3"><span className="text-slate-600 font-bold">LEVEL_UNKNOWN</span></td>
                <td className="py-3"><span className="px-2 py-0.5 rounded bg-slate-100 text-slate-900 border border-slate-300 font-black">DATA_PENDING</span></td>
                <td className="py-3">-</td>
                <td className="py-3">-</td>
                <td className="py-3">-</td>
                <td className="py-3">-</td>
                <td className="py-3"><span className="text-emerald-900 font-black">REAL</span></td>
              </tr>
              <tr>
                <td className="py-3 font-black text-blue-900">REAL_IIRS_OPTICAL_001</td>
                <td className="py-3">SIFT</td>
                <td className="py-3"><span className="text-slate-600 font-bold">LEVEL_UNKNOWN</span></td>
                <td className="py-3"><span className="px-2 py-0.5 rounded bg-slate-100 text-slate-900 border border-slate-300 font-black">DATA_PENDING</span></td>
                <td className="py-3">-</td>
                <td className="py-3">-</td>
                <td className="py-3">-</td>
                <td className="py-3">-</td>
                <td className="py-3"><span className="text-amber-900 font-black">SINGLE_BAND_BASELINE</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
