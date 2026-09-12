import { useHealthCheck } from '../../hooks/useHealthCheck';
import styles from './Header.module.css';

const STATUS_LABEL: Record<string, string> = {
  checking: 'Checking backend…',
  online: 'Backend online',
  offline: 'Backend offline',
};

export function Header() {
  const backendState = useHealthCheck();

  return (
    <header className={styles.header}>
      <div className={styles.brandBlock}>
        <div className={styles.logoWrap} aria-label="FloodLens logo">
          <span className={styles.logoMark}>FL</span>
        </div>
        <div className={styles.brandText}>
          <span className={styles.logo}>FloodLens</span>
          <span className={styles.tagline}>Flood Risk Intelligence</span>
        </div>
      </div>

      <div className={styles.meta}>
        <span className={styles.regionBadge}>Bihar–Southern Nepal</span>
        <div className={styles.status} data-state={backendState}>
          <span className={styles.dot} />
          {STATUS_LABEL[backendState]}
        </div>
      </div>
    </header>
  );
}
