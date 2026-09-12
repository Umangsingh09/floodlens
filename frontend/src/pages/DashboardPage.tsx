import { RiskMapPlaceholder } from '../components/map/RiskMapPlaceholder';
import styles from './DashboardPage.module.css';

function MetricCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <article className={styles.metricCard}>
      <span className={styles.metricLabel}>{label}</span>
      <strong className={styles.metricValue}>{value}</strong>
    </article>
  );
}

export function DashboardPage() {
  return (
    <div className={styles.page}>
      <header className={styles.hero}>
        <div>
          <p className={styles.eyebrow}>Monitoring overview</p>
          <h1>Flood Risk Dashboard</h1>
        </div>
      </header>

      <section className={styles.metricsGrid} aria-label="Risk summary metrics">
        <MetricCard label="Overall Risk" value="N/A" />
        <MetricCard label="High-Risk Area" value="Awaiting model" />
        <MetricCard label="Active Alerts" value="Not available" />
        <MetricCard label="Latest Satellite Pass" value="N/A" />
      </section>

      <section className={styles.primaryGrid}>
        <div className={styles.mapPanel}>
          <div className={styles.panelHeader}>
            <h2>Flood Risk Map</h2>
            <span className={styles.panelTag}>FloodLens study region</span>
          </div>
          <RiskMapPlaceholder />
        </div>

        <aside className={styles.summaryPanel}>
          <div className={styles.panelHeader}>
            <h2>Risk Summary</h2>
          </div>

          <dl className={styles.summaryList}>
            <div className={styles.summaryRow}>
              <dt>Current Risk Status</dt>
              <dd>N/A</dd>
            </div>
            <div className={styles.summaryRow}>
              <dt>Risk Score</dt>
              <dd>Awaiting backend</dd>
            </div>
            <div className={styles.summaryRow}>
              <dt>Prediction Time</dt>
              <dd>N/A</dd>
            </div>
            <div className={styles.summaryRow}>
              <dt>Satellite Acquisition</dt>
              <dd>N/A</dd>
            </div>
            <div className={styles.summaryRow}>
              <dt>Prediction Lag</dt>
              <dd>Awaiting backend</dd>
            </div>
            <div className={styles.summaryRow}>
              <dt>Model Status</dt>
              <dd>Awaiting backend</dd>
            </div>
          </dl>
        </aside>
      </section>

      <section className={styles.infoGrid}>
        <article className={styles.infoCard}>
          <h3>Historical Flood Validation</h3>
          <p className={styles.eventName}>2017 Bihar–Nepal Flood</p>
          <p className={styles.eventStatus}>Validation pending</p>
        </article>

        <article className={styles.infoCard}>
          <h3>Data Sources</h3>
          <ul className={styles.sourceList}>
            <li>Sentinel-1 SAR</li>
            <li>Digital Elevation Model</li>
            <li>Bihar–Southern Nepal study region</li>
          </ul>
        </article>
      </section>
    </div>
  );
}
