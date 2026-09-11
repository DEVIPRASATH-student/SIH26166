import {
  Observation,
  Correspondence,
  RegistrationExperiment,
  LunarEntity,
  EntityDetail,
  KnowledgeGap,
  Recommendation,
  StressScenario,
  RedTeamTest,
  SystemHealth,
} from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`API Error [${res.status}]: ${errorBody}`);
  }
  return res.json();
}

export const api = {
  // System
  getHealth: () => fetchJson<SystemHealth>(`${API_BASE}/system/health`),

  // Demo Mission
  runDemoMission: () =>
    fetchJson<{
      status: string;
      message: string;
      execution_time_seconds: number;
      observations_created: number;
      correspondences_analyzed: number;
      entities_resolved: number;
      knowledge_gaps_found: number;
      top_recommendation: any;
    }>(`${API_BASE}/demo/run`, { method: 'POST' }),

  // Observations
  getObservations: () => fetchJson<Observation[]>(`${API_BASE}/observations`),
  getObservation: (id: string) => fetchJson<Observation>(`${API_BASE}/observations/${id}`),

  // Correspondence
  getCorrespondences: () => fetchJson<Correspondence[]>(`${API_BASE}/correspondence`),
  getCorrespondence: (id: string) => fetchJson<Correspondence>(`${API_BASE}/correspondence/${id}`),
  analyzeCorrespondence: (srcId: string, tgtId: string, algo: string = 'SIFT') =>
    fetchJson<Correspondence>(`${API_BASE}/correspondence/analyze`, {
      method: 'POST',
      body: JSON.stringify({
        source_observation_id: srcId,
        target_observation_id: tgtId,
        matcher_algorithm: algo,
        ratio_threshold: 0.8,
      }),
    }),

  // Registration
  getRegistration: (corrId: string) =>
    fetchJson<RegistrationExperiment>(`${API_BASE}/registration/${corrId}`),
  runRegistration: (corrId: string, subpixel: boolean = true) =>
    fetchJson<RegistrationExperiment>(`${API_BASE}/registration/run`, {
      method: 'POST',
      body: JSON.stringify({
        correspondence_id: corrId,
        apply_subpixel_ecc: subpixel,
      }),
    }),

  // Entities & World Model
  getEntities: () => fetchJson<LunarEntity[]>(`${API_BASE}/entities`),
  getEntityDetail: (entityId: string) =>
    fetchJson<EntityDetail>(`${API_BASE}/entities/${entityId}`),

  // Graph
  getFullGraph: () => fetchJson<{ nodes: any[]; edges: any[] }>(`${API_BASE}/graph/full`),

  // Knowledge Gaps
  getKnowledgeGaps: () => fetchJson<KnowledgeGap[]>(`${API_BASE}/knowledge-gaps`),

  // Recommendations
  getNextObservation: (entityId: string, question: string) =>
    fetchJson<Recommendation>(`${API_BASE}/recommendations/next-observation`, {
      method: 'POST',
      body: JSON.stringify({
        entity_id: entityId,
        scientific_question: question,
      }),
    }),

  // Benchmarks
  getBenchmarks: () =>
    fetchJson<{ scenarios: StressScenario[]; total_scenarios_evaluated: number; overall_winner: string }>(
      `${API_BASE}/benchmark/results`
    ),
  runBenchmarks: () =>
    fetchJson<{ scenarios: StressScenario[]; total_scenarios_evaluated: number; overall_winner: string }>(
      `${API_BASE}/benchmark/run`,
      { method: 'POST' }
    ),

  // Red Team
  runRedTeam: () =>
    fetchJson<{
      tests: RedTeamTest[];
      total_deceptive_tests: number;
      false_positives_prevented: number;
      prevention_rate: number;
    }>(`${API_BASE}/red-team/run`, { method: 'POST' }),
};
