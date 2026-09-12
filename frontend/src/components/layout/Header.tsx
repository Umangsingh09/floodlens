import { formatRelativeTime } from '../../lib/format';
import type { RegionInfo } from '../../types/region';
import type { RiskSnapshot } from '../../types/risk';
import styles from './Header.module.css';

interface HeaderProps {
  region: RegionInfo | null;
  risk: RiskSnapshot | null;
  refreshing: boolean;
  onRefresh: () => void;
}

function Mark() {
  return (
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none" aria-hidden="true">
      <circle cx="15" cy="15" r="13.5" stroke="currentColor" strokeOpacity="0.25" />
      <circle cx="15" cy="15" r="9" stroke="currentColor" strokeOpacity="0.5" />
      <circle cx="15" cy="15" r="3.2" fill="currentColor" />
      <path d="M15 1.5V6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

export function Header({ region, risk, refreshing, onRefresh }: HeaderProps) {
  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <span className={styles.mark}>
          <Mark />
        </span>
        <div className={styles.brandText}>
          <span className={styles.name}>FloodLens</span>
          <span className={styles.region}>{region?.aoiName ?? 'Bihar flood corridor'}</span>
        </div>
      </div>

      <div className={styles.actions}>
        <span className={styles.synced}>
          {risk ? `Synced ${formatRelativeTime(risk.predictionTimestamp)}` : ' '}
        </span>
        <button
          type="button"
          className={styles.refreshButton}
          onClick={onRefresh}
          disabled={refreshing}
          aria-label="Run a new observation pass"
          data-busy={refreshing}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path
              d="M13.5 8a5.5 5.5 0 1 1-1.6-3.87M13.5 2.5v3h-3"
              stroke="currentColor"
              strokeWidth="1.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>
    </header>
  );
}
