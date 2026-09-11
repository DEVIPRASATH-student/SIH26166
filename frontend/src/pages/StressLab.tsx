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
    <div className="space-y-6 font-mono">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-lunar-50 flex items-center space-x-2">
            <Flame className="w-5 h-5 text-amber-400" />
            <span>Lunar Cross-Modal Stress Lab</span>
          </h1>
          <p className="text-xs text-lunar-400">
            Systematic benchmarking under extreme lunar illumination, multi-scale resolution jumps, and heavy sensor noise.
          </p>
        </div>

        <button
          onClick={runBenchmark}
          disabled={isRunning}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-space-cyan to-blue-600 hover:from-sky-400 hover:to-blue-500 text-lunar-950 font-bold text-xs shadow-md transition-all shrink-0"
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
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-space-cyan/15 border-space-cyan shadow-md'
                  : 'telemetry-panel border-lunar-700/60 hover:bg-lunar-800'
              }`}
            >
              <span className="text-[10px] uppercase font-bold text-space-cyan block mb-1">
                {scn.scenario_id}
              </span>
              <h3 className="text-xs font-bold text-lunar-100 mb-1">{scn.scenario_name}</h3>
              <p className="text-[11px] text-lunar-400 line-clamp-2">{scn.description}</p>
            </div>
          );
        })}
      </div>

      {/* Active Scenario Evaluation Matrix */}
      {activeScenario && (
        <div className="telemetry-panel p-5 rounded-xl border border-lunar-700/60 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-lunar-800 pb-3">
            <div>
              <h2 className="text-sm font-bold text-lunar-50">{activeScenario.scenario_name}</h2>
              <p className="text-xs text-lunar-300 mt-0.5">{activeScenario.description}</p>
            </div>
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-space-emerald/20 text-space-emerald border border-space-emerald/30">
              WINNER: {activeScenario.winner_algorithm}
            </span>
          </div>

          {/* Comparative Metrics Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-lunar-950 text-lunar-400 uppercase text-[10px] border-b border-lunar-800">
                <tr>
                  <th className="py-2.5 px-3">Algorithm</th>
                  <th className="py-2.5 px-3">Candidates</th>
                  <th className="py-2.5 px-3">Inliers</th>
                  <th className="py-2.5 px-3">Inlier Ratio</th>
                  <th className="py-2.5 px-3">RMSE</th>
                  <th className="py-2.5 px-3">Reproj Error</th>
                  <th className="py-2.5 px-3">False Match Rate</th>
                  <th className="py-2.5 px-3">Verdict</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-lunar-800 text-lunar-200">
                {activeScenario.algorithms_evaluated.map((algo, idx) => {
                  const isVerifiedPipeline = algo.algorithm === 'LunarSynapse-Verified';
                  return (
                    <tr
                      key={idx}
                      className={
                        isVerifiedPipeline
                          ? 'bg-space-emerald/10 font-semibold text-lunar-50'
                          : 'hover:bg-lunar-850'
                      }
                    >
                      <td className="py-3 px-3 flex items-center space-x-2">
                        {isVerifiedPipeline ? (
                          <ShieldCheck className="w-4 h-4 text-space-emerald" />
                        ) : null}
                        <span>{algo.algorithm}</span>
                      </td>
                      <td className="py-3 px-3">{algo.candidate_matches}</td>
                      <td className="py-3 px-3">{algo.inliers}</td>
                      <td className="py-3 px-3 text-space-cyan">
                        {Math.round(algo.inlier_ratio * 100)}%
                      </td>
                      <td className="py-3 px-3 text-lunar-100">{algo.rmse}</td>
                      <td className="py-3 px-3">{algo.mean_reprojection_error_px} px</td>
                      <td className="py-3 px-3 text-space-rose">
                        {Math.round(algo.false_correspondence_rate * 100)}%
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                            algo.decision === 'VERIFIED' || algo.decision === 'ACCEPTED'
                              ? 'bg-space-emerald/20 text-space-emerald'
                              : 'bg-space-rose/20 text-space-rose'
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

          <div className="p-3 rounded-lg bg-lunar-950 border border-lunar-800 text-xs text-lunar-300">
            <strong>Key Finding: </strong> {activeScenario.summary}
          </div>
        </div>
      )}
    </div>
  );
};
