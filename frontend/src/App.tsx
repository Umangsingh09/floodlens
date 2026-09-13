import { useState } from 'react';
import { ErrorBanner } from './components/layout/ErrorBanner';
import { Header } from './components/layout/Header';
import { TabNav, type TabKey } from './components/layout/TabNav';
import { useEvents } from './hooks/useEvents';
import { useLatestRisk } from './hooks/useLatestRisk';
import { useRegion } from './hooks/useRegion';
import { useRiskHistory } from './hooks/useRiskHistory';
import { AppLayout } from './layouts/AppLayout';
import { AboutPage } from './pages/AboutPage';
import { DashboardPage } from './pages/DashboardPage';
import { EventsPage } from './pages/EventsPage';
import { HistoryPage } from './pages/HistoryPage';
import { MapPage } from './pages/MapPage';

function App() {
  const [tab, setTab] = useState<TabKey>('dashboard');
  const { region, loading: regionLoading } = useRegion();
  const { risk, loading: riskLoading, error: riskError, refreshing, refresh } = useLatestRisk();
  const { events, loading: eventsLoading } = useEvents();
  const { points: historyPoints, loading: historyLoading } = useRiskHistory(risk?.predictionId, 50);

  return (
    <AppLayout
      header={<Header region={region} risk={risk} refreshing={refreshing} onRefresh={refresh} />}
      tabs={<TabNav active={tab} onChange={setTab} />}
    >
      {riskError && <ErrorBanner message={riskError} />}

      {tab === 'dashboard' && (
        <DashboardPage
          region={region}
          risk={risk}
          regionLoading={regionLoading}
          riskLoading={riskLoading}
          events={events}
          eventsLoading={eventsLoading}
        />
      )}
      {tab === 'map' && (
        <MapPage region={region} risk={risk} regionLoading={regionLoading} riskLoading={riskLoading} />
      )}
      {tab === 'events' && <EventsPage events={events} loading={eventsLoading} />}
      {tab === 'history' && <HistoryPage points={historyPoints} loading={historyLoading} />}
      {tab === 'about' && <AboutPage region={region} risk={risk} events={events} />}
    </AppLayout>
  );
}

export default App;
