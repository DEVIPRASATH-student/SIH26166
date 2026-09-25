import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  HelpCircle,
  Zap,
  Target,
  AlertTriangle,
  ArrowRight,
  Info,
  Layers,
  Database,
  CheckCircle2,
  XCircle,
  Clock,
  Compass,
} from 'lucide-react';
import { DemonstrationScenario, ScenarioExplanation } from '../types';
import { api } from '../services/api';
import { ExplainabilityModal } from '../components/ExplainabilityModal';

const CANONICAL_SCENARIOS_FALLBACK: DemonstrationScenario[] = [
  {
    scenario_id: 'SCENARIO-A',
    scenario_name: 'Real Lunar Negative Control (OHRC vs TMC-2)',
    scenario_type: 'REAL_NEGATIVE_CONTROL',
    real_or_synthetic: 'REAL',
    is_synthetic: false,
    source_observation: 'urn:isro:isda:ch2_cho.ohr:data_calibrated:ch2_ohr_ncp_20210402t0546284043_d_img_d18',
    target_observation: 'urn:isro:isda:ch2_cho.tmc:data_calibrated:ch2_tmc_nca_20240523t1600309581_d_img_d18',
    correspondence_id: 'CORR-urn:isro:isda:ch2_cho.ohr:data_calibrated:ch2_ohr_ncp_20210402t0546284043_d_img_d18-urn:isro:isda:ch2_cho.tmc:data_calibrated:ch2_tmc_nca_20240523t1600309581_d_img_d18',
    candidate_count: 26,
    candidate_count_notes: 'CURRENT DEMONSTRATION INSTANCE: 26 visual feature candidates generated under current pipeline configuration. SIFT = 31 candidates / 8 geometric inliers under baseline settings.',
    geometric_result: 'VISUAL_CANDIDATES_FOUND (26 feature matches detected in image space, forming candidate correspondence hypothesis)',
    physical_result: 'REJECTED (GATE 3 / GATE 4: Calibrated GroundGrid footprint non-overlap; target falls outside calibrated swath by ~1.49 km - 2.04 km; physical correspondence not validated)',
    gate_metrics_notes: 'GATE METRICS DISTINCTION: Bidirectional image-space residual threshold <= 4.0 px; Physical ground-space residual rejection threshold > 15 m; Footprint separation ~1.49-2.04 km.',
    evidence_state: {
      GEOMETRIC: { status: 'HYPOTHESIS_FORMED', confidence: 0.35, description: '26 visual candidates in image coordinates' },
      TERRAIN: { status: 'INCOMPATIBLE', confidence: 0.0, description: 'DEM projection outside calibrated overlap footprint' },
      ILLUMINATION: { status: 'EVALUATED', confidence: 0.50, description: 'Phase angle divergence evaluated' },
      SPECTRAL: { status: 'UNAVAILABLE', confidence: 0.0, description: 'IIRS cross-band calibration pending' },
      SCALE: { status: 'DISPARATE', confidence: 0.20, description: '0.25 m/px (OHRC) vs 5.0 m/px (TMC-2) (20x scale ratio)' },
      TEMPORAL: { status: 'EVALUATED', confidence: 0.40, description: 'Epoch separation: 2021-04-02 to 2024-05-23 (~3 years)' },
      TEXTURE: { status: 'AVAILABLE', confidence: 0.60, description: 'Local entropy sufficient for SIFT feature extraction' },
      REGISTRATION: { status: 'FAILED', confidence: 0.0, description: 'Sub-pixel ECC registration divergence due to spatial separation' },
      PHYSICAL: { status: 'REJECTED', confidence: 0.0, description: 'Footprint non-overlap (~1.49 km - 2.04 km separation)' },
      MANUAL: { status: 'UNAVAILABLE', confidence: 0.0, description: 'No independent ground truth tie points available' },
      SYNTHETIC: { status: 'NOT_APPLICABLE', confidence: 0.0, description: 'Real flight observations (is_synthetic = false)' }
    },
    uncertainty_state: {
      scalar_uncertainty: 0.95,
      epistemic_uncertainty: 0.90,
      aleatoric_uncertainty: 0.25,
      qualitative_risk: 'HIGH_EPISTEMIC_RISK',
      status: 'UNKNOWN',
      confidence_interval: [0.0, 0.08],
      calibration_note: 'REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED'
    },
    knowledge_gap: {
      gap_id: 'GAP-REAL-FOOTPRINT-001',
      gap_type: 'FOOTPRINT_NON_OVERLAP',
      description: 'Calibrated footprint non-overlap (~1.49-2.04 km separation) between OHRC swath and TMC-2 strip prevents physical correspondence verification.',
      priority: 0.92
    },
    recommendation: {
      recommendation_id: 'REC-REAL-OBS-001',
      recommendation_type: 'POTENTIALLY_REDUCES_UNCERTAINTY',
      recommended_sensor: 'TMC-2_ADJACENT_STRIP',
      expected_information_gain: 0.78,
      description: 'Target adjacent ground footprint tile with verified physical ground track coordinates to potentially reduce geometric uncertainty.',
      warning: 'Active observation recommendations are autonomous decision-support proposals, NOT spacecraft tasking, orbital scheduling, or mission commands.'
    },
    limitations: [
      'REAL-DATA ACCURACY = N/A',
      'PHYSICAL CORRESPONDENCE NOT VALIDATED',
      'REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED',
      'The evaluated physical geometry does not support correspondence for this pair.',
      'Visual candidates do not imply physical correspondence.',
      'No independent real-lunar tie-point ground truth.'
    ]
  },
  {
    scenario_id: 'SCENARIO-B',
    scenario_name: 'Controlled Synthetic OHRC Homologous Pair',
    scenario_type: 'SYNTHETIC_POSITIVE_CONTROL',
    real_or_synthetic: 'SYNTHETIC',
    is_synthetic: true,
    source_observation: 'OBS-OHRC-SYNTH-01',
    target_observation: 'OBS-OHRC-SYNTH-02',
    correspondence_id: 'CORR-OBS-OHRC-SYNTH-01-OBS-OHRC-SYNTH-02',
    candidate_count: 184,
    candidate_count_notes: 'CURRENT DEMONSTRATION INSTANCE: Synthetic homography validation instance yielding 184 visual candidates and 168 geometric inliers (91.3% inlier ratio).',
    geometric_result: 'GEOMETRICALLY_CONSISTENT (168 inliers, RANSAC inlier ratio 0.913)',
    physical_result: 'PHYSICALLY_VERIFIED (All 6 physical gates passed under known synthetic conditions)',
    gate_metrics_notes: 'GATE METRICS DISTINCTION: Image-space residual = 1.2 px; Physical ground-space residual = 2.1 m; Inlier count 168.',
    evidence_state: {
      GEOMETRIC: { status: 'SUPPORTED', confidence: 0.92, description: '168 verified geometric inliers' },
      TERRAIN: { status: 'CONSISTENT', confidence: 0.88, description: 'DEM ray-casting reprojection delta < 3.0 m' },
      ILLUMINATION: { status: 'CONSISTENT', confidence: 0.85, description: 'Azimuth divergence < 15.0 deg' },
      SPECTRAL: { status: 'UNAVAILABLE', confidence: 0.0, description: 'Single-modality OHRC synthetic control' },
      SCALE: { status: 'CONSISTENT', confidence: 0.95, description: 'Identical nominal ground sampling resolution' },
      TEMPORAL: { status: 'CONSISTENT', confidence: 0.90, description: 'Simulated simultaneous acquisition' },
      TEXTURE: { status: 'EXCELLENT', confidence: 0.88, description: 'High SIFT keypoint density across crater field' },
      REGISTRATION: { status: 'CONVERGED', confidence: 0.91, description: 'Sub-pixel ECC registration RMSE = 0.42 px' },
      PHYSICAL: { status: 'PASSED', confidence: 0.94, description: 'All Six Physical Gates cleared' },
      MANUAL: { status: 'UNAVAILABLE', confidence: 0.0, description: 'Automated synthetic verification' },
      SYNTHETIC: { status: 'KNOWN_GROUND_TRUTH', confidence: 1.0, description: 'Synthetically warped with known homography matrix' }
    },
    uncertainty_state: {
      scalar_uncertainty: 0.08,
      epistemic_uncertainty: 0.05,
      aleatoric_uncertainty: 0.06,
      qualitative_risk: 'LOW_EPISTEMIC_RISK',
      status: 'VERIFIED',
      confidence_interval: [0.88, 0.96],
      calibration_note: 'Synthetic positive control demonstrates algorithmic correctness under ground-truth conditions.'
    },
    knowledge_gap: undefined,
    recommendation: undefined,
    limitations: [
      'This controlled synthetic result demonstrates pipeline behavior under known conditions.',
      'It does NOT establish real-lunar accuracy.',
      'Synthetic verification is a necessary engineering sanity check, not flight qualification.'
    ]
  },
  {
    scenario_id: 'SCENARIO-C',
    scenario_name: 'Opposing Solar Azimuth Illumination Verification Rejection',
    scenario_type: 'SYNTHETIC_ILLUMINATION_CONTRADICTION',
    real_or_synthetic: 'SYNTHETIC',
    is_synthetic: true,
    source_observation: 'OBS-ILLUM-001',
    target_observation: 'OBS-ILLUM-002',
    correspondence_id: 'CORR-OBS-ILLUM-001-OBS-ILLUM-002',
    candidate_count: 45,
    candidate_count_notes: 'CURRENT DEMONSTRATION INSTANCE: 45 2D visual candidates form a superficial visual hypothesis due to crater rim symmetry under opposing shadows.',
    geometric_result: 'VISUAL_HYPOTHESIS_ONLY (45 keypoint candidates formed along crater rims under deceptive 2D shadow symmetry)',
    physical_result: 'REJECTED (Illumination verification rejected candidate due to 180° solar azimuth divergence)',
    gate_metrics_notes: 'GATE METRICS DISTINCTION: Illumination verification is a separate physics validation mechanism from the six physical gates.',
    evidence_state: {
      GEOMETRIC: { status: 'AMBIGUOUS', confidence: 0.40, description: 'Visual candidates present along crater rims' },
      TERRAIN: { status: 'CONTRADICTORY', confidence: 0.10, description: 'Shadow-derived slope vectors contradict DEM topography' },
      ILLUMINATION: { status: 'REJECTED', confidence: 0.0, description: 'Opposing solar azimuth (180.0 deg divergence)' },
      SPECTRAL: { status: 'UNAVAILABLE', confidence: 0.0, description: 'Single-band test' },
      SCALE: { status: 'CONSISTENT', confidence: 0.90, description: 'Identical nominal ground resolution' },
      TEMPORAL: { status: 'EVALUATED', confidence: 0.50, description: 'Simulated differing illumination epochs' },
      TEXTURE: { status: 'AVAILABLE', confidence: 0.70, description: 'Rim contrast generates keypoints' },
      REGISTRATION: { status: 'REJECTED', confidence: 0.0, description: 'Physical verification gates halted registration' },
      PHYSICAL: { status: 'REJECTED', confidence: 0.0, description: 'Photometric physics contradiction detected by illumination verification' },
      MANUAL: { status: 'UNAVAILABLE', confidence: 0.0, description: 'No manual labels' },
      SYNTHETIC: { status: 'KNOWN_CONTRADICTION', confidence: 1.0, description: 'Synthetically induced illumination inversion' }
    },
    uncertainty_state: {
      scalar_uncertainty: 0.88,
      epistemic_uncertainty: 0.85,
      aleatoric_uncertainty: 0.30,
      qualitative_risk: 'HIGH_EPISTEMIC_RISK',
      status: 'REJECTED_UNPHYSICAL',
      confidence_interval: [0.05, 0.18],
      calibration_note: 'Uncertainty model correctly flags adversarial illumination contradiction.'
    },
    knowledge_gap: {
      gap_id: 'GAP-SYNTH-ILLUM-001',
      gap_type: 'ILLUMINATION_CONTRADICTION',
      description: 'Opposing solar azimuth (180 deg) causes shadow inversion, inducing deceptive 2D visual feature similarity incompatible with lunar photometric physics.',
      priority: 0.85
    },
    recommendation: {
      recommendation_id: 'REC-SYNTH-ILLUM-001',
      recommendation_type: 'POTENTIALLY_REDUCES_UNCERTAINTY',
      recommended_sensor: 'OHRC_CONGRUENT_ILLUMINATION',
      expected_information_gain: 0.72,
      description: 'Acquire observation with solar azimuth within 30 degrees of reference to potentially reduce illumination-induced uncertainty.',
      warning: 'Active observation recommendations are autonomous decision-support proposals, NOT spacecraft tasking, orbital scheduling, or mission commands.'
    },
    limitations: [
      'Physically unsupported under the tested conditions. Does not represent a "wrong lunar feature" classification.',
      'Visual similarity != physical correspondence.',
      'Controlled synthetic demonstration only.'
    ]
  },
  {
    scenario_id: 'SCENARIO-D',
    scenario_name: 'Permanently Shadowed Region (PSR) Low-Evidence Control',
    scenario_type: 'UNKNOWN_INSUFFICIENT_EVIDENCE',
    real_or_synthetic: 'SYNTHETIC',
    is_synthetic: true,
    source_observation: 'OBS-UNKNOWN-001',
    target_observation: 'OBS-UNKNOWN-002',
    correspondence_id: 'CORR-OBS-UNKNOWN-001-OBS-UNKNOWN-002',
    candidate_count: 2,
    candidate_count_notes: 'CURRENT DEMONSTRATION INSTANCE: 2 visual keypoint candidates extracted in deep shadow region; minimum 4 required.',
    geometric_result: 'INSUFFICIENT_FEATURES (N=2 < 4 candidates; cannot construct geometric hypothesis)',
    physical_result: 'EVALUATION_INCOMPLETE (Insufficient visual candidates to construct geometric homography; decision unforced)',
    gate_metrics_notes: 'GATE METRICS DISTINCTION: Keypoint count = 2; UNKNOWN != NEGATIVE.',
    evidence_state: {
      GEOMETRIC: { status: 'INSUFFICIENT', confidence: 0.05, description: 'Only 2 keypoints detected' },
      TERRAIN: { status: 'UNAVAILABLE', confidence: 0.0, description: 'DEM ray-casting cannot resolve without inlier tie points' },
      ILLUMINATION: { status: 'DEEP_SHADOW', confidence: 0.10, description: 'PSR extreme shadow with SNR < 3 dB' },
      SPECTRAL: { status: 'UNAVAILABLE', confidence: 0.0, description: 'No multi-band coverage' },
      SCALE: { status: 'NOMINAL', confidence: 0.50, description: 'Matched scale but zero SNR' },
      TEMPORAL: { status: 'UNAVAILABLE', confidence: 0.0, description: 'Temporal baseline uninformative under shadow' },
      TEXTURE: { status: 'DEGRADED', confidence: 0.05, description: 'Near-zero gradient variance in shadowed floor' },
      REGISTRATION: { status: 'HALTED', confidence: 0.0, description: 'Registration requires valid geometric seed' },
      PHYSICAL: { status: 'UNRESOLVED', confidence: 0.0, description: 'Physical gates unreached due to lack of candidate hypothesis' },
      MANUAL: { status: 'UNAVAILABLE', confidence: 0.0, description: 'No manual inspection available' },
      SYNTHETIC: { status: 'SIMULATED_PSR', confidence: 1.0, description: 'Synthetic PSR shadow simulation' }
    },
    uncertainty_state: {
      scalar_uncertainty: 1.0,
      epistemic_uncertainty: 1.0,
      aleatoric_uncertainty: 0.80,
      qualitative_risk: 'HIGH_EPISTEMIC_RISK',
      status: 'UNKNOWN',
      confidence_interval: [0.0, 0.05],
      calibration_note: 'Maximum epistemic uncertainty: lack of evidence does NOT constitute negative evidence.'
    },
    knowledge_gap: {
      gap_id: 'GAP-PSR-EVIDENCE-001',
      gap_type: 'INSUFFICIENT_EVIDENCE',
      description: 'High noise floor and deep shadow in PSR region yields insufficient visual keypoints (N=2 < 4).',
      priority: 0.88
    },
    recommendation: {
      recommendation_id: 'REC-PSR-LIGHT-001',
      recommendation_type: 'POTENTIALLY_REDUCES_UNCERTAINTY',
      recommended_sensor: 'OHRC_SECONDARY_LIGHT',
      expected_information_gain: 0.82,
      description: 'Schedule high-sensitivity secondary scattered light observation to potentially reduce epistemic uncertainty.',
      warning: 'Active observation recommendations are autonomous decision-support proposals, NOT spacecraft tasking.'
    },
    limitations: [
      'UNKNOWN != NEGATIVE: Lack of evidence does not indicate absence of feature.',
      'Pipeline refrains from forcing an ungrounded binary decision.',
      'Controlled demonstration only.'
    ]
  },
  {
    scenario_id: 'SCENARIO-E',
    scenario_name: 'Cross-Modal Scale Disparity Knowledge Gap → Next-Best Observation',
    scenario_type: 'KNOWLEDGE_GAP_NBO',
    real_or_synthetic: 'SYNTHETIC',
    is_synthetic: true,
    source_observation: 'OBS-OHRC-001',
    target_observation: 'OBS-TMC2-001',
    correspondence_id: 'CORR-OBS-OHRC-001-OBS-TMC2-001',
    candidate_count: 8,
    candidate_count_notes: 'CURRENT DEMONSTRATION INSTANCE: 8 candidate matches formed across 20x cross-scale disparity.',
    geometric_result: 'AMBIGUOUS_SCALE_MATCH (8 candidate matches; scale disparity 20x prevents stable sub-pixel consensus)',
    physical_result: 'UNCERTAIN (Scale disparity limits direct physical gate validation; triggers knowledge gap and autonomous recommendation)',
    gate_metrics_notes: 'GATE METRICS DISTINCTION: Cross-band registration requires intermediate scale bridging observation.',
    evidence_state: {
      GEOMETRIC: { status: 'AMBIGUOUS', confidence: 0.45, description: '8 keypoints detected across 20x scale step' },
      TERRAIN: { status: 'EVALUATED', confidence: 0.50, description: 'DEM resolution gap bounds elevation comparison' },
      ILLUMINATION: { status: 'CONSISTENT', confidence: 0.70, description: 'Simulated similar solar zenith' },
      SPECTRAL: { status: 'CROSS_BAND', confidence: 0.30, description: 'OHRC panchromatic vs TMC-2 stereo' },
      SCALE: { status: 'HIGH_DISPARITY', confidence: 0.15, description: '0.25 m/px vs 5.0 m/px (20x resolution gap)' },
      TEMPORAL: { status: 'EVALUATED', confidence: 0.60, description: 'Nominal temporal separation' },
      TEXTURE: { status: 'LIMITING', confidence: 0.40, description: 'Coarse TMC-2 pixel size averages fine OHRC texture' },
      REGISTRATION: { status: 'AMBIGUOUS', confidence: 0.30, description: 'ECC optimizer saturates on scale boundary' },
      PHYSICAL: { status: 'UNRESOLVED', confidence: 0.35, description: 'Scale step exceeds single-stage physical tolerance' },
      MANUAL: { status: 'UNAVAILABLE', confidence: 0.0, description: 'No manual ground truth' },
      SYNTHETIC: { status: 'CONTROLLED_SCALE_GAP', confidence: 1.0, description: 'Controlled synthetic scale step experiment' }
    },
    uncertainty_state: {
      scalar_uncertainty: 0.75,
      epistemic_uncertainty: 0.70,
      aleatoric_uncertainty: 0.35,
      qualitative_risk: 'MODERATE_EPISTEMIC_RISK',
      status: 'UNCERTAIN',
      confidence_interval: [0.15, 0.35],
      calibration_note: 'High scale disparity induces epistemic uncertainty requiring multi-scale bridging.'
    },
    knowledge_gap: {
      gap_id: 'GAP-SCALE-DISPARITY-001',
      gap_type: 'SCALE_GAP',
      description: '20x scale step (0.25 m/px to 5.0 m/px) creates resolution boundary beyond single-pass registration bounds.',
      priority: 0.80
    },
    recommendation: {
      recommendation_id: 'REC-SCALE-BRIDGE-001',
      recommendation_type: 'POTENTIALLY_REDUCES_UNCERTAINTY',
      recommended_sensor: 'IIRS_INTERMEDIATE_SCALE',
      expected_information_gain: 0.75,
      description: 'Acquire intermediate resolution (1.0-2.0 m/px) observation to potentially bridge scale gap between OHRC and TMC-2.',
      warning: 'Active observation recommendations are autonomous decision-support proposals, NOT spacecraft tasking.'
    },
    limitations: [
      'Scale gap exceeds direct single-stage physical gate bounds.',
      'Triggers autonomous knowledge gap instantiation.',
      'Controlled demonstration scenario.'
    ]
  }
];

