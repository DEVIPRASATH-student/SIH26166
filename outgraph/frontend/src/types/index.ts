export type SensorType = 'OHRC' | 'TMC-2' | 'IIRS' | 'LROC_NAC' | 'SELENE_TC' | 'SIMULATED_OPTICAL';

export interface Observation {
  id: string;
  sensor_type: SensorType;
  sensor?: string;
  image_url: string;
  acquisition_timestamp?: string;
  acquisition_time?: string;
  lat_min: number;
  lat_max: number;
  lon_min: number;
  lon_max: number;
  footprint?: {
    lat_min: number;
    lat_max: number;
    lon_min: number;
    lon_max: number;
  };
  spatial_resolution_m: number;
  spatial_resolution?: number;
  sun_azimuth_deg: number;
  sun_elevation_deg: number;
  incidence_angle_deg: number;
  emission_angle_deg: number;
  phase_angle_deg: number;
  solar_geometry?: {
    sun_azimuth_deg: number;
    sun_elevation_deg: number;
    incidence_angle_deg: number;
    emission_angle_deg: number;
    phase_angle_deg: number;
  };
  spacecraft_geometry?: Record<string, any>;
  metadata: Record<string, any>;
  preprocessing_history: string[];
  is_synthetic: boolean;
  product_id?: string;
  mission?: string;
  instrument?: string;
  product_type?: string;
  processing_level?: string;
  num_bands?: number;
  data_type?: string;
  source?: string;
  provenance?: Record<string, any>;
  data_provenance?: Record<string, any>;
}

export interface MatchPoint {
  src_x: number;
  src_y: number;
  tgt_x: number;
  tgt_y: number;
  is_inlier: boolean;
  distance: number;
}

export interface EvidenceProfile {
  visual_score: number;
  geometry_score: number;
  illumination_score: number;
  terrain_score: number;
  scale_score: number;
  spatial_score: number;
  overall_confidence: number;
  status: string;
  rejection_reasons: string[];
}

export interface UncertaintyBreakdown {
  total_uncertainty: number;
  evidence_disagreement: number;
  geometric_instability: number;
  feature_ambiguity: number;
  spatial_sparsity: number;
  calibration_status: string;
  saturation_limit?: string;
}

export interface PhysicalGateResult {
  gate_id: string;
  gate_name: string;
  status: 'PASS' | 'REJECTED' | 'NOT_EVALUATED';
  reason: string;
  threshold?: string;
  observed_value?: string;
}

export interface PhysicalVerificationResponse {
  correspondence_id: string;
  passed: boolean;
  status: string;
  gates: Record<string, PhysicalGateResult>;
  rejection_reasons: string[];
  limitations: string[];
  provenance: {
    is_synthetic: boolean;
    type: string;
  };
}

export interface GateCatalogEntry {
  gate_id: string;
  gate_name: string;
  description: string;
  failure_criterion: string;
  threshold: string;
}

export interface GateCatalogResponse {
  description: string;
  gates: Record<string, GateCatalogEntry>;
  policy: string;
}

export interface EvidenceDetailResponse {
  correspondence_id: string;
  dimensions: {
    GEOMETRIC: number;
    TERRAIN: number;
    ILLUMINATION: number;
    SPECTRAL: number;
    SCALE: number;
    TEMPORAL: number;
    TEXTURE: number;
    REGISTRATION: number;
    PHYSICAL: number;
    MANUAL: number;
    SYNTHETIC: number;
    [key: string]: number;
  };
  supporting_evidence: string[];
  missing_evidence: string[];
  unknown_not_negative_preservation: boolean;
  overall_confidence: number;
  total_uncertainty: number;
  evidence_disagreement: number;
  status: string;
  rejection_reasons: string[];
  is_synthetic: boolean;
}

export interface UncertaintyResponse {
  correspondence_id: string;
  scalar: number;
  interval: {
    lower: number;
    upper: number;
    confidence_level: number;
  };
  covariance_proxy: number[][];
  qualitative: 'LOW' | 'MODERATE' | 'HIGH' | 'SATURATED';
  decomposition: {
    evidence_disagreement: number;
    geometric_instability: number;
    feature_ambiguity: number;
    spatial_sparsity: number;
  };
  calibration_status: string;
  scientific_limitations: string[];
}

export interface UncertaintySummaryResponse {
  mean_correspondence_uncertainty: number;
  mean_evidence_disagreement: number;
  mean_entity_uncertainty: number;
  total_evaluated_correspondences: number;
  calibration_status: string;
  real_data_calibration_status: string;
  uncertainty_saturation_limit: string;
  unknown_preservation: string;
  description: string;
}

export interface Correspondence {
  id: string;
  source_observation_id: string;
  target_observation_id: string;
  matcher_algorithm: string;
  num_candidate_matches: number;
  num_inliers: number;
  inlier_ratio: number;
  visual_confidence: number;
  overall_confidence: number;
  status: string;
  is_synthetic: boolean;
  matches: MatchPoint[];
  evidence_profile?: EvidenceProfile;
  uncertainty_breakdown?: UncertaintyBreakdown;
  created_at: string;

