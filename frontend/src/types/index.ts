export type SensorType = 'OHRC' | 'TMC-2' | 'IIRS';

export interface Observation {
  id: string;
  sensor_type: SensorType;
  image_url: string;
  acquisition_timestamp: string;
  lat_min: number;
  lat_max: number;
  lon_min: number;
  lon_max: number;
  spatial_resolution_m: number;
  sun_azimuth_deg: number;
  sun_elevation_deg: number;
  incidence_angle_deg: number;
  emission_angle_deg: number;
  phase_angle_deg: number;
  metadata: Record<string, any>;
  preprocessing_history: string[];
  is_synthetic: boolean;
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
  status: 'VERIFIED' | 'UNCERTAIN' | 'REJECTED';
  rejection_reasons: string[];
}

export interface UncertaintyBreakdown {
  total_uncertainty: number;
  evidence_disagreement: number;
  geometric_instability: number;
  feature_ambiguity: number;
  spatial_sparsity: number;
  calibration_status: string;
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
  status: 'VERIFIED' | 'UNCERTAIN' | 'REJECTED';
  matches: MatchPoint[];
  evidence_profile?: EvidenceProfile;
  uncertainty_breakdown?: UncertaintyBreakdown;
  created_at: string;
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
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  reason: string;
  recommended_sensor: string;
  status: string;
  created_at: string;
}

export interface Recommendation {
  id: string;
  entity_id: string;
  scientific_question: string;
  recommended_sensor: string;
  expected_information_gain: number;
  uncertainty_reduction: number;
  feasibility: number;
  explanation: string;
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
