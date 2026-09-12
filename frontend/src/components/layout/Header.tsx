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
      <div className={styles.brand}>
        <span className={styles.logo}>FloodLens</span>
        <span className={styles.tagline}>Flood-risk intelligence — Bihar</span>
      </div>
      <div className={styles.status} data-state={backendState}>
        <span className={styles.dot} />
        {STATUS_LABEL[backendState]}
      </div>
    </header>
  );
}