  // Phase 8.2 scientific contract fields
  candidate_count?: number;
  inlier_count?: number;
  matcher?: string;
  geometric_status?: string;
  physical_verification_status?: string;
  physical_gate_results?: Record<string, any>;
  rejection_reasons?: string[];
  uncertainty?: UncertaintyBreakdown;
  world_model_effect?: {
    entity_id: string;
    entity_state: string;
  };
  knowledge_gaps?: any[];
  recommendations?: any[];
  explanation?: {
    decision?: string;
    primary_reason?: string;
    failed_gate?: string | null;
    rejection_reasons?: string[];
    limitations?: string[];
    [key: string]: any;
  };
  provenance?: {
    type: string;
    is_synthetic: boolean;
  };
  data_provenance?: {
    type: string;
    is_synthetic: boolean;
  };
  limitations?: string[];
  scientific_limitations?: string[];
}

export interface RegistrationExperiment {
  id: string;
  correspondence_id: string;
  is_success: boolean;
  transformation_matrix: number[][];
  registered_image_url: string;
  difference_image_url: string;
  rmse: number;
  subpixel_error_px: number;
  inlier_ratio: number;
  spatial_coverage: number;
  algorithm: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface WorldModelHypothesis {
  property_name: string;
  hypothesis_value: string;
  confidence: number;
  uncertainty: number;
  evidence_count: number;
  supporting_evidence: string[];
  conflicting_evidence: string[];
}

export interface LunarEntity {
  entity_id: string;
  entity_type: string;
  latitude: number;
  longitude: number;
  spatial_extent_m: number;
  confidence: number;
  uncertainty: number;
  associated_observations_count: number;
  sensors_present: string[];
  created_at: string;
}

export interface EntityDetail extends LunarEntity {
  morphology: Record<string, any>;
  elevation: Record<string, any>;
  spectral: Record<string, any>;
  observations: {
    observation_id: string;
    sensor_type: string;
    correspondence_id?: string;
    attached_at: string;
    confidence: number;
  }[];
  hypotheses: WorldModelHypothesis[];
}

export interface KnowledgeGap {
  id: string;
  entity_id: string;
  gap_type: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  reason: string;
  recommended_sensor: string;
  status: string;
  is_synthetic?: boolean;
  created_at: string;
}

export interface Recommendation {
  id: string;
  entity_id: string;
  scientific_question: string;
  recommended_sensor: string;
  expected_information_gain: number;
  uncertainty_reduction: number;
  uncertainty_reduction_basis?: string;
  feasibility: number;
  payload_status?: 'AVAILABLE' | 'PAYLOAD_UNAVAILABLE' | string;
  explanation: string;
  sensor_requirement?: string;
  spatial_requirement?: string;
  temporal_requirement?: string;
  rationale?: string;
  ranked_sensors: {
    sensor: string;
    expected_information_gain: number;
    uncertainty_reduction: number;
    relevance_score: number;
    feasibility: number;
    description: string;
    explanation: string;
    is_new_modality: boolean;
  }[];
  provenance?: {
    type: string;
    is_synthetic: boolean;
  };
  data_provenance?: {
    type: string;
    is_synthetic: boolean;
  };
  is_synthetic?: boolean;
  created_at: string;
}

export interface StressScenario {
  scenario_id: string;
  scenario_name: string;
  description: string;
  algorithms_evaluated: {
    algorithm: string;
    candidate_matches: number;
    inliers: number;
    inlier_ratio: number;
    rmse: number;
    mean_reprojection_error_px: number;
    false_correspondence_rate: number;
    spatial_coverage: number;
    decision: string;
  }[];
  winner_algorithm: string;
  summary: string;
}

export interface RedTeamTest {
  test_id: string;
  name: string;
  attack_vector: string;
  raw_matcher_result: string;
  physics_verification_result: string;
  final_decision: string;
  rejection_reasons: string[];
  evidence_breakdown: Record<string, number>;
  explanation: string;
}

export interface RedTeamResponse {
  tests: RedTeamTest[];
  total_deceptive_tests: number;
  false_positives_prevented: number;
  prevention_rate: number;
}

export interface SystemHealth {
  status: string;
  version: string;
  database_connected: boolean;
  ml_backends: Record<string, boolean>;
  storage_healthy: boolean;
  total_observations: number;
  total_entities: number;
  total_verified_matches: number;
}

export interface SystemStatus {
  status: string;
  version: string;
  database_connected: boolean;
  scientific_pipeline: string;
  dem_availability: {
    SLDEM2015_cached: boolean;
    elevation_range_m: number[];
    status: string;
  };
  groundgrid_availability: {
    OHRC_calibrated_grid: boolean;
    TMC2_calibrated_grid: boolean;
    status: string;
  };
  ml_backends: Record<string, boolean>;
  raw_data_integrity: string;
  storage_healthy: boolean;
  total_observations: number;
  total_entities: number;
  total_verified_matches: number;
}

export interface DemonstrationScenario {
  scenario_id: string;
  scenario_name: string;
  scenario_type: string;
  real_or_synthetic: string;
  is_synthetic: boolean;
  source_observation: string;
  target_observation: string;
  correspondence_id?: string;
  candidate_count: number;
  candidate_count_notes?: string;
  geometric_result: string;
  physical_result: string;
  gate_metrics_notes?: string;
  evidence_state: Record<string, { status: string; confidence: number; description: string }>;
  uncertainty_state: {
    scalar_uncertainty: number;
    epistemic_uncertainty?: number;
    aleatoric_uncertainty?: number;
    qualitative_risk?: string;
    status?: string;
    confidence_interval?: number[];
    calibration_note?: string;
    [key: string]: any;
  };
  knowledge_gap?: {
    gap_id: string;
    gap_type: string;
    description: string;
    priority: number;
    [key: string]: any;
  };
  recommendation?: {
    recommendation_id: string;
    recommendation_type: string;
    recommended_sensor: string;
    expected_information_gain: number;
    description: string;
    warning?: string;
    [key: string]: any;
  };
  limitations: string[];
}

export interface PhysicalGateDetail {
  gate_id: number;
  gate_name: string;
  input: string;
  result: string;
  reason: string;
  metric: string;
  unit: string;
  threshold: string;
  actual_value?: string;
  note?: string;
}

export interface ExplainabilityTraceStep {
  step: number;
  name: string;
  status: string;
  reason: string;
  source: string;
  metric?: string;
}

export interface ScenarioExplanation {
  scenario_id: string;
  scenario_name: string;
  decision: string;
  primary_reason: string;
  summary: string;
  judge_card: {
    question: string;
    high_level_verdict: string;
    does_this_mean_images_are_unrelated: string;
    physical_gates_verdict: string;
    uncertainty_impact: string;
    is_real_or_synthetic: string;
  };
  provenance: {
    source_observation: string;
    target_observation: string;
    product_id_source: string;
    product_id_target: string;
    sensor_source: string;
    sensor_target: string;
    acquisition_time_source?: string;
    acquisition_time_target?: string;
    data_provenance: string;
    is_synthetic: boolean;
    source_gsd_m?: number;
    target_gsd_m?: number;
    source_dimensions?: number[];
    target_dimensions?: number[];
    source_solar_azimuth_deg?: number;
    source_solar_elevation_deg?: number;
    source_incidence_angle_deg?: number;
    target_solar_azimuth_deg?: number;
    target_solar_elevation_deg?: number;
    target_incidence_angle_deg?: number;
    dem_source?: string;
    processing_stage?: string;
    matcher?: string;
    physical_verifier?: string;
    derived_status?: string;
  };
  input_metadata: Record<string, any>;
  candidate_generation: {
    current_demonstration_instance: {
      matcher_used: string;
      candidate_count: number;
      candidate_description: string;
      feature_scale?: string;
      preprocessing_applied?: string;
      fallback_matcher_used?: boolean;
    };
    historical_phase7_benchmark?: {
      matcher_used: string;
      candidate_count: number;
      geometric_inliers: number;
      inlier_ratio_pct: number;
      note: string;
    };
  };
  geometric_evidence: {
    verification_method: string;
    transformation_model: string;
    inlier_count: number;
    reprojection_residual_px?: number | null;
    degeneracy_status?: string;
    condition_number?: number | null;
    geometric_decision: string;
    scientific_distinction?: string;
  };
  physical_gates: {
    overall_result: string;
    decisive_gate: string;
    gates: PhysicalGateDetail[];
  };
  illumination_evidence: {
    section_title: string;
    status: string;
    source_solar_azimuth_deg?: number;
    target_solar_azimuth_deg?: number;
    source_solar_elevation_deg?: number;
    target_solar_elevation_deg?: number;
    solar_azimuth_difference_deg?: number;
    solar_elevation_difference_deg?: number;
    incidence_angle_divergence_deg?: number;
    temporal_difference_days?: number;
    illumination_divergence_result: string;
    explanation: string;
    gate_distinction_note: string;
  };
  evidence_dimensions: Record<
    string,
    {
      status: string;
      evidence_present: string;
      evidence_missing: string;
      evidence_source: string;
      confidence: number;
    }
  >;
  uncertainty: {
    scalar_uncertainty: number;
    epistemic_uncertainty?: number;
    aleatoric_uncertainty?: number;
    qualitative_risk?: string;
    status?: string;
    decomposition?: {
      evidence_disagreement: string;
      geometric_instability: string;
      feature_ambiguity: string;
      spatial_sparsity: string;
    };
    confidence_interval?: number[];
    covariance_representation?: Record<string, number>;
    calibration_statement?: string;
    saturation_note?: string;
  };
  knowledge_gap?: {
    gap_id: string;
    gap_type: string;
    what_is_known: string;
    what_is_unknown: string;
    why_is_it_unknown: string;
    what_evidence_is_missing: string;
  } | null;
  recommendation?: {
    recommendation_id: string;
    recommendation_type: string;
    candidate_observation: string;
    expected_uncertainty_reduction: number;
    operational_requirements?: string;
    payload_availability?: string;
    disclaimer?: string;
  } | null;
  explainability_trace: ExplainabilityTraceStep[];
  limitations: string[];
}