export const ScenariosLab: React.FC = () => {
  const [scenarios, setScenarios] = useState<DemonstrationScenario[]>(CANONICAL_SCENARIOS_FALLBACK);
  const [activeScenarioId, setActiveScenarioId] = useState<string>('SCENARIO-A');
  const [viewMode, setViewMode] = useState<'DETAIL' | 'COMPARISON'>('DETAIL');
  const [loading, setLoading] = useState<boolean>(false);
  const [activeExplanation, setActiveExplanation] = useState<ScenarioExplanation | null>(null);
  const [explainingLoading, setExplainingLoading] = useState<boolean>(false);

  const handleExplain = async (scenarioId: string) => {
    try {
      setExplainingLoading(true);
      const exp = await api.getScenarioExplanation(scenarioId);
      setActiveExplanation(exp);
    } catch (err) {
      console.warn('API getScenarioExplanation failed, checking local data:', err);
    } finally {
      setExplainingLoading(false);
    }
  };

  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        setLoading(true);
        const data = await api.getScenarios();
        if (data && data.length > 0) {
          setScenarios(data);
        }
      } catch (err) {
        console.warn('API scenarios fetch fallback to canonical defaults:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchScenarios();
  }, []);

  const activeScenario = scenarios.find((s) => s.scenario_id === activeScenarioId) || scenarios[0];

  return (
    <div className="space-y-6 font-sans max-w-6xl mx-auto pb-12">
      {/* Hero Banner */}
      <div className="bg-white p-6 rounded-2xl text-slate-900 shadow-sm relative overflow-hidden border border-slate-200">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] uppercase font-black px-3 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300 tracking-wider">
                DEMONSTRATION SUITE
              </span>
              <span className="text-xs text-slate-700 font-extrabold">ISRO Canonical Scenarios</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-[#0d2247] mt-1.5 tracking-tight">
              Scientific Demonstration Scenarios
            </h1>
            <p className="text-xs text-slate-900 font-bold mt-1">
              Controlled comparative evaluation separating Real Flight Lunar Data from Synthetic Controlled Testbeds.
            </p>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <button
              onClick={() => setViewMode('DETAIL')}
              className={`px-4 py-2.5 rounded-xl text-xs font-black transition-all border ${
                viewMode === 'DETAIL'
                  ? 'bg-blue-700 text-white border-blue-800 shadow-sm'
                  : 'bg-slate-100 text-slate-800 border-slate-300 hover:bg-slate-200'
              }`}
            >
              Scenario Inspection
            </button>
            <button
              onClick={() => setViewMode('COMPARISON')}
              className={`px-4 py-2.5 rounded-xl text-xs font-black transition-all border ${
                viewMode === 'COMPARISON'
                  ? 'bg-blue-700 text-white border-blue-800 shadow-sm'
                  : 'bg-slate-100 text-slate-800 border-slate-300 hover:bg-slate-200'
              }`}
            >
              Scenario Comparison Matrix
            </button>
          </div>
        </div>

        {/* Axiom Banner */}
        <div className="mt-5 p-3.5 rounded-xl bg-amber-50/80 border border-amber-300 flex items-center justify-between text-xs font-bold">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0" />
            <span className="text-amber-950 font-black">CORE SCIENTIFIC AXIOM:</span>
            <span className="text-slate-900 font-bold">VISUAL SIMILARITY ≠ PHYSICAL CORRESPONDENCE</span>
          </div>
          <div className="hidden lg:flex items-center space-x-4 text-[11px] text-slate-800 font-extrabold">
            <span>ENTITY ASSOCIATION ≠ DIRECT IMAGE CORRESPONDENCE</span>
            <span>•</span>
            <span>UNKNOWN ≠ NEGATIVE</span>
          </div>
        </div>
      </div>

      {/* Scenario Selector Tabs - Clean Light Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {scenarios.map((sc) => {
          const isSelected = sc.scenario_id === activeScenarioId;
          const isReal = !sc.is_synthetic;
          return (
            <button
              key={sc.scenario_id}
              onClick={() => {
                setActiveScenarioId(sc.scenario_id);
                setViewMode('DETAIL');
              }}
              className={`p-4 rounded-2xl text-left border transition-all ${
                isSelected
                  ? 'bg-white border-blue-600 shadow-md ring-2 ring-blue-500/20'
                  : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300 shadow-sm'
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-bold mb-1.5">
                <span className={isSelected ? 'text-blue-700 font-extrabold' : 'text-slate-500'}>{sc.scenario_id}</span>
                <span
                  className={`px-2 py-0.5 rounded-full text-[9px] uppercase font-extrabold border ${
                    isReal
                      ? 'bg-amber-100 text-amber-800 border-amber-200'
                      : 'bg-purple-100 text-purple-800 border-purple-200'
                  }`}
                >
                  {isReal ? 'REAL LUNAR' : 'SYNTHETIC'}
                </span>
              </div>
              <div className="text-xs font-bold truncate text-slate-800">{sc.scenario_name}</div>
              <div className="text-[10px] text-slate-500 mt-1 truncate font-medium">
                {sc.candidate_count} Candidates | {sc.physical_result.includes('REJECTED') ? 'Rejected' : sc.physical_result.includes('VERIFIED') ? 'Verified' : 'Uncertain'}
              </div>
            </button>
          );
        })}
      </div>

      {/* VIEW MODE: COMPARISON MATRIX */}
      {viewMode === 'COMPARISON' && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-800 flex items-center space-x-2">
              <Compass className="w-5 h-5 text-blue-600" />
              <span>Canonical Demonstration Scenario Comparison</span>
            </h2>
            <span className="text-xs text-slate-500 font-medium">5 Scenarios Evaluated</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 text-[10px] uppercase font-bold bg-slate-50">
                  <th className="p-3.5">Scenario</th>
                  <th className="p-3.5">Data Provenance</th>
                  <th className="p-3.5">Observation Pair</th>
                  <th className="p-3.5">Visual Candidates</th>
                  <th className="p-3.5">Physical Result</th>
                  <th className="p-3.5">Uncertainty State</th>
                  <th className="p-3.5">Scientific Meaning</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {scenarios.map((sc) => {
                  const isReal = !sc.is_synthetic;
                  return (
                    <tr key={sc.scenario_id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-3.5 font-bold text-slate-800">
                        <div>{sc.scenario_name}</div>
                        <span className="text-[10px] text-slate-400 font-normal">{sc.scenario_id}</span>
                      </td>
                      <td className="p-3.5">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-bold border inline-block ${
                            isReal
                              ? 'bg-amber-50 text-amber-800 border-amber-200'
                              : 'bg-purple-50 text-purple-800 border-purple-200'
                          }`}
                        >
                          {isReal ? 'REAL LUNAR DATA' : 'SYNTHETIC CONTROL'}
                        </span>
                      </td>
                      <td className="p-3.5 text-[11px] text-slate-600 max-w-[200px] truncate">
                        <div>Src: {sc.source_observation}</div>
                        <div>Tgt: {sc.target_observation}</div>
                      </td>
                      <td className="p-3.5 font-bold text-blue-700">
                        {sc.candidate_count}
                      </td>
                      <td className="p-3.5">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-bold border inline-block ${
                            sc.physical_result.includes('REJECTED')
                              ? 'bg-rose-50 text-rose-800 border-rose-200'
                              : sc.physical_result.includes('VERIFIED')
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                              : 'bg-amber-50 text-amber-800 border-amber-200'
                          }`}
                        >
                          {sc.physical_result.includes('REJECTED')
                            ? 'REJECTED'
                            : sc.physical_result.includes('VERIFIED')
                            ? 'VERIFIED'
                            : 'UNCERTAIN'}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <div className="text-slate-800 font-bold">U = {sc.uncertainty_state.scalar_uncertainty.toFixed(2)}</div>
                        <div className="text-[10px] text-slate-500">{sc.uncertainty_state.qualitative_risk}</div>
                      </td>
                      <td className="p-3.5 text-slate-600 max-w-[250px] leading-relaxed">
                        {sc.scenario_id === 'SCENARIO-A' &&
                          'Physical geometry incompatible (~1.49-2.04 km separation); correspondence not validated.'}
                        {sc.scenario_id === 'SCENARIO-B' &&
                          'Controlled synthetic homography; all 6 gates pass.'}
                        {sc.scenario_id === 'SCENARIO-C' &&
                          '180° illumination divergence; candidate rejected under illumination contradiction.'}
                        {sc.scenario_id === 'SCENARIO-D' &&
                          'Low SNR shadow boundary; N < 4 candidates; UNKNOWN != NEGATIVE.'}
                        {sc.scenario_id === 'SCENARIO-E' &&
                          '20x scale step triggers SCALE_GAP and autonomous recommendation.'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* VIEW MODE: DETAIL INSPECTION */}
      {viewMode === 'DETAIL' && (
        <div className="space-y-6">
          {/* Active Scenario Card Header */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
              <div>
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] uppercase font-extrabold border ${
                      !activeScenario.is_synthetic
                        ? 'bg-amber-100 text-amber-800 border-amber-200'
                        : 'bg-purple-100 text-purple-800 border-purple-200'
                    }`}
                  >
                    {!activeScenario.is_synthetic ? 'REAL LUNAR DATA' : 'SYNTHETIC CONTROLLED DATA'}
                  </span>
                  <span className="text-xs text-slate-500 font-bold">{activeScenario.scenario_id}</span>
                </div>
                <h2 className="text-2xl font-extrabold text-[#0d2247] mt-1.5 tracking-tight">
                  {activeScenario.scenario_name}
                </h2>
                <div className="text-xs text-slate-500 mt-1 font-medium">
                  Type: <span className="text-slate-800 font-bold">{activeScenario.scenario_type}</span>
                </div>
              </div>

              {/* Status Pill & Explain Button */}
              <div className="flex flex-col items-start md:items-end gap-2">
                <span
                  className={`px-3 py-1.5 rounded-full text-xs font-bold border ${
                    activeScenario.physical_result.includes('REJECTED')
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : activeScenario.physical_result.includes('VERIFIED')
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200'
                  }`}
                >
                  {activeScenario.physical_result.includes('REJECTED')
                    ? 'PHYSICAL REJECTION'
                    : activeScenario.physical_result.includes('VERIFIED')
                    ? 'PHYSICALLY VERIFIED'
                    : 'UNCERTAIN / UNKNOWN'}
                </span>
                <span className="text-[11px] text-slate-500 font-medium">
                  Scalar Uncertainty: {activeScenario.uncertainty_state.scalar_uncertainty.toFixed(2)}
                </span>
                <button
                  id="btn-explain-decision"
                  onClick={() => handleExplain(activeScenario.scenario_id)}
                  disabled={explainingLoading}
                  className="px-4 py-2 rounded-xl bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 text-xs font-bold transition-all flex items-center space-x-1.5 shadow-sm mt-1"
                >
                  <HelpCircle className="w-4 h-4 text-blue-600" />
                  <span>{explainingLoading ? 'ANALYZING...' : 'WHY THIS RESULT? (EXPLAIN DECISION)'}</span>
                </button>
              </div>
            </div>

            {/* Scientific Narrative & Flow Card (Light Clean White Theme) */}
            {activeScenario.scenario_id === 'SCENARIO-A' && (
              <div className="p-5 rounded-2xl bg-amber-50/60 border border-amber-200 space-y-3">
                <div className="text-xs font-bold text-amber-900 uppercase tracking-wide">
                  SCENARIO A EXECUTION FLOW (REAL NEGATIVE CONTROL):
                </div>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="px-3 py-1 rounded-xl bg-white border border-amber-200 text-slate-800 font-bold shadow-sm">
                    OHRC Swath
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-amber-600" />
                  <span className="px-3 py-1 rounded-xl bg-white border border-amber-200 text-slate-800 font-bold shadow-sm">
                    26 Visual Candidates
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-amber-600" />
                  <span className="px-3 py-1 rounded-xl bg-white border border-amber-200 text-slate-800 font-bold shadow-sm">
                    GroundGrid / DEM Geometry
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-amber-600" />
                  <span className="px-3 py-1 rounded-xl bg-rose-100 border border-rose-300 text-rose-800 font-extrabold shadow-sm">
                    GATE 3 & GATE 4
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-amber-600" />
                  <span className="px-3 py-1 rounded-xl bg-rose-100 border border-rose-300 text-rose-800 font-extrabold shadow-sm">
                    FOOTPRINT NON-OVERLAP (~1.49 - 2.04 km)
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-amber-600" />
                  <span className="px-3 py-1 rounded-xl bg-rose-600 text-white font-extrabold shadow-md">
                    NOT PHYSICALLY VALIDATED
                  </span>
                </div>
                <p className="text-xs text-amber-950 leading-relaxed font-medium pt-1">
                  The evaluated physical geometry does not support correspondence for this pair. Visual candidates form an initial hypothesis, but pushbroom ground grids place the target footprints ~1.49 km – 2.04 km apart.
                </p>
              </div>
            )}

            {activeScenario.scenario_id === 'SCENARIO-B' && (
              <div className="p-5 rounded-2xl bg-emerald-50/60 border border-emerald-200 space-y-3">
                <div className="text-xs font-bold text-emerald-900 uppercase tracking-wide">
                  SCENARIO B EXECUTION FLOW (CONTROLLED SYNTHETIC POSITIVE):
                </div>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="px-3 py-1 rounded-xl bg-white border border-emerald-200 text-slate-800 font-bold shadow-sm">
                    Synthetic OHRC Pair
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="px-3 py-1 rounded-xl bg-white border border-emerald-200 text-slate-800 font-bold shadow-sm">
                    184 Visual Candidates
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="px-3 py-1 rounded-xl bg-emerald-100 border border-emerald-300 text-emerald-800 font-extrabold shadow-sm">
                    168 Inliers (91.3%)
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="px-3 py-1 rounded-xl bg-emerald-600 text-white font-extrabold shadow-md">
                    ALL 6 PHYSICAL GATES PASSED
                  </span>
                </div>
              </div>
            )}

            {activeScenario.scenario_id === 'SCENARIO-C' && (
              <div className="p-5 rounded-2xl bg-purple-50/60 border border-purple-200 space-y-3">
                <div className="text-xs font-bold text-purple-900 uppercase tracking-wide">
                  SCENARIO C EXECUTION FLOW (ILLUMINATION CONTRADICTION):
                </div>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="px-3 py-1 rounded-xl bg-white border border-purple-200 text-slate-800 font-bold shadow-sm">
                    180° Solar Azimuth Divergence
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-purple-600" />
                  <span className="px-3 py-1 rounded-xl bg-white border border-purple-200 text-slate-800 font-bold shadow-sm">
                    45 Visual Candidates
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-purple-600" />
                  <span className="px-3 py-1 rounded-xl bg-rose-100 border border-rose-300 text-rose-800 font-extrabold shadow-sm">
                    Illumination Verification (180° Divergence)
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-purple-600" />
                  <span className="px-3 py-1 rounded-xl bg-rose-600 text-white font-extrabold shadow-md">
                    PHYSICALLY UNSUPPORTED
                  </span>
                </div>
              </div>
            )}

            {/* Metadata Pair Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <span className="text-[10px] text-slate-500 uppercase font-bold block">
                  OBSERVATION PAIR
                </span>
                <div className="space-y-1 font-mono text-[11px]">
                  <div>
                    <span className="text-slate-400 font-bold">Source:</span>{' '}
                    <span className="text-slate-800 font-bold break-all">{activeScenario.source_observation}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 font-bold">Target:</span>{' '}
                    <span className="text-slate-800 font-bold break-all">{activeScenario.target_observation}</span>
                  </div>
                </div>
              </div>

              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <span className="text-[10px] text-slate-500 uppercase font-bold block">
                  FEATURE & GEOMETRIC CONSISTENCY
                </span>
                <div className="space-y-1 text-xs">
                  <div>
                    <span className="text-slate-500 font-medium">Visual Candidates:</span>{' '}
                    <span className="text-blue-700 font-extrabold text-sm">{activeScenario.candidate_count}</span>
                  </div>
                  {activeScenario.candidate_count_notes && (
                    <div className="text-[11px] text-slate-600 leading-snug">
                      {activeScenario.candidate_count_notes}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 11 Evidence Dimensions Grid */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase font-bold text-slate-700">
                  11 Dimensional Scientific Evidence Ledger
                </span>
                <span className="text-[10px] text-slate-400 font-medium">
                  Missing dimensions remain uninstantiated (Never converted to negative)
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5 text-xs">
                {Object.entries(activeScenario.evidence_state).map(([dimension, detail]) => {
                  const isAvailable = detail.confidence > 0;
                  const isRejected = detail.status === 'REJECTED' || detail.status === 'INCOMPATIBLE';
                  return (
                    <div
                      key={dimension}
                      className={`p-3 rounded-xl border text-left ${
                        isRejected
                          ? 'bg-rose-50 border-rose-200 text-rose-800'
                          : isAvailable
                          ? 'bg-blue-50 border-blue-200 text-blue-900'
                          : 'bg-slate-50 border-slate-200 text-slate-400'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] font-bold">
                        <span>{dimension}</span>
                        <span>{detail.confidence > 0 ? (detail.confidence * 100).toFixed(0) + '%' : 'N/A'}</span>
                      </div>
                      <div className="text-[10px] font-extrabold mt-0.5 truncate">{detail.status}</div>
                      <div className="text-[10px] opacity-80 mt-1 line-clamp-2 leading-tight font-medium">
                        {detail.description}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Uncertainty Profile */}
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold text-slate-500">
                  Epistemic Uncertainty Breakdown
                </span>
                <span className="text-[10px] text-amber-700 font-bold bg-amber-100 px-2.5 py-0.5 rounded-full border border-amber-200">
                  {activeScenario.uncertainty_state.calibration_note || 'CALIBRATION STATUS'}
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-sm">
                  <div className="text-[10px] text-slate-500 font-bold uppercase">Scalar UQ</div>
                  <div className="text-lg font-extrabold text-blue-700 mt-0.5">
                    {activeScenario.uncertainty_state.scalar_uncertainty.toFixed(2)}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-sm">
                  <div className="text-[10px] text-slate-500 font-bold uppercase">Epistemic Risk</div>
                  <div className="text-xs font-bold text-amber-700 mt-1">
                    {activeScenario.uncertainty_state.qualitative_risk}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-sm">
                  <div className="text-[10px] text-slate-500 font-bold uppercase">State</div>
                  <div className="text-xs font-bold text-slate-800 mt-1">
                    {activeScenario.uncertainty_state.status}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-sm">
                  <div className="text-[10px] text-slate-500 font-bold uppercase">Confidence Interval</div>
                  <div className="text-xs font-bold text-slate-800 mt-1 font-mono">
                    {activeScenario.uncertainty_state.confidence_interval
                      ? `[${activeScenario.uncertainty_state.confidence_interval[0]}, ${activeScenario.uncertainty_state.confidence_interval[1]}]`
                      : 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Phase 8.5 Explainability & Provenance Modal */}
      {activeExplanation && (
        <ExplainabilityModal
          explanation={activeExplanation}
          onClose={() => setActiveExplanation(null)}
        />
      )}
    </div>
  );
};
