import {
  Observation,
  Correspondence,
  RegistrationExperiment,
  LunarEntity,
  EntityDetail,
  KnowledgeGap,
  Recommendation,
  StressScenario,
  RedTeamResponse,
  SystemHealth,
  SystemStatus,
  PhysicalVerificationResponse,
  GateCatalogResponse,
  EvidenceDetailResponse,
  UncertaintyResponse,
  UncertaintySummaryResponse,
  DemonstrationScenario,
  ScenarioExplanation,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

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
  // System Health & Subsystems Status
  getHealth: () => fetchJson<SystemHealth>(`${API_BASE}/system/health`),
  getSystemStatus: () => fetchJson<SystemStatus>(`${API_BASE}/system/status`),

  // Demo Mission Execution
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
  analyzeCorrespondence: (
    srcId: string,
    tgtId: string,
    algo: string = 'SIFT',
    question: string = 'spectral analysis'
  ) =>
    fetchJson<Correspondence>(`${API_BASE}/correspondence/analyze`, {
      method: 'POST',
      body: JSON.stringify({
        source_observation_id: srcId,
        target_observation_id: tgtId,
        matcher_algorithm: algo,
        ratio_threshold: 0.8,
        scientific_question: question,
      }),
    }),

  // Physical Verification
  getPhysicalGates: () => fetchJson<GateCatalogResponse>(`${API_BASE}/physical-verification/gates`),
  getPhysicalVerification: (corrId: string) =>
    fetchJson<PhysicalVerificationResponse>(`${API_BASE}/physical-verification/${corrId}`),

  // Evidence Dimensions & Details
  getEvidenceDimensions: () =>
    fetchJson<{ dimensions: string[]; policy: string }>(`${API_BASE}/evidence/dimensions`),
  getEvidence: (corrId: string) =>
    fetchJson<EvidenceDetailResponse>(`${API_BASE}/evidence/${corrId}`),

  // Uncertainty
  getUncertaintySummary: () =>
    fetchJson<UncertaintySummaryResponse>(`${API_BASE}/uncertainty/summary`),
  getUncertainty: (corrId: string) =>
    fetchJson<UncertaintyResponse>(`${API_BASE}/uncertainty/${corrId}`),

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
  getKnowledgeGapTypes: () =>
    fetchJson<{ supported_gap_types: string[]; description: string }>(
      `${API_BASE}/knowledge-gaps/types`
    ),
  getKnowledgeGaps: () => fetchJson<KnowledgeGap[]>(`${API_BASE}/knowledge-gaps`),
  getKnowledgeGap: (gapId: string) =>
    fetchJson<KnowledgeGap>(`${API_BASE}/knowledge-gaps/${gapId}`),

  // Next-Best Observation & Recommendations
  getRecommendations: () => fetchJson<Recommendation[]>(`${API_BASE}/recommendations`),
  getRecommendation: (id: string) =>
    fetchJson<Recommendation>(`${API_BASE}/recommendations/${id}`),
  getNextObservation: (entityId: string, question: string) =>
    fetchJson<Recommendation>(`${API_BASE}/recommendations/next-observation`, {
      method: 'POST',
      body: JSON.stringify({
        entity_id: entityId,
        scientific_question: question,
      }),
    }),

  // Adversarial Red Team Suite
  runRedTeam: () => fetchJson<RedTeamResponse>(`${API_BASE}/red-team/run`, { method: 'POST' }),

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

  // Phase 2 Real-Data Baseline Benchmark
  getPhase2Benchmark: (pairId?: string, matcher?: string) => {
    let url = `${API_BASE}/benchmark/phase2`;
    const params = new URLSearchParams();
    if (pairId) params.append('pair_id', pairId);
    if (matcher) params.append('matcher', matcher);
    if (params.toString()) url += `?${params.toString()}`;
    return fetchJson<{
      phase: string;
      total_results: number;
      summary: any;
      results: any[];
    }>(url);
  },

  // Demonstration Scenarios (Phase 8.4)
  getScenarios: () => fetchJson<DemonstrationScenario[]>(`${API_BASE}/demo/scenarios`),
  getScenario: (scenarioId: string) =>
    fetchJson<DemonstrationScenario>(`${API_BASE}/demo/scenarios/${scenarioId}`),

  // Scenario Explanations & Provenance (Phase 8.5)
  getScenarioExplanations: () =>
    fetchJson<ScenarioExplanation[]>(`${API_BASE}/demo/scenarios-explanations`),
  getScenarioExplanation: (scenarioId: string) =>
    fetchJson<ScenarioExplanation>(`${API_BASE}/demo/scenarios/${scenarioId}/explanation`),
};


