import { Panel } from '../components/dashboard/Panel';
import { RiskTrend } from '../components/dashboard/RiskTrend';
import { ClockIcon } from '../components/icons/Icons';
import { formatPercent, formatShortDate, formatTime, normalizeAlertLevel, tierColor, tierEmoji, tierLabel } from '../lib/format';
import type { RiskHistoryPoint } from '../types/risk';
import styles from './HistoryPage.module.css';

interface HistoryPageProps {
  points: RiskHistoryPoint[];
  loading: boolean;
}

export function HistoryPage({ points, loading }: HistoryPageProps) {
  const ordered = [...points].reverse();

  return (
    <div className={styles.wrap}>
      <div className={styles.pageHead}>
        <span className={styles.eyebrow}>Prediction history</span>
        <h1 className={styles.heading}>Mean risk over past observation passes</h1>
        <p className={styles.lede}>
          Every entry is a real inference run — either the scheduled background refresh or a
          manually triggered one — recorded with the same alert level shown live on the dashboard.
        </p>
      </div>

      {loading ? (
        <div className={styles.skeleton} />
      ) : points.length === 0 ? (
        <div className={styles.empty}>
          <p>No prediction runs recorded yet.</p>
        </div>
      ) : (
        <>
          <Panel icon={<ClockIcon />} title="Trend" subtitle={`${points.length} readings`} span="full">
            <RiskTrend points={points} variant="full" />
          </Panel>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Prediction</th>
                  <th>Mean risk</th>
                  <th>Alert level</th>
                </tr>
              </thead>
              <tbody>
                {ordered.map((point) => {
                  const tier = normalizeAlertLevel(point.alertLevel);
                  return (
                    <tr key={point.predictionId}>
                      <td>
                        <span className={styles.timestamp}>
                          {formatShortDate(point.predictionTimestamp)} · {formatTime(point.predictionTimestamp)}
                        </span>
                        <span className={styles.predictionId}>{point.predictionId}</span>
                      </td>
                      <td className={styles.mean}>{formatPercent(point.mean)}</td>
                      <td>
                        <span className={styles.alertBadge} style={{ color: tierColor(tier), borderColor: tierColor(tier) }}>
                          {tierEmoji(tier)} {tierLabel(tier)}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
