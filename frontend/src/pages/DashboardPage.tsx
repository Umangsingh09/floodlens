import { RiskMapPlaceholder } from '../components/map/RiskMapPlaceholder';
import styles from './DashboardPage.module.css';

export function DashboardPage() {
  return (
    <div className={styles.page}>
      <section className={styles.summary}>
        <h1>Dashboard</h1>
        <p className={styles.description}>
          FloodLens will surface spatial flood-risk predictions for a
          flood-prone region of Bihar. This dashboard is a structural
          placeholder — no satellite data, model, or predictions are
          connected yet.
        </p>
      </section>

      <section className={styles.mapSection}>
        <h2>Flood Risk Map</h2>
        <RiskMapPlaceholder />
      </section>
    </div>
  );
}
