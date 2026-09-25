import React, { useState, useEffect, useCallback } from 'react';
import { TopHeader } from './components/TopHeader';
import { Sidebar, PageId } from './components/Sidebar';
import { LoginPage } from './components/LoginPage';
import { MissionOverview } from './pages/MissionOverview';
import { ObservationWorkspace } from './pages/ObservationWorkspace';
import { CorrespondenceAnalysis } from './pages/CorrespondenceAnalysis';
import { PhysicalVerificationPage } from './pages/PhysicalVerificationPage';
import { EvidenceDashboard } from './pages/EvidenceDashboard';
import { UncertaintyView } from './pages/UncertaintyView';
import { EntityGraph } from './pages/EntityGraph';
import { KnowledgeGaps } from './pages/KnowledgeGaps';
import { NextObservation } from './pages/NextObservation';
import { SystemStatusPage } from './pages/SystemStatusPage';
import { PresentationMode } from './pages/PresentationMode';
import { RegistrationLab } from './pages/RegistrationLab';
import { EntityExplorer } from './pages/EntityExplorer';
import { StressLab } from './pages/StressLab';
import { RedTeam } from './pages/RedTeam';
import { ScenariosLab } from './pages/ScenariosLab';
import {
  Observation,
  Correspondence,
  LunarEntity,
  KnowledgeGap,
  Recommendation,
  SystemHealth,
  SystemStatus,
} from './types';
import { api } from './services/api';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<{ id: string; role: string } | null>(null);
  const [currentPage, setCurrentPage] = useState<PageId>('overview');
  const [dataMode, setDataMode] = useState<'ALL' | 'REAL' | 'SYNTHETIC'>('ALL');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [correspondences, setCorrespondences] = useState<Correspondence[]>([]);
  const [entities, setEntities] = useState<LunarEntity[]>([]);
  const [gaps, setGaps] = useState<KnowledgeGap[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [topRec, setTopRec] = useState<Recommendation | null>(null);
  const [isRunningDemo, setIsRunningDemo] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    try {
      const [h, sysStatus] = await Promise.allSettled([
        api.getHealth(),
        api.getSystemStatus(),
      ]);
      if (h.status === 'fulfilled') setHealth(h.value);
      if (sysStatus.status === 'fulfilled') setSystemStatus(sysStatus.value);
    } catch (err) {
      console.error('System health/status fetch failed', err);
    }

    try {
      const [obs, corrs, ents, gp, recs] = await Promise.allSettled([
        api.getObservations(),
        api.getCorrespondences(),
        api.getEntities(),
        api.getKnowledgeGaps(),
        api.getRecommendations(),
      ]);

      if (obs.status === 'fulfilled') setObservations(obs.value);
      if (corrs.status === 'fulfilled') setCorrespondences(corrs.value);
      if (ents.status === 'fulfilled') setEntities(ents.value);
      if (gp.status === 'fulfilled') setGaps(gp.value);
      if (recs.status === 'fulfilled') {
        setRecommendations(recs.value);
        if (recs.value.length > 0) {
          setTopRec(recs.value[0]);
        }
      }

      if (ents.status === 'fulfilled' && ents.value.length > 0 && recs.status !== 'fulfilled') {
        try {
          const rec = await api.getNextObservation(ents.value[0].entity_id, 'spectral analysis');
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
    if (currentUser) {
      loadData();
    }
  }, [currentUser, loadData]);

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

  // If user is not logged in, display the ISRO Official LoginPage
  if (!currentUser) {
    return <LoginPage onLoginSuccess={(user) => setCurrentUser(user)} />;
  }

  // Filter observations and correspondences based on global data mode filter
  const displayedObservations = observations.filter((obs) => {
    if (dataMode === 'REAL') return !obs.is_synthetic;
    if (dataMode === 'SYNTHETIC') return obs.is_synthetic;
    return true;
  });

  const displayedCorrespondences = correspondences.filter((corr) => {
    if (dataMode === 'REAL') return !corr.is_synthetic;
    if (dataMode === 'SYNTHETIC') return corr.is_synthetic;
    return true;
  });

  return (
    <div className="min-h-screen bg-white text-slate-900 flex flex-col font-sans selection:bg-space-cyan selection:text-lunar-950">
      {/* Top Header */}
      <TopHeader
        health={health}
        systemStatus={systemStatus}
        dataMode={dataMode}
        onChangeDataMode={setDataMode}
        isRunningDemo={isRunningDemo}
        onRunDemo={handleRunDemoMission}
        onLaunchPresentation={() => setCurrentPage('presentation')}
        currentUser={currentUser}
        onLogout={() => setCurrentUser(null)}
      />


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
              observations={displayedObservations}
              correspondences={displayedCorrespondences}
              entities={entities}
              gaps={gaps}
              topRec={topRec}
              onNavigate={setCurrentPage}
              onRunDemo={handleRunDemoMission}
              isRunningDemo={isRunningDemo}
            />
          )}

          {currentPage === 'scenarios' && <ScenariosLab />}

          {currentPage === 'presentation' && (
            <PresentationMode
              observations={observations}
              correspondences={correspondences}
              entities={entities}
              gaps={gaps}
              recommendations={recommendations}
              onNavigatePage={setCurrentPage}
            />
          )}

          {currentPage === 'observations' && (
            <ObservationWorkspace observations={displayedObservations} />
          )}

          {currentPage === 'correspondence' && (
            <CorrespondenceAnalysis
              correspondences={displayedCorrespondences}
              observations={observations}
              onRefresh={loadData}
              onNavigateToGates={() => setCurrentPage('physical-verification')}
              onNavigateToEvidence={() => setCurrentPage('evidence')}
              onNavigateToGraph={() => setCurrentPage('graph')}
            />
          )}

          {currentPage === 'physical-verification' && (
            <PhysicalVerificationPage correspondences={correspondences} />
          )}

          {currentPage === 'evidence' && (
            <EvidenceDashboard correspondences={correspondences} />
          )}

          {currentPage === 'uncertainty' && (
            <UncertaintyView correspondences={correspondences} />
          )}

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

          {currentPage === 'system-status' && <SystemStatusPage />}

          {currentPage === 'registration' && (
            <RegistrationLab
              correspondences={correspondences}
              observations={observations}
            />
          )}

          {currentPage === 'entities' && <EntityExplorer entities={entities} />}

          {currentPage === 'stress' && <StressLab />}

          {currentPage === 'redteam' && <RedTeam />}
        </main>
      </div>
    </div>
  );
};
