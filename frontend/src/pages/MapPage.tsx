import { Panel } from '../components/dashboard/Panel';
import { StatTile } from '../components/dashboard/StatTile';
import { GridIcon } from '../components/icons/Icons';
import { RiskMap } from '../components/map/RiskMap';
import { ALERT_LABELS, formatDuration, formatShortDate, formatTime } from '../lib/format';
import type { RegionInfo } from '../types/region';
import type { RiskSnapshot } from '../types/risk';
import styles from './MapPage.module.css';

interface MapPageProps {
  region: RegionInfo | null;
  risk: RiskSnapshot | null;
  regionLoading: boolean;
  riskLoading: boolean;
}

export function MapPage({ region, risk, regionLoading, riskLoading }: MapPageProps) {
  if (regionLoading || riskLoading) {
    return (
      <div className={styles.page}>
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
        <span className={styles.eyebrow}>Risk map</span>
        <h1 className={styles.heading}>Spatial flood risk across {region.aoiName}</h1>
        <p className={styles.lede}>
          {risk
            ? `Observed via ${risk.satellite} at ${formatShortDate(risk.sourcePassTimestamp)} · ${formatTime(
                risk.sourcePassTimestamp,
              )}, aggregated to a ${risk.resolutionMeters}m grid. Scroll to zoom, drag to pan.`
            : 'No observation pass has been run yet, so the risk overlay below is empty — this is the base region only, not a placeholder prediction.'}
        </p>
      </div>

      {risk && (
        <Panel icon={<GridIcon />} title="At a glance" subtitle="current prediction snapshot">
          <div className={styles.metaRow}>
            <StatTile label="Alert level" value={ALERT_LABELS[risk.alert.level] ?? risk.alert.level} />
            <StatTile label="Processing lag" value={formatDuration(risk.processingLagSeconds)} />
            <StatTile label="Outlook" value={`${Math.round(risk.predictionHorizonHours / 24)}d`} />
            <StatTile label="Grid resolution" value={`${risk.resolutionMeters}m`} />
          </div>
        </Panel>
      )}

      <RiskMap region={region} risk={risk} variant="full" />

      {!risk && (
        <p className={styles.muted}>
          The risk overlay will appear here once a live observation pass has been run — use the
          refresh control in the header, or check back after the next scheduled pass.
        </p>
      )}
    </div>
  );
}
