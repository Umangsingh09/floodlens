import { ObservationWindow } from '../components/dashboard/ObservationWindow';
import { Panel } from '../components/dashboard/Panel';
import { PipelineSteps } from '../components/dashboard/PipelineSteps';
import { RiskGauge } from '../components/dashboard/RiskGauge';
import { RiskTrend } from '../components/dashboard/RiskTrend';
import { StatTile } from '../components/dashboard/StatTile';
import { SummaryCards } from '../components/dashboard/SummaryCards';
import { ClockIcon, GridIcon, SatelliteIcon, TrendIcon } from '../components/icons/Icons';
import { RiskMap } from '../components/map/RiskMap';
import { useRiskGrid } from '../hooks/useRiskGrid';
import { useRiskHistory } from '../hooks/useRiskHistory';
import { formatPercent } from '../lib/format';
import type { HistoricalEvent } from '../types/events';
import type { RegionInfo } from '../types/region';
import type { RiskSnapshot } from '../types/risk';
import styles from './DashboardPage.module.css';

interface DashboardPageProps {
  region: RegionInfo | null;
  risk: RiskSnapshot | null;
  regionLoading: boolean;
  riskLoading: boolean;
  events: HistoricalEvent[];
  eventsLoading: boolean;
}

export function DashboardPage({ region, risk, regionLoading, riskLoading, events, eventsLoading }: DashboardPageProps) {
  const { points: history } = useRiskHistory(risk?.predictionId);
  const { grid, loading: gridLoading } = useRiskGrid(risk?.gridUrl);

  if (regionLoading || riskLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.skeletonHero} />
        <div className={styles.skeletonMap} />
      </div>
    );
  }

  if (!region) {
    return (
      <div className={styles.empty}>
        <p>Region configuration is unavailable right now.</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.pageHead}>
        <span className={styles.eyebrow}>
          {risk ? `${Math.round(risk.predictionHorizonHours / 24)}-day outlook` : 'Spatial outlook'}
        </span>
        <h1 className={styles.heading}>Where flood risk is elevated across {region.aoiName}</h1>
        <p className={styles.lede}>
          Derived from Sentinel-1 radar backscatter change and terrain features, aggregated to a{' '}
          {risk?.resolutionMeters ?? 250}m grid.
        </p>
      </div>

      <SummaryCards
        risk={risk}
        grid={grid}
        gridLoading={gridLoading}
        eventCount={events.length}
        eventsLoading={eventsLoading}
      />

      {risk ? (
        <>
          <div className={styles.grid}>
            <Panel icon={<TrendIcon />} title="Mean risk" subtitle={`peak cell ${formatPercent(risk.risk.max)}`}>
              <div className={styles.gaugeRow}>
                <RiskGauge value={risk.risk.mean} alertLevel={risk.alert.level} />
                <div className={styles.gaugeStats}>
                  <StatTile label="Outlook" value={`${Math.round(risk.predictionHorizonHours / 24)}d`} />
                  <StatTile label="Grid" value={`${risk.resolutionMeters}m`} />
                </div>
              </div>
            </Panel>

            <Panel
              icon={<SatelliteIcon />}
              title="Observation window"
              subtitle="most recent Sentinel-1 passes"
            >
              {risk.observationWindowScenes && risk.observationWindowScenes.length > 0 ? (
                <ObservationWindow scenes={risk.observationWindowScenes} />
              ) : (
                <p className={styles.muted}>No scene metadata recorded for this pass.</p>
              )}
            </Panel>

            <Panel icon={<ClockIcon />} title="Recent readings" subtitle="mean risk per observation">
              <RiskTrend points={history} />
            </Panel>
          </div>

          <Panel icon={<GridIcon />} title="Spatial risk map" subtitle={region.aoiName} span="full">
            <RiskMap region={region} risk={risk} />
          </Panel>

          <Panel title="From satellite pass to prediction" span="full">
            <PipelineSteps risk={risk} />
          </Panel>

          <div className={styles.caption}>
            <span>{risk.satellite}</span>
            <span>·</span>
            <span>{region.satelliteCollection}</span>
            <span>·</span>
            <span>model {risk.modelVersion}</span>
          </div>
        </>
      ) : (
        <Panel title="Spatial risk map" subtitle={region.aoiName} span="full">
          <RiskMap region={region} risk={null} />
        </Panel>
      )}
    </div>
  );
}
