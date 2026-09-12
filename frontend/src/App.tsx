import { useState } from 'react';
import { Header } from './components/layout/Header';
import { TabNav, type TabKey } from './components/layout/TabNav';
import { useEvents } from './hooks/useEvents';
import { useLatestRisk } from './hooks/useLatestRisk';
import { useRegion } from './hooks/useRegion';
import { AppLayout } from './layouts/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { HistoryPage } from './pages/HistoryPage';

function App() {
  const [tab, setTab] = useState<TabKey>('overview');
  const { region, loading: regionLoading } = useRegion();
  const { risk, loading: riskLoading, refreshing, refresh } = useLatestRisk();
  const { events, loading: eventsLoading } = useEvents();

  return (
    <AppLayout
      header={<Header region={region} risk={risk} refreshing={refreshing} onRefresh={refresh} />}
      tabs={<TabNav active={tab} onChange={setTab} />}
    >
      {tab === 'overview' ? (
        <DashboardPage region={region} risk={risk} regionLoading={regionLoading} riskLoading={riskLoading} />
      ) : (
        <HistoryPage events={events} loading={eventsLoading} />
      )}
    </AppLayout>
  );
}

export default App;
