import React, { useState, useEffect, useCallback } from 'react';
import { TopHeader } from './components/TopHeader';
import { Sidebar, PageId } from './components/Sidebar';
import { DisclaimerBanner } from './components/DisclaimerBanner';
import { MissionOverview } from './pages/MissionOverview';
import { ObservationWorkspace } from './pages/ObservationWorkspace';
import { CorrespondenceAnalysis } from './pages/CorrespondenceAnalysis';
import { RegistrationLab } from './pages/RegistrationLab';
import { EntityExplorer } from './pages/EntityExplorer';
import { EntityGraph } from './pages/EntityGraph';
import { KnowledgeGaps } from './pages/KnowledgeGaps';
import { NextObservation } from './pages/NextObservation';
import { StressLab } from './pages/StressLab';
import { RedTeam } from './pages/RedTeam';
import {
  Observation,
  Correspondence,
  LunarEntity,
  KnowledgeGap,
  Recommendation,
  SystemHealth,
} from './types';
import { api } from './services/api';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('overview');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [correspondences, setCorrespondences] = useState<Correspondence[]>([]);
  const [entities, setEntities] = useState<LunarEntity[]>([]);
  const [gaps, setGaps] = useState<KnowledgeGap[]>([]);
  const [topRec, setTopRec] = useState<Recommendation | null>(null);
  const [isRunningDemo, setIsRunningDemo] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    try {
      const h = await api.getHealth();
      setHealth(h);
    } catch (err) {
      console.error('Health check failed', err);
    }

    try {
      const obs = await api.getObservations();
      setObservations(obs);

      const corrs = await api.getCorrespondences();
      setCorrespondences(corrs);

      const ents = await api.getEntities();
      setEntities(ents);

      const gp = await api.getKnowledgeGaps();
      setGaps(gp);

      if (ents.length > 0) {
        try {
          const rec = await api.getNextObservation(ents[0].entity_id, 'spectral analysis');
          setTopRec(rec);
        } catch (rErr) {
          console.error(rErr);
        }
      }
    } catch (err) {
      console.error('Failed to load mission data', err);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRunDemoMission = async () => {
    setIsRunningDemo(true);
    try {
      await api.runDemoMission();
      await loadData();
    } catch (err) {
      console.error('Demo mission execution failed', err);
    } finally {
      setIsRunningDemo(false);
    }
  };

  return (
    <div className="min-h-screen bg-lunar-950 text-lunar-100 flex flex-col font-sans selection:bg-space-cyan selection:text-lunar-950">
      {/* Top Header */}
      <TopHeader
        health={health}
        isRunningDemo={isRunningDemo}
        onRunDemo={handleRunDemoMission}
      />

      {/* Scientific Honesty Disclaimer Banner */}
      <DisclaimerBanner />

      {/* Main Workspace Layout */}
      <div className="flex flex-1">
        {/* Left Sidebar Navigation */}
        <Sidebar
          currentPage={currentPage}
          onSelectPage={setCurrentPage}
          entityCount={entities.length}
          gapCount={gaps.length}
        />

        {/* Dynamic Page Viewport */}
        <main className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full overflow-y-auto">
          {currentPage === 'overview' && (
            <MissionOverview
              observations={observations}
              correspondences={correspondences}
              entities={entities}
              gaps={gaps}
              topRec={topRec}
              onNavigate={setCurrentPage}
              onRunDemo={handleRunDemoMission}
              isRunningDemo={isRunningDemo}
            />
          )}

          {currentPage === 'observations' && (
            <ObservationWorkspace observations={observations} />
          )}

          {currentPage === 'correspondence' && (
            <CorrespondenceAnalysis
              correspondences={correspondences}
              observations={observations}
              onRefresh={loadData}
            />
          )}

          {currentPage === 'registration' && (
            <RegistrationLab
              correspondences={correspondences}
              observations={observations}
            />
          )}

          {currentPage === 'entities' && <EntityExplorer entities={entities} />}

          {currentPage === 'graph' && <EntityGraph />}

          {currentPage === 'knowledge' && (
            <KnowledgeGaps
              gaps={gaps}
              onNavigateToRecommendation={() => setCurrentPage('recommendations')}
            />
          )}

          {currentPage === 'recommendations' && (
            <NextObservation entities={entities} />
          )}

          {currentPage === 'stress' && <StressLab />}

          {currentPage === 'redteam' && <RedTeam />}
        </main>
      </div>
    </div>
  );
};
