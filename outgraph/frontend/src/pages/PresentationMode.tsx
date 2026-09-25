import React, { useState } from 'react';
import {
  Play,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Sparkles,
  Layers,
  Activity,
  Globe,
  Target,
  RefreshCw,
} from 'lucide-react';
import { Observation, Correspondence, LunarEntity, KnowledgeGap, Recommendation } from '../types';
import { RealNegativeControlPanel } from '../components/RealNegativeControlPanel';
import { SyntheticPositiveControlPanel } from '../components/SyntheticPositiveControlPanel';

interface PresentationModeProps {
  observations: Observation[];
  correspondences: Correspondence[];
  entities: LunarEntity[];
  gaps: KnowledgeGap[];
  recommendations: Recommendation[];
  onNavigatePage: (pageId: any) => void;
}

export const PresentationMode: React.FC<PresentationModeProps> = ({
  observations,
  correspondences,
  entities,
  gaps,
  recommendations,
  onNavigatePage,
}) => {
  const [currentStep, setCurrentStep] = useState<number>(1);

  const realCorr = correspondences.find((c) => !c.is_synthetic);
  const synthCorr = correspondences.find((c) => c.is_synthetic && c.status === 'ACCEPTED');

  const totalSteps = 6;

  return (
    <div className="space-y-6 font-sans max-w-5xl mx-auto">
      {/* Presentation Header */}
      <div className="bg-white p-6 rounded-3xl text-slate-900 shadow-sm border border-slate-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] uppercase font-extrabold px-3 py-1 rounded-full bg-blue-100 text-blue-900 border border-blue-300 tracking-wider">
                SIH 26166 EVALUATION FLOW
              </span>
              <span className="text-xs text-slate-700 font-extrabold">Step {currentStep} of {totalSteps}</span>
            </div>
            <h1 className="text-2xl font-black text-[#0d2247] mt-1.5 tracking-tight">
              Scientific Jury Presentation Mode
            </h1>
            <p className="text-xs text-slate-900 font-bold mt-1">
              Deterministic evidence-grounded walkthrough comparing Real Lunar Negative Control vs Synthetic Positive Control.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentStep((s) => Math.max(1, s - 1))}
              disabled={currentStep === 1}
              className={`p-2.5 rounded-xl border text-xs font-extrabold transition-all ${
                currentStep === 1
                  ? 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed'
                  : 'bg-slate-100 text-slate-900 border-slate-300 hover:bg-slate-200'
              }`}
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentStep((s) => Math.min(totalSteps, s + 1))}
              disabled={currentStep === totalSteps}
              className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl border text-xs font-black transition-all ${
                currentStep === totalSteps
                  ? 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed'
                  : 'bg-sky-400 hover:bg-sky-500 text-slate-950 border-sky-500 shadow-md active:scale-95'
              }`}
            >
              <span>Next Stage</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Step Progression Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mt-5 text-center text-[10px] font-bold">
          {[
            '1. Mission Overview',
            '2. Real Negative Control',
            '3. Six Kinematic Gates',
            '4. Evidence & UQ Axiom',
            '5. Synthetic Testbed',
            '6. Final Ledger',
          ].map((title, idx) => {
            const stepNum = idx + 1;
            const isCompleted = stepNum < currentStep;
            const isCurrent = stepNum === currentStep;

            return (
              <button
                key={idx}
                onClick={() => setCurrentStep(stepNum)}
                className={`py-2 px-2 rounded-xl transition-all truncate border font-black ${
                  isCurrent
                    ? 'bg-sky-400 text-slate-950 border-sky-500 shadow-md'
                    : isCompleted
                    ? 'bg-emerald-100 border-emerald-400 text-emerald-950'
                    : 'bg-slate-100 border-slate-300 text-slate-800 hover:bg-slate-200'
                }`}
              >
                {title}
              </button>
            );
          })}
        </div>
      </div>

      {/* STEP 1: Problem Statement & Scientific Baseline */}
      {currentStep === 1 && (
        <div className="space-y-4">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-lg font-extrabold text-[#0d2247] flex items-center space-x-2">
              <Globe className="w-5 h-5 text-blue-600" />
              <span>SIH 26166: Core Scientific Challenge & LunarSynapse Thesis</span>
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-5 rounded-2xl bg-amber-50/70 border border-amber-300 space-y-2.5">
                <span className="text-[10px] text-amber-900 font-extrabold block uppercase tracking-wide">
                  THE DANGEROUS PITFALL IN COMPUTER VISION
                </span>
                <p className="text-slate-900 font-bold leading-relaxed">
                  Deep feature matchers (SIFT, ORB, SuperPoint, LoFTR) routinely produce confident candidate matches on identical repetitive craters even when the underlying image footprints are hundreds of kilometers apart.
                </p>
                <div className="p-3 rounded-xl bg-rose-100 border border-rose-300 text-rose-950 text-[11px] font-extrabold">
                  Naive AI: Visual Similarity ➔ Incorrectly Flags as Confirmed Match
                </div>
              </div>

              <div className="p-5 rounded-2xl bg-emerald-50/70 border border-emerald-300 space-y-2.5">
                <span className="text-[10px] text-emerald-900 font-extrabold block uppercase tracking-wide">
                  THE LUNARSYNAPSE PHYSICS-AWARE PARADIGM
                </span>
                <p className="text-slate-900 font-bold leading-relaxed">
                  Every candidate correspondence is merely a hypothesis. Before entering the World Model memory, it must satisfy rigorous pushbroom GroundGrid rays, SLDEM2015 topography, and non-clamping geometric bounds.
                </p>
                <div className="p-3 rounded-xl bg-emerald-100 border border-emerald-300 text-emerald-950 text-[11px] font-extrabold">
                  LunarSynapse: Visual Match + Rigorous Physics ➔ Grounded Epistemic Decision
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setCurrentStep(2)}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-700 hover:bg-blue-800 text-white font-extrabold text-xs shadow-md transition-all active:scale-95"
              >
                <span>Proceed to Real Lunar Negative Control</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: Real Lunar Negative Control */}
      {currentStep === 2 && (
        <div className="space-y-4">
          <RealNegativeControlPanel
            correspondence={realCorr}
            observations={observations}
            onNavigateToGates={() => setCurrentStep(3)}
            onNavigateToGaps={() => onNavigatePage('knowledge')}
          />
        </div>
      )}

      {/* STEP 3: Six Kinematic Gates Demonstration */}
      {currentStep === 3 && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <span className="text-[10px] uppercase font-extrabold text-blue-700">STEP 3 EVIDENCE TRACE</span>
              <h2 className="text-lg font-extrabold text-[#0d2247]">Six-Gate Physical Verification Execution</h2>
            </div>
            <span className="text-xs px-3 py-1 rounded-full bg-rose-100 text-rose-900 border border-rose-300 font-extrabold">
              GATE 3 & GATE 4 HALT FALSE MATCH
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-bold">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] text-slate-500 block font-extrabold uppercase">GATE 1: GROUNDGRID</span>
              <span className="text-emerald-700 font-extrabold">PASS</span>
              <p className="text-[11px] text-slate-700 font-medium">Valid SPICE pushbroom trajectory found.</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] text-slate-500 block font-extrabold uppercase">GATE 2: SLDEM2015</span>
              <span className="text-emerald-700 font-extrabold">PASS</span>
              <p className="text-[11px] text-slate-700 font-medium">Topography tiles within valid range.</p>
            </div>

            <div className="p-4 rounded-xl bg-rose-50 border border-rose-300 space-y-1">
              <span className="text-[10px] text-rose-900 block font-extrabold uppercase">GATE 3: SWATH OVERLAP</span>
              <span className="text-rose-700 font-extrabold">REJECTED</span>
              <p className="text-[11px] text-rose-950 font-semibold">
                Footprints separated by ~1.49 km - 2.04 km. No overlap.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-rose-50 border border-rose-300 space-y-1">
              <span className="text-[10px] text-rose-900 block font-extrabold uppercase">GATE 4: CLAMPING CHECK</span>
              <span className="text-rose-700 font-extrabold">REJECTED</span>
              <p className="text-[11px] text-rose-950 font-semibold">
                18 projected points artificially clamped to edge.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] text-slate-500 block font-extrabold uppercase">GATE 5: ELEVATION CORRIDOR</span>
              <span className="text-slate-600 font-extrabold">NOT EVALUATED</span>
              <p className="text-[11px] text-slate-500 font-medium">Evaluation short-circuited at Gate 3/4.</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] text-slate-500 block font-extrabold uppercase">GATE 6: RAY RESIDUAL</span>
              <span className="text-slate-600 font-extrabold">NOT EVALUATED</span>
              <p className="text-[11px] text-slate-500 font-medium">Evaluation short-circuited at Gate 3/4.</p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 font-semibold leading-relaxed">
            <strong className="text-[#0d2247] font-extrabold">Deterministic Safety Property: </strong>
            Visual matches are never allowed to bypass physical verification. The real Chandrayaan-2 OHRC vs TMC-2 negative control is preserved as physically rejected without forced matching.
          </div>

          <div className="flex justify-between items-center pt-2">
            <button
              onClick={() => setCurrentStep(2)}
              className="px-4 py-2 rounded-xl bg-slate-100 text-slate-800 border border-slate-300 text-xs font-bold hover:bg-slate-200"
            >
              Back
            </button>
            <button
              onClick={() => setCurrentStep(4)}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-700 hover:bg-blue-800 text-white font-extrabold text-xs shadow-md transition-all active:scale-95"
            >
              <span>Next: Evidence & Uncertainty Axioms</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: Evidence & Uncertainty Guardrails */}
      {currentStep === 4 && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
          <div className="border-b border-slate-100 pb-3">
            <span className="text-[10px] uppercase font-extrabold text-blue-700">STEP 4 SCIENTIFIC INTEGRITY</span>
            <h2 className="text-lg font-extrabold text-[#0d2247]">Epistemic Uncertainty & Evidence Guardrails</h2>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-4 rounded-2xl bg-blue-50/70 border border-blue-200 flex items-start space-x-3">
              <CheckCircle2 className="w-5 h-5 text-blue-700 shrink-0 mt-0.5" />
              <div>
                <span className="font-extrabold text-blue-950 text-sm block">AXIOM 1: UNKNOWN ≠ NEGATIVE</span>
                <p className="text-slate-900 font-semibold mt-1 leading-relaxed">
                  Missing sensor modalities (e.g. unobserved IIRS hyperspectral bands) are represented as unknown values, not penalized as negative evidence.
                </p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-300 flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
              <div>
                <span className="font-extrabold text-amber-950 text-sm block">AXIOM 2: REAL-LUNAR CALIBRATION DISCLAIMER</span>
                <p className="text-slate-900 font-semibold mt-1 leading-relaxed">
                  Real-lunar empirical uncertainty calibration is not established. Dispersion saturates deterministically above &gt;4 px.
                </p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-purple-50/70 border border-purple-200 flex items-start space-x-3">
              <Globe className="w-5 h-5 text-purple-700 shrink-0 mt-0.5" />
              <div>
                <span className="font-extrabold text-purple-950 text-sm block">AXIOM 3: WORLD MODEL RELATIONAL INTEGRITY</span>
                <p className="text-slate-900 font-semibold mt-1 leading-relaxed">
                  Entity Association ≠ Direct Image Correspondence. Spatial proximity ≠ Entity Identity. Failed correspondence ≠ Negative entity evidence.
                </p>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center pt-2">
            <button
              onClick={() => setCurrentStep(3)}
              className="px-4 py-2 rounded-xl bg-slate-100 text-slate-800 border border-slate-300 text-xs font-bold hover:bg-slate-200"
            >
              Back
            </button>
            <button
              onClick={() => setCurrentStep(5)}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-700 hover:bg-blue-800 text-white font-extrabold text-xs shadow-md transition-all active:scale-95"
            >
              <span>Next: Synthetic Controlled Positive Case</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: Synthetic Controlled Positive Case */}
      {currentStep === 5 && (
        <div className="space-y-4">
          <SyntheticPositiveControlPanel
            correspondence={synthCorr}
            observations={observations}
            onNavigateToEvidence={() => onNavigatePage('evidence')}
            onNavigateToGraph={() => onNavigatePage('graph')}
          />
        </div>
      )}

      {/* STEP 6: Final SIH Conclusion & Ledger */}
      {currentStep === 6 && (
        <div className="bg-white p-6 rounded-2xl border border-emerald-300 shadow-sm space-y-5">
          <div className="border-b border-slate-100 pb-3">
            <span className="text-[10px] uppercase font-extrabold text-emerald-800">DEMONSTRATION COMPLETE</span>
            <h2 className="text-lg font-extrabold text-[#0d2247]">SIH 26166 Scientific Demonstration Summary</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-bold">
            <div className="p-5 rounded-2xl bg-emerald-50/60 border border-emerald-200 space-y-2.5">
              <span className="text-[10px] text-emerald-900 font-extrabold block uppercase">WHAT LUNARSYNAPSE PROVED</span>
              <ul className="space-y-2 text-slate-900">
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0" />
                  <span>Physics verification prevents false correspondences deterministically.</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0" />
                  <span>Real Chandrayaan-2 negative control correctly rejected at Gate 3.</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0" />
                  <span>Knowledge gap engine triggers uncertainty-reducing observation plans.</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0" />
                  <span>Raw real data modified: strictly 0 bytes.</span>
                </li>
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-amber-50/60 border border-amber-200 space-y-2.5">
              <span className="text-[10px] text-amber-900 font-extrabold block uppercase">WHAT LUNARSYNAPSE DOES NOT CLAIM</span>
              <ul className="space-y-2 text-slate-900">
                <li className="flex items-center space-x-2">
                  <XCircle className="w-4 h-4 text-amber-700 shrink-0" />
                  <span>No claim of universal invariance across arbitrary sun angles or scales.</span>
                </li>
                <li className="flex items-center space-x-2">
                  <XCircle className="w-4 h-4 text-amber-700 shrink-0" />
                  <span>No claim that synthetic positive validation establishes real-lunar accuracy.</span>
                </li>
                <li className="flex items-center space-x-2">
                  <XCircle className="w-4 h-4 text-amber-700 shrink-0" />
                  <span>No real-time spacecraft tasking or orbital mechanics simulated.</span>
                </li>
                <li className="flex items-center space-x-2">
                  <XCircle className="w-4 h-4 text-amber-700 shrink-0" />
                  <span>Real-lunar empirical uncertainty calibration is not established.</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="flex justify-between items-center pt-2">
            <button
              onClick={() => setCurrentStep(1)}
              className="px-4 py-2 rounded-xl bg-slate-100 text-slate-800 border border-slate-300 text-xs font-bold hover:bg-slate-200"
            >
              Restart Presentation Tour
            </button>
            <button
              onClick={() => onNavigatePage('overview')}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-700 hover:bg-blue-800 text-white font-extrabold text-xs shadow-md transition-all active:scale-95"
            >
              <span>Return to Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

