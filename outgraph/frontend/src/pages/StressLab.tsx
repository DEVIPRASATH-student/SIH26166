import React, { useState, useEffect } from 'react';
import { StressScenario } from '../types';
import { Flame, Play, CheckCircle2, AlertTriangle, ShieldCheck, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export const StressLab: React.FC = () => {
  const [scenarios, setScenarios] = useState<StressScenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('');
  const [isRunning, setIsRunning] = useState<boolean>(false);

  const runBenchmark = async () => {
    setIsRunning(true);
    try {
      const data = await api.runBenchmarks();
      setScenarios(data.scenarios);
      if (!selectedScenarioId && data.scenarios.length > 0) {
        setSelectedScenarioId(data.scenarios[0].scenario_id);
      }
    } catch (err) {
      console.error('Failed to run benchmark suite', err);
    } finally {
      setIsRunning(false);
    }
  };

  useEffect(() => {
    api
      .getBenchmarks()
      .then((data) => {
        setScenarios(data.scenarios);
        if (data.scenarios.length > 0) {
          setSelectedScenarioId(data.scenarios[0].scenario_id);
        }
      })
      .catch((err) => console.error(err));
  }, []);

  const activeScenario =
    scenarios.find((s) => s.scenario_id === selectedScenarioId) || scenarios[0];

  return (
    <div className="space-y-6 font-sans">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-[#0d2247] flex items-center space-x-2 tracking-tight">
            <Flame className="w-6 h-6 text-amber-500" />
            <span>Lunar Cross-Modal Stress Lab</span>
          </h1>
          <p className="text-xs text-slate-600 font-semibold mt-1">
            Systematic benchmarking under extreme lunar illumination, multi-scale resolution jumps, and heavy sensor noise.
          </p>
        </div>

        <button
          onClick={runBenchmark}
          disabled={isRunning}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-700 hover:bg-blue-800 text-white font-bold text-xs shadow-md transition-all shrink-0 active:scale-95"
        >
          <RefreshCw className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
          <span>{isRunning ? 'Benchmarking...' : 'Execute Stress Suite'}</span>
        </button>
      </div>

      {/* Scenario Selector Tabs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {scenarios.map((scn) => {
          const isSelected = scn.scenario_id === activeScenario?.scenario_id;
          return (
            <div
              key={scn.scenario_id}
              onClick={() => setSelectedScenarioId(scn.scenario_id)}
              className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-white border-blue-600 shadow-md ring-2 ring-blue-500/20'
                  : 'bg-white border-slate-200 hover:border-slate-300 shadow-sm'
              }`}
            >
              <span className="text-[10px] uppercase font-extrabold text-blue-700 block mb-1">
                {scn.scenario_id}
              </span>
              <h3 className="text-xs font-bold text-slate-900 mb-1">{scn.scenario_name}</h3>
              <p className="text-[11px] text-slate-600 line-clamp-2 font-medium">{scn.description}</p>
            </div>
          );
        })}
      </div>

      {/* Active Scenario Evaluation Matrix */}
      {activeScenario && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-100 pb-4">
            <div>
              <h2 className="text-base font-extrabold text-[#0d2247]">{activeScenario.scenario_name}</h2>
              <p className="text-xs text-slate-600 mt-0.5 font-medium">{activeScenario.description}</p>
            </div>
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
              WINNER: {activeScenario.winner_algorithm}
            </span>
          </div>

          {/* Comparative Metrics Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead className="bg-slate-50 text-slate-700 uppercase text-[10px] font-bold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-3">Algorithm</th>
                  <th className="py-3 px-3">Candidates</th>
                  <th className="py-3 px-3">Inliers</th>
                  <th className="py-3 px-3">Inlier Ratio</th>
                  <th className="py-3 px-3">RMSE</th>
                  <th className="py-3 px-3">Reproj Error</th>
                  <th className="py-3 px-3">False Match Rate</th>
                  <th className="py-3 px-3">Verdict</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-900 font-medium">
                {activeScenario.algorithms_evaluated.map((algo, idx) => {
                  const isVerifiedPipeline = algo.algorithm === 'LunarSynapse-Verified';
                  return (
                    <tr
                      key={idx}
                      className={
                        isVerifiedPipeline
                          ? 'bg-emerald-50/70 font-bold text-slate-900'
                          : 'hover:bg-slate-50'
                      }
                    >
                      <td className="py-3 px-3 flex items-center space-x-2">
                        {isVerifiedPipeline ? (
                          <ShieldCheck className="w-4 h-4 text-emerald-600" />
                        ) : null}
                        <span>{algo.algorithm}</span>
                      </td>
                      <td className="py-3 px-3">{algo.candidate_matches}</td>
                      <td className="py-3 px-3">{algo.inliers}</td>
                      <td className="py-3 px-3 text-blue-700 font-bold">
                        {Math.round(algo.inlier_ratio * 100)}%
                      </td>
                      <td className="py-3 px-3 text-slate-900 font-bold">{algo.rmse}</td>
                      <td className="py-3 px-3">{algo.mean_reprojection_error_px} px</td>
                      <td className="py-3 px-3 text-rose-600 font-bold">
                        {Math.round(algo.false_correspondence_rate * 100)}%
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`text-[10px] px-2.5 py-1 rounded-full font-bold uppercase ${
                            algo.decision === 'VERIFIED' || algo.decision === 'ACCEPTED'
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                              : 'bg-rose-100 text-rose-800 border border-rose-200'
                          }`}
                        >
                          {algo.decision}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-xs text-blue-900 font-medium">
            <strong className="text-[#0d2247]">Key Finding: </strong> {activeScenario.summary}
          </div>
        </div>
      )}
    </div>
  );
};
